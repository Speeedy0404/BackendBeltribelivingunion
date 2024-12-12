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

        try:

            kod_xoz = self.request.headers.get('Kodrn')
            cow_filter = Q(kodxoz=kod_xoz) & Q(datavybr__isnull=True)

            if data.get('minEBVUdoi'):
                cow_filter &= Q(milkproductionindex__ebv_milk__gte=data['minEBVUdoi'])
            if data.get('maxEBVUdoi'):
                cow_filter &= Q(milkproductionindex__ebv_milk__lte=data['maxEBVUdoi'])

            if data.get('minEBVZhirKg'):
                cow_filter &= Q(milkproductionindex__ebv_fkg__gte=data['minEBVZhirKg'])
            if data.get('maxEBVZhirKg'):
                cow_filter &= Q(milkproductionindex__ebv_fkg__lte=data['maxEBVZhirKg'])

            if data.get('minEBVZhirPprc'):
                cow_filter &= Q(milkproductionindex__ebv_fprc__gte=data['minEBVZhirPprc'])
            if data.get('maxEBVZhirPprc'):
                cow_filter &= Q(milkproductionindex__ebv_fprc__lte=data['maxEBVZhirPprc'])

            if data.get('minEBVBelokKg'):
                cow_filter &= Q(milkproductionindex__ebv_pkg__gte=data['minEBVBelokKg'])
            if data.get('maxEBVBelokKg'):
                cow_filter &= Q(milkproductionindex__ebv_pkg__lte=data['maxEBVBelokKg'])

            if data.get('minEBVBelokPprc'):
                cow_filter &= Q(milkproductionindex__ebv_pprc__gte=data['minEBVBelokPprc'])
            if data.get('maxEBVBelokPprc'):
                cow_filter &= Q(milkproductionindex__ebv_pprc__lte=data['maxEBVBelokPprc'])

            if data.get('minRBVT'):
                cow_filter &= Q(conformationindex__rbvt__gte=data['minRBVT'])
            if data.get('maxRBVT'):
                cow_filter &= Q(conformationindex__rbvt__lte=data['maxRBVT'])

            if data.get('minRBVF'):
                cow_filter &= Q(conformationindex__rbvf__gte=data['minRBVF'])
            if data.get('maxRBVF'):
                cow_filter &= Q(conformationindex__rbvf__lte=data['maxRBVF'])

            if data.get('minRBVU'):
                cow_filter &= Q(conformationindex__rbvu__gte=data['minRBVU'])
            if data.get('maxRBVU'):
                cow_filter &= Q(conformationindex__rbvu__lte=data['maxRBVU'])

            if data.get('minRC'):
                cow_filter &= Q(conformationindex__rc__gte=data['minRC'])
            if data.get('maxRC'):
                cow_filter &= Q(conformationindex__rc__lte=data['maxRC'])

            if data.get('minRF'):
                cow_filter &= Q(reproductionindex__rf__gte=data['minRF'])
            if data.get('maxRF'):
                cow_filter &= Q(reproductionindex__rf__lte=data['maxRF'])

            if data.get('minRscs'):
                cow_filter &= Q(somaticcellindex__rscs__gte=data['minRscs'])
            if data.get('maxRscs'):
                cow_filter &= Q(somaticcellindex__rscs__lte=data['maxRscs'])

            if data.get('minRBVZhirKg'):
                cow_filter &= Q(milkproductionindex__rbv_fkg__gte=data['minRBVZhirKg'])
            if data.get('maxRBVZhirKg'):
                cow_filter &= Q(milkproductionindex__rbv_fkg__lte=data['maxRBVZhirKg'])

            if data.get('minRBVBelokKg'):
                cow_filter &= Q(milkproductionindex__rbv_pkg__gte=data['minRBVBelokKg'])
            if data.get('maxRBVBelokKg'):
                cow_filter &= Q(milkproductionindex__rbv_pkg__lte=data['maxRBVBelokKg'])

            if data.get('minRM'):
                cow_filter &= Q(complexindex__rm__gte=data['minRM'])
            if data.get('maxRM'):
                cow_filter &= Q(complexindex__rm__lte=data['maxRM'])

            if data.get('minPI'):
                cow_filter &= Q(complexindex__pi__gte=data['minPI'])
            if data.get('maxPI'):
                cow_filter &= Q(complexindex__pi__lte=data['maxPI'])

            if data.get('selectedComplex') or data.get('selectedLine'):
                if data.get('selectedComplex') and data.get('selectedLine'):
                    bull_keys = PKBull.objects.filter(
                        kompleks__in=data['selectedComplex'], lin__branch_name=data['selectedLine'],
                    ).values('uniq_key')
                elif data.get('selectedComplex'):
                    bull_keys = PKBull.objects.filter(
                        kompleks__in=data['selectedComplex'],
                    ).values('uniq_key')
                else:
                    bull_keys = PKBull.objects.filter(
                        lin__branch_name=data['selectedLine']
                    ).values('uniq_key')

                cow_filter &= Q(uniq_key__in=Subquery(
                    Parentage.objects.filter(
                        ukeyo__in=bull_keys
                    ).values('uniq_key')
                ))

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
