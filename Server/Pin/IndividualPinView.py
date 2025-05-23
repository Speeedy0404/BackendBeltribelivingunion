import sys
import os
import numpy as np
from ..models import PK, Farms
from collections import Counter
from rest_framework import status
from scipy.stats import gaussian_kde
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import IndividualPinSerializer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fields import MAPPING


def get_density(object_with_data):
    density_data = gaussian_kde(object_with_data)
    x = np.linspace(min(object_with_data), max(object_with_data), 1000).tolist()
    y = density_data(x).tolist()
    return x, y


def get_count(object_with_data):
    count_data = Counter(object_with_data)
    unique_values = list(count_data.keys())
    frequencies = list(count_data.values())
    x = np.array(unique_values).tolist()  # Это ось X
    y = np.array(frequencies).tolist()  # Это ось Y
    return x, y


def create_data(ids):
    # Получаем данные, связанные с объектами PK
    data = PK.objects.filter(id__in=ids).select_related(
        'milkproductionindex',
        'conformationindex',
        'reproductionindex',
        'scs',
        'complexindex'
    ).values_list(
        'milkproductionindex__ebv_milk',
        'milkproductionindex__ebv_fkg',
        'milkproductionindex__ebv_fprc',
        'milkproductionindex__ebv_pkg',
        'milkproductionindex__ebv_pprc',
        'milkproductionindex__rbv_milk',
        'milkproductionindex__rbv_fprc',
        'milkproductionindex__rbv_pprc',
        'milkproductionindex__rm',
        'conformationindex__rbvt',
        'conformationindex__rbvf',
        'conformationindex__rbvu',
        'conformationindex__rc',
        'reproductionindex__rbv_crh',
        'reproductionindex__rbv_ctfi',
        'reproductionindex__rbv_do',
        'reproductionindex__rf',
        'scs__scs',
        'complexindex__pi'
    )

    # Словарь для хранения данных
    results = []

    # Поля для использования get_density
    density_fields = [
        ['milkproductionindex__ebv_milk', 'EBV Молоко'],
        ['milkproductionindex__ebv_fkg', 'EBV Жир кг'],
        ['milkproductionindex__ebv_fprc', 'EBV Жир %'],
        ['milkproductionindex__ebv_pkg', 'EBV Белок кг'],
        ['milkproductionindex__ebv_pprc', 'EBV Белок %'],
        ['scs__scs', 'Rscs']
    ]

    # Поля для использования get_count
    count_fields = [
        ['milkproductionindex__rbv_milk', 'RBV Молоко'],
        ['milkproductionindex__rbv_fprc', 'RBV Жир %'],
        ['milkproductionindex__rbv_pprc', 'RBV Белок %'],
        ['milkproductionindex__rm', 'RM'],
        ['conformationindex__rbvt', 'RBVT'],
        ['conformationindex__rbvf', 'RBVF'],
        ['conformationindex__rbvu', 'RBVU'],
        ['conformationindex__rc', 'RC'],
        ['reproductionindex__rbv_crh', 'RCHr'],
        ['reproductionindex__rbv_ctfi', 'RCTF'],
        ['reproductionindex__rbv_do', 'RDO'],
        ['reproductionindex__rf', 'RF'],
        ['complexindex__pi', 'PI']
    ]

    # Обработка полей для get_density
    for field in density_fields:
        values = list(data.filter(**{f"{field[0]}__isnull": False}).values_list(field[0], flat=True))
        if values:  # Проверяем, что список не пустой
            x, y = get_density(values)
            results.append({'name': f'Плотность для {field[1]}', 'data': y, 'labels': x})

    # Обработка полей для get_count
    for field in count_fields:
        values = list(data.filter(**{f"{field[0]}__isnull": False}).order_by(field[0]).values_list(field[0], flat=True))
        if values:  # Проверяем, что список не пустой
            x_count, y_count = get_count(values)
            results.append({'name': f'Количество для {field[1]}', 'data': y_count, 'labels': x_count})

    return results


def mapping_label(group_list):
    for item in group_list:
        param_name = item['param']
        item['param'] = MAPPING[param_name]
    return group_list


class IndividualPinView(APIView):

    def post(self, request):
        serializer = IndividualPinSerializer(data=request.data)
        if serializer.is_valid():
            farm_code = serializer.validated_data['farmCode']
            farm_name = serializer.validated_data['farmName']
            try:
                farm = Farms.objects.get(korg=farm_code, norg=farm_name)

                lactation_data = [
                    farm.jsonfarmsdata.aggregated_data["aggregated_data"]["lak_one"],
                    farm.jsonfarmsdata.aggregated_data["aggregated_data"]["lak_two"],
                    farm.jsonfarmsdata.aggregated_data["aggregated_data"]["lak_three"]
                ]
                aggregated_data = farm.jsonfarmsdata.aggregated_data["aggregated_data"]

                forecasting_1 = aggregated_data["forecasting_section_one"]
                forecasting_1 = mapping_label(forecasting_1)
                forecasting_2 = aggregated_data["forecasting_section_two"]
                forecasting_2 = mapping_label(forecasting_2)
                forecasting_3 = aggregated_data["forecasting_section_three"]
                forecasting_3 = mapping_label(forecasting_3)
                forecasting_4 = aggregated_data["forecasting_section_four"]
                forecasting_4 = mapping_label(forecasting_4)

                table_one = mapping_label(aggregated_data["breeding_value_of_milk_productivity"])
                table_two = mapping_label(aggregated_data["relative_breeding_value_of_milk_productivity"])

                result_data = {
                    'lactation_data': lactation_data,
                    'breeding_value_of_milk_productivity': table_one,
                    'relative_breeding_value_of_milk_productivity': table_two,
                    'forecasting_1': forecasting_1,
                    'forecasting_2': forecasting_2,
                    'forecasting_3': forecasting_3,
                    'forecasting_4': forecasting_4,
                    'density_data': farm.jsonfarmsdata.chart_data["char_data"],
                }

                return Response(result_data, status=status.HTTP_200_OK)
            except Farms.DoesNotExist:
                return Response({"error": "Проблема с данными"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
