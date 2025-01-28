from rest_framework import serializers
from .models import User, PKBull, PK, Farms, ComplexIndex, Scs, ReproductionIndex, ConformationIndex, \
    MilkProductionIndex, ReproductionIndexBull, ConformationIndexBull, MilkProductionIndexBull, ComplexIndexBull, \
    SomaticCellIndex, SomaticCellIndexBull, LAK, Parentage, ConformationIndexDiagramBull, PKYoungAnimals, BookBranches, \
    BookBreeds, Report
from django.db.models import Avg, Count, Max, Min, StdDev, Q, Sum
import numpy as np
from collections import defaultdict


class FarmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farms
        fields = ['korg', 'norg']


class BookBranchesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookBranches
        fields = ['branch_name', 'abbreviated_branch_name', 'branch_code', 'kompleks']


class BookFarmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farms
        fields = ['korg', 'norg', 'kter', 'area', 'region']


class BookBreedsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookBreeds
        fields = ['breed_name', 'breed_code']


class GroupPinSerializer(serializers.Serializer):
    farmCode = serializers.IntegerField()
    gppCode = serializers.IntegerField()


class IndividualPinSerializer(serializers.Serializer):
    farmName = serializers.CharField()
    farmCode = serializers.IntegerField()


class CowListMilkProductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndex
        fields = ['ebv_milk', 'rel_milk', 'ebv_fprc', 'rel_fprc', 'ebv_pprc', 'rel_pprc', 'rm']


class CowConformationIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndex
        fields = ['rc']


class CowReproductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionIndex
        fields = ['rf']


class CowComplexIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplexIndex
        fields = ['pi']


class CowSomaticCellIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SomaticCellIndex
        fields = ['rscs']


class BullListMilkProductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndexBull
        fields = ['ebv_milk', 'rel_milk', 'rm']


class BullConformationIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndexBull
        fields = ['rc']


class BullReproductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionIndexBull
        fields = ['rf']


class BullSomaticCellIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SomaticCellIndexBull
        fields = ['rscs']


class BullComplexIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplexIndexBull
        fields = ['pi']


class CowFatherSerializer(serializers.Serializer):
    lin_name = serializers.CharField()
    kompleks = serializers.CharField()


