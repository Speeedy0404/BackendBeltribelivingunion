import os
import re
from datetime import datetime
from django.conf import settings
from rest_framework import status
from transliterate import translit
from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Farms, PK, PKYoungAnimals, Parentage

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont, pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, KeepTogether

PDF_DIR = os.path.join(settings.BASE_DIR, 'pdf_reports')
ICON_PATH = os.path.join(settings.BASE_DIR, 'image\\dna.png')
FONT_PATH = os.path.join(settings.BASE_DIR, 'text\\DejaVuSans.ttf')
FONT_BOLD_PATH = os.path.join(settings.BASE_DIR, 'text\\DejaVuSans-Bold.ttf')


def perform_consolidation(cows, mod):
    if mod == 'cow':
        cows = PK.objects.filter(uniq_key__in=cows)
        for cow in cows:
            cow.consolidation = True
            cow.save()
    else:
        cows = PKYoungAnimals.objects.filter(uniq_key__in=cows)
        for cow in cows:
            cow.consolidation = True
            cow.save()


def get_ancestors_for_animals(animals, generations=3):
    ancestry = defaultdict(lambda: defaultdict(list))

    current_animals = set(animals)
    animals_with_few_relatives = []

    for generation in range(1, generations + 1):
        parentages = Parentage.objects.filter(uniq_key__in=current_animals)
        next_animals = set()
        for parentage in parentages:
            if parentage.ukeyo:
                ancestry[parentage.uniq_key][generation].append(parentage.ukeyo)
                next_animals.add(parentage.ukeyo)
            if parentage.ukeym:
                ancestry[parentage.uniq_key][generation].append(parentage.ukeym)
                next_animals.add(parentage.ukeym)
        current_animals = next_animals

    def build_full_ancestry(animal, current_gen=1):
        """Рекурсивно добавляет предков в родословную."""
        if current_gen > generations or animal not in ancestry:
            return []

        parents = ancestry[animal].get(current_gen, [])

        grandparents = []
        for parent in parents:
            grandparents.extend(build_full_ancestry(parent, current_gen + 1))
        return parents + grandparents

    full_ancestry = {}
    for animal in animals:
        full_ancestry[animal] = {}
        parents = build_full_ancestry(animal)

        if len(parents) < 14:
            full_ancestry[animal][1] = parents
            full_ancestry[animal][2] = []
            full_ancestry[animal][3] = []

            animals_with_few_relatives.append({'animal': animal, 'relatives_count': len(parents)})
        else:
            full_ancestry[animal][1] = parents[0:2]
            full_ancestry[animal][2] = parents[2:4] + parents[8:10]
            full_ancestry[animal][3] = parents[4:8] + parents[10:14]

    return full_ancestry, animals_with_few_relatives


def check_inbreeding(bulls, cows):
    """Функция проверяет на инбридинг для списка быков и коров"""
    results = []

    ancestry_bull, not_full_bull = get_ancestors_for_animals(bulls)
    ancestry_cow, not_full_cow = get_ancestors_for_animals(cows)

    print(len(ancestry_bull))
    print(len(ancestry_cow))

    for bull, bull_tree in ancestry_bull.items():
        for cow, cow_tree in ancestry_cow.items():
            for bull_level, bull_ancestors in bull_tree.items():
                for cow_level, cow_ancestors in cow_tree.items():
                    common_ancestors = set(bull_ancestors) & set(cow_ancestors)
                    if common_ancestors:
                        results.append({
                            'bull': bull,
                            'cow': cow,
                            'bull_level': bull_level,
                            'cow_level': cow_level,
                            'common_ancestors': list(common_ancestors)
                        })

    if len(results) < 1:
        results.append('Нет инбредных животных')

    print(len(not_full_bull))
    print(len(not_full_cow))
    print(not_full_cow)

    not_full_cow.extend(not_full_bull)
    return results


def sanitize_filename(name):
    """Преобразование названия в нижний регистр, замена пробелов на подчеркивания и транслитерация."""
    name = translit(name, 'ru', reversed=True)
    name = name.lower()  # Переводим в нижний регистр
    name = re.sub(r'\s+', '_', name)
    return name


def get_unique_pdf_filename(base_name):
    """Создание уникального имени файла с добавлением текущей даты и времени. Создание директории, если ее нет."""
    directory_path = os.path.join(PDF_DIR, f'{base_name}')

    if not os.path.isdir(directory_path):
        os.mkdir(directory_path)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf_path = os.path.join(directory_path, f'{base_name}_{current_time}.pdf')

    return pdf_path


