import numpy as np
from ..models import PK, Farms
from collections import Counter
from rest_framework import status
from scipy.stats import gaussian_kde
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import IndividualPinSerializer, AggregatedDataSerializer


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


class IndividualPinView(APIView):

    def post(self, request):
        serializer = IndividualPinSerializer(data=request.data)
        if serializer.is_valid():
            farm_code = serializer.validated_data['farmCode']
            farm_name = serializer.validated_data['farmName']
            try:
                farm = Farms.objects.get(korg=farm_code, norg=farm_name)

                cow_ids = PK.objects.filter(kodxoz=farm.korg, datavybr__isnull=True).values_list('id', flat=True)
                data = {'cow_ids': list(cow_ids)}

                aggregated_serializer = AggregatedDataSerializer(data=data)
                aggregated_serializer.is_valid(raise_exception=True)
                aggregated_data = aggregated_serializer.data

                density_data = create_data(cow_ids)

                result_data = {
                    'aggregated_data': aggregated_data,
                    'density_data': density_data,
                }

                return Response(result_data, status=status.HTTP_200_OK)
            except Farms.DoesNotExist:
                return Response({"error": "Хозяйство не найдено"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
