import json
from rest_framework import status
from django.db.models import Q, Subquery
from rest_framework.views import APIView
from ..models import Parentage, PK, PKBull
from rest_framework.response import Response
from ..serializers import CowIndividualAvgSerializer, CowIndividualSerializer


class IndividualCowView(APIView):

    def post(self, request):

        data = request.data

        filters_map = {
            'minEBVUdoi': ('milkproductionindex__ebv_milk__gte', 'maxEBVUdoi', 'milkproductionindex__ebv_milk__lte'),
            'minEBVZhirKg': ('milkproductionindex__ebv_fkg__gte', 'maxEBVZhirKg', 'milkproductionindex__ebv_fkg__lte'),
            'minEBVZhirPprc': (
                'milkproductionindex__ebv_fprc__gte', 'maxEBVZhirPprc', 'milkproductionindex__ebv_fprc__lte'),
            'minEBVBelokKg': (
                'milkproductionindex__ebv_pkg__gte', 'maxEBVBelokKg', 'milkproductionindex__ebv_pkg__lte'),
            'minEBVBelokPprc': (
                'milkproductionindex__ebv_pprc__gte', 'maxEBVBelokPprc', 'milkproductionindex__ebv_pprc__lte'),
            'minRBVT': ('conformationindex__rbvt__gte', 'maxRBVT', 'conformationindex__rbvt__lte'),
            'minRBVF': ('conformationindex__rbvf__gte', 'maxRBVF', 'conformationindex__rbvf__lte'),
            'minRBVU': ('conformationindex__rbvu__gte', 'maxRBVU', 'conformationindex__rbvu__lte'),
            'minRC': ('conformationindex__rc__gte', 'maxRC', 'conformationindex__rc__lte'),
            'minRF': ('reproductionindex__rf__gte', 'maxRF', 'reproductionindex__rf__lte'),
            'minRscs': ('somaticcellindex__rscs__gte', 'maxRscs', 'somaticcellindex__rscs__lte'),
            'minRBVZhirKg': ('milkproductionindex__rbv_fkg__gte', 'maxRBVZhirKg', 'milkproductionindex__rbv_fkg__lte'),
            'minRBVBelokKg': (
                'milkproductionindex__rbv_pkg__gte', 'maxRBVBelokKg', 'milkproductionindex__rbv_pkg__lte'),
            'minRM': ('complexindex__rm__gte', 'maxRM', 'complexindex__rm__lte'),
            'minPI': ('complexindex__pi__gte', 'maxPI', 'complexindex__pi__lte'),
        }

        non_empty_values = {
            key: value for key, value in data.items()
            if key in filters_map and value not in ['', None, []]
        }

        try:

            kod_xoz = self.request.headers.get('Kodrn')
            cow_filter = Q(kodxoz=kod_xoz) & Q(datavybr__isnull=True)
            if len(non_empty_values) > 0:
                for key, value in non_empty_values.items():
                    if key in filters_map:
                        min_filter, max_key, max_filter = filters_map[key]

                        # Проверяем min значение
                        if key in data:
                            cow_filter &= Q(**{min_filter: value})

                        # Проверяем max значение (соответствующий max_key)
                        if max_key in data and data[max_key] not in ['', None, []]:
                            cow_filter &= Q(**{max_filter: data[max_key]})

            if data.get('selectedComplex'):
                cow_filter &= Q(kompleks__in=data['selectedComplex'])
            if data.get('selectedLine'):
                cow_filter &= Q(lin__branch_name=data['selectedLine'])

            cow = list(PK.objects.filter(cow_filter).values_list('uniq_key', flat=True))

            queryset = PK.objects.filter(
                uniq_key__in=cow
            ).select_related(
                'milkproductionindex', 'conformationindex', 'reproductionindex',
                'somaticcellindex', 'complexindex'
            ).order_by('id')

            cow_ids = queryset.values_list('id', flat=True)
            data_second = {'cow_ids': list(cow_ids)}
            aggregated_serializer = CowIndividualAvgSerializer(data=data_second)
            aggregated_serializer.is_valid(raise_exception=True)
            aggregated_data = aggregated_serializer.data

            serializer = CowIndividualSerializer(queryset, many=True)

            cow_count = queryset.count()

            return Response({'count': cow_count, 'results': serializer.data, 'aggregated_data': aggregated_data},
                            status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)

        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
