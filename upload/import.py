import csv
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackendBeltribelivingunion.settings')
django.setup()
from Server.serializers import AggregatedDataSerializer, GetBullRatingDataFlat, GetAnimalSerializer
from сonfiguration import *
from datetime import datetime
from django.db import transaction
from django.db.models import Count
from django.contrib.auth.models import User
from multiprocessing import Process
from collections import defaultdict
from django.db.models import Subquery
import numpy as np
from scipy.stats import gaussian_kde
from collections import Counter
import json
import logging
from PIL import Image
import os
import re
from Prepare.ExcelProcessor import ExcelProcessor

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_date(date_str):
    if len(date_str) > 8:
        return datetime.strptime(date_str, '%d.%m.%Y').date() if date_str else None
    else:
        return datetime.strptime(date_str, '%d.%m.%y').date() if date_str else None


def get_pk_dict(rows, keys, model):
    uniq_key_idx = keys.index('uniq_key')

    uniq_key = [row[uniq_key_idx] for row in rows]
    if model is PKBull:
        pk_objects = PKBull.objects.filter(uniq_key__in=uniq_key)
    else:
        pk_objects = PK.objects.filter(uniq_key__in=uniq_key)

    return {obj.uniq_key: obj for obj in pk_objects}


def create_object(model, data, fields, pk=None):
    field_values = {}
    for field in fields:
        if 'int' in field['type']:
            field_values[field['key']] = int(float(data[field['key']])) if data[field['key']] else None
        elif 'float' in field['type']:
            field_values[field['key']] = float(data[field['key']]) if data[field['key']] else None
        elif 'date' in field['type']:
            field_values[field['key']] = parse_date(data[field['key']])
        elif 'str' in field['type']:
            field_values[field['key']] = data[field['key']]
        elif 'foreign_key' in field['type']:
            if pk is None:
                return None
            else:
                field_values[field['key']] = pk
        elif 'branch' in field['type']:
            field_values[field['key']] = BookBranches.objects.get(branch_code=data[field['key']])
    return model(**field_values)


def import_data(chunk, batch_size, model, fields, pk_dict=None):
    data_batch = []
    keys = chunk['keys']
    rows = chunk['rows']

    for row in rows:
        data = dict(zip(keys, row))
        pk_instance = pk_dict.get(data['uniq_key']) if pk_dict else None
        if pk_dict and pk_instance:
            obj = create_object(model, data, fields, pk_instance)
            if obj is not None:
                data_batch.append(obj)
        else:
            obj = create_object(model, data, fields)
            if obj is not None:
                data_batch.append(obj)
        if len(data_batch) >= batch_size:
            with transaction.atomic():
                model.objects.bulk_create(data_batch)
            data_batch = []

    if data_batch:
        with transaction.atomic():
            model.objects.bulk_create(data_batch)


def process_chunk(chunk, batch_size, model, fields, pk_dict=None):
    process = Process(target=import_data,
                      args=(chunk, batch_size, model, fields, pk_dict) if pk_dict else (
                          chunk, batch_size, model, fields))
    process.start()
    return process


def process_chunks(model, fields, file_path, chunk_size=102000, batch_size=5000, pk_model=None):
    processes = []
    start_batch_time = time.time()

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=' ')
        header = next(csvreader)
        rows = []
        for i, row in enumerate(csvreader):
            rows.append(row)
            if (i + 1) % chunk_size == 0:
                chunk = {'keys': header, 'rows': rows}
                pk_dict = None
                if model not in [PK, PKBull, Farms, Parentage, BookBreeds, BookBranches, PKYoungAnimals]:
                    pk_dict = get_pk_dict(rows, header, pk_model)
                process = process_chunk(chunk, batch_size, model, fields, pk_dict)
                processes.append(process)
                rows = []
        if rows:
            chunk = {'keys': header, 'rows': rows}
            pk_dict = None
            if model not in [PK, PKBull, Farms, Parentage, BookBreeds, BookBranches, PKYoungAnimals]:
                pk_dict = get_pk_dict(rows, header, pk_model)
            process = process_chunk(chunk, batch_size, model, fields, pk_dict)
            processes.append(process)

    for process in processes:
        process.join()

    end_batch_time = time.time()
    print(f"Импорт данных из [{file_path}] завершен за {end_batch_time - start_batch_time:.2f} секунд.")


def create_json():
    cow_ids = PK.objects.filter(datavybr__isnull=True).values_list('id', flat=True)
    data = {'cow_ids': list(cow_ids)}

    aggregated_serializer = AggregatedDataSerializer(data=data)
    aggregated_serializer.is_valid(raise_exception=True)
    aggregated_data = aggregated_serializer.data

    cows_with_milkproduction = PK.objects.filter(
        datavybr__isnull=True
    ).annotate(
        milk_count=Count('milkproductionindex')
    ).filter(
        milk_count__gt=0
    )

    result_data = {
        'aggregated_data': aggregated_data,
        'info': {
            'count': "{:,.0f}".format(len(cow_ids)).replace(",", "."),
            'in_assessment': "{:,.0f}".format(cows_with_milkproduction.count()).replace(",", ".")
        }
    }

    json_data = json.dumps(result_data, ensure_ascii=False, indent=4)

    with open('../files_data/json/statistics_data.json', 'w', encoding='utf-8') as file:
        file.write(json_data)

    print("Данные успешно сохранены в файл json")


