from PhenoWorker import PhenoWorker
from ExcelProcessor import ExcelProcessor
from PrepareMethods import prepare_reports, prepare_pedigree, process_csv_form_general, delete_duplicates, \
    create_list, remove_first_line, convert_to_utf8, remove_bull

target_file = 'PK_Bull.xlsx'
main_file = 'PK_Young_Animals.xlsx'
save_path = "../files_data/output/"

# remove_first_line(lactation_path[0])
# remove_first_line(lactation_path[0])
# convert_to_utf8(lactation_path[0])

if __name__ == "__main__":
    excel_main_young = None
    excel_bull_path = None
    pk_path = create_list("pk")
    pheno_path = create_list("pheno")
    report_path = create_list("report")
    pedigree_path = create_list("pedigree")
    lactation_path = create_list("lactation")
    excel_young_path = create_list("excel")

    for path in excel_young_path:
        if target_file in path:
            excel_bull_path = path
            excel_young_path.remove(path)
            break
    for path in excel_young_path:
        if main_file in path:
            excel_main_young = path
            break

    processor = PhenoWorker()
    for file_path in pheno_path:
        processor.prepare_pheno(file_path)

    prepare_reports(report_path)
    prepare_pedigree(pedigree_path)
    process_csv_form_general(pk_path)
    process_csv_form_general(lactation_path, save_path + "lactation")

    if excel_main_young is not None:
        processor_main = ExcelProcessor(excel_main_young)

    for file in excel_young_path:
        processor = ExcelProcessor(file)
        processor.remove_first_row()
        processor.remove_columns(-2)
        processor.replace_headers(["uniq_key", "breed", "datarojd", "m_regnomer", "m_breed", "f_regnomer",
                                   "f_breed", "place_of_birth", "kodrn", "kodxoz"])
        processor.replace_text(".  .", None)
        processor.save_to_excel()

    if excel_main_young is not None:
        processor = ExcelProcessor(excel_main_young)
        excel_young_path.remove(excel_main_young)
        for file in excel_young_path:
            processor.merge_with_another_excel(file)
        processor.save_to_csv(save_path + "pk/PK_Young_Animals.csv")
        delete_duplicates(save_path + "pk/PK_Young_Animals.csv")

    if excel_bull_path is not None:
        processor = ExcelProcessor(excel_bull_path)
        processor.remove_first_row()
        processor.remove_columns(-1)
        processor.replace_headers(
            ["nomer", "klichka", "uniq_key", "ovner", "kodmestrojd", "por", "lin", "vet", "kompleks", "mast",
             "datarojd", "datavybr", "sperma", "dliaispolzovaniiavsegodoz"])
        processor.replace_text(".  .", None)
        processor.save_to_excel()
        processor.save_to_csv(save_path + "pk/PK_Bull.csv")
        remove_bull(save_path + "pk/PK_Bull.csv")
