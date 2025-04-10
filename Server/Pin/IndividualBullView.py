import json
import urllib.parse
from ..models import PKBull
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import BullIndividualFlatSerializer


def get_filtered_bulls(data, bull_filter):
    bulls = []
    i = 0
    key_mapping = {
        "rbv_crh": "reproductionindexbull__rbv_crh",
        "rbv_ctfi": "reproductionindexbull__rbv_ctfi",
        "rbv_do": "reproductionindexbull__rbv_do",
        "rbv_fprc": "milkproductionindexbull__rbv_fprc",
        "rbv_fkg": "milkproductionindexbull__rbv_fkg",
        "rbv_milk": "milkproductionindexbull__rbv_milk",
        "rbv_pprc": "milkproductionindexbull__rbv_pprc",
        "rbv_pkg": "milkproductionindexbull__rbv_pkg",
        "pi": "complexindexbull__pi",
        "rbvt": "conformationindexbull__rbvt",
        "rbvu": "conformationindexbull__rbvu",
        "rc": "conformationindexbull__rc",
        "rf": "reproductionindexbull__rf",
        "rm": "milkproductionindexbull__rm",
        "rscs": "somaticcellindexbull__rscs",
        "rbvf": "conformationindexbull__rbvf",
        "rbv_sust": "conformationindexdiagrambull__rbv_sust",
        "rbv_vzcv": "conformationindexdiagrambull__rbv_vzcv",
        "rbv_gv": "conformationindexdiagrambull__rbv_gv",
        "rbv_gt": "conformationindexdiagrambull__rbv_gt",
        "rbv_ds": "conformationindexdiagrambull__rbv_ds",
        "rbv_kt": "conformationindexdiagrambull__rbv_kt",
        "rbv_pz": "conformationindexdiagrambull__rbv_pz",
        "rbv_pzkb": "conformationindexdiagrambull__rbv_pzkb",
        "rbv_pzkz": "conformationindexdiagrambull__rbv_pzkz",
        "rbv_pzkop": "conformationindexdiagrambull__rbv_pzkop",
        "rbv_pdv": "conformationindexdiagrambull__rbv_pdv",
        "rbv_rzs": "conformationindexdiagrambull__rbv_rzs",
        "rbv_rps": "conformationindexdiagrambull__rbv_rps",
        "rbv_rost": "conformationindexdiagrambull__rbv_rost",
        "rbv_tip": "conformationindexdiagrambull__rbv_tip",
        "rbv_csv": "conformationindexdiagrambull__rbv_csv",
        "rbv_shz": "conformationindexdiagrambull__rbv_shz",
        "rbv_szcv": "conformationindexdiagrambull__rbv_szcv",
    }

    for elements in data:
        key_filter = Q()
        for param in elements:
            param_name, value, operator = param
            db_key = key_mapping.get(param_name)

            if not db_key or value == 'Не указан':
                continue

            if operator == 'improve':
                value = int(value) + 10
                key_filter &= Q(**{f"{db_key}__gte": value})
            elif operator == 'keep':
                value = int(value)
                key_filter &= Q(**{f"{db_key}__gte": value})

        combined_filter = bull_filter & key_filter
        current_bulls = list(PKBull.objects.filter(combined_filter).values_list('uniq_key', flat=True))

        bulls = list(set(bulls + current_bulls))

        i += 1

    return bulls