def process_cow_batch(cows_batch, father_dict, ancestry):
    updated_cows = []

    for cow in cows_batch:
        father_keys = ancestry[cow.uniq_key]
        need_father = father_dict.get(father_keys)
        if need_father:
            cow.kompleks = need_father.kompleks
            cow.lin = need_father.lin
            cow.vet = need_father.vet
            cow.por = need_father.por
            updated_cows.append(cow)

    if updated_cows:
        PK.objects.bulk_update(updated_cows, ['kompleks', 'lin', 'vet', 'por'])


def process_chunk_cow(cows_batch, father_dict, ancestry):
    process = Process(target=process_cow_batch,
                      args=(cows_batch, father_dict, ancestry))
    process.start()
    return process


def add_date_cow_table():
    processes = []
    ancestry = defaultdict(int)

    cow_ids = PK.objects.values_list('uniq_key', flat=True)
    parent = Parentage.objects.filter(uniq_key__in=cow_ids)
    parent = parent.exclude(ukeyo__in=[0, '0', None, ''])

    for parentage in parent:
        if parentage.ukeyo:
            ancestry[parentage.uniq_key] = parentage.ukeyo

    keys_list = list(ancestry.keys())

    father_dict = {father.uniq_key: father for father in PKBull.objects.filter(
        uniq_key__in=Subquery(
            Parentage.objects.filter(uniq_key__in=keys_list).values('ukeyo')
        )
    )}

    ancestry = {key: value for key, value in ancestry.items() if value in father_dict}
    keys_list = list(ancestry.keys())

    all_cows = PK.objects.filter(uniq_key__in=keys_list)

    batch_size = 5000
    cows_batches = [all_cows[i:i + batch_size] for i in range(0, len(all_cows), batch_size)]

    for cows_batch in cows_batches:
        relevant_ancestry = {cow.uniq_key: ancestry[cow.uniq_key] for cow in cows_batch}
        relevant_fathers = {relevant_ancestry[cow.uniq_key]: father_dict[relevant_ancestry[cow.uniq_key]] for cow in
                            cows_batch}

        process = process_chunk_cow(cows_batch, relevant_fathers, relevant_ancestry)
        processes.append(process)

    for process in processes:
        process.join()


def json_data_for_farms(batch):
    data_batch = []

    for farm in batch:
        field_values = {}
        cow_ids = PK.objects.filter(datavybr__isnull=True, kodxoz=farm.korg).values_list('id', flat=True)
        data = {'cow_ids': list(cow_ids)}

        aggregated_serializer = AggregatedDataSerializer(data=data)
        aggregated_serializer.is_valid(raise_exception=True)
        aggregated_data = aggregated_serializer.data

        result_data = {
            'aggregated_data': aggregated_data,
        }

        # field_values['pk_farm'] = farm
        # field_values['aggregated_data'] = result_data
        # data_batch.append(JsonFarmsData(**field_values))

        json_data = JsonFarmsData.objects.get(pk_farm=farm)
        json_data.aggregated_data = result_data
        data_batch.append(json_data)

        if len(data_batch) > 10:
            if data_batch:
                with transaction.atomic():
                    JsonFarmsData.objects.bulk_update(data_batch, ['aggregated_data', ])
            data_batch = []

    if data_batch:
        with transaction.atomic():
            JsonFarmsData.objects.bulk_update(data_batch, ['aggregated_data', ])


def process_chunk_json_aggregated_data(farm_batch):
    process = Process(target=json_data_for_farms,
                      args=(farm_batch,))
    process.start()
    return process


def add_json_aggregated_data_for_farms():
    batch_size = 350
    processes = []
    farms = Farms.objects.all()
    farms_batches = [farms[i:i + batch_size] for i in range(0, len(farms), batch_size)]

    for farm_batch in farms_batches:
        process = process_chunk_json_aggregated_data(farm_batch)
        processes.append(process)

    for process in processes:
        process.join()


def get_density(object_with_data):
    if not object_with_data or len(object_with_data) < 2:
        return [], []

    # Проверяем уникальные значения
    unique_values = np.unique(object_with_data)
    if len(unique_values) < 2:
        # Если данные одномерны или имеют только одну уникальную точку
        return [], []

    try:
        density_data = gaussian_kde(object_with_data)
        x = np.linspace(min(object_with_data), max(object_with_data), 1000).tolist()
        y = density_data(x).tolist()
        return x, y
    except np.linalg.LinAlgError as e:
        # Обработка исключения, если матрица ковариации вырождена
        print(f"Ошибка KDE: {e}")
        return [], []


