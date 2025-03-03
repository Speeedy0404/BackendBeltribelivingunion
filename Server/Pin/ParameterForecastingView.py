import os

from django.conf import settings
from openpyxl import load_workbook
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Farms, PK, PKYoungAnimals, PKBull, Report, JsonFarmsData
from ..serializers import CowParameterForecastingSerializer, BullParameterForecastingSerializer

REPORT_DIR = os.path.join(settings.BASE_DIR, 'reports')


def calculate_weighted_average(bull_data, index_type):
    total_ebv_rel = {}
    total_rel = {}

    for bull in bull_data:
        index = bull[index_type]
        if index is None:
            pass
        else:
            for parameter, value in index.items():
                if parameter.startswith('ebv_'):
                    rel_parameter = parameter.replace('ebv_', 'rel_')
                    rel_value = index[rel_parameter]

                    if value is None or rel_value is None:
                        continue

                    ebv_rel_value = value * (rel_value / 100)

                    if parameter not in total_ebv_rel:
                        total_ebv_rel[parameter] = 0
                        total_rel[parameter] = 0
                    total_ebv_rel[parameter] += ebv_rel_value
                    total_rel[parameter] += 1

    if len(total_ebv_rel) == 0 or len(total_rel) == 0:
        return {'param': 0}
    else:
        average_values = {parameter: total_ebv_rel[parameter] / total_rel[parameter] for parameter in total_ebv_rel}

    return average_values


def calculate_weighted_average_with_bulls(cow_data, averages, index_type):
    cows = []

    for cow in cow_data:
        count = -1
        cow_averages = {}
        for index in index_type:
            count += 1
            cow_index = cow.get(index)
            bull_average = averages[count]
            if cow_index is None:
                cow_averages[index] = None
            else:
                current_param = {}
                for parameter, value in cow_index.items():
                    if parameter.startswith('ebv_'):
                        rel_parameter = parameter.replace('ebv_', 'rel_')
                        rel_value = cow_index.get(rel_parameter)
                        if value is None or rel_value is None:
                            current_param[parameter] = None
                        else:
                            average_need = bull_average.get(parameter, 0)
                            ebv_rel_value = ((value * (rel_value / 100)) + average_need) / 2
                            current_param[parameter] = ebv_rel_value
                cow_averages[index] = current_param
        cows.append(cow_averages)
    return cows


def calculate_average(params_list, data, param_key):
    total = 0
    count = 0
    for cow in params_list:
        value = cow.get(data, {})
        if value is None:
            pass
        else:
            value = value.get(param_key, None)

        if value is not None:
            total += value
            count += 1
    return total / count if count > 0 else 0


def count_valid_conformationindex(params_list):
    count = 0
    for cow in params_list:
        conformationindex = cow.get('conformationindex', None)
        if conformationindex is not None:
            count += 1
    return count


def calculate_difference(current, forecasting):
    result = {}
    for key in current:
        result[key] = forecasting.get(key, 0) - current[key]
    return result