class IndividualBullView(APIView):

    def post(self, request):
        data = request.data

        book = {
            'РУП ВИТЕБСКОЕ ПП': 556905,
            'РСУП БРЕСТСКОЕ ПП': 554553,
            'РСУП ГОМЕЛЬСКОЕ ГПП': 73617,
            'РУСП ГРОДНЕНСКОЕ ПП': 73643,
            'РУСП МИНСКОЕ ПП': 556895,
            'РУСПП МОГИЛЕВСКОЕ ПП': 73679,
            'ПОКУПНЫЕ': 0.0,
        }

        not_need = [556905, 554553, 73617, 73643, 556895, 73679]
        try:

            filter_values = data.get('filterValues', {})
            selected_complexes = data.get('selectedComplexes', [])
            selected_line = data.get('selectedLine', None)
            selected_gpp = data.get('selectedGpp', [])
            bound_choices = data.get('boundChoices', None)

            filters_map = {
                'EBVUdoi': ('milkproductionindexbull__ebv_milk__gte', 'milkproductionindexbull__ebv_milk__lte'),
                'EBVZhirKg': ('milkproductionindexbull__ebv_fkg__gte', 'milkproductionindexbull__ebv_fkg__lte'),
                'EBVZhirPprc': ('milkproductionindexbull__ebv_fprc__gte', 'milkproductionindexbull__ebv_fprc__lte'),
                'EBVBelokKg': ('milkproductionindexbull__ebv_pkg__gte', 'milkproductionindexbull__ebv_pkg__lte'),
                'EBVBelokPprc': ('milkproductionindexbull__ebv_pprc__gte', 'milkproductionindexbull__ebv_pprc__lte'),
                'RBVT': ('conformationindexbull__rbvt__gte', 'conformationindexbull__rbvt__lte'),
                'RBVF': ('conformationindexbull__rbvf__gte', 'conformationindexbull__rbvf__lte'),
                'RBVU': ('conformationindexbull__rbvu__gte', 'conformationindexbull__rbvu__lte'),
                'RC': ('conformationindexbull__rc__gte', 'conformationindexbull__rc__lte'),
                'RF': ('reproductionindexbull__rf__gte', 'reproductionindexbull__rf__lte'),
                'Rscs': ('somaticcellindexbull__rscs__gte', 'somaticcellindexbull__rscs__lte'),
                'RBVZhirKg': ('milkproductionindexbull__rbv_fkg__gte', 'milkproductionindexbull__rbv_fkg__lte'),
                'RBVBelokKg': ('milkproductionindexbull__rbv_pkg__gte', 'milkproductionindexbull__rbv_pkg__lte'),
                'RM': ('complexindexbull__rm__gte', 'complexindexbull__rm__lte'),
                'PI': ('complexindexbull__pi__gte', 'complexindexbull__pi__lte'),
            }

            bull_filter = Q()

            # Фильтрация по параметрам (если переданы)
            for key, (min_filter, max_filter) in filters_map.items():
                min_value = filter_values.get(key, {}).get('min')
                max_value = filter_values.get(key, {}).get('max')

                if min_value not in ['', None]:
                    bull_filter &= Q(**{min_filter: min_value})
                if max_value not in ['', None]:
                    bull_filter &= Q(**{max_filter: max_value})

            if len(selected_complexes) >= 1:
                bull_filter &= Q(kompleks__in=selected_complexes)

            if selected_line not in ['', None, 'Нет', ',БЕЗ ЛИНИИ']:
                bull_filter &= Q(lin__branch_name=selected_line)

            bull_filter_purchased = None

            if len(selected_gpp) >= 1:
                codes = []
                for item in selected_gpp:
                    codes.append(book[item])
                if 0.0 in codes:
                    bull_filter_purchased = bull_filter
                    bull_filter_purchased &= Q(nomer__startswith='7')
                    bull_filter_purchased &= Q(sperma__gte=0)
                    bull_filter_purchased &= Q(sperma__lt=10)
                    bull_filter_purchased &= ~Q(ovner__in=not_need)
                if 0.0 not in codes:
                    bull_filter &= Q(ovner__in=codes)
                else:
                    codes.remove(0.0)
                    result = [item for item in not_need if item not in codes]
                    bull_filter &= ~Q(ovner__in=result)
            else:
                bull_filter_purchased = bull_filter
                bull_filter_purchased &= Q(nomer__startswith='7')
                bull_filter_purchased &= Q(sperma__gte=0)
                bull_filter_purchased &= Q(sperma__lt=10)
                bull_filter_purchased &= ~Q(ovner__in=not_need)

            bull_filter &= Q(sperma__gte=10)

            bulls_purchased = None

            if bound_choices and len(bound_choices) > 0:
                bulls = get_filtered_bulls(bound_choices, bull_filter)
                if bull_filter_purchased is not None:
                    bulls_purchased = get_filtered_bulls(bound_choices, bull_filter_purchased)
            else:
                bulls = list(PKBull.objects.filter(bull_filter).values_list('uniq_key', flat=True))
                if bull_filter_purchased is not None:
                    bulls_purchased = list(
                        PKBull.objects.filter(bull_filter_purchased).values_list('uniq_key', flat=True))

            if bulls_purchased is not None:
                bulls = bulls + bulls_purchased

            queryset = PKBull.objects.filter(
                uniq_key__in=bulls
            ).select_related(
                'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
                'somaticcellindexbull', 'complexindexbull'
            ).order_by('id')

            serializer = BullIndividualFlatSerializer(queryset, many=True)

            return Response({'results': serializer.data}, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