def get_count(object_with_data):
    count_data = Counter(object_with_data)
    unique_values = list(count_data.keys())
    frequencies = list(count_data.values())
    x = np.array(unique_values).tolist()
    y = np.array(frequencies).tolist()
    return x, y


def create_json_char_data(farm_batch):
    data_batch = []

    for farm in farm_batch:
        cow_ids = PK.objects.filter(datavybr__isnull=True, kodxoz=farm.korg).values_list('id', flat=True)

        data = PK.objects.filter(id__in=cow_ids).select_related(
            'milkproductionindex', 'conformationindex', 'reproductionindex', 'scs', 'complexindex'
        ).values_list(
            'milkproductionindex__ebv_milk', 'milkproductionindex__ebv_fkg', 'milkproductionindex__ebv_fprc',
            'milkproductionindex__ebv_pkg', 'milkproductionindex__ebv_pprc', 'milkproductionindex__rbv_milk',
            'milkproductionindex__rbv_fprc', 'milkproductionindex__rbv_pprc', 'milkproductionindex__rm',
            'conformationindex__rbvt', 'conformationindex__rbvf', 'conformationindex__rbvu', 'conformationindex__rc',
            'reproductionindex__rbv_crh', 'reproductionindex__rbv_ctfi', 'reproductionindex__rbv_do',
            'reproductionindex__rf', 'scs__scs', 'complexindex__pi'
        )

        results = []

        density_fields = [
            ['milkproductionindex__ebv_milk', 'EBV Молоко'],
            ['milkproductionindex__ebv_fkg', 'EBV Жир кг'],
            ['milkproductionindex__ebv_fprc', 'EBV Жир %'],
            ['milkproductionindex__ebv_pkg', 'EBV Белок кг'],
            ['milkproductionindex__ebv_pprc', 'EBV Белок %'],
            ['scs__scs', 'Rscs']
        ]

        count_fields = [
            ['milkproductionindex__rbv_milk', 'RBV Молоко'],
            ['milkproductionindex__rbv_fprc', 'RBV Жир %'],
            ['milkproductionindex__rbv_pprc', 'RBV Белок %'],
            ['milkproductionindex__rm', 'RM'],
            ['conformationindex__rbvt', 'RBVT'],
            ['conformationindex__rbvf', 'RBVF'],
            ['conformationindex__rbvu', 'RBVU'],
            ['conformationindex__rc', 'RC'],
            ['reproductionindex__rbv_crh', 'RCHr'],
            ['reproductionindex__rbv_ctfi', 'RCTF'],
            ['reproductionindex__rbv_do', 'RDO'],
            ['reproductionindex__rf', 'RF'],
            ['complexindex__pi', 'PI']
        ]

        for field in density_fields:
            values = list(data.filter(**{f"{field[0]}__isnull": False}).values_list(field[0], flat=True))
            if values:
                x, y = get_density(values)
                results.append({'name': f'Плотность для {field[1]}', 'data': y, 'labels': x})

        for field in count_fields:
            values = list(
                data.filter(**{f"{field[0]}__isnull": False}).order_by(field[0]).values_list(field[0], flat=True))
            if values:
                x_count, y_count = get_count(values)
                results.append({'name': f'Количество для {field[1]}', 'data': y_count, 'labels': x_count})

        data = {
            'char_data': results
        }

        json_data = JsonFarmsData.objects.get(pk_farm=farm)
        json_data.chart_data = data
        data_batch.append(json_data)

        if len(data_batch) > 10:
            if data_batch:
                with transaction.atomic():
                    JsonFarmsData.objects.bulk_update(data_batch, ['chart_data', ])
            data_batch = []

    if data_batch:
        with transaction.atomic():
            JsonFarmsData.objects.bulk_update(data_batch, ['chart_data', ])


def process_chunk_json_char_data(farm_batch):
    process = Process(target=create_json_char_data,
                      args=(farm_batch,))
    process.start()
    return process


def add_json_char_data_for_farms():
    batch_size = 450
    processes = []
    farms = Farms.objects.all()
    farms_batches = [farms[i:i + batch_size] for i in range(0, len(farms), batch_size)]

    for farm_batch in farms_batches:
        process = process_chunk_json_char_data(farm_batch)
        processes.append(process)

    for process in processes:
        process.join()


