import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackendBeltribelivingunion.settings')
django.setup()
from Server.models import *

MAPPING = {
    'rbvt': 'RVBT',
    'rbvf': 'RBVF',
    'rbvu': 'RBVU',
    'rc': 'RC',
    'crh': 'CRH',
    'ctfi': 'CTFI',
    'rbv_do': 'DO',
    'rf': 'RF',
    'do': 'DO',
    'pi': 'PI',
    'rscs': 'RSCS',
    'scs': 'SCS',
    'tip': 'Тип',
    'kt': 'Крепость телосложения',
    'rost': 'Рост',
    'gt': 'Глубина туловища',
    'pz': 'Положение зада',
    'shz': 'Ширина зада',
    'pzkb': 'Постановка задних конечностей (сбоку)',
    'pzkz': 'Постановка задних конечностей (сзади)',
    'sust': 'Выраженность скакательного сустава',
    'pzkop': 'Постановка задних копыт',
    'gv': 'Глубина вымени',
    'pdv': 'Прикрепление передней долей вымени',
    'vzcv': 'Высота задней части вымени',
    'szcv': 'Ширина задней части вымени',
    'csv': 'Центральная связка (глубина доли)',
    'rps': 'Расположение передних сосков',
    'rzs': 'Расположение задних сосков',
    'ds': 'Длина сосков (передних)',
    'milk': 'EBV Молоко',
    'ebv_milk': 'EBV Молоко',
    'rbv_milk': 'RBV Молоко',
    'fkg': 'EBV Жир кг',
    'fprc': 'EBV Жир %',
    'ebv_fprc': 'EBV Жир %',
    'rbv_fprc': 'RBV Жир %',
    'pkg': 'EBV Белок кг',
    'pprc': 'EBV Белок %',
    'ebv_pprc': 'EBV Белок %',
    'rbv_pprc': 'RBV Белок %',
    'rm': 'RM',
}
FIELDS = {
    'PK_Cow':
        {
            'model': PK,
            'date':
                [
                    {'key': 'nomer', 'type': 'int'},
                    {'key': 'dopnomer', 'type': 'int'},
                    {'key': 'uniq_key', 'type': 'str'},
                    {'key': 'kodrn', 'type': 'int'},
                    {'key': 'kodxoz', 'type': 'int'},
                    {'key': 'kodfer', 'type': 'int'},
                    {'key': 'datarojd', 'type': 'date'},
                    {'key': 'kodmestrojd', 'type': 'int'},
                    {'key': 'datavybr', 'type': 'date'},
                    {'key': 'prichvybr', 'type': 'int'},
                ]
        },
    'PK_Bull':
        {
            'model': PKBull,
            'date':
                [
                    {'key': 'nomer', 'type': 'int'},
                    {'key': 'klichka', 'type': 'str'},
                    {'key': 'uniq_key', 'type': 'str'},
                    {'key': 'ovner', 'type': 'int'},
                    {'key': 'kodmestrojd', 'type': 'int'},
                    {'key': 'por', 'type': 'int'},
                    {'key': 'lin', 'type': 'branch'},
                    {'key': 'vet', 'type': 'int'},
                    {'key': 'kompleks', 'type': 'int'},
                    {'key': 'mast', 'type': 'int'},
                    {'key': 'datarojd', 'type': 'date'},
                    {'key': 'datavybr', 'type': 'date'},
                    {'key': 'sperma', 'type': 'int'},
                    {'key': 'dliaispolzovaniiavsegodoz', 'type': 'int'},
                ]
        },
    'PK_Young_Animals':
        {
            'model': PKYoungAnimals,
            'date':
                [
                    {'key': 'nomer', 'type': 'str'},
                    {'key': 'uniq_key', 'type': 'str'},
                    {'key': 'datarojd', 'type': 'date'},
                    {'key': 'breed', 'type': 'int'},
                    {'key': 'f_regnomer', 'type': 'str'},
                    {'key': 'f_breed', 'type': 'int'},
                    {'key': 'm_regnomer', 'type': 'str'},
                    {'key': 'm_breed', 'type': 'int'},
                    {'key': 'kodrn', 'type': 'int'},
                    {'key': 'kodxoz', 'type': 'int'},
                    {'key': 'kodfer', 'type': 'int'}
                ]
        },
    'LAK':
        {
            'model': LAK,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'nomlak', 'type': 'int'},
                    {'key': 'dataosem', 'type': 'date'},
                    {'key': 'dataotela', 'type': 'date'},
                    {'key': 'legotel', 'type': 'int'},
                    {'key': 'rezotel', 'type': 'str'},
                    {'key': 'datazapusk', 'type': 'date'},
                    {'key': 'u305', 'type': 'int'},
                    {'key': 'ulak', 'type': 'int'},
                    {'key': 'j305kg', 'type': 'int'},
                    {'key': 'jlakkg', 'type': 'int'},
                    {'key': 'b305kg', 'type': 'int'},
                    {'key': 'blakkg', 'type': 'int'},
                    {'key': 'somkl', 'type': 'int'},
                ]
        },
    'FinalReport_MilkProductivityIndex_FULL':
        {
            'pk': MilkProductionIndex,
            'pk_bull': MilkProductionIndexBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'num_daug_est', 'type': 'float'},
                    {'key': 'num_herd_est', 'type': 'float'},
                    {'key': 'ebv_pprc', 'type': 'float'},
                    {'key': 'rel_pprc', 'type': 'int'},
                    {'key': 'ebv_fkg', 'type': 'float'},
                    {'key': 'rel_fkg', 'type': 'int'},
                    {'key': 'ebv_pkg', 'type': 'float'},
                    {'key': 'rel_pkg', 'type': 'int'},
                    {'key': 'ebv_fprc', 'type': 'float'},
                    {'key': 'rel_fprc', 'type': 'int'},
                    {'key': 'ebv_milk', 'type': 'float'},
                    {'key': 'rel_milk', 'type': 'int'},
                    {'key': 'mp_kg', 'type': 'float'},
                    {'key': 'rbv_milk', 'type': 'float'},
                    {'key': 'rbv_fkg', 'type': 'float'},
                    {'key': 'rbv_pkg', 'type': 'float'},
                    {'key': 'rbv_fprc', 'type': 'float'},
                    {'key': 'rbv_pprc', 'type': 'float'},
                    {'key': 'rm', 'type': 'int'}
                ]
        },
    'FinalReport_ComplexIndex_FULL':
        {
            'pk': ComplexIndex,
            'pk_bull': ComplexIndexBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'rm', 'type': 'int'},
                    {'key': 'rc', 'type': 'int'},
                    {'key': 'rf', 'type': 'int'},
                    {'key': 'rscs', 'type': 'int'},
                    {'key': 'pi', 'type': 'int'},
                ]
        },
    'FinalReport_ConformationIndex_FULL':
        {
            'pk': ConformationIndex,
            'pk_bull': ConformationIndexBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'num_daug_est', 'type': 'float'},
                    {'key': 'num_herd_est', 'type': 'float'},
                    {'key': 'ebv_csv', 'type': 'float'},
                    {'key': 'rel_csv', 'type': 'int'},
                    {'key': 'ebv_ds', 'type': 'float'},
                    {'key': 'rel_ds', 'type': 'int'},
                    {'key': 'ebv_pzkop', 'type': 'float'},
                    {'key': 'rel_pzkop', 'type': 'int'},
                    {'key': 'ebv_rps', 'type': 'float'},
                    {'key': 'rel_rps', 'type': 'int'},
                    {'key': 'ebv_pdv', 'type': 'float'},
                    {'key': 'rel_pdv', 'type': 'int'},
                    {'key': 'ebv_gt', 'type': 'float'},
                    {'key': 'rel_gt', 'type': 'int'},
                    {'key': 'ebv_rost', 'type': 'float'},
                    {'key': 'rel_rost', 'type': 'int'},
                    {'key': 'ebv_pzkb', 'type': 'float'},
                    {'key': 'rel_pzkb', 'type': 'int'},
                    {'key': 'ebv_gv', 'type': 'float'},
                    {'key': 'rel_gv', 'type': 'int'},
                    {'key': 'ebv_szcv', 'type': 'float'},
                    {'key': 'rel_szcv', 'type': 'int'},
                    {'key': 'ebv_pzkz', 'type': 'float'},
                    {'key': 'rel_pzkz', 'type': 'int'},
                    {'key': 'ebv_rzs', 'type': 'float'},
                    {'key': 'rel_rzs', 'type': 'int'},
                    {'key': 'ebv_kt', 'type': 'float'},
                    {'key': 'rel_kt', 'type': 'int'},
                    {'key': 'ebv_tip', 'type': 'float'},
                    {'key': 'rel_tip', 'type': 'int'},
                    {'key': 'ebv_vzcv', 'type': 'float'},
                    {'key': 'rel_vzcv', 'type': 'int'},
                    {'key': 'ebv_shz', 'type': 'float'},
                    {'key': 'rel_shz', 'type': 'int'},
                    {'key': 'ebv_sust', 'type': 'float'},
                    {'key': 'rel_sust', 'type': 'int'},
                    {'key': 'ebv_pz', 'type': 'float'},
                    {'key': 'rel_pz', 'type': 'int'},
                    {'key': 'rbv_tip', 'type': 'int'},
                    {'key': 'rbv_kt', 'type': 'int'},
                    {'key': 'rbv_rost', 'type': 'int'},
                    {'key': 'rbv_gt', 'type': 'int'},
                    {'key': 'rbv_pz', 'type': 'int'},
                    {'key': 'rbv_shz', 'type': 'int'},
                    {'key': 'rbv_pzkb', 'type': 'int'},
                    {'key': 'rbv_pzkz', 'type': 'int'},
                    {'key': 'rbv_sust', 'type': 'int'},
                    {'key': 'rbv_pzkop', 'type': 'int'},
                    {'key': 'rbv_gv', 'type': 'int'},
                    {'key': 'rbv_pdv', 'type': 'int'},
                    {'key': 'rbv_vzcv', 'type': 'int'},
                    {'key': 'rbv_szcv', 'type': 'int'},
                    {'key': 'rbv_csv', 'type': 'int'},
                    {'key': 'rbv_rps', 'type': 'int'},
                    {'key': 'rbv_rzs', 'type': 'int'},
                    {'key': 'rbv_ds', 'type': 'int'},
                    {'key': 'rbvt', 'type': 'int'},
                    {'key': 'rbvf', 'type': 'int'},
                    {'key': 'rbvu', 'type': 'int'},
                    {'key': 'rc', 'type': 'int'}
                ]
        },
    'FinalReport_ConformationIndex_FULL_without_optim':
        {

            'pk_bull': ConformationIndexDiagramBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'rbv_tip', 'type': 'int'},
                    {'key': 'rbv_kt', 'type': 'int'},
                    {'key': 'rbv_rost', 'type': 'int'},
                    {'key': 'rbv_gt', 'type': 'int'},
                    {'key': 'rbv_pz', 'type': 'int'},
                    {'key': 'rbv_shz', 'type': 'int'},
                    {'key': 'rbv_pzkb', 'type': 'int'},
                    {'key': 'rbv_pzkz', 'type': 'int'},
                    {'key': 'rbv_sust', 'type': 'int'},
                    {'key': 'rbv_pzkop', 'type': 'int'},
                    {'key': 'rbv_gv', 'type': 'int'},
                    {'key': 'rbv_pdv', 'type': 'int'},
                    {'key': 'rbv_vzcv', 'type': 'int'},
                    {'key': 'rbv_szcv', 'type': 'int'},
                    {'key': 'rbv_csv', 'type': 'int'},
                    {'key': 'rbv_rps', 'type': 'int'},
                    {'key': 'rbv_rzs', 'type': 'int'},
                    {'key': 'rbv_ds', 'type': 'int'},
                ]
        },
    'FinalReport_ReproductionIndex_FULL':
        {
            'pk': ReproductionIndex,
            'pk_bull': ReproductionIndexBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'num_daug_est', 'type': 'float'},
                    {'key': 'num_herd_est', 'type': 'float'},
                    {'key': 'ebv_crh', 'type': 'float'},
                    {'key': 'rel_crh', 'type': 'int'},
                    {'key': 'ebv_ctfi', 'type': 'float'},
                    {'key': 'rel_ctfi', 'type': 'int'},
                    {'key': 'ebv_do', 'type': 'float'},
                    {'key': 'rel_do', 'type': 'int'},
                    {'key': 'rbv_crh', 'type': 'int'},
                    {'key': 'rbv_ctfi', 'type': 'int'},
                    {'key': 'rbv_do', 'type': 'int'},
                    {'key': 'rf', 'type': 'int'}
                ]
        },
    'FinalReport_SomaticCellIndex_FULL':
        {
            'pk': SomaticCellIndex,
            'pk_bull': SomaticCellIndexBull,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'num_daug_est', 'type': 'float'},
                    {'key': 'num_herd_est', 'type': 'float'},
                    {'key': 'ebv_scs', 'type': 'float'},
                    {'key': 'rel_scs', 'type': 'int'},
                    {'key': 'rscs', 'type': 'int'}
                ]
        },
    'pheno_MILK':
        {
            'model': Milk,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'milk', 'type': 'float'},
                    {'key': 'fkg', 'type': 'float'},
                    {'key': 'fprc', 'type': 'float'},
                    {'key': 'pkg', 'type': 'float'},
                    {'key': 'pprc', 'type': 'float'}
                ]

        },
    'pheno_CONFORM':
        {
            'model': Conform,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'tip', 'type': 'int'},
                    {'key': 'kt', 'type': 'int'},
                    {'key': 'rost', 'type': 'int'},
                    {'key': 'gt', 'type': 'int'},
                    {'key': 'pz', 'type': 'int'},
                    {'key': 'shz', 'type': 'int'},
                    {'key': 'pzkb', 'type': 'int'},
                    {'key': 'pzkz', 'type': 'int'},
                    {'key': 'sust', 'type': 'int'},
                    {'key': 'pzkop', 'type': 'int'},
                    {'key': 'gv', 'type': 'int'},
                    {'key': 'pdv', 'type': 'int'},
                    {'key': 'vzcv', 'type': 'int'},
                    {'key': 'szcv', 'type': 'int'},
                    {'key': 'csv', 'type': 'int'},
                    {'key': 'rps', 'type': 'int'},
                    {'key': 'rzs', 'type': 'int'},
                    {'key': 'ds', 'type': 'int'}
                ]
        },
    'pheno_REPROD':
        {
            'model': Reprod,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'crh', 'type': 'float'},
                    {'key': 'ctfi', 'type': 'float'},
                    {'key': 'do', 'type': 'float'}
                ]
        },
    'pheno_SCS':
        {
            'model': Scs,
            'date':
                [
                    {'key': 'pk_cattle', 'type': 'foreign_key'},
                    {'key': 'scs', 'type': 'float'}
                ]
        },
    'ped':
        {
            'model': Parentage,
            'date':
                [
                    {'key': 'uniq_key', 'type': 'str'},
                    {'key': 'ukeyo', 'type': 'str'},
                    {'key': 'ukeym', 'type': 'str'}
                ]
        },
    'Breeds':
        {
            'model': BookBreeds,
            'date':
                [
                    {'key': 'breed_name', 'type': 'str'},
                    {'key': 'breed_code', 'type': 'str'},
                ]
        },
    'Branch':
        {
            'model': BookBranches,
            'date':
                [
                    {'key': 'branch_name', 'type': 'str'},
                    {'key': 'abbreviated_branch_name', 'type': 'str'},
                    {'key': 'kompleks', 'type': 'int'},
                    {'key': 'branch_code', 'type': 'int'},
                ]
        },
    'Farm':
        {
            'model': Farms,
            'date':
                [
                    {'key': 'korg', 'type': 'int'},
                    {'key': 'norg', 'type': 'str'},
                    {'key': 'kter', 'type': 'int'},
                    {'key': 'area', 'type': 'str'},
                    {'key': 'region', 'type': 'str'},
                ]
        },
}