class ParameterForecastingView(APIView):
    def post(self, request):
        try:
            cows_param = []
            cow_numbers = []
            bull_numbers = []

            farm = Farms.objects.get(korg=self.request.headers.get('Kodrn'))
            paths = Report.objects.filter(title__icontains=farm.norg).values_list('path', flat=True)

            if len(paths) == 0:
                if farm.jsonfarmsdata.parameter_forecasting is None:
                    pass
                else:
                    farm.jsonfarmsdata.parameter_forecasting = {'parameter_forecasting': {
                        'tip': 0,
                        'kt': 0,
                        'rost': 0,
                        'gt': 0,
                        'pz': 0,
                        'shz': 0,
                        'pzkb': 0,
                        'pzkz': 0,
                        'sust': 0,
                        'pzkop': 0,
                        'gv': 0,
                        'pdv': 0,
                        'vzcv': 0,
                        'szcv': 0,
                        'csv': 0,
                        'rps': 0,
                        'rzs': 0,
                        'ds': 0,

                        'milk': 0,
                        'fkg': 0,
                        'fprc': 0,
                        'pkg': 0,
                        'pprc': 0,

                        'crh': 0,
                        'ctfi': 0,
                        'do': 0,

                        'scs': 0
                    }}
                    farm.jsonfarmsdata.save()
                return Response({'parameter_forecasting': {
                    'tip': 0,
                    'kt': 0,
                    'rost': 0,
                    'gt': 0,
                    'pz': 0,
                    'shz': 0,
                    'pzkb': 0,
                    'pzkz': 0,
                    'sust': 0,
                    'pzkop': 0,
                    'gv': 0,
                    'pdv': 0,
                    'vzcv': 0,
                    'szcv': 0,
                    'csv': 0,
                    'rps': 0,
                    'rzs': 0,
                    'ds': 0,

                    'milk': 0,
                    'fkg': 0,
                    'fprc': 0,
                    'pkg': 0,
                    'pprc': 0,

                    'crh': 0,
                    'ctfi': 0,
                    'do': 0,

                    'scs': 0
                }, }, status=status.HTTP_200_OK)

            new_paths = [path + ".xlsx" for path in paths]
            directory_path = new_paths[0].split('__')[0][:-16]

            reports = []
            for new_path in new_paths:
                xlsx_path = os.path.join(REPORT_DIR, directory_path, new_path)
                if os.path.exists(xlsx_path):
                    workbook = load_workbook(xlsx_path)
                    sheet = workbook.active
                    for row in sheet.iter_rows(min_row=5, min_col=1, max_col=1, values_only=True):
                        if row[0]:
                            cow_numbers.append(row[0])
                    for row in sheet.iter_rows(min_row=5, min_col=7, max_col=7, values_only=True):
                        if row[0]:
                            bull_numbers.append(row[0])
                reports.append([cow_numbers, bull_numbers])
                cow_numbers = []
                bull_numbers = []

            for report in reports:
                cows = PK.objects.filter(uniq_key__in=report[0]).values_list('uniq_key', flat=True)

                if len(cows) == len(report[0]):
                    queryset = PK.objects.filter(
                        uniq_key__in=cows
                    ).select_related(
                        'milkproductionindex', 'conformationindex', 'reproductionindex',
                        'somaticcellindex',
                    ).order_by('id')

                    serializer = CowParameterForecastingSerializer(queryset, many=True)
                    cow_data = serializer.data

                    queryset = PKBull.objects.filter(
                        uniq_key__in=report[1]
                    ).select_related(
                        'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
                        'somaticcellindexbull',
                    ).order_by('id')

                    serializer = BullParameterForecastingSerializer(queryset, many=True)
                    bull_data = serializer.data

                    average_conformation = calculate_weighted_average(bull_data, 'conformationindexbull')
                    average_milk = calculate_weighted_average(bull_data, 'milkproductionindexbull')
                    average_reproduction = calculate_weighted_average(bull_data, 'reproductionindexbull')
                    average_somaticcell = calculate_weighted_average(bull_data, 'somaticcellindexbull')

                    cows = calculate_weighted_average_with_bulls(cow_data,
                                                                 [average_conformation, average_milk,
                                                                  average_reproduction,
                                                                  average_somaticcell],
                                                                 ['conformationindex', 'milkproductionindex',
                                                                  'reproductionindex', 'somaticcellindex'])

                    cows_param.extend(cows)
                else:
                    pass

            forecasting = {
                'tip': calculate_average(cows_param, 'conformationindex', 'ebv_tip'),
                'kt': calculate_average(cows_param, 'conformationindex', 'ebv_kt'),
                'rost': calculate_average(cows_param, 'conformationindex', 'ebv_rost'),
                'gt': calculate_average(cows_param, 'conformationindex', 'ebv_gt'),
                'pz': calculate_average(cows_param, 'conformationindex', 'ebv_pz'),
                'shz': calculate_average(cows_param, 'conformationindex', 'ebv_shz'),
                'pzkb': calculate_average(cows_param, 'conformationindex', 'ebv_pzkb'),
                'pzkz': calculate_average(cows_param, 'conformationindex', 'ebv_pzkz'),
                'sust': calculate_average(cows_param, 'conformationindex', 'ebv_sust'),
                'pzkop': calculate_average(cows_param, 'conformationindex', 'ebv_pzkop'),
                'gv': calculate_average(cows_param, 'conformationindex', 'ebv_gv'),
                'pdv': calculate_average(cows_param, 'conformationindex', 'ebv_pdv'),
                'vzcv': calculate_average(cows_param, 'conformationindex', 'ebv_vzcv'),
                'szcv': calculate_average(cows_param, 'conformationindex', 'ebv_szcv'),
                'csv': calculate_average(cows_param, 'conformationindex', 'ebv_csv'),
                'rps': calculate_average(cows_param, 'conformationindex', 'ebv_rps'),
                'rzs': calculate_average(cows_param, 'conformationindex', 'ebv_rzs'),
                'ds': calculate_average(cows_param, 'conformationindex', 'ebv_ds'),

                'milk': calculate_average(cows_param, 'milkproductionindex', 'ebv_milk'),
                'fkg': calculate_average(cows_param, 'milkproductionindex', 'ebv_fkg'),
                'fprc': calculate_average(cows_param, 'milkproductionindex', 'ebv_fprc'),
                'pkg': calculate_average(cows_param, 'milkproductionindex', 'ebv_pkg'),
                'pprc': calculate_average(cows_param, 'milkproductionindex', 'ebv_pprc'),

                'crh': calculate_average(cows_param, 'reproductionindex', 'ebv_crh'),
                'ctfi': calculate_average(cows_param, 'reproductionindex', 'ebv_ctfi'),
                'do': calculate_average(cows_param, 'reproductionindex', 'ebv_do'),

                'scs': calculate_average(cows_param, 'somaticcellindex', 'ebv_scs'),
            }
            current = {
                'tip': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_tip") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_tip", 0),
                'kt': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_kt") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf",
                                                                                                                 {}).get(
                    "avg_ebv_kt", 0),
                'rost': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_rost") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_rost", 0),
                'gt': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_gt") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf",
                                                                                                                 {}).get(
                    "avg_ebv_gt", 0),
                'pz': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_pz") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf",
                                                                                                                 {}).get(
                    "avg_ebv_pz", 0),
                'shz': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_shz") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_shz", 0),
                'pzkb': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_pzkb") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_pzkb", 0),
                'pzkz': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_pzkz") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_pzkz", 0),
                'sust': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_sust") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_sust", 0),
                'pzkop': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_pzkop") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_pzkop", 0),
                'gv': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_gv") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf",
                                                                                                                 {}).get(
                    "avg_ebv_gv", 0),
                'pdv': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_pdv") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_pdv", 0),
                'vzcv': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_vzcv") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_vzcv", 0),
                'szcv': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_szcv") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_szcv", 0),
                'csv': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_csv") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_csv", 0),
                'rps': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_rps") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_rps", 0),
                'rzs': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_rzs") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "conf", {}).get("avg_ebv_rzs", 0),
                'ds': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf", {}).get(
                    "avg_ebv_ds") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("conf",
                                                                                                                 {}).get(
                    "avg_ebv_ds", 0),

                'milk': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("milk", {}).get(
                    "avg_ebv_milk") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "milk", {}).get("avg_ebv_milk", 0),
                'fkg': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("milk", {}).get(
                    "avg_ebv_fkg") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "milk", {}).get("avg_ebv_fkg", 0),
                'fprc': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("milk", {}).get(
                    "avg_ebv_fprc") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "milk", {}).get("avg_ebv_fprc", 0),
                'pkg': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("milk", {}).get(
                    "avg_ebv_pkg") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "milk", {}).get("avg_ebv_pkg", 0),
                'pprc': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("milk", {}).get(
                    "avg_ebv_pprc") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "milk", {}).get("avg_ebv_pprc", 0),

                'crh': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("reprod", {}).get(
                    "avg_ebv_crh") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "reprod", {}).get("avg_ebv_crh", 0),
                'ctfi': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("reprod", {}).get(
                    "avg_ebv_ctfi") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "reprod", {}).get("avg_ebv_ctfi", 0),
                'do': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("reprod", {}).get(
                    "avg_ebv_do") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get(
                    "reprod", {}).get("avg_ebv_do", 0),

                'scs': 0 if farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("scs", {}).get(
                    "avg_ebv_scs") is None else farm.jsonfarmsdata.aggregated_data.get("aggregated_data", {}).get("scs",
                                                                                                                  {}).get(
                    "avg_ebv_scs", 0),
            }

            result = calculate_difference(current, forecasting)

            farm.jsonfarmsdata.parameter_forecasting = {'parameter_forecasting': result}
            farm.jsonfarmsdata.save()

            result_data = {
                'parameter_forecasting': result,
            }
            return Response(result_data, status=status.HTTP_200_OK)
        except Farms.DoesNotExist:
            return Response({"error": "Проблема с данными"}, status=status.HTTP_400_BAD_REQUEST)
