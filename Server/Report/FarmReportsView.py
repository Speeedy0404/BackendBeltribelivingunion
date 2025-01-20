import os
import re
from django.conf import settings
from rest_framework import status
from transliterate import translit
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import Report
from Server.serializers import ReportSerializer

REPORT_DIR = os.path.join(settings.BASE_DIR, 'reports')


def sanitize_filename(name):
    """Преобразование названия в нижний регистр, замена пробелов на подчеркивания и транслитерация."""
    name = translit(name, 'ru', reversed=True)
    name = name.lower()  # Переводим в нижний регистр
    name = re.sub(r'\s+', '_', name)
    return name


class FarmReportsView(APIView):
    """API для получения списка отчетов для конкретного хозяйства"""

    def get(self, request, farm_name):
        farm_directory = os.path.join(REPORT_DIR, sanitize_filename(farm_name))

        if os.path.exists(farm_directory) and os.path.isdir(farm_directory):
            reports = [f for f in os.listdir(farm_directory) if f.endswith('.pdf')]
            report_names_without_extension = [os.path.splitext(report)[0] for report in reports]
            try:
                report_ids = Report.objects.filter(path__in=report_names_without_extension).values_list('id', flat=True)
                report = ReportSerializer(Report.objects.filter(id__in=report_ids).order_by('title'), many=True)
                return Response({"reports": report.data}, status=status.HTTP_200_OK)
            except Exception as e:
                print("Ошибка при извлечении отчетов:", str(e))
                return Response({"error": "Ошибка при получении отчетов."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Хозяйство не найдено."}, status=status.HTTP_404_NOT_FOUND)
