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


def safe_get(data, key, default=0):
    value = data.get(key)
    if value is None:
        return default
    return value


class GetInfoView(APIView):

    def post(self, request):
        search = request.query_params.get('uniq_key', None)
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

            info = {
                'uniq_key': bull_data[0].get('uniq_key', ''),
                'nomer': bull_data[0].get('nomer', ''),
                'klichka': bull_data[0].get('klichka', ''),
                'datarojd': bull_data[0].get('datarojd', ''),
                'mestorojd': rojd.first() if hasattr(rojd, 'first') else '',
                'ovner': ovner.first() if hasattr(ovner, 'first') else '',
                'kompleks': bull_data[0].get('kompleks', ''),
                'sperma': bull_data[0].get('sperma', ''),
                'branch': branch.first() if hasattr(branch, 'first') else '',
                'lin': bull_data[0].get('lin_name', ''),
                'por': por.first() if hasattr(por, 'first') else ''
            }
            parent = [
                {
                    'ped': 'father',
                    'klichka': tree.get('O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('O',
                                                                                                  '') else 'Нет данных',
                    'uniq_key': tree.get('O', 'Нет данных').split('(')[0] if '(' in tree.get('O', '') else tree.get('O',
                                                                                                                    'Нет данных')
                },
                {
                    'ped': 'mother',
                    'klichka': 'Нет клички',
                    'uniq_key': tree.get('M', 'Нет данных')
                },
                {
                    'ped': 'father of father',
                    'klichka': tree.get('O O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('O O',
                                                                                                    '') else 'Нет данных',
                    'uniq_key': tree.get('O O', 'Нет данных').split('(')[0] if '(' in tree.get('O O', '') else tree.get(
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
                    'klichka': tree.get('M O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('M O',
                                                                                                    '') else 'Нет данных',
                    'uniq_key': tree.get('M O', 'Нет данных').split('(')[0] if '(' in tree.get('M O', '') else tree.get(
                        'M O', 'Нет данных')
                }
            ]
            livestock = {
                1: 0 if bull_data[0].get('milkproductionindexbull') is None else bull_data[0].get(
                    'milkproductionindexbull', {}).get('num_daug_est', 0),
                4: 0 if bull_data[0].get('reproductionindexbull') is None else bull_data[0].get('reproductionindexbull',
                                                                                                {}).get('num_daug_est',
                                                                                                        0),
                7: 0 if bull_data[0].get('somaticcellindexbull') is None else bull_data[0].get('somaticcellindexbull',
                                                                                               {}).get('num_daug_est',
                                                                                                       0),
                0: 0 if bull_data[0].get('conformationindexbull') is None else bull_data[0].get('conformationindexbull',
                                                                                                {}).get('num_daug_est',
                                                                                                        0)
            }
            herd = {
                1: 0 if bull_data[0].get('milkproductionindexbull') is None else bull_data[0].get(
                    'milkproductionindexbull', {}).get('num_herd_est', 0),
                4: 0 if bull_data[0].get('reproductionindexbull') is None else bull_data[0].get('reproductionindexbull',
                                                                                                {}).get('num_herd_est',
                                                                                                        0),
                7: 0 if bull_data[0].get('somaticcellindexbull') is None else bull_data[0].get('somaticcellindexbull',
                                                                                               {}).get('num_herd_est',
                                                                                                       0),
                0: 0 if bull_data[0].get('conformationindexbull') is None else bull_data[0].get('conformationindexbull',
                                                                                                {}).get('num_herd_est',
                                                                                                        0)
            }
            indices_bull = [
                {
                    'name': 'M kg',
                    'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('ebv_milk', 0), 2),
                    'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rel_milk', 0), 2),
                    'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rbv_milk', 0), 2)
                },
                {
                    'name': 'F kg',
                    'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('ebv_fkg', 0), 2),
                    'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rel_fkg', 0), 2),
                    'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rbv_fkg', 0), 2)
                },
                {
                    'name': 'F %',
                    'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('ebv_fprc', 0), 2),
                    'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rel_fprc', 0), 2),
                    'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rbv_fprc', 0), 2)
                },
                {
                    'name': 'P kg',
                    'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('ebv_pkg', 0), 2),
                    'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rel_pkg', 0), 2),
                    'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rbv_pkg', 0), 2)
                },
                {
                    'name': 'P %',
                    'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('ebv_pprc', 0), 2),
                    'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rel_pprc', 0), 2),
                    'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        bull_data[0].get('milkproductionindexbull', {}).get('rbv_pprc', 0), 2)
                },
                {
                    'name': 'CRH',
                    'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('ebv_crh', 0), 2),
                    'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rel_crh', 0), 2),
                    'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rbv_crh', 0), 2)
                },
                {
                    'name': 'CTF',
                    'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('ebv_ctfi', 0), 2),
                    'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rel_ctfi', 0), 2),
                    'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rbv_ctfi', 0), 2)
                },
                {
                    'name': 'DO',
                    'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('ebv_do', 0), 2),
                    'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rel_do', 0), 2),
                    'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        bull_data[0].get('reproductionindexbull', {}).get('rbv_do', 0), 2)
                },
                {
                    'name': 'SCS',
                    'evb': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
                        bull_data[0].get('somaticcellindexbull', {}).get('ebv_scs', 0), 2),
                    'rel': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
                        bull_data[0].get('somaticcellindexbull', {}).get('rel_scs', 0), 2),
                    'rbv': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
                        bull_data[0].get('somaticcellindexbull', {}).get('rscs', 0), 2)
                }
            ]
            additional_info = [
                {
                    'name': 'RBVT',
                    'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvt')),
                },
                {
                    'name': 'RBVF',
                    'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvf')),
                },
                {
                    'name': 'RBVU',
                    'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvu')),
                },
                {
                    'name': 'RC',
                    'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('conformationindexbull', {}), 'rc')),
                },
                {
                    'name': 'RM',
                    'value': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('milkproductionindexbull', {}), 'rm')),
                },
                {
                    'name': 'RF',
                    'value': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('reproductionindexbull', {}), 'rf')),
                },
                {
                    'name': 'RSCS',
                    'value': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('somaticcellindexbull', {}), 'rscs')),
                },
                {
                    'name': 'PI',
                    'value': 0 if bull_data[0].get('complexindexbull', {}) is None else round(
                        safe_get(bull_data[0].get('complexindexbull', {}), 'pi')),
                },
            ]

            result_data = {
                'info': info,
                'parent': parent,
                'livestock': livestock,
                'herd': herd,
                'indices': indices_bull,
                'additional_info': additional_info,
                'linear_profile': bull_data[0].get('conformationindexdiagrambull', {}),
                'photo': bull_data[0].get('photo', '')
            }
            return Response(result_data, status=status.HTTP_200_OK)

        except PKBull.DoesNotExist:

            return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)
