import csv
import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()
from Server.serializers import AggregatedDataSerializer
from сonfiguration import *
from datetime import datetime
from django.db import transaction
from django.db.models import Count
from multiprocessing import Process
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


if __name__ == '__main__':
    start_time = time.time()

    for component in import_list:
        if len(component) == 3:
            process_chunks(model=component[0], fields=component[1], file_path=component[2])
        else:
            process_chunks(model=component[0], fields=component[1], file_path=component[2], pk_model=component[3])

    end_time = time.time()
    print(f"Импорт данных  за {end_time - start_time:.2f} секунд.")

    create_json()
