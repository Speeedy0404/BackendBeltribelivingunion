import os
import sys
import json
from .models import *
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .serializers import GetCowParamsSerializer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fields import MAPPING


class CustomPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 3000


def mapping_label(group_list):
    for item in group_list:
        param_name = item['param']
        item['param'] = MAPPING[param_name]
    return group_list


class StatisticsListView(APIView):

    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'files_data', 'json', 'statistics_data.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                result_data = json.load(file)
                take_value = result_data['aggregated_data']
                lactation_data = [
                    take_value["lak_one"],
                    take_value["lak_two"],
                    take_value["lak_three"]
                ]
                table_one = mapping_label(take_value["breeding_value_of_milk_productivity"])
                table_two = mapping_label(take_value["relative_breeding_value_of_milk_productivity"])

                result = {
                    'lactation_data': lactation_data,
                    'breeding_value_of_milk_productivity': table_one,
                    'relative_breeding_value_of_milk_productivity': table_two,
                    'info': result_data['info']
                }

            return Response(result, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CowParamsView(APIView):
    """API для получения списка отчетов для конкретного хозяйства"""

    def get(self, request, uniq_key):
        try:
            model = ['milkproductionindex', 'conformationindex', 'reproductionindex', 'somaticcellindex',
                     'complexindex']

            default_values = {
                'milkproductionindex': {
                    'rbv_milk': 'Не указан', 'rbv_fkg': 'Не указан',
                    'rbv_fprc': 'Не указан', 'rbv_pkg': 'Не указан',
                    'rbv_pprc': 'Не указан', 'rm': 'Не указан'
                },
                'conformationindex': {
                    'rbv_tip': 'Не указан', 'rbv_kt': 'Не указан', 'rbv_rost': 'Не указан', 'rbv_gt': 'Не указан',
                    'rbv_pz': 'Не указан', 'rbv_shz': 'Не указан', 'rbv_pzkb': 'Не указан', 'rbv_pzkz': 'Не указан',
                    'rbv_sust': 'Не указан', 'rbv_pzkop': 'Не указан', 'rbv_gv': 'Не указан', 'rbv_pdv': 'Не указан',
                    'rbv_vzcv': 'Не указан', 'rbv_szcv': 'Не указан', 'rbv_csv': 'Не указан', 'rbv_rps': 'Не указан',
                    'rbv_rzs': 'Не указан', 'rbv_ds': 'Не указан',
                    'rbvt': 'Не указан', 'rbvf': 'Не указан', 'rbvu': 'Не указан', 'rc': 'Не указан'
                },
                'reproductionindex': {
                    'rbv_crh': 'Не указан', 'rbv_ctfi': 'Не указан',
                    'rbv_do': 'Не указан', 'rf': 'Не указан'
                },
                'somaticcellindex': {
                    'rscs': 'Не указан'
                },
                'complexindex': {
                    'pi': 'Не указан'
                }
            }

            queryset = PK.objects.filter(
                uniq_key=uniq_key
            ).select_related(
                'milkproductionindex', 'conformationindex', 'reproductionindex',
                'somaticcellindex', 'complexindex',
            ).order_by('id')

            if not queryset.exists():
                return Response({"Answer": "Данные отсутсвуют."}, status=status.HTTP_200_OK)

            serializer = GetCowParamsSerializer(queryset, many=True)
            cow_data = serializer.data

            for mod in model:
                if cow_data[0].get(mod) is None:
                    cow_data[0][mod] = default_values.get(mod, {})

            ordered_data = {
                **cow_data[0].get('milkproductionindex', {}),
                **cow_data[0].get('reproductionindex', {}),
                **cow_data[0].get('somaticcellindex', {}),
                **{key: cow_data[0]['conformationindex'].get(key, 'Не указан') for key in [
                    'rbvt', 'rbvf', 'rbvu', 'rc']},
                **cow_data[0].get('complexindex', {}),
                **{key: cow_data[0]['conformationindex'].get(key, 'Не указан') for key in [
                    'rbv_tip', 'rbv_kt', 'rbv_rost', 'rbv_gt', 'rbv_pz', 'rbv_shz',
                    'rbv_pzkb', 'rbv_pzkz', 'rbv_sust', 'rbv_pzkop', 'rbv_gv', 'rbv_pdv',
                    'rbv_vzcv', 'rbv_szcv', 'rbv_csv', 'rbv_rps', 'rbv_rzs', 'rbv_ds']}
            }

            return Response({"params": ordered_data}, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RatingOfFarms(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = JsonFarmsData.objects.all().values_list('rating_data', flat=True)
            return Response({'rating_data': data}, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
