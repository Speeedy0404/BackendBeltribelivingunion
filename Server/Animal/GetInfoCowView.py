from rest_framework import status
from django.db.models import Subquery
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import GetCowAnimalSerializer
from ..models import BookBreeds, PK, PKBull, Farms, Parentage, BookBranches


def build_tree_info(uniq_key, level=2):
    """Функция строит дерево предков до заданного уровня и возвращает данные в виде словаря"""
    tree = {}

    def recurse(key, current_level, relation=""):
        if current_level > level:
            return

        try:
            animal = Parentage.objects.get(uniq_key=key)
        except Parentage.DoesNotExist:
            return

        # Добавляем отца и мать в дерево с учетом уровня и отношения
        if animal.ukeyo:
            bull_name = PKBull.objects.filter(uniq_key=animal.ukeyo).values_list('klichka', flat=True).first()
            tree[f'{relation}O'] = f"{animal.ukeyo} ({bull_name})" if bull_name else animal.ukeyo
            recurse(animal.ukeyo, current_level + 1, relation=f'{relation}O ')
        if animal.ukeym:
            tree[f'{relation}M'] = animal.ukeym
            recurse(animal.ukeym, current_level + 1, relation=f'{relation}M ')

    recurse(uniq_key, 1)

    return tree


def safe_get(data, key, default=0):
    value = data.get(key)
    if value is None:
        return default
    return value


class GetInfoCowView(APIView):
    def post(self, request):
        search = request.query_params.get('uniq_key', None)
        if not search:
            return Response({"error": "Uniqkey not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            queryset = PK.objects.filter(
                uniq_key=search
            ).select_related(
                'milkproductionindex', 'conformationindex', 'reproductionindex',
                'somaticcellindex', 'complexindex',
            ).order_by('id')

            if not queryset.exists():
                return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)

            serializer = GetCowAnimalSerializer(queryset, many=True)
            cow_data = serializer.data

            tree = build_tree_info(search)

            por = BookBreeds.objects.filter(
                breed_code=queryset.first().por
            ).values_list('breed_name', flat=True)

            branch = BookBranches.objects.filter(
                branch_code=queryset.first().vet
            ).values_list('branch_name', flat=True)
            kompleks = queryset.first().kompleks
            lin = queryset.first().lin.abbreviated_branch_name

            rojd = Farms.objects.filter(
                korg=Subquery(
                    PK.objects.filter(uniq_key=search).values('kodmestrojd')
                )
            ).values_list('norg', flat=True)

            info = {
                'uniq_key': cow_data[0].get('uniq_key', ''),
                'nomer': cow_data[0].get('nomer', ''),
                'datarojd': cow_data[0].get('datarojd', ''),
                'mestorojd': rojd.first() if hasattr(rojd, 'first') else '',
                'kompleks': kompleks if kompleks is not None else '',
                'branch': branch.first() if hasattr(branch, 'first') else '',
                'lin': lin if lin is not None else '',
                'por': por.first() if hasattr(por, 'first') else ''
            }
            parent = [
                {
                    'ped': 'father',
                    'klichka': tree.get('O', 'Нет данных').split('(')[1][0:-1] if '(' in
                                                                                  tree.get('O',
                                                                                           'Нет данных') else 'Нет данных',

                    'uniq_key': tree.get('O', 'Нет данных').split('(')[0][0:-1] if '(' in
                                                                                   tree.get('O',
                                                                                            'Нет данных') else tree.get(
                        'O', 'Нет данных')
                },
                {
                    'ped': 'mother',
                    'klichka': 'Нет клички',
                    'uniq_key': tree.get('M', 'Нет данных')
                },
                {
                    'ped': 'father of father',
                    'klichka': tree.get('O O', 'Нет данных').split('(')[1][0:-1] if '(' in
                                                                                    tree.get('O O',
                                                                                             'Нет данных') else 'Нет данных',
                    'uniq_key': tree.get('O O', 'Нет данных').split('(')[0][0:-1] if '(' in
                                                                                     tree.get('O O',
                                                                                              'Нет данных') else tree.get(
                        'O O', 'Нет данных')
                },
                {
                    'ped': 'mother of mother',
                    'klichka': 'Нет клички',
                    'uniq_key': tree.get('M M', 'Нет данных')
                },
                {
                    'ped': 'mother of father',
                    'klichka': 'Нет клички',
                    'uniq_key': tree.get('O M', 'Нет данных')
                },
                {
                    'ped': 'father of mother',
                    'klichka': tree.get('M O', 'Нет данных').split('(')[1][0:-1] if '(' in
                                                                                    tree.get('M O',
                                                                                             'Нет данных') else 'Нет данных',
                    'uniq_key': tree.get('M O', 'Нет данных').split('(')[0][0:-1] if '(' in
                                                                                     tree.get('M O',
                                                                                              'Нет данных') else tree.get(
                        'M O', 'Нет данных')
                },
            ]
            indices_cow = [
                {
                    'name': 'M kg',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'ebv_milk'), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rel_milk'), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rbv_milk'), 2)
                },
                {
                    'name': 'F kg',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'ebv_fkg'), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rel_fkg'), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rbv_fkg'), 2)
                },
                {
                    'name': 'F %',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'ebv_fprc'), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rel_fprc'), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rbv_fprc'), 2)
                },
                {
                    'name': 'P kg',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'ebv_pkg'), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rel_pkg'), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rbv_pkg'), 2)
                },
                {
                    'name': 'P %',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'ebv_pprc'), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rel_pprc'), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rbv_pprc'), 2)
                },
                {
                    'name': 'RM %',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('milkproductionindex', {}), 'rm'), 2)
                },
                {
                    'name': 'CRH',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'ebv_crh'), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rel_crh'), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rbv_crh'), 2)
                },
                {
                    'name': 'CTF',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'ebv_ctfi'), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rel_ctfi'), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rbv_ctfi'), 2)
                },
                {
                    'name': 'DO',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'ebv_do'), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rel_do'), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rbv_do'), 2)
                },
                {
                    'name': 'RF',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        safe_get(cow_data[0].get('reproductionindex', {}), 'rf'), 2)
                },
                {
                    'name': 'RSCS',
                    'evb': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        safe_get(cow_data[0].get('somaticcellindex', {}), 'ebv_scs'), 2),
                    'rel': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        safe_get(cow_data[0].get('somaticcellindex', {}), 'rel_scs'), 2),
                    'rbv': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        safe_get(cow_data[0].get('somaticcellindex', {}), 'rscs'), 2)
                },
                {
                    'name': 'RBVT',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        safe_get(cow_data[0].get('conformationindex', {}), 'rbvt'), 2)
                },
                {
                    'name': 'RBVF',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        safe_get(cow_data[0].get('conformationindex', {}), 'rbvf'), 2)
                },
                {
                    'name': 'RBVU',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        safe_get(cow_data[0].get('conformationindex', {}), 'rbvu'), 2)
                },
                {
                    'name': 'RC',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        safe_get(cow_data[0].get('conformationindex', {}), 'rc'), 2)
                },
                {
                    'name': 'PI',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('complexindex', {}) is None else round(
                        safe_get(cow_data[0].get('complexindex', {}), 'pi'), 2)
                },
            ]

            result_data = {
                'info': info,
                'parent': parent,
                'indices': indices_cow,
                'exterior_assessment': cow_data[0].get('conformationindex', {})
            }

            return Response(result_data, status=status.HTTP_200_OK)

        except PKBull.DoesNotExist:

            return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)
