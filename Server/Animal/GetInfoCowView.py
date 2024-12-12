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
        search = self.request.headers.get('Uniqkey')

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

            father = PKBull.objects.filter(
                uniq_key__in=Subquery(Parentage.objects.filter(uniq_key=search).values('ukeyo')))

            if father.exists():
                por = BookBreeds.objects.filter(
                    breed_code=father.first().por
                ).values_list('breed_name', flat=True)

                branch = BookBranches.objects.filter(
                    branch_code=father.first().vet
                ).values_list('branch_name', flat=True)
                kompleks = father.first().kompleks
                lin = father.first().lin.abbreviated_branch_name
            else:
                por = 'Не указан'
                branch = 'Не указан'
                lin = 'Не указан'
                kompleks = 'Не указан'

            rojd = Farms.objects.filter(
                korg=Subquery(
                    PK.objects.filter(uniq_key=search).values('kodmestrojd')
                )
            ).values_list('norg', flat=True)

            result_data = {
                'info': cow_data,
                'parent': tree,
                'mestorojd': rojd,
                'por': por,
                'lin': lin,
                'kompleks': kompleks,
                'branch': branch
            }

            return Response(result_data, status=status.HTTP_200_OK)

        except PKBull.DoesNotExist:
            return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)
