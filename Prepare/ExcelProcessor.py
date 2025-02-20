import pandas as pd
import os


class ExcelProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = pd.read_excel(file_path, engine='openpyxl', header=0)

    def remove_first_row(self):
        if not self.df.empty:
            new_headers = self.df.iloc[0]
            self.df = self.df[1:].reset_index(drop=True)
            self.df.columns = new_headers
            print("Первая строка удалена, новые заголовки установлены.")

    def remove_columns(self, n):
        if n > 0:
            self.df = self.df.iloc[:, n:]
            print(f"Удалены первые {n} столбцов.")
        elif n < 0:
            self.df = self.df.iloc[:, :n]
            print(f"Удалены последние {abs(n)} столбцов.")
        else:
            print("Не указан диапазон для удаления столбцов.")

    def replace_headers(self, new_headers):
        if len(new_headers) != len(self.df.columns):
            print("Ошибка: количество новых заголовков не совпадает с количеством столбцов.")
            return False
        self.df.columns = new_headers
        print("Заголовки столбцов заменены.")

    def set_headers(self, new_headers):
        if self.df.empty:
            self.df = pd.DataFrame(columns=new_headers)
        else:
            for i in range(len(new_headers) - len(self.df.columns)):
                self.df[f'Unnamed: {len(self.df.columns) + i}'] = None
        self.df.columns = new_headers
        print("Новые заголовки установлены.")

    def merge_with_another_excel(self, other_file_path):

        other_df = pd.read_excel(other_file_path, engine='openpyxl')

        if list(self.df.columns) == list(other_df.columns):

            self.df = pd.concat([self.df, other_df], ignore_index=True)
            print(f"Данные из {other_file_path} успешно объединены с текущим файлом.")
        else:
            print(f"Ошибка: заголовки столбцов файла {other_file_path} не совпадают с заголовками текущего файла.")

    def save_to_csv(self, output_path=None):
        if output_path is None:
            output_path = os.path.splitext(self.file_path)[0] + '.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8', sep=' ')
        print(f"Файл сохранен как {output_path}")

    def save_to_excel(self, output_path=None):

        if output_path is None:
            directory = os.path.dirname(self.file_path)
            output_path = os.path.join(directory, os.path.basename(self.file_path))

        self.df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"Файл сохранен как {output_path}")

    def replace_text(self, old_value, new_value):
        self.df.replace(to_replace=old_value, value=new_value, inplace=True)
        print(f"Все вхождения '{old_value}' заменены на '{new_value}'.")
