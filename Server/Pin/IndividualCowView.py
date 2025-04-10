import json
from rest_framework import status
from django.db.models import Q, Subquery
from rest_framework.views import APIView
from ..models import Parentage, PK, PKBull
from rest_framework.response import Response
from ..serializers import CowIndividualFlatSerializer


class IndividualCowView(APIView):

    def post(self, request):
        data = request.data

        filter_values = data.get('filterValues', {})
        selected_complexes = data.get('selectedComplexes', [])
        selected_line = data.get('selectedLine', None)

        filters_map = {
            'EBVUdoi': ('milkproductionindex__ebv_milk__gte', 'milkproductionindex__ebv_milk__lte'),
            'EBVZhirKg': ('milkproductionindex__ebv_fkg__gte', 'milkproductionindex__ebv_fkg__lte'),
            'EBVZhirPprc': ('milkproductionindex__ebv_fprc__gte', 'milkproductionindex__ebv_fprc__lte'),
            'EBVBelokKg': ('milkproductionindex__ebv_pkg__gte', 'milkproductionindex__ebv_pkg__lte'),
            'EBVBelokPprc': ('milkproductionindex__ebv_pprc__gte', 'milkproductionindex__ebv_pprc__lte'),
            'RBVT': ('conformationindex__rbvt__gte', 'conformationindex__rbvt__lte'),
            'RBVF': ('conformationindex__rbvf__gte', 'conformationindex__rbvf__lte'),
            'RBVU': ('conformationindex__rbvu__gte', 'conformationindex__rbvu__lte'),
            'RC': ('conformationindex__rc__gte', 'conformationindex__rc__lte'),
            'RF': ('reproductionindex__rf__gte', 'reproductionindex__rf__lte'),
            'Rscs': ('somaticcellindex__rscs__gte', 'somaticcellindex__rscs__lte'),
            'RBVZhirKg': ('milkproductionindex__rbv_fkg__gte', 'milkproductionindex__rbv_fkg__lte'),
            'RBVBelokKg': ('milkproductionindex__rbv_pkg__gte', 'milkproductionindex__rbv_pkg__lte'),
            'RM': ('complexindex__rm__gte', 'complexindex__rm__lte'),
            'PI': ('complexindex__pi__gte', 'complexindex__pi__lte'),
        }

        kod_xoz = request.headers.get('Kodrn')
        cow_filter = Q(kodxoz=kod_xoz) & Q(datavybr__isnull=True)

        # Фильтрация по параметрам (если переданы)
        for key, (min_filter, max_filter) in filters_map.items():
            min_value = filter_values.get(key, {}).get('min')
            max_value = filter_values.get(key, {}).get('max')

            if min_value not in ['', None]:
                cow_filter &= Q(**{min_filter: min_value})
            if max_value not in ['', None]:
                cow_filter &= Q(**{max_filter: max_value})

        # Фильтрация по комплексам
        if len(selected_complexes) >= 1:
            cow_filter &= Q(kompleks__in=selected_complexes)

        # Фильтрация по линии
        if selected_line not in ['', None, 'Нет', ',БЕЗ ЛИНИИ']:
            cow_filter &= Q(lin__branch_name=selected_line)

        try:
            cow = list(PK.objects.filter(cow_filter).values_list('uniq_key', flat=True))
            queryset = PK.objects.filter(uniq_key__in=cow).select_related(
                'milkproductionindex', 'conformationindex', 'reproductionindex',
                'somaticcellindex', 'complexindex'
            ).order_by('id')

            serializer = CowIndividualFlatSerializer(queryset, many=True)

            return Response({'results': serializer.data, },
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
