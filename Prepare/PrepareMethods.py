import os
import csv
import pandas as pd
from pathlib import Path
from fields import FIELDS
from collections import defaultdict

relative_path = "../files_data/input/"


def create_list(path):
    path = relative_path + path
    return [str(Path(path) / file.name) for file in Path(path).iterdir() if
            file.is_file() and file.name != '.DS_Store']


def remove_first_line(path):
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
        if len(lines) > 1:
            with open(path, 'w') as file:
                file.writelines(lines[1:])
            print(f"Первая строка успешно удалена из файла {path}.")
        else:
            print(f"Ошибка: Файл {path} содержит только одну строку, удаление невозможно.")
    except Exception as e:
        print(f"Ошибка при удалении первой строки из файла {path}: {e}")


def convert_to_utf8(path):
    temp_file = path + '.temp'

    try:
        with open(path, 'r', encoding='cp1251') as infile:
            content = infile.read()
    except Exception as e:
        print(f"Ошибка при чтении файла {path} с кодировкой cp1251: {e}")
        return False

    try:
        with open(temp_file, 'w', encoding='utf-8') as outfile:
            outfile.write(content)
    except Exception as e:
        print(f"Ошибка при записи в файл {temp_file}: {e}")
        return False

    os.replace(temp_file, path)
    print(f"Файл {path} успешно преобразован в UTF-8")
    return True


def header_content_all(header, field_spec, file_name):
    header_lower = [col.lower() for col in header]
    required_keys = [field['key'] for field in field_spec['date']]
    if 'pk_cattle' in required_keys:
        required_keys.remove('pk_cattle')

    if not all(key in header_lower for key in required_keys):
        print(f"Ошибка: Заголовки файла {file_name} не содержат всех необходимых ключей.")
        return False
    return True


def remove_bull(file_path):
    df = pd.read_csv(file_path, sep=' ')

    df['sperma'] = pd.to_numeric(df['sperma'], errors='coerce')

    df_unique = df.loc[df.groupby('uniq_key')['sperma'].idxmax()]

    df_unique.to_csv(file_path, index=False, sep=' ')


def delete_duplicates(file_path):
    df = pd.read_csv(file_path, delimiter=' ', encoding='utf-8')

    def filter_rows(group):
        condition = (group['place_of_birth'] != group['kodxoz']) | group['f_regnomer'].isna() | group[
            'f_regnomer'].str.startswith('F')
        filtered_group = group[~condition]
        if not filtered_group.empty:
            if len(filtered_group) > 1:
                return filtered_group.head(1)
            return filtered_group
        return group.head(1)

    result_df = df.groupby('uniq_key', group_keys=False).apply(filter_rows)

    result_df.to_csv(file_path, sep=' ', index=False, encoding='utf-8')


def prepare_pedigree(paths, default_path="../files_data/output/pedigree"):
    default_path = Path(default_path)
    default_path.mkdir(parents=True, exist_ok=True)

    for path in paths:
        file_name = Path(path).stem
        field_spec = FIELDS.get(file_name)

        if not field_spec:
            print(f"Ошибка: Неизвестный тип файла {file_name}")
            return False

        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        header = lines[0].strip().split()
        if not header_content_all(header, field_spec, file_name):
            return False

        rows_dict = defaultdict(list)
        header_lower = [key.lower() for key in header]

        for line in lines[1:]:
            columns = line.strip().split()
            identifier = columns[0][:-3] if columns[0].endswith(('_MA', '_OA')) else columns[0]
            suffix = columns[0][-3:] if columns[0].endswith(('_MA', '_OA')) else ''
            cleaned_columns = [col[:-3] if col.endswith(('_MA', '_OA')) else col for col in columns]
            cleaned_line = ' '.join(cleaned_columns)
            rows_dict[identifier].append((suffix, cleaned_line))

        deleted_rows_count = 0
        filtered_lines = []

        for identifier, rows in rows_dict.items():
            if len(rows) > 1:
                non_ma_rows = [row for row in rows if row[0] != '_MA']
                ma_rows = [row for row in rows if row[0] == '_MA']

                if non_ma_rows:
                    filtered_lines.append(non_ma_rows[0][1])
                    deleted_rows_count += len(ma_rows)
                else:
                    filtered_lines.append(rows[0][1])
                    deleted_rows_count += len(rows) - 1
            else:
                filtered_lines.append(rows[0][1])

        output_path = default_path / f"{file_name}.csv"

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(' '.join(header_lower) + '\n')
            for line in filtered_lines:
                file.write(line + '\n')

        print(f"Файл: {output_path} - Удалено строк: {deleted_rows_count}")


def prepare_reports(paths, default_path="../files_data/output/report"):
    default_path = Path(default_path)
    default_path.mkdir(parents=True, exist_ok=True)

    for path in paths:
        file_name = Path(path).stem
        field_spec = FIELDS.get(file_name)

        if not field_spec:
            print(f"Ошибка: Неизвестный тип файла {file_name}")
            return False

        with open(path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            header = next(csvreader)
            keys = [key.lower() for key in header[0].split(' ')]

            if not header_content_all(keys, field_spec, file_name):
                return False

            rows_dict = defaultdict(list)
            all_rows = []

            for row in csvreader:
                all_rows.append(row[0])
                split_row = row[0].split(' ')
                identifier = split_row[0][:-3]
                suffix = split_row[0][-3:]
                split_row[0] = identifier
                split_row.append(suffix)
                rows_dict[identifier].append(split_row)

            deleted_rows_count = 0

            filtered_rows = []
            for identifier, rows in rows_dict.items():
                if len(rows) > 1:
                    non_ma_rows = [row for row in rows if row[-1] != '_MA']
                    ma_rows = [row for row in rows if row[-1] == '_MA']

                    if non_ma_rows:
                        filtered_rows.append(non_ma_rows[0])
                        deleted_rows_count += len(ma_rows)
                    else:
                        filtered_rows.append(rows[0])
                        deleted_rows_count += len(rows) - 1
                else:
                    filtered_rows.append(rows[0])

            output_path = default_path / f"{file_name}.csv"

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=' ')
                csvwriter.writerow(keys)

                for row in filtered_rows:
                    original_row = row[:-1]
                    csvfile.write(' '.join(original_row) + '\n')

            print(f"Файл: {output_path} - Удалено строк: {deleted_rows_count}")


def process_csv_form_general(paths, default_path="../files_data/output/pk"):
    default_path = Path(default_path)
    default_path.mkdir(parents=True, exist_ok=True)

    for path in paths:
        file_name = Path(path).stem
        field_spec = FIELDS.get(file_name)

        if not field_spec:
            print(f"Ошибка: Неизвестный тип файла {file_name}")
            return False

        with open(path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter='\t')

            header = next(csvreader)
            header = [key.lower() for key in header]

            if not header_content_all(header, field_spec, file_name):
                return False

            uniq_key_index = header.index('uniq_key')

            rows = []

            for row in csvreader:
                row = [value.replace('\t', ' ') for value in row]

                uniq_key = row[uniq_key_index]
                if uniq_key.endswith('_MA') or uniq_key.endswith('_OA'):
                    row[uniq_key_index] = uniq_key[:-3]

                rows.append(row)

        output_path = default_path / f"{file_name}.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=' ')

            csvwriter.writerow(header)

            for row in rows:
                csvfile.write(' '.join(row) + '\n')

        print(f"Файл успешно преобразован и сохранен как: {output_path}")
