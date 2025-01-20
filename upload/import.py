import csv
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackendBeltribelivingunion.settings')
django.setup()
from Server.serializers import AggregatedDataSerializer
from сonfiguration import *
from datetime import datetime
from django.db import transaction
from django.db.models import Count
from multiprocessing import Process
from collections import defaultdict
from django.db.models import Subquery
import numpy as np
from scipy.stats import gaussian_kde
from collections import Counter
import json
import logging

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

        field_values['pk_farm'] = farm
        field_values['aggregated_data'] = result_data
        data_batch.append(JsonFarmsData(**field_values))

        if len(data_batch) > 10:
            if data_batch:
                with transaction.atomic():
                    JsonFarmsData.objects.bulk_create(data_batch)
            data_batch = []

    if data_batch:
        with transaction.atomic():
            JsonFarmsData.objects.bulk_create(data_batch)


def process_chunk_json_aggregated_data(farm_batch):
    process = Process(target=json_data_for_farms,
                      args=(farm_batch,))
    process.start()
    return process


def add_json_aggregated_data_for_farms():
    batch_size = 450
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


if __name__ == '__main__':
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
    #
    # start_time = time.time()
    # add_json_char_data_for_farms()
    # end_time = time.time()
    # print(f"Добавление графических данных для хозяйств {end_time - start_time:.2f} секунд.")

    # cow = PK.objects.filter(consolidation=True)
    # for c in cow:
    #     c.consolidation = False
    #     c.save()

    from django.contrib.auth.models import User

    # user_m = User.objects.create_user('belPlem_Minsk', 'Minsk@example.com', 'Lbj79gN_HOl27D5')
    # user_m.save()
    #
    # user_g = User.objects.create_user('belPlem_Grodno', 'Grodno@example.com', 'Fzlkjy_E3XO9rD')
    # user_g.save()
    #
    # user_b = User.objects.create_user('belPlem_Brest', 'Brest@example.com', 'lChLxj_L6igW5jT')
    # user_b.save()

    # user_b = User.objects.create_user('belPlem_Vitebsk', 'Vitebsk@example.com', 'K62Sv9_COqT3WTl8')
    # user_b.save()
