from rest_framework import status
from django.db.models import Subquery
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import GetAnimalSerializer
from ..models import BookBreeds, PKBull, Farms, Parentage, BookBranches


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


class GetInfoView(APIView):

    def post(self, request):
        search = self.request.headers.get('Uniqkey')

        if not search:
            return Response({"error": "Uniqkey not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            queryset = PKBull.objects.filter(
                uniq_key=search
            ).select_related(
                'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
                'somaticcellindexbull', 'complexindexbull', 'conformationindexdiagrambull'
            ).order_by('id')

            if not queryset.exists():
                return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)

            serializer = GetAnimalSerializer(queryset, many=True)
            bull_data = serializer.data

            tree = build_tree_info(search)

            por = BookBreeds.objects.filter(
                breed_code=Subquery(
                    PKBull.objects.filter(uniq_key=search).values('por')
                )
            ).values_list('breed_name', flat=True)

            rojd = Farms.objects.filter(
                korg=Subquery(
                    PKBull.objects.filter(uniq_key=search).values('kodmestrojd')
                )
            ).values_list('norg', flat=True)

            ovner = Farms.objects.filter(
                korg=Subquery(
                    PKBull.objects.filter(uniq_key=search).values('ovner')
                )
            ).values_list('norg', flat=True)

            branch = BookBranches.objects.filter(
                branch_code=Subquery(
                    PKBull.objects.filter(uniq_key=search).values('vet')
                )
            ).values_list('branch_name', flat=True)

            result_data = {
                'info': bull_data,
                'parent': tree,
                'por': por,
                'mestorojd': rojd,
                'ovner': ovner,
                'branch': branch
            }

            return Response(result_data, status=status.HTTP_200_OK)

        except PKBull.DoesNotExist:
            return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)
