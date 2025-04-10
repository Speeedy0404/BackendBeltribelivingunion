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
                        cow_data[0].get('milkproductionindex', {}).get('ebv_milk', 0), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rel_milk', 0), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rbv_milk', 0), 2)
                },
                {
                    'name': 'F kg',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('ebv_fkg', 0), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rel_fkg', 0), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rbv_fkg', 0), 2)
                },
                {
                    'name': 'F %',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('ebv_fprc', 0), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rel_fprc', 0), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rbv_fprc', 0), 2)
                },
                {
                    'name': 'P kg',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('ebv_pkg', 0), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rel_pkg', 0), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rbv_pkg', 0), 2)
                },
                {
                    'name': 'P %',
                    'evb': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('ebv_pprc', 0), 2),
                    'rel': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rel_pprc', 0), 2),
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rbv_pprc', 0), 2)
                },
                {
                    'name': 'RM %',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('milkproductionindex', {}) is None else round(
                        cow_data[0].get('milkproductionindex', {}).get('rm', 0), 2)
                },
                {
                    'name': 'CRH',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('ebv_crh', 0), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rel_crh', 0), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rbv_crh', 0), 2)
                },
                {
                    'name': 'CTF',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('ebv_ctfi', 0), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rel_ctfi', 0), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rbv_ctfi', 0), 2)
                },
                {
                    'name': 'DO',
                    'evb': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('ebv_do', 0), 2),
                    'rel': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rel_do', 0), 2),
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rbv_do', 0), 2)
                },
                {
                    'name': 'RF',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('reproductionindex', {}) is None else round(
                        cow_data[0].get('reproductionindex', {}).get('rf', 0), 2)
                },
                {
                    'name': 'RSCS',
                    'evb': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        cow_data[0].get('somaticcellindex', {}).get('ebv_scs', 0), 2),
                    'rel': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        cow_data[0].get('somaticcellindex', {}).get('rel_scs', 0), 2),
                    'rbv': 0 if cow_data[0].get('somaticcellindex', {}) is None else round(
                        cow_data[0].get('somaticcellindex', {}).get('rscs', 0), 2)
                },
                {
                    'name': 'RBVT',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        cow_data[0].get('conformationindex', {}).get('rbvt', 0), 2)
                },
                {
                    'name': 'RBVF',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        cow_data[0].get('conformationindex', {}).get('rbvf', 0), 2)
                },
                {
                    'name': 'RBVU',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        cow_data[0].get('conformationindex', {}).get('rbvu', 0), 2)
                },
                {
                    'name': 'RC',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('conformationindex', {}) is None else round(
                        cow_data[0].get('conformationindex', {}).get('rc', 0), 2)
                },
                {
                    'name': 'PI',
                    'evb': '',
                    'rel': '',
                    'rbv': 0 if cow_data[0].get('complexindex', {}) is None else round(
                        cow_data[0].get('complexindex', {}).get('pi', 0), 2)
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
