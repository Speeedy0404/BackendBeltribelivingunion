import os
from django.conf import settings
from rest_framework import status
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response

PDF_DIR = os.path.join(settings.BASE_DIR, 'pdf_reports')


class PdfReportView(APIView):

    def get(self, request, filename):
        """Отправка PDF файла для скачивания по его имени."""
        if '__' in filename:
            directory_path = filename.split('__')[0]
        else:
            directory_path = filename.split('.')[0]

        directory_path = directory_path[:-16]

        pdf_path = os.path.join(PDF_DIR, directory_path)
        pdf_path = os.path.join(pdf_path, filename)

        if os.path.exists(pdf_path):
            # Отправляем PDF файл пользователю
            return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=filename)
        else:
            return Response({"error": "Отчет не найден."}, status=status.HTTP_404_NOT_FOUND)
