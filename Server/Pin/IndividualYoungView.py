import json
from rest_framework import status
from django.db.models import Q, Subquery
from rest_framework.views import APIView
from ..models import PKYoungAnimals, PKBull
from rest_framework.response import Response
from ..serializers import PKYoungAnimalsSerializerData, PKYoungAnimalsFlatSerializer


class IndividualYoungView(APIView):

    def post(self, request):
        data = request.data
        try:
            kod_xoz = self.request.headers.get('Kodrn')
            if not kod_xoz:
                return Response({"error": "Отсутствует заголовок Kodrn."}, status=status.HTTP_400_BAD_REQUEST)

            young_filter = Q(kodxoz=kod_xoz)
            selected_complex = data.get('selectedComplexes', [])
            selected_line = data.get('selectedLine', None)

            if selected_complex or selected_line:
                bull_filter = Q()
                if selected_complex:
                    bull_filter &= Q(kompleks__in=selected_complex)
                if selected_line:
                    bull_filter &= Q(lin__branch_name=selected_line)

                bull_keys = PKBull.objects.filter(bull_filter).values('uniq_key')
                young_filter &= Q(uniq_key__in=Subquery(
                    PKYoungAnimals.objects.filter(f_regnomer__in=bull_keys).values('uniq_key')
                ))

            queryset = PKYoungAnimals.objects.filter(young_filter).order_by('id')

            serializer = PKYoungAnimalsFlatSerializer(queryset, many=True)
            young_count = queryset.count()

            return Response({'count': young_count, 'results': serializer.data, }, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "JSON файл не найден."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Ошибка декодирования JSON."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

