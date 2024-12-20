import os
from django.conf import settings
from rest_framework import status
from transliterate import translit
from rest_framework.views import APIView
from rest_framework.response import Response

REPORT_DIR = os.path.join(settings.BASE_DIR, 'reports')


def reverse_sanitize_filename(name):
    """Обратное преобразование: замена подчеркиваний на пробелы и обратная транслитерация."""
    name = name.replace('_', ' ')  # Заменяем подчеркивания на пробелы
    name = translit(name, 'ru')  # Обратная транслитерация в русский
    # name = name.capitalize()  # Первая буква в верхний регистр
    name = name.upper()  # Переводим всё в верхний регистр
    return name


class FarmsReportListView(APIView):
    """API для получения списка хозяйств и их отчетов"""

    def get(self, request):
        for_user_understand = []
        try:
            # Получаем список всех директорий (хозяйств)
            farms = next(os.walk(REPORT_DIR))[1]
            for farm in farms:
                for_user_understand.append(reverse_sanitize_filename(farm))
            return Response({"farms": for_user_understand}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
