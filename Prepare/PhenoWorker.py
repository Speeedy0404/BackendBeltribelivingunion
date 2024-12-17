import pandas as pd
from pathlib import Path
import re
from fields import FIELDS


class PhenoWorker:
    def __init__(self, default_path="../files_data/output/pheno"):
        self.default_path = Path(default_path)
        self.default_path.mkdir(parents=True, exist_ok=True)

    def prepare_pheno(self, path):

        file_name = Path(path).stem
        field_spec = FIELDS.get(Path(path).stem)

        if not field_spec:
            print(f"Ошибка: Неизвестный тип файла {file_name}")
            return False

        try:
            df = pd.read_csv(path, delimiter=' ', engine='python')
        except Exception as e:
            print(f"Ошибка при чтении файла {path}: {e}")
            return False

        if not self.header_valid(df):
            print(f"Ошибка: Заголовок файла {file_name} не прошел валидацию.")
            return False
        if not self.header_content_all(df, field_spec, file_name):
            return False

        if 'uniq_key' in df.columns:
            df['uniq_key'] = df['uniq_key'].apply(self.remove_prefix)
        else:
            print(f"Ошибка: Заголовок файла {file_name} не содержит ключей+.")
            return False

        output_file = self.default_path / f"{file_name}.csv"
        df.to_csv(output_file, index=False, sep=' ')
        print(f"Файл {file_name} обработан и сохранен по пути {output_file}")
        return True

    @staticmethod
    def header_valid(df):
        if df.empty or not df.columns[0]:
            return False
        header = ''.join(df.columns)
        return not re.search('[а-яА-Я]', header)

    @staticmethod
    def header_content_all(df, field_spec, file_name):
        df.columns = [col.lower() for col in df.columns]
        required_keys = [field['key'] for field in field_spec['date'] if field['key'] != 'pk_cattle']
        if not all(key in df.columns for key in required_keys):
            print(f"Ошибка: Заголовки файла {file_name} не содержат всех необходимых ключей.")
            return False
        return True

    @staticmethod
    def remove_prefix(value):
        if isinstance(value, str) and (value.endswith('_MA') or value.endswith('_OA')):
            return value[:-3]
        return value
