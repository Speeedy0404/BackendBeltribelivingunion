import json
from rest_framework import status
from django.db.models import Q, Subquery
from rest_framework.views import APIView
from ..models import PKYoungAnimals, PKBull
from rest_framework.response import Response
from ..serializers import PKYoungAnimalsSerializerData


class IndividualYoungView(APIView):

    def post(self, request):
        data = request.data
        try:
            kod_xoz = self.request.headers.get('Kodrn')
            young_filter = Q(kodxoz=kod_xoz)

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

                young_filter &= Q(uniq_key__in=Subquery(
                    PKYoungAnimals.objects.filter(
                        f_regnomer__in=bull_keys
                    ).values('uniq_key')
                ))

            queryset = PKYoungAnimals.objects.filter(young_filter).order_by('id')

            serializer = PKYoungAnimalsSerializerData(queryset, many=True)
            young_count = queryset.count()

            return Response({'count': young_count, 'results': serializer.data, }, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
