import json
import urllib.parse
from ..models import PKBull
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import BullIndividualAvgSerializer, BullIndividualSerializer


def get_filtered_bulls(data, bull_filter):
    bulls = []
    i = 0

    key_mapping = {
        "CRh": "reproductionindexbull__rbv_crh",
        "CTF": "reproductionindexbull__rbv_ctfi",
        "DO": "reproductionindexbull__rbv_do",
        "F,%": "milkproductionindexbull__rbv_fprc",
        "F,kg": "milkproductionindexbull__rbv_fkg",
        "M,kg": "milkproductionindexbull__rbv_milk",
        "P,%": "milkproductionindexbull__rbv_pprc",
        "P,kg": "milkproductionindexbull__rbv_pkg",
        "PI": "complexindexbull__pi",
        "RBVT": "conformationindexbull__rbvt",
        "RBVU": "conformationindexbull__rbvu",
        "RC": "conformationindexbull__rc",
        "RF": "reproductionindexbull__rf",
        "RM": "milkproductionindexbull__rm",
        "RSCS": "somaticcellindexbull__rscs",
        "RVBF": "conformationindexbull__rbvf",
        "Выраженность скакательного сустава": "conformationindexdiagrambull__rbv_sust",
        "Высота задней части вымени": "conformationindexdiagrambull__rbv_szcv",
        "Глубина вымени": "conformationindexdiagrambull__rbv_gv",
        "Глубина туловища": "conformationindexdiagrambull__rbv_gt",
        "Длина сосков (передних)": "conformationindexdiagrambull__rbv_ds",
        "Крепость телосложения": "conformationindexdiagrambull__rbv_kt",
        "Положение зада": "conformationindexdiagrambull__rbv_pz",
        "Постановка задних конечностей (сбоку)": "conformationindexdiagrambull__rbv_pzkb",
        "Постановка задних конечностей (сзади)": "conformationindexdiagrambull__rbv_pzkz",
        "Постановка задних копыт": "conformationindexdiagrambull__rbv_pzkop",
        "Прикрепление передней долей вымени": "conformationindexdiagrambull__rbv_vzcv",
        "Расположение задних сосков": "conformationindexdiagrambull__rbv_rzs",
        "Расположение передних сосков": "conformationindexdiagrambull__rbv_rps",
        "Рост": "conformationindexdiagrambull__rbv_rost",
        "Тип": "conformationindexdiagrambull__rbv_tip",
        "Центральная связка (глубина доли)": "conformationindexdiagrambull__rbv_csv",
        "Ширина зада": "conformationindexdiagrambull__rbv_shz",
        "Ширина задней части вымени": "conformationindexdiagrambull__rbv_szcv",
    }

    while str(i) in data:
        item_data = data[str(i)][1]
        key_filter = Q()

        # Парсим и применяем условия
        for param in item_data:
            param_name, value, operator = param
            db_key = key_mapping.get(param_name)

            if not db_key or value == 'Не указан':
                continue

            if operator == '+':
                value = int(value) + 10
                key_filter &= Q(**{f"{db_key}__gte": value})
            elif operator == '=':
                value = int(value)
                key_filter &= Q(**{f"{db_key}__gte": value})
            elif operator == '?':
                continue

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

            gpp = self.request.headers.get('Kodrn')
            decoded_string = urllib.parse.unquote(gpp)

            # bull_filter = Q(milkproductionindexbull__rm__isnull=False)
            bull_filter = Q(sperma__gte=10)

            if len(decoded_string) > 1:
                codes = []
                for item in decoded_string.split(','):
                    codes.append(book[item])
                if 0.0 not in codes:
                    bull_filter &= Q(ovner__in=codes)
                else:
                    codes.remove(0.0)
                    result = [item for item in not_need if item not in codes]
                    bull_filter &= ~Q(ovner__in=result)

            if data.get('minEBVUdoi'):
                bull_filter &= Q(milkproductionindexbull__ebv_milk__gte=data['minEBVUdoi'])
            if data.get('maxEBVUdoi'):
                bull_filter &= Q(milkproductionindexbull__ebv_milk__lte=data['maxEBVUdoi'])

            if data.get('minEBVZhirKg'):
                bull_filter &= Q(milkproductionindexbull__ebv_fkg__gte=data['minEBVZhirKg'])
            if data.get('maxEBVZhirKg'):
                bull_filter &= Q(milkproductionindexbull__ebv_fkg__lte=data['maxEBVZhirKg'])

            if data.get('minEBVZhirPprc'):
                bull_filter &= Q(milkproductionindexbull__ebv_fprc__gte=data['minEBVZhirPprc'])
            if data.get('maxEBVZhirPprc'):
                bull_filter &= Q(milkproductionindexbull__ebv_fprc__lte=data['maxEBVZhirPprc'])

            if data.get('minEBVBelokKg'):
                bull_filter &= Q(milkproductionindexbull__ebv_pkg__gte=data['minEBVBelokKg'])
            if data.get('maxEBVBelokKg'):
                bull_filter &= Q(milkproductionindexbull__ebv_pkg__lte=data['maxEBVBelokKg'])

            if data.get('minEBVBelokPprc'):
                bull_filter &= Q(milkproductionindexbull__ebv_pprc__gte=data['minEBVBelokPprc'])
            if data.get('maxEBVBelokPprc'):
                bull_filter &= Q(milkproductionindexbull__ebv_pprc__lte=data['maxEBVBelokPprc'])

            if data.get('minRBVT'):
                bull_filter &= Q(conformationindexbull__rbvt__gte=data['minRBVT'])
            if data.get('maxRBVT'):
                bull_filter &= Q(conformationindexbull__rbvt__lte=data['maxRBVT'])

            if data.get('minRBVF'):
                bull_filter &= Q(conformationindexbull__rbvf__gte=data['minRBVF'])
            if data.get('maxRBVF'):
                bull_filter &= Q(conformationindexbull__rbvf__lte=data['maxRBVF'])

            if data.get('minRBVU'):
                bull_filter &= Q(conformationindexbull__rbvu__gte=data['minRBVU'])
            if data.get('maxRBVU'):
                bull_filter &= Q(conformationindexbull__rbvu__lte=data['maxRBVU'])

            if data.get('minRC'):
                bull_filter &= Q(conformationindexbull__rc__gte=data['minRC'])
            if data.get('maxRC'):
                bull_filter &= Q(conformationindexbull__rc__lte=data['maxRC'])

            if data.get('minRF'):
                bull_filter &= Q(reproductionindexbull__rf__gte=data['minRF'])
            if data.get('maxRF'):
                bull_filter &= Q(reproductionindexbull__rf__lte=data['maxRF'])

            if data.get('minRscs'):
                bull_filter &= Q(somaticcellindexbull__rscs__gte=data['minRscs'])
            if data.get('maxRscs'):
                bull_filter &= Q(somaticcellindexbull__rscs__lte=data['maxRscs'])

            if data.get('minRBVZhirKg'):
                bull_filter &= Q(milkproductionindexbull__rbv_fkg__gte=data['minRBVZhirKg'])
            if data.get('maxRBVZhirKg'):
                bull_filter &= Q(milkproductionindexbull__rbv_fkg__lte=data['maxRBVZhirKg'])

            if data.get('minRBVBelokKg'):
                bull_filter &= Q(milkproductionindexbull__rbv_pkg__gte=data['minRBVBelokKg'])
            if data.get('maxRBVBelokKg'):
                bull_filter &= Q(milkproductionindexbull__rbv_pkg__lte=data['maxRBVBelokKg'])

            if data.get('minRM'):
                bull_filter &= Q(complexindexbull__rm__gte=data['minRM'])
            if data.get('maxRM'):
                bull_filter &= Q(complexindexbull__rm__lte=data['maxRM'])

            if data.get('minPI'):
                bull_filter &= Q(complexindexbull__pi__gte=data['minPI'])
            if data.get('maxPI'):
                bull_filter &= Q(complexindexbull__pi__lte=data['maxPI'])

            if data.get('selectedComplex'):
                bull_filter &= Q(kompleks__in=data['selectedComplex'])

            if data.get('selectedLine'):
                bull_filter &= Q(lin__branch_name=data['selectedLine'])

            data_element = data.get('0')

            if data_element:
                bulls = get_filtered_bulls(data, bull_filter)
            else:
                bulls = list(PKBull.objects.filter(bull_filter).values_list('uniq_key', flat=True))

            queryset = PKBull.objects.filter(
                uniq_key__in=bulls
            ).select_related(
                'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
                'somaticcellindexbull', 'complexindexbull'
            ).order_by('id')

            bull_ids = queryset.values_list('id', flat=True)
            data_second = {'bull_ids': list(bull_ids)}
            aggregated_serializer = BullIndividualAvgSerializer(data=data_second)
            aggregated_serializer.is_valid(raise_exception=True)
            aggregated_data = aggregated_serializer.data

            serializer = BullIndividualSerializer(queryset, many=True)
            bull_count = queryset.count()

            return Response({'count': bull_count, 'results': serializer.data, 'aggregated_data': aggregated_data},
                            status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