def add_rating_for_farms():
    data_farms = Farms.objects.all()

    for farm in data_farms:
        farm.jsonfarmsdata.rating_data = [
            farm.norg,
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['milk']['avg_rm'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['milk']['avg_rm'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvt'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvt'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvf'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvf'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvu'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rbvu'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rc'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['conf']['avg_rc'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['reprod']['avg_rf'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['reprod']['avg_rf'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['com']['avg_pi'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['com']['avg_pi'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_one']['avg_u305'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_one']['avg_u305'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_two']['avg_u305'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_two']['avg_u305'],
            0 if farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_three']['avg_u305'] is None else
            farm.jsonfarmsdata.aggregated_data['aggregated_data']['lak_three']['avg_u305'],
        ]
        farm.jsonfarmsdata.save()


if __name__ == '__main__':
    pass


    # start_time = time.time()
    #
    # for component in import_list:
    #     if len(component) == 3:
    #         process_chunks(model=component[0], fields=component[1], file_path=component[2])
    #     else:
    #         process_chunks(model=component[0], fields=component[1], file_path=component[2], pk_model=component[3])
    #
    # end_time = time.time()
    # print(f"Импорт данных  за {end_time - start_time:.2f} секунд.")
    #
    # start_time = time.time()
    # create_json()
    # end_time = time.time()
    # print(f"Создание json за {end_time - start_time:.2f} секунд.")
    #
    # start_time = time.time()
    # add_date_cow_table()
    # end_time = time.time()
    # print(f"Добавление необходимых данных коровам  за {end_time - start_time:.2f} секунд.")
    #

    # start_time = time.time()
    # add_json_aggregated_data_for_farms()
    # end_time = time.time()
    # print(f"Добавление агрегированых данных для хозяйств {end_time - start_time:.2f} секунд.")

    # start_time = time.time()
    # add_json_char_data_for_farms()
    # end_time = time.time()
    # print(f"Добавление графических данных для хозяйств {end_time - start_time:.2f} секунд.")
    #
    # start_time = time.time()
    # add_rating_for_farms()
    # end_time = time.time()
    # print(f"Добавление рейтинга для хозяйств {end_time - start_time:.2f} секунд.")

    # ----------------------------------------------------------------------------------------------------------------------

    # cow = PK.objects.filter(consolidation=True, kodxoz=39224)
    # for c in cow:
    #     c.consolidation = False
    #     c.save()

    # farm = Farms.objects.get(korg=39224)
    # farm.jsonfarmsdata.parameter_forecasting=None
    # farm.jsonfarmsdata.save()

    # cow = PKYoungAnimals.objects.filter(kodxoz=381878, uniq_key= 'BY000125655411', consolidation=True)
    # for c in cow:
    #     c.consolidation = False
    #     c.save()

    # farms = Farms.objects.all()
    # for farm in farms:
    #     if '/' in farm.norg:
    #         farm.norg = farm.norg.replace('/', '')  # сохраняем результат замены
    #     if '.' in farm.norg:
    #         farm.norg = farm.norg.replace('.', ' ')  # сохраняем результат замены
    #     if farm.norg.endswith(' '):
    #         farm.norg = farm.norg.rstrip()
    #
    #     farm.norg = re.sub(r'\s+', ' ', farm.norg)
    #
    #     farm.save()

    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # перерегенерация отчетов

    # from django.conf import settings
    # from openpyxl import Workbook
    # from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
    # from openpyxl import load_workbook
    #
    # REPORT_DIR = os.path.join(settings.BASE_DIR, 'reports')
    #
    #
    # def create_xlsx_report(cows, bulls, name_xlsx, mode, directory_path, title):
    #     try:
    #
    #         NEW = os.path.join(settings.BASE_DIR, 'reports', 'AAAAA', directory_path)
    #
    #         if not os.path.exists(NEW):
    #             os.makedirs(NEW)
    #
    #         xlsx_path = name_xlsx
    #         bulls_date = PKBull.objects.filter(uniq_key__in=bulls).values_list('nomer', 'uniq_key', 'klichka',
    #                                                                            'milkproductionindexbull__rm')
    #
    #         if mode != 'young':
    #             cows = PK.objects.filter(uniq_key__in=cows).values_list('uniq_key', 'nomer', 'kodfer',
    #                                                                     'milkproductionindex__rm').order_by('kodfer')
    #         else:
    #             cows = PKYoungAnimals.objects.filter(uniq_key__in=cows).values_list('uniq_key', 'nomer',
    #                                                                                 'kodfer').order_by(
    #                 'kodfer')
    #
    #         wb = Workbook()
    #         ws = wb.active
    #         ws.title = "Закрепление"
    #         thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'),
    #                              bottom=Side(style='thin'))
    #
    #         # Установка жирной границы для серой разделительной линии
    #         thick_border = Border(left=Side(style='thick'), right=Side(style='thick'), top=Side(style='thick'),
    #                               bottom=Side(style='thick'))
    #
    #         ws.merge_cells('A1:I2')
    #         ws['A1'] = title
    #         ws['A1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    #         ws['A1'].font = Font(bold=True)
    #         ws.merge_cells('A3:D3')
    #         ws['A3'] = 'Коровы'
    #         ws['A3'].alignment = Alignment(horizontal="center", vertical="center")
    #
    #         ws.merge_cells('F3:I3')
    #         ws['F3'] = 'Быки'
    #         ws['F3'].alignment = Alignment(horizontal="center", vertical="center")
    #
    #         ws['A4'] = 'Индивидуальный номер'
    #         ws['A4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['B4'] = 'Рабочий номер'
    #         ws['B4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['C4'] = 'Код фермы'
    #         ws['C4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['D4'] = 'RM'
    #         ws['D4'].alignment = Alignment(horizontal="center", vertical="center")
    #
    #         ws['F4'] = 'Рабочий номер'
    #         ws['F4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['G4'] = 'Индивидуальный номер'
    #         ws['G4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['H4'] = 'Кличка'
    #         ws['H4'].alignment = Alignment(horizontal="center", vertical="center")
    #         ws['I4'] = 'RM'
    #         ws['I4'].alignment = Alignment(horizontal="center", vertical="center")
    #
    #         for row in ws['A1:I2']:
    #             for cell in row:
    #                 cell.border = thick_border
    #         for row in ws['F3:I3']:
    #             for cell in row:
    #                 cell.border = thick_border
    #         for row in ws['F4:I4']:
    #             for cell in row:
    #                 cell.border = thick_border
    #         for row in ws['A3:D4']:
    #             for cell in row:
    #                 cell.border = thick_border
    #
    #         # Установка ширины столбцов
    #         ws.column_dimensions['A'].width = 25
    #         ws.column_dimensions['B'].width = 18
    #         ws.column_dimensions['C'].width = 12
    #         ws.column_dimensions['D'].width = 10
    #
    #         ws.column_dimensions['E'].width = 15
    #
    #         ws.column_dimensions['F'].width = 18
    #         ws.column_dimensions['G'].width = 25
    #         ws.column_dimensions['H'].width = 25
    #         ws.column_dimensions['I'].width = 10
    #
    #         row_start = 5
    #
    #         for row_num, row_data in enumerate(cows, start=row_start):
    #             cell = ws.cell(row=row_num, column=1, value=row_data[0])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #             cell = ws.cell(row=row_num, column=2, value=row_data[1])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #             cell = ws.cell(row=row_num, column=3, value=row_data[2])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #             if mode != 'young':
    #                 cell = ws.cell(row=row_num, column=4, value=row_data[3])
    #                 cell.border = thin_border
    #                 cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #         for row_num, row_data in enumerate(bulls_date, start=row_start):
    #             cell = ws.cell(row=row_num, column=6, value=row_data[0])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #             cell = ws.cell(row=row_num, column=7, value=row_data[1])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #             cell = ws.cell(row=row_num, column=8, value=row_data[2])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #             cell = ws.cell(row=row_num, column=9, value=row_data[3])
    #             cell.border = thin_border
    #             cell.alignment = Alignment(horizontal="center", vertical="center")
    #
    #         wb.save(xlsx_path)
    #
    #         return xlsx_path
    #     except Exception as e:
    #         print(f"Ошибка при создании xlsx отчета: {e}")
    #         raise
    #
    #
    # farms = next(os.walk(REPORT_DIR))[1]
    #
    # diii = []
    # all_ex_path = []
    # new_path = []
    #
    # for farm in farms:
    #     farm_directory = os.path.join(REPORT_DIR, farm)
    #     if os.path.exists(farm_directory) and os.path.isdir(farm_directory):
    #         reports = [f for f in os.listdir(farm_directory) if f.endswith('.xlsx')]
    #     diii.append((farm, reports))
    #
    # for element in diii:
    #     directory_path = element[0]
    #     reports = element[1]
    #     for filename in reports:
    #         report_path = os.path.join(REPORT_DIR, directory_path, filename)
    #
    #         title = Report.objects.get(path=filename.replace('.xlsx', ''))
    #         all_ex_path.append([report_path, element[0], title.title.split('(')[0]])
    #
    # for path in all_ex_path:
    #     new_path.append([path[0].replace('reports', 'reports\\AAAAA'), path[1], path[2]])
    #
    # for count in range(len(new_path)):
    #     xlsx_path = all_ex_path[count][0]
    #     new_path_p = new_path[count][0]
    #
    #     cow_numbers = []
    #     bull_number = []
    #
    #     if os.path.exists(xlsx_path):
    #
    #         workbook = load_workbook(xlsx_path)
    #         sheet = workbook.active
    #
    #         for row in sheet.iter_rows(min_row=5, max_col=1, values_only=True):
    #             if row[0]:
    #                 cow_numbers.append(row[0])
    #
    #         for row in sheet.iter_rows(min_row=5, max_col=6, values_only=True):
    #             if row[5]:
    #                 bull_number.append(row[5])
    #
    #         cow = PK.objects.filter(uniq_key__in=cow_numbers).values_list('uniq_key', flat=True)
    #
    #         if len(cow) == len(cow_numbers):
    #             create_xlsx_report(cow_numbers, bull_number, new_path_p, 'cow', new_path[count][1], new_path[count][2])
    #         else:
    #             create_xlsx_report(cow_numbers, bull_number, new_path_p, 'young', new_path[count][1],
    #                                new_path[count][2])

    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    # сохранения фото быков ну да
    # from django.core.files import File
    #
    #
    # # Путь к директории с изображениями
    # file_directory = r'D:\Projects\WebApplication\BackendBeltribelivingunion\bull_image'
    #
    # # Получаем список всех файлов в директории
    # files = os.listdir(file_directory)
    #
    # # Фильтруем только изображения (например, .jpg и .jpeg)
    # image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
    #
    # # Проходим по каждому файлу
    # for image_file in image_files:
    #     animal_number = os.path.splitext(image_file)[0]
    #
    #     try:
    #         # Находим быка по номеру
    #         bull = PKBull.objects.get(nomer=animal_number)
    #
    #         # Полный путь к изображению
    #         image_path = os.path.join(file_directory, image_file)
    #
    #         # Открываем файл и сохраняем в поле photo
    #         with open(image_path, 'rb') as f:
    #             bull.photo.save(f'bull_{animal_number}.jpg', File(f), save=True)
    #             print(f'Фото для быка {animal_number} успешно сохранено.')
    #
    #     except PKBull.DoesNotExist:
    #         print(f'Бык с номером {animal_number} не найден в базе данных.')
    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------
    # сжатие фото

    # def compress_image(input_path, output_path, max_size_kb=2000, quality=85):
    #     # Открываем изображение
    #     img = Image.open(input_path)
    #
    #     # Получаем текущие размеры изображения
    #     width, height = img.size
    #
    #     # Уменьшаем размер изображения, если оно слишком большое
    #     max_width = 1920  # Максимальная ширина изображения
    #     max_height = 1080  # Максимальная высота изображения
    #
    #     if width > max_width or height > max_height:
    #         img.thumbnail((max_width, max_height))
    #
    #     # Сжимаем изображение в формат JPEG с нужным качеством
    #     img.save(output_path, 'JPEG', quality=quality)
    #
    #     # Проверяем размер файла и повторяем процесс с меньшим качеством, если нужно
    #     file_size = os.path.getsize(output_path) / 1024  # в KB
    #     while file_size > max_size_kb:
    #         quality -= 5  # Уменьшаем качество на 5
    #         img.save(output_path, 'JPEG', quality=quality)
    #         file_size = os.path.getsize(output_path) / 1024  # обновляем размер файла
    #
    #     print(f"Изображение сохранено с размером {file_size} KB на пути: {output_path}")

    # # Путь к исходной директории с изображениями
    # file_directory = r'D:\Projects\WebApplication\BackendBeltribelivingunion\image\main'
    #
    # # Путь к директории, в которую будем сохранять уменьшенные изображения
    # output_directory = r'D:\Projects\WebApplication\BackendBeltribelivingunion\image\main_k'
    #
    # # Проверяем, существует ли директория для сохранения
    # if not os.path.exists(output_directory):
    #     os.makedirs(output_directory)
    #
    # # Получаем список всех файлов в директории
    # files = os.listdir(file_directory)
    #
    # # Проходим по каждому файлу в директории
    # for file in files:
    #     # Проверяем, что это изображение (например, .jpg или .jpeg)
    #     if file.lower().endswith(('.jpg', '.jpeg', '.png')):
    #         # Путь к исходному файлу
    #         input_path = os.path.join(file_directory, file)
    #
    #         # Путь для сохранения уменьшенного изображения в новой директории
    #         output_path = os.path.join(output_directory, file)
    #
    #         # Вызываем функцию для сжатия изображения
    #         compress_image(input_path, output_path)

    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------

    # импорт полной инфы быка

    # def safe_get(data, key, default=0):
    #     value = data.get(key)
    #     if value is None:
    #         return default
    #     return value
    #
    #
    # def build_tree_info(uniq_key, level=2):
    #     """Функция строит дерево предков до заданного уровня и возвращает данные в виде словаря"""
    #     tree = {}
    #
    #     def recurse(key, current_level, relation=""):
    #         if current_level > level:
    #             return
    #
    #         try:
    #             animal = Parentage.objects.get(uniq_key=key)
    #         except Parentage.DoesNotExist:
    #             return
    #
    #         # Добавляем отца и мать в дерево с учетом уровня и отношения
    #         if animal.ukeyo:
    #             bull_name = PKBull.objects.filter(uniq_key=animal.ukeyo).values_list('klichka', flat=True).first()
    #             tree[f'{relation}O'] = f"{animal.ukeyo} ({bull_name})" if bull_name else animal.ukeyo
    #             recurse(animal.ukeyo, current_level + 1, relation=f'{relation}O ')
    #         if animal.ukeym:
    #             tree[f'{relation}M'] = animal.ukeym
    #             recurse(animal.ukeym, current_level + 1, relation=f'{relation}M ')
    #
    #     recurse(uniq_key, 1)
    #
    #     return tree
    #
    #
    # import pandas as pd
    #
    #
    # all_bulls_data = []
    # for search in ['DE0361239926', 'NL648440402', 'NL718141776', 'BY000017585156', 'BY000084039686',
    #                'DE0360385748', 'BY000039274924', 'BY000081581984']:
    #     queryset = PKBull.objects.filter(
    #         uniq_key=search
    #     ).select_related(
    #         'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
    #         'somaticcellindexbull', 'complexindexbull', 'conformationindexdiagrambull'
    #     ).order_by('id')
    #
    #     if not queryset.exists():
    #         print(f"Нет данных по быку с ключом {search}")
    #         continue
    #
    #     serializer = GetAnimalSerializer(queryset, many=True)
    #     bull_data = serializer.data
    #     tree = build_tree_info(search)
    #
    #     por = BookBreeds.objects.filter(
    #         breed_code=Subquery(
    #             PKBull.objects.filter(uniq_key=search).values('por')
    #         )
    #     ).values_list('breed_name', flat=True)
    #
    #     rojd = Farms.objects.filter(
    #         korg=Subquery(
    #             PKBull.objects.filter(uniq_key=search).values('kodmestrojd')
    #         )
    #     ).values_list('norg', flat=True)
    #
    #     ovner = Farms.objects.filter(
    #         korg=Subquery(
    #             PKBull.objects.filter(uniq_key=search).values('ovner')
    #         )
    #     ).values_list('norg', flat=True)
    #
    #     branch = BookBranches.objects.filter(
    #         branch_code=Subquery(
    #             PKBull.objects.filter(uniq_key=search).values('vet')
    #         )
    #     ).values_list('branch_name', flat=True)
    #
    #     info = {
    #         'uniq_key': bull_data[0].get('uniq_key', ''),
    #         'nomer': bull_data[0].get('nomer', ''),
    #         'klichka': bull_data[0].get('klichka', ''),
    #         'datarojd': bull_data[0].get('datarojd', ''),
    #         'mestorojd': rojd.first() if hasattr(rojd, 'first') else '',
    #         'ovner': ovner.first() if hasattr(ovner, 'first') else '',
    #         'kompleks': bull_data[0].get('kompleks', ''),
    #         'sperma': bull_data[0].get('sperma', ''),
    #         'branch': branch.first() if hasattr(branch, 'first') else '',
    #         'lin': bull_data[0].get('lin_name', ''),
    #         'por': por.first() if hasattr(por, 'first') else ''
    #     }
    #     parent = [
    #         {
    #             'ped': 'father',
    #             'klichka': tree.get('O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('O',
    #                                                                                           '') else 'Нет данных',
    #             'uniq_key': tree.get('O', 'Нет данных').split('(')[0] if '(' in tree.get('O', '') else tree.get('O',
    #                                                                                                             'Нет данных')
    #         },
    #         {
    #             'ped': 'mother',
    #             'klichka': 'Нет клички',
    #             'uniq_key': tree.get('M', 'Нет данных')
    #         },
    #         {
    #             'ped': 'father of father',
    #             'klichka': tree.get('O O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('O O',
    #                                                                                             '') else 'Нет данных',
    #             'uniq_key': tree.get('O O', 'Нет данных').split('(')[0] if '(' in tree.get('O O', '') else tree.get(
    #                 'O O', 'Нет данных')
    #         },
    #         {
    #             'ped': 'mother of mother',
    #             'klichka': 'Нет клички',
    #             'uniq_key': tree.get('M M', 'Нет данных')
    #         },
    #         {
    #             'ped': 'mother of father',
    #             'klichka': 'Нет клички',
    #             'uniq_key': tree.get('O M', 'Нет данных')
    #         },
    #         {
    #             'ped': 'father of mother',
    #             'klichka': tree.get('M O', 'Нет данных').split('(')[1][0:-1] if '(' in tree.get('M O',
    #                                                                                             '') else 'Нет данных',
    #             'uniq_key': tree.get('M O', 'Нет данных').split('(')[0] if '(' in tree.get('M O', '') else tree.get(
    #                 'M O', 'Нет данных')
    #         }
    #     ]
    #     livestock = {
    #         1: 0 if bull_data[0].get('milkproductionindexbull') is None else bull_data[0].get(
    #             'milkproductionindexbull', {}).get('num_daug_est', 0),
    #         4: 0 if bull_data[0].get('reproductionindexbull') is None else bull_data[0].get('reproductionindexbull',
    #                                                                                         {}).get('num_daug_est',
    #                                                                                                 0),
    #         7: 0 if bull_data[0].get('somaticcellindexbull') is None else bull_data[0].get('somaticcellindexbull',
    #                                                                                        {}).get('num_daug_est',
    #                                                                                                0),
    #         0: 0 if bull_data[0].get('conformationindexbull') is None else bull_data[0].get('conformationindexbull',
    #                                                                                         {}).get('num_daug_est',
    #                                                                                                 0)
    #     }
    #     herd = {
    #         1: 0 if bull_data[0].get('milkproductionindexbull') is None else bull_data[0].get(
    #             'milkproductionindexbull', {}).get('num_herd_est', 0),
    #         4: 0 if bull_data[0].get('reproductionindexbull') is None else bull_data[0].get('reproductionindexbull',
    #                                                                                         {}).get('num_herd_est',
    #                                                                                                 0),
    #         7: 0 if bull_data[0].get('somaticcellindexbull') is None else bull_data[0].get('somaticcellindexbull',
    #                                                                                        {}).get('num_herd_est',
    #                                                                                                0),
    #         0: 0 if bull_data[0].get('conformationindexbull') is None else bull_data[0].get('conformationindexbull',
    #                                                                                         {}).get('num_herd_est',
    #                                                                                                 0)
    #     }
    #     indices_bull = [
    #         {
    #             'name': 'M kg',
    #             'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('ebv_milk', 0), 2),
    #             'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rel_milk', 0), 2),
    #             'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rbv_milk', 0), 2)
    #         },
    #         {
    #             'name': 'F kg',
    #             'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('ebv_fkg', 0), 2),
    #             'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rel_fkg', 0), 2),
    #             'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rbv_fkg', 0), 2)
    #         },
    #         {
    #             'name': 'F %',
    #             'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('ebv_fprc', 0), 2),
    #             'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rel_fprc', 0), 2),
    #             'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rbv_fprc', 0), 2)
    #         },
    #         {
    #             'name': 'P kg',
    #             'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('ebv_pkg', 0), 2),
    #             'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rel_pkg', 0), 2),
    #             'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rbv_pkg', 0), 2)
    #         },
    #         {
    #             'name': 'P %',
    #             'evb': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('ebv_pprc', 0), 2),
    #             'rel': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rel_pprc', 0), 2),
    #             'rbv': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('milkproductionindexbull', {}).get('rbv_pprc', 0), 2)
    #         },
    #         {
    #             'name': 'CRH',
    #             'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('ebv_crh', 0), 2),
    #             'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rel_crh', 0), 2),
    #             'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rbv_crh', 0), 2)
    #         },
    #         {
    #             'name': 'CTF',
    #             'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('ebv_ctfi', 0), 2),
    #             'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rel_ctfi', 0), 2),
    #             'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rbv_ctfi', 0), 2)
    #         },
    #         {
    #             'name': 'DO',
    #             'evb': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('ebv_do', 0), 2),
    #             'rel': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rel_do', 0), 2),
    #             'rbv': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 bull_data[0].get('reproductionindexbull', {}).get('rbv_do', 0), 2)
    #         },
    #         {
    #             'name': 'SCS',
    #             'evb': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
    #                 bull_data[0].get('somaticcellindexbull', {}).get('ebv_scs', 0), 2),
    #             'rel': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
    #                 bull_data[0].get('somaticcellindexbull', {}).get('rel_scs', 0), 2),
    #             'rbv': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
    #                 bull_data[0].get('somaticcellindexbull', {}).get('rscs', 0), 2)
    #         }
    #     ]
    #     additional_info = [
    #         {
    #             'name': 'RBVT',
    #             'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvt')),
    #         },
    #         {
    #             'name': 'RBVF',
    #             'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvf')),
    #         },
    #         {
    #             'name': 'RBVU',
    #             'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('conformationindexbull', {}), 'rbvu')),
    #         },
    #         {
    #             'name': 'RC',
    #             'value': 0 if bull_data[0].get('conformationindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('conformationindexbull', {}), 'rc')),
    #         },
    #         {
    #             'name': 'RM',
    #             'value': 0 if bull_data[0].get('milkproductionindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('milkproductionindexbull', {}), 'rm')),
    #         },
    #         {
    #             'name': 'RF',
    #             'value': 0 if bull_data[0].get('reproductionindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('reproductionindexbull', {}), 'rf')),
    #         },
    #         {
    #             'name': 'RSCS',
    #             'value': 0 if bull_data[0].get('somaticcellindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('somaticcellindexbull', {}), 'rscs')),
    #         },
    #         {
    #             'name': 'PI',
    #             'value': 0 if bull_data[0].get('complexindexbull', {}) is None else round(
    #                 safe_get(bull_data[0].get('complexindexbull', {}), 'pi')),
    #         },
    #     ]
    #
    #     result_data = {
    #         'info': info,
    #         'parent': parent,
    #         'livestock': livestock,
    #         'herd': herd,
    #         'indices': indices_bull,
    #         'additional_info': additional_info,
    #         'linear_profile': bull_data[0].get('conformationindexdiagrambull', {}),
    #     }
    #
    #     print(result_data)
    #
    #     # Распаковываем данные в плоский словарь
    #     flat_data = result_data['info'].copy()
    #
    #     # Родители
    #     for p in result_data['parent']:
    #         flat_data[f"{p['ped']} кличка"] = p['klichka']
    #         flat_data[f"{p['ped']} uniq_key"] = p['uniq_key']
    #
    #     # Индексы
    #     for idx in result_data['indices']:
    #         flat_data[f"{idx['name']} EVB"] = idx['evb']
    #         flat_data[f"{idx['name']} REL"] = idx['rel']
    #         flat_data[f"{idx['name']} RBV"] = idx['rbv']
    #
    #     # Доп. инфо
    #     for add in result_data['additional_info']:
    #         flat_data[add['name']] = add['value']
    #
    #     # Линейный профиль
    #     for k, v in result_data['linear_profile'].items():
    #         flat_data[k] = v
    #
    #     # Сохраняем в Excel
    #     all_bulls_data.append(flat_data)
    #
    # df = pd.DataFrame(all_bulls_data)
    # df.to_excel("bull_data.xlsx", index=False)

    # ----------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------