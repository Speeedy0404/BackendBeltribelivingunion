from fields import *
from pathlib import Path
from fields import FIELDS

default_path = "../files_data/output/"


def create_list(path):
    return [str(Path(path) / file.name) for file in Path(path).iterdir() if file.is_file()]


from pathlib import Path


def add_import_list(all_path, identifier=None, model=None):
    for path in all_path:
        # print(f"Processing path: {path}")
        path_obj = Path(path)

        # Проверка на корректность пути
        if not path_obj.stem:  # Пустое имя файла ( ".file")
            print(f"Skipping invalid path or missing file name: {path}")
            continue

        if not path_obj.suffix:  # Нет расширения файла
            print(f"Skipping file without extension: {path}")
            continue

        if path_obj.stem not in FIELDS:
            print(f"Missing key in FIELDS for: {path_obj.stem}")
            continue

        date = FIELDS[path_obj.stem]

        if identifier is not None:
            import_list.append([date[identifier], date['date'], path, model])
        else:
            import_list.append([date['model'], date['date'], path])


import_list = []

pk_path = default_path + "pk"
lactation_path = default_path + "lactation"
report_path = default_path + "report"
pheno_path = default_path + "pheno"
pedigree_path = default_path + "pedigree"
books_path = default_path + "books"

pk = create_list(pk_path)
lactation = create_list(lactation_path)
reports = create_list(report_path)
pheno = create_list(pheno_path)
pedigree = create_list(pedigree_path)
books = create_list(books_path)
single_report = None

for path in reports:
    if "FinalReport_ConformationIndex_FULL_without_optim.csv" in path:
        single_report = path
        reports.remove(path)
        break

add_import_list(books)
add_import_list(pk)
add_import_list(lactation)
add_import_list(reports, identifier='pk', model=PK)
add_import_list(reports, identifier='pk_bull', model=PKBull)
if single_report is not None:
    add_import_list([single_report], identifier='pk_bull', model=PKBull)
add_import_list(pheno)
add_import_list(pedigree)