class PKYoungAnimalsSerializerData(serializers.ModelSerializer):
    father_info = serializers.SerializerMethodField()

    class Meta:
        model = PKYoungAnimals
        fields = ['uniq_key', 'datarojd', 'father_info', 'consolidation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Предварительно загружаем данные о отцах
        cow_ids = [obj.uniq_key for obj in self.instance]
        parent_keys = PKYoungAnimals.objects.filter(uniq_key__in=cow_ids).values_list('uniq_key', 'f_regnomer')
        parent_dict = {uniq_key: f_regnomer for uniq_key, f_regnomer in parent_keys}

        bull_keys = PKBull.objects.filter(
            uniq_key__in=[f_regnomer for uniq_key, f_regnomer in parent_keys]).select_related('lin')
        bull_dict = {bull.uniq_key: bull for bull in bull_keys}

        # Сохраняем предварительно загруженные данные в self
        self.parent_dict = parent_dict
        self.bull_dict = bull_dict

    def get_father_info(self, obj):
        parent_key = self.parent_dict.get(obj.uniq_key)
        bull_info = self.bull_dict.get(parent_key)

        if bull_info:
            return {
                'lin_name': bull_info.lin.abbreviated_branch_name,
                'kompleks': bull_info.kompleks
            }
        else:
            return {
                'lin_name': '',
                'kompleks': ''
            }


class PKSerializerData(serializers.ModelSerializer):
    milkproductionindex = CowListMilkProductionIndexSerializer()
    conformationindex = CowConformationIndexSerializer()
    reproductionindex = CowReproductionIndexSerializer()
    somaticcellindex = CowSomaticCellIndexSerializer()
    complexindex = CowComplexIndexSerializer()

    father_info = serializers.SerializerMethodField()

    class Meta:
        model = PK
        fields = ['id', 'nomer', 'datarojd', 'uniq_key', 'father_info', 'milkproductionindex', 'conformationindex',
                  'reproductionindex', 'somaticcellindex', 'complexindex']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Предварительно загружаем данные о отцах
        cow_ids = [obj.uniq_key for obj in self.instance]
        parent_keys = Parentage.objects.filter(uniq_key__in=cow_ids).values_list('uniq_key', 'ukeyo')
        parent_dict = {uniq_key: ukeyo for uniq_key, ukeyo in parent_keys}

        bull_keys = PKBull.objects.filter(uniq_key__in=[ukeyo for uniq_key, ukeyo in parent_keys]).select_related('lin')
        bull_dict = {bull.uniq_key: bull for bull in bull_keys}

        # Сохраняем предварительно загруженные данные в self
        self.parent_dict = parent_dict
        self.bull_dict = bull_dict

    def get_father_info(self, obj):
        parent_key = self.parent_dict.get(obj.uniq_key)
        bull_info = self.bull_dict.get(parent_key)

        if bull_info:
            return {
                'lin_name': bull_info.lin.abbreviated_branch_name,
                'kompleks': bull_info.kompleks
            }
        else:
            return {
                'lin_name': '',
                'kompleks': ''
            }


class PKBullSerializer(serializers.ModelSerializer):
    milkproductionindexbull = BullListMilkProductionIndexSerializer()
    conformationindexbull = BullConformationIndexSerializer()
    reproductionindexbull = BullReproductionIndexSerializer()
    complexindexbull = BullComplexIndexSerializer()
    somaticcellindexbull = BullSomaticCellIndexSerializer()

    lin_name = serializers.CharField(source='lin.abbreviated_branch_name', read_only=True)

    class Meta:
        model = PKBull
        fields = ['id', 'nomer', 'datarojd', 'uniq_key', 'kompleks', 'sperma', 'milkproductionindexbull',
                  'conformationindexbull', 'reproductionindexbull', 'somaticcellindexbull', 'complexindexbull',
                  'lin_name']


class AnimalFindSerializer(serializers.ModelSerializer):
    class Meta:
        model = PKBull
        fields = ['nomer', 'klichka', 'uniq_key']


class InfoMilkProductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndexBull
        fields = ['num_daug_est', 'num_herd_est',
                  'ebv_milk', 'ebv_fkg', 'ebv_fprc', 'ebv_pkg', 'ebv_pprc',
                  'rel_milk', 'rel_fkg', 'rel_fprc', 'rel_pkg', 'rel_pprc',
                  'rbv_milk', 'rbv_fkg', 'rbv_fprc', 'rbv_pkg', 'rbv_pprc',
                  'rm']


class InfoReproductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionIndexBull
        fields = ['num_daug_est', 'num_herd_est',
                  'ebv_crh', 'ebv_ctfi', 'ebv_do',
                  'rel_crh', 'rel_ctfi', 'rel_do',
                  'rbv_crh', 'rbv_ctfi', 'rbv_do',
                  'rf'
                  ]


class InfoConformationIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndexBull
        fields = ['num_daug_est', 'num_herd_est',
                  'rbvt', 'rbvf', 'rbvu', 'rc']


class InfoSomaticCellIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SomaticCellIndexBull
        fields = ['num_daug_est', 'num_herd_est',
                  'ebv_scs', 'rel_scs', 'rscs']


class InfoConformationIndexDiagramSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndexDiagramBull
        fields = ['rbv_tip', 'rbv_kt', 'rbv_rost', 'rbv_gt', 'rbv_pz', 'rbv_shz', 'rbv_pzkb', 'rbv_pzkz', 'rbv_sust',
                  'rbv_pzkop', 'rbv_gv', 'rbv_pdv', 'rbv_vzcv', 'rbv_szcv', 'rbv_csv', 'rbv_rps', 'rbv_rzs', 'rbv_ds']


class GetAnimalSerializer(serializers.ModelSerializer):
    milkproductionindexbull = InfoMilkProductionIndexSerializer()
    conformationindexbull = InfoConformationIndexSerializer()
    reproductionindexbull = InfoReproductionIndexSerializer()
    somaticcellindexbull = InfoSomaticCellIndexSerializer()
    conformationindexdiagrambull = InfoConformationIndexDiagramSerializer()
    complexindexbull = BullComplexIndexSerializer()
    lin_name = serializers.CharField(source='lin.abbreviated_branch_name', read_only=True)

    class Meta:
        model = PKBull
        fields = ['id', 'nomer', 'datarojd', 'kodmestrojd', 'datavybr', 'klichka', 'uniq_key', 'vet', 'ovner',
                  'kompleks', 'sperma', 'milkproductionindexbull', 'conformationindexbull', 'reproductionindexbull',
                  'somaticcellindexbull', 'lin_name', 'conformationindexdiagrambull', 'complexindexbull']


class AnimalCowFindSerializer(serializers.ModelSerializer):
    class Meta:
        model = PK
        fields = ['nomer', 'uniq_key']


class CowInfoMilkProductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndex
        fields = [
            'ebv_milk', 'ebv_fkg', 'ebv_fprc', 'ebv_pkg', 'ebv_pprc',
            'rel_milk', 'rel_fkg', 'rel_fprc', 'rel_pkg', 'rel_pprc',
            'rbv_milk', 'rbv_fkg', 'rbv_fprc', 'rbv_pkg', 'rbv_pprc',
            'rm']


class CowInfoReproductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionIndex
        fields = [
            'ebv_crh', 'ebv_ctfi', 'ebv_do',
            'rel_crh', 'rel_ctfi', 'rel_do',
            'rbv_crh', 'rbv_ctfi', 'rbv_do',
            'rf'
        ]


class CowInfoConformationIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndex
        fields = [
            'rbv_tip', 'rbv_kt', 'rbv_rost', 'rbv_gt', 'rbv_pz', 'rbv_shz', 'rbv_pzkb', 'rbv_pzkz', 'rbv_sust',
            'rbv_pzkop', 'rbv_gv', 'rbv_pdv', 'rbv_vzcv', 'rbv_szcv', 'rbv_csv', 'rbv_rps', 'rbv_rzs', 'rbv_ds',

            'rbvt', 'rbvf', 'rbvu', 'rc'
        ]


class CowInfoSomaticCellIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SomaticCellIndex
        fields = [
            'ebv_scs', 'rel_scs', 'rscs']


class GetCowAnimalSerializer(serializers.ModelSerializer):
    milkproductionindex = CowInfoMilkProductionIndexSerializer()
    conformationindex = CowInfoConformationIndexSerializer()
    reproductionindex = CowInfoReproductionIndexSerializer()
    somaticcellindex = CowInfoSomaticCellIndexSerializer()
    complexindex = CowComplexIndexSerializer()

    class Meta:
        model = PK
        fields = ['id', 'nomer', 'datarojd', 'kodmestrojd', 'datavybr', 'uniq_key', 'kodxoz',
                  'milkproductionindex', 'conformationindex', 'reproductionindex',
                  'somaticcellindex', 'complexindex']


class CowParamsMilkProductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndex
        fields = [
            'rbv_milk', 'rbv_fkg', 'rbv_fprc', 'rbv_pkg', 'rbv_pprc',
            'rm']


class CowParamsReproductionIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReproductionIndex
        fields = [
            'rbv_crh', 'rbv_ctfi', 'rbv_do',
            'rf'
        ]


class CowParamsSomaticCellIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SomaticCellIndex
        fields = ['rscs']


class GetCowParamsSerializer(serializers.ModelSerializer):
    milkproductionindex = CowParamsMilkProductionIndexSerializer()
    conformationindex = CowInfoConformationIndexSerializer()
    reproductionindex = CowParamsReproductionIndexSerializer()
    somaticcellindex = CowParamsSomaticCellIndexSerializer()
    complexindex = CowComplexIndexSerializer()

    class Meta:
        model = PK
        fields = \
            [
                'milkproductionindex', 'conformationindex', 'reproductionindex',
                'somaticcellindex', 'complexindex'
            ]


class AggregatedDataSerializer(serializers.Serializer):
    cow_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    lak_one = serializers.DictField(read_only=True)
    lak_two = serializers.DictField(read_only=True)
    lak_three = serializers.DictField(read_only=True)
    milk = serializers.DictField(read_only=True)
    median_milk = serializers.DictField(read_only=True)
    conf = serializers.DictField(read_only=True)
    median_conf = serializers.DictField(read_only=True)
    reprod = serializers.DictField(read_only=True)
    reprod_median = serializers.DictField(read_only=True)
    scs = serializers.DictField(read_only=True)
    median_scs = serializers.DictField(read_only=True)
    com = serializers.DictField(read_only=True)
    median_com = serializers.DictField(read_only=True)

    def get_lak_values(self, number, ids):

        average_values = LAK.objects.filter(
            pk_cattle__in=ids,
            nomlak=number
        ).aggregate(
            avg_u305=Avg('u305', filter=Q(u305__isnull=False)),
            count_u305=Count('u305', filter=Q(u305__isnull=False))
        )

        queryset_j = LAK.objects.filter(
            pk_cattle__in=ids,
            nomlak=number,
            j305kg__gt=0,
        )

        queryset_b = LAK.objects.filter(
            pk_cattle__in=ids,
            nomlak=number,
            b305kg__gt=0
        )

        aggregated_j = queryset_j.aggregate(
            sum_u305=Sum('u305'),
            sum_j305kg=Sum('j305kg'),
            avg_j305kg=Avg('j305kg'),
        )

        aggregated_b = queryset_b.aggregate(
            sum_u305=Sum('u305'),
            sum_b305kg=Sum('b305kg'),
            avg_b305kg=Avg('b305kg'),
        )

        sum_u305_j = aggregated_j['sum_u305']
        sum_u305_b = aggregated_b['sum_u305']

        sum_j305kg = aggregated_j['sum_j305kg']
        sum_b305kg = aggregated_b['sum_b305kg']

        avg_j305kg = aggregated_j['avg_j305kg']
        avg_b305kg = aggregated_b['avg_b305kg']

        fat_percentage = (sum_j305kg / sum_u305_j) * 100 if sum_u305_j else 0
        protein_percentage = (sum_b305kg / sum_u305_b) * 100 if sum_u305_b else 0

        return {
            'avg_u305': average_values['avg_u305'],
            'count_u305': average_values['count_u305'],
            'avg_j305kg': avg_j305kg,
            'avg_b305kg': avg_b305kg,
            'fat_percentage': fat_percentage,
            'protein_percentage': protein_percentage
        }

    def get_values_of_data(self, ids, fields, model):
        queryset = model.objects.filter(pk_cattle__in=ids).values_list(*fields)

        aggregation_params = {}
        for field in fields:
            aggregation_params[f'count_{field}'] = Count(field, filter=Q(**{f"{field}__isnull": False}))
            aggregation_params[f'avg_{field}'] = Avg(field, filter=Q(**{f"{field}__isnull": False}))
            aggregation_params[f'min_{field}'] = Min(field, filter=Q(**{f"{field}__isnull": False}))
            aggregation_params[f'max_{field}'] = Max(field, filter=Q(**{f"{field}__isnull": False}))
            aggregation_params[f'stddev_{field}'] = StdDev(field, filter=Q(**{f"{field}__isnull": False}))

        average_values = queryset.aggregate(**aggregation_params)

        median_values = {}
        for field in fields:
            values = queryset.filter(**{f"{field}__isnull": False}).values_list(field, flat=True)
            median_values[f'median_{field}'] = np.median(values) if values else None

        return average_values, median_values

    def to_representation(self, validated_data):
        cow_ids = validated_data.get('cow_ids')

        lak_one = self.get_lak_values(1, cow_ids)
        lak_two = self.get_lak_values(2, cow_ids)
        lak_three = self.get_lak_values(3, cow_ids)
        milk, median_milk = self.get_values_of_data(
            cow_ids,
            ['ebv_milk', 'ebv_fkg', 'ebv_fprc', 'ebv_pkg', 'ebv_pprc', 'rbv_milk', 'rbv_fprc', 'rbv_pprc', 'rm'],
            MilkProductionIndex
        )
        conf, median_conf = self.get_values_of_data(
            cow_ids,
            ['rbvt', 'rbvf', 'rbvu', 'rc'],
            ConformationIndex
        )
        reprod, reprod_median = self.get_values_of_data(
            cow_ids,
            ['rbv_crh', 'rbv_ctfi', 'rbv_do', 'rf'],
            ReproductionIndex
        )
        scs, median_scs = self.get_values_of_data(
            cow_ids,
            ['rscs'],
            SomaticCellIndex
        )
        com, median_com = self.get_values_of_data(
            cow_ids,
            ['pi'],
            ComplexIndex
        )

        return {
            'lak_one': lak_one,
            'lak_two': lak_two,
            'lak_three': lak_three,
            'milk': milk,
            'median_milk': median_milk,
            'conf': conf,
            'median_conf': median_conf,
            'reprod': reprod,
            'reprod_median': reprod_median,
            'scs': scs,
            'median_scs': median_scs,
            'com': com,
            'median_com': median_com
        }


class IndividualBullRmSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndexBull
        fields = ['rm']


class IndividualBullRcSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndexBull
        fields = ['rbvt', 'rbvf', 'rbvu', 'rc']


class IndividualCowRmSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProductionIndex
        fields = ['rm']


class IndividualCowRcSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformationIndex
        fields = ['rbvt', 'rbvf', 'rbvu', 'rc']


class BullIndividualSerializer(serializers.ModelSerializer):
    milkproductionindexbull = IndividualBullRmSerializer()
    conformationindexbull = IndividualBullRcSerializer()
    reproductionindexbull = BullReproductionIndexSerializer()
    complexindexbull = BullComplexIndexSerializer()

    class Meta:
        model = PKBull
        fields = ['id', 'datarojd', 'uniq_key', 'nomer', 'kompleks', 'milkproductionindexbull', 'conformationindexbull',
                  'reproductionindexbull', 'complexindexbull', 'sperma']


class BullIndividualAvgSerializer(serializers.Serializer):
    bull_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    milk = serializers.DictField(read_only=True)
    conf = serializers.DictField(read_only=True)
    reprod = serializers.DictField(read_only=True)
    com = serializers.DictField(read_only=True)

    def get_values_of_data(self, ids, fields, model):
        queryset = model.objects.filter(pk_cattle__in=ids).values_list(*fields)

        aggregation_params = {}
        for field in fields:
            aggregation_params[f'avg_{field}'] = Avg(field, filter=Q(**{f"{field}__isnull": False}))

        average_values = queryset.aggregate(**aggregation_params)

        return average_values

    def to_representation(self, validated_data):
        cow_ids = validated_data.get('bull_ids')

        milk = self.get_values_of_data(
            cow_ids,
            ['rm'],
            MilkProductionIndexBull
        )
        conf = self.get_values_of_data(
            cow_ids,
            ['rbvt', 'rbvf', 'rbvu', 'rc'],
            ConformationIndexBull
        )
        reprod = self.get_values_of_data(
            cow_ids,
            ['rf'],
            ReproductionIndexBull
        )
        com = self.get_values_of_data(
            cow_ids,
            ['pi'],
            ComplexIndexBull
        )

        return {
            'milk': milk,
            'conf': conf,
            'reprod': reprod,
            'com': com,
        }


class CowIndividualSerializer(serializers.ModelSerializer):
    milkproductionindex = IndividualCowRmSerializer()
    conformationindex = IndividualCowRcSerializer()
    reproductionindex = CowReproductionIndexSerializer()
    complexindex = CowComplexIndexSerializer()
    father_info = serializers.SerializerMethodField()

    class Meta:
        model = PK
        fields = ['id', 'datarojd', 'uniq_key', 'consolidation', 'milkproductionindex',
                  'conformationindex', 'reproductionindex', 'complexindex', 'father_info']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cow_ids = [obj.uniq_key for obj in self.instance]
        parent_keys = Parentage.objects.filter(uniq_key__in=cow_ids).values_list('uniq_key', 'ukeyo')
        parent_dict = {uniq_key: ukeyo for uniq_key, ukeyo in parent_keys}

        bull_keys = PKBull.objects.filter(uniq_key__in=[ukeyo for uniq_key, ukeyo in parent_keys])
        bull_dict = {bull.uniq_key: bull for bull in bull_keys}

        self.parent_dict = parent_dict
        self.bull_dict = bull_dict

    def get_father_info(self, obj):
        parent_key = self.parent_dict.get(obj.uniq_key)
        bull_info = self.bull_dict.get(parent_key)

        if bull_info:
            return {
                'kompleks': bull_info.kompleks
            }
        else:
            return {
                'kompleks': ''
            }


class CowIndividualAvgSerializer(serializers.Serializer):
    cow_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    milk = serializers.DictField(read_only=True)
    conf = serializers.DictField(read_only=True)
    reprod = serializers.DictField(read_only=True)
    com = serializers.DictField(read_only=True)

    def get_values_of_data(self, ids, fields, model):
        queryset = model.objects.filter(pk_cattle__in=ids).values_list(*fields)

        aggregation_params = {}
        for field in fields:
            aggregation_params[f'avg_{field}'] = Avg(field, filter=Q(**{f"{field}__isnull": False}))

        average_values = queryset.aggregate(**aggregation_params)

        return average_values

    def to_representation(self, validated_data):
        cow_ids = validated_data.get('cow_ids')

        milk = self.get_values_of_data(
            cow_ids,
            ['rm'],
            MilkProductionIndex
        )
        conf = self.get_values_of_data(
            cow_ids,
            ['rbvt', 'rbvf', 'rbvu', 'rc'],
            ConformationIndex
        )
        reprod = self.get_values_of_data(
            cow_ids,
            ['rf'],
            ReproductionIndex
        )
        com = self.get_values_of_data(
            cow_ids,
            ['pi'],
            ComplexIndex
        )

        return {
            'milk': milk,
            'conf': conf,
            'reprod': reprod,
            'com': com,
        }


class ReportSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ['title', 'path', 'created_at', 'user_name']

    def get_user_name(self, obj):
        return obj.user.username