def create_pdf_report(cows, bulls, name_pdf, user_name=None):
    """Создание PDF отчета о закреплении коров за быками."""
    try:
        if not os.path.exists(PDF_DIR):
            os.makedirs(PDF_DIR)

        sanitized_name = sanitize_filename(name_pdf)
        pdf_path = get_unique_pdf_filename(sanitized_name)

        if user_name is not None:
            user_name = sanitize_filename(user_name)
            pdf_path = pdf_path[:-4] + '__' + user_name + pdf_path[-4:]

        print(pdf_path)

        pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', FONT_BOLD_PATH))

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=40, bottomMargin=30)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontName='DejaVu',
            fontSize=16,
            alignment=1,
            spaceAfter=12,
            leading=18
        )
        normal_style = ParagraphStyle(name='NormalStyle', fontName='DejaVu', fontSize=12, spaceAfter=4)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVu'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

        try:
            logo = Image(ICON_PATH, width=30, height=30)
            logo.hAlign = 'LEFT'
        except Exception as e:
            print(f"Ошибка при загрузке иконки: {e}")
            logo = None

        title = Paragraph(
            f"Отчет о закреплении коров за быками в хозяйстве <font name='DejaVu-Bold' size=14>'{name_pdf}'</font>",
            title_style
        )

        header_table_data = [[logo, title]]
        header_table = Table(header_table_data, colWidths=[0.7 * inch, 5.3 * inch])
        header_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT')]))

        current_date = datetime.now().strftime('%d %B %Y')
        current_date_russian = current_date.replace('January', 'Январь').replace('February', 'Февраль').replace(
            'March', 'Март').replace('April', 'Апрель').replace('May', 'Май').replace('June', 'Июнь').replace(
            'July', 'Июль').replace('August', 'Август').replace('September', 'Сентябрь').replace('October',
                                                                                                 'Октябрь').replace(
            'November', 'Ноябрь').replace('December', 'Декабрь')
        date_info = Paragraph(f"Дата: {current_date_russian}", normal_style)

        def draw_separator(canvas, doc):
            canvas.setStrokeColor(colors.black)
            canvas.setLineWidth(1)
            canvas.line(72, 710, 540, 710)

        def create_cow_table(data, title):
            cow_table = Table(data, colWidths=[0.5 * inch, 2 * inch], repeatRows=1, splitByRow=True)
            cow_table.setStyle(table_style)
            return cow_table

        if len(cows) > 33:
            first_cow_data = [['№', 'Коровы']] + [[str(idx), cow] for idx, cow in enumerate(cows[:33], start=1)]
            second_cow_data = [['№', 'Коровы']] + [[str(idx + 33), cow] for idx, cow in enumerate(cows[33:], start=1)]

            first_cow_table = create_cow_table(first_cow_data, 'Коровы')
            second_cow_table = create_cow_table(second_cow_data, 'Коровы')

            bull_data = [['№', 'Быки']]
            bull_data.extend([[str(idx), bull] for idx, bull in enumerate(bulls, start=1)])
            bull_table = create_cow_table(bull_data, 'Быки')

            animal_tables = Table([[first_cow_table, bull_table]], colWidths=[3 * inch, 3 * inch], splitByRow=True)
            animal_tables.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        else:
            cow_data = [['№', 'Коровы']] + [[str(idx), cow] for idx, cow in enumerate(cows, start=1)]
            cow_table = create_cow_table(cow_data, 'Коровы')

            bull_data = [['№', 'Быки']]
            bull_data.extend([[str(idx), bull] for idx, bull in enumerate(bulls, start=1)])
            bull_table = create_cow_table(bull_data, 'Быки')

            animal_tables = Table([[cow_table, bull_table]], colWidths=[3 * inch, 3 * inch], splitByRow=True)
            animal_tables.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        signature = Paragraph("Подпись: Белплемживобъединение", normal_style)
        if len(cows) > 33:

            content = [
                header_table,
                Spacer(1, 20),
                date_info,
                Spacer(1, 20),
                KeepTogether(animal_tables),
                Spacer(1, 20),
                second_cow_table,
                Spacer(1, 20),
                signature
            ]
        else:

            content = [
                header_table,
                Spacer(1, 20),
                date_info,
                Spacer(1, 20),
                KeepTogether(animal_tables),
                Spacer(1, 20),
                signature
            ]
        doc.build(content, onFirstPage=draw_separator)

        return pdf_path

    except Exception as e:
        print(f"Ошибка при создании PDF отчета: {e}")
        raise


class ConsolidationView(APIView):

    def post(self, request):
        data = request.data
        user_name = data['name']
        cows = data['cows']
        bulls = data['bulls']
        mode = data['mode']

        try:
            name_pdf = Farms.objects.get(korg=self.request.headers.get('Kodrn')).norg
            mod = self.request.headers.get('Mode')
        except Farms.DoesNotExist:
            return Response({"error": "Ферма не найдена."}, status=status.HTTP_404_NOT_FOUND)

        try:
            if mod == 'standard':
                inbreeding_results = check_inbreeding(bulls, cows)
                if len(inbreeding_results) == 1 and inbreeding_results[0] == 'Нет инбредных животных':
                    perform_consolidation(cows, mode)
                    if user_name:
                        pdf_file_path = create_pdf_report(cows, bulls, name_pdf, user_name)
                    else:
                        pdf_file_path = create_pdf_report(cows, bulls, name_pdf)
                    return Response({
                        "inbreeding_check": True,
                        "pdf_filename": os.path.basename(pdf_file_path)  # Имя PDF файла для фронтенда
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "inbreeding_check": False,
                        "inbred_animals": inbreeding_results
                    }, status=status.HTTP_200_OK)
            elif mod == "With":
                perform_consolidation(cows, mode)
                if user_name:
                    pdf_file_path = create_pdf_report(cows, bulls, name_pdf, user_name)
                else:
                    pdf_file_path = create_pdf_report(cows, bulls, name_pdf)
                return Response({
                    "inbreeding_check": True,
                    "pdf_filename": os.path.basename(pdf_file_path)
                }, status=status.HTTP_200_OK)
            elif mod == "Without":
                without = data['inbred']
                cows_to_remove = {entry['cow'] for entry in without}
                filtered_cows = [cow for cow in cows if cow not in cows_to_remove]
                perform_consolidation(filtered_cows, mode)
                if user_name:
                    pdf_file_path = create_pdf_report(filtered_cows, bulls, name_pdf, user_name)
                else:
                    pdf_file_path = create_pdf_report(filtered_cows, bulls, name_pdf)
                return Response({
                    "inbreeding_check": True,
                    "pdf_filename": os.path.basename(pdf_file_path)
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
