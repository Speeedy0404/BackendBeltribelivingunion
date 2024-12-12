import os
import re
from django.conf import settings
from rest_framework import status
from transliterate import translit
from rest_framework.views import APIView
from rest_framework.response import Response

PDF_DIR = os.path.join(settings.BASE_DIR, 'pdf_reports')


def sanitize_filename(name):
    """Преобразование названия в нижний регистр, замена пробелов на подчеркивания и транслитерация."""
    name = translit(name, 'ru', reversed=True)
    name = name.lower()  # Переводим в нижний регистр
    name = re.sub(r'\s+', '_', name)
    return name


class FarmReportsView(APIView):
    """API для получения списка отчетов для конкретного хозяйства"""

    def get(self, request, farm_name):
        farm_directory = os.path.join(PDF_DIR, sanitize_filename(farm_name))

        if os.path.exists(farm_directory) and os.path.isdir(farm_directory):
            # Получаем список всех PDF файлов в выбранной директории
            reports = [f for f in os.listdir(farm_directory) if f.endswith('.pdf')]
            return Response({"reports": reports}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Хозяйство не найдено."}, status=status.HTTP_404_NOT_FOUND)
