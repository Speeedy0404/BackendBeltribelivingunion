from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.urls import reverse
from django.contrib.auth.models import User


class PK(models.Model):
    nomer = models.IntegerField(verbose_name='nomer', null=True, blank=True)
    dopnomer = models.IntegerField(verbose_name='dopnomer', null=True, blank=True)
    uniq_key = models.CharField(max_length=20, unique=True, verbose_name='uniq_key')
    kodrn = models.IntegerField(verbose_name='kodrn', null=True, blank=True)
    kodxoz = models.IntegerField(verbose_name='kodxoz', null=True, blank=True)
    kodfer = models.IntegerField(verbose_name='kodfer', null=True, blank=True)
    datarojd = models.DateField(null=True, blank=True)
    kodmestrojd = models.IntegerField(verbose_name='kodmestorojd', null=True, blank=True)
    datavybr = models.DateField(null=True, blank=True)
    prichvybr = models.IntegerField(verbose_name='prichvybr', null=True, blank=True)
    consolidation = models.BooleanField(verbose_name='consolidation', default=False)

    kompleks = models.IntegerField(verbose_name='kompleks', null=True, blank=True)
    lin = models.ForeignKey('BookBranches', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='lin')
    por = models.IntegerField(verbose_name='por', null=True, blank=True)
    vet = models.IntegerField(verbose_name='vet', null=True, blank=True)

    def __str__(self):
        return f'{self.nomer} - {self.uniq_key}'

    class Meta:
        verbose_name = 'Крупно рогатый скот'
        verbose_name_plural = 'Крупно рогатый скот'


class PKBull(models.Model):
    nomer = models.IntegerField(verbose_name='nomer', null=True, blank=True)
    klichka = models.CharField(max_length=20, verbose_name='klichka', null=True, blank=True)
    uniq_key = models.CharField(max_length=20, unique=True, verbose_name='uniq_key')
    ovner = models.IntegerField(verbose_name='ovner', null=True, blank=True)
    kodmestrojd = models.IntegerField(verbose_name='kodmestrojd', null=True, blank=True)
    por = models.IntegerField(verbose_name='por', null=True, blank=True)
    lin = models.ForeignKey('BookBranches', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='lin')
    vet = models.IntegerField(verbose_name='vet', null=True, blank=True)
    kompleks = models.IntegerField(verbose_name='kompleks', null=True, blank=True)
    mast = models.IntegerField(verbose_name='mast', null=True, blank=True)
    datarojd = models.DateField(null=True, blank=True)
    datavybr = models.DateField(null=True, blank=True)
    sperma = models.IntegerField(verbose_name='sperma', null=True, blank=True)
    dliaispolzovaniiavsegodoz = models.IntegerField(verbose_name='dliaispolzovaniiavsegodoz', null=True, blank=True)
    photo = models.ImageField(upload_to='bull_photos/', null=True, blank=True, verbose_name='Фотография')

    def __str__(self):
        return f'{self.nomer} - {self.uniq_key}'

    class Meta:
        verbose_name = 'Крупно рогатый скот'
        verbose_name_plural = 'Крупно рогатый скот'


class PKYoungAnimals(models.Model):
    nomer = models.IntegerField(verbose_name='nomer', null=True, blank=True)
    uniq_key = models.CharField(max_length=20, unique=True, verbose_name='uniq_key')
    datarojd = models.DateField(null=True, blank=True)
    breed = models.IntegerField(verbose_name='breed', null=True, blank=True)
    f_regnomer = models.CharField(max_length=20, verbose_name='f_regnomer', null=True, blank=True)
    f_breed = models.IntegerField(verbose_name='f_breed', null=True, blank=True)
    m_regnomer = models.CharField(max_length=20, verbose_name='m_regnomer', null=True, blank=True)
    m_breed = models.IntegerField(verbose_name='m_breed', null=True, blank=True)
    kodrn = models.IntegerField(verbose_name='kodrn', null=True, blank=True)
    kodxoz = models.IntegerField(verbose_name='kodxoz', null=True, blank=True)
    kodfer = models.IntegerField(verbose_name='kodfer', null=True, blank=True)
    consolidation = models.BooleanField(verbose_name='consolidation', default=False)


class LAK(models.Model):
    pk_cattle = models.ForeignKey(PK, on_delete=models.CASCADE)
    nomlak = models.IntegerField(verbose_name='nomlak', null=True, blank=True)
    dataosem = models.DateField(verbose_name='dataosem', null=True, blank=True)
    dataotela = models.DateField(verbose_name='dataotela', null=True, blank=True)
    legotel = models.IntegerField(verbose_name='legotel', null=True, blank=True)
    rezotel = models.CharField(max_length=1, verbose_name='rezotel', null=True, blank=True)
    datazapusk = models.DateField(verbose_name='datazapusk', null=True, blank=True)
    u305 = models.IntegerField(verbose_name='u305', null=True, blank=True)
    ulak = models.IntegerField(verbose_name='ulak', null=True, blank=True)
    j305kg = models.IntegerField(verbose_name='j305kg', null=True, blank=True)
    jlakkg = models.IntegerField(verbose_name='jlakkg', null=True, blank=True)
    b305kg = models.IntegerField(verbose_name='b305kg', null=True, blank=True)
    blakkg = models.IntegerField(verbose_name='blakkg', null=True, blank=True)
    somkl = models.IntegerField(verbose_name='somkl', null=True, blank=True)

    def __str__(self):
        return self.uniq_key

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class ComplexIndex(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    rm = models.IntegerField(verbose_name='rm', null=True, blank=True)
    rc = models.IntegerField(verbose_name='rc', null=True, blank=True)
    rf = models.IntegerField(verbose_name='rf', null=True, blank=True)
    rscs = models.IntegerField(verbose_name='rscs', null=True, blank=True)
    pi = models.IntegerField(verbose_name='pi', null=True, blank=True)


class ComplexIndexBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    rm = models.IntegerField(verbose_name='rm', null=True, blank=True)
    rc = models.IntegerField(verbose_name='rc', null=True, blank=True)
    rf = models.IntegerField(verbose_name='rf', null=True, blank=True)
    rscs = models.IntegerField(verbose_name='rscs', null=True, blank=True)
    pi = models.IntegerField(verbose_name='pi', null=True, blank=True)


class ConformationIndex(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_csv = models.FloatField(verbose_name='ebv_csv', null=True, blank=True)
    rel_csv = models.IntegerField(verbose_name='rel_csv', null=True, blank=True)
    ebv_ds = models.FloatField(verbose_name='ebv_ds', null=True, blank=True)
    rel_ds = models.IntegerField(verbose_name='rel_ds', null=True, blank=True)
    ebv_pzkop = models.FloatField(verbose_name='ebv_pzkop', null=True, blank=True)
    rel_pzkop = models.IntegerField(verbose_name='rel_pzkop', null=True, blank=True)
    ebv_rps = models.FloatField(verbose_name='ebv_rps', null=True, blank=True)
    rel_rps = models.IntegerField(verbose_name='rel_rps', null=True, blank=True)
    ebv_pdv = models.FloatField(verbose_name='ebv_pdv', null=True, blank=True)
    rel_pdv = models.IntegerField(verbose_name='rel_pdv', null=True, blank=True)
    ebv_gt = models.FloatField(verbose_name='ebv_gt', null=True, blank=True)
    rel_gt = models.IntegerField(verbose_name='rel_gt', null=True, blank=True)
    ebv_rost = models.FloatField(verbose_name='ebv_rost', null=True, blank=True)
    rel_rost = models.IntegerField(verbose_name='rel_rost', null=True, blank=True)
    ebv_pzkb = models.FloatField(verbose_name='ebv_pzkb', null=True, blank=True)
    rel_pzkb = models.IntegerField(verbose_name='rel_pzkb', null=True, blank=True)
    ebv_gv = models.FloatField(verbose_name='ebv_gv', null=True, blank=True)
    rel_gv = models.IntegerField(verbose_name='rel_gv', null=True, blank=True)
    ebv_szcv = models.FloatField(verbose_name='ebv_szcv', null=True, blank=True)
    rel_szcv = models.IntegerField(verbose_name='rel_szcv', null=True, blank=True)
    ebv_pzkz = models.FloatField(verbose_name='ebv_pzkz', null=True, blank=True)
    rel_pzkz = models.IntegerField(verbose_name='rel_pzkz', null=True, blank=True)
    ebv_rzs = models.FloatField(verbose_name='ebv_rzs', null=True, blank=True)
    rel_rzs = models.IntegerField(verbose_name='rel_rzs', null=True, blank=True)
    ebv_kt = models.FloatField(verbose_name='ebv_kt', null=True, blank=True)
    rel_kt = models.IntegerField(verbose_name='rel_kt', null=True, blank=True)
    ebv_tip = models.FloatField(verbose_name='ebv_tip', null=True, blank=True)
    rel_tip = models.IntegerField(verbose_name='rel_tip', null=True, blank=True)
    ebv_vzcv = models.FloatField(verbose_name='ebv_vzcv', null=True, blank=True)
    rel_vzcv = models.IntegerField(verbose_name='rel_vzcv', null=True, blank=True)
    ebv_shz = models.FloatField(verbose_name='ebv_shz', null=True, blank=True)
    rel_shz = models.IntegerField(verbose_name='rel_shz', null=True, blank=True)
    ebv_sust = models.FloatField(verbose_name='ebv_sust', null=True, blank=True)
    rel_sust = models.IntegerField(verbose_name='rel_sust', null=True, blank=True)
    ebv_pz = models.FloatField(verbose_name='ebv_pz', null=True, blank=True)
    rel_pz = models.IntegerField(verbose_name='rel_pz', null=True, blank=True)
    rbv_tip = models.IntegerField(verbose_name='rbv_tip', null=True, blank=True)
    rbv_kt = models.IntegerField(verbose_name='rbv_kt', null=True, blank=True)
    rbv_rost = models.IntegerField(verbose_name='rbv_rost', null=True, blank=True)
    rbv_gt = models.IntegerField(verbose_name='rbv_gt', null=True, blank=True)
    rbv_pz = models.IntegerField(verbose_name='rbv_pz', null=True, blank=True)
    rbv_shz = models.IntegerField(verbose_name='rbv_shz', null=True, blank=True)
    rbv_pzkb = models.IntegerField(verbose_name='rbv_pzkb', null=True, blank=True)
    rbv_pzkz = models.IntegerField(verbose_name='rbv_pzkz', null=True, blank=True)
    rbv_sust = models.IntegerField(verbose_name='rbv_sust', null=True, blank=True)
    rbv_pzkop = models.IntegerField(verbose_name='rbv_pzkop', null=True, blank=True)
    rbv_gv = models.IntegerField(verbose_name='rbv_gv', null=True, blank=True)
    rbv_pdv = models.IntegerField(verbose_name='rbv_pdv', null=True, blank=True)
    rbv_vzcv = models.IntegerField(verbose_name='rbv_vzcv', null=True, blank=True)
    rbv_szcv = models.IntegerField(verbose_name='rbv_szcv', null=True, blank=True)
    rbv_csv = models.IntegerField(verbose_name='rbv_csv', null=True, blank=True)
    rbv_rps = models.IntegerField(verbose_name='rbv_rps', null=True, blank=True)
    rbv_rzs = models.IntegerField(verbose_name='rbv_rzs', null=True, blank=True)
    rbv_ds = models.IntegerField(verbose_name='rbv_ds', null=True, blank=True)
    rbvt = models.IntegerField(verbose_name='rbvt', null=True, blank=True)
    rbvf = models.IntegerField(verbose_name='rbvf', null=True, blank=True)
    rbvu = models.IntegerField(verbose_name='rbvu', null=True, blank=True)
    rc = models.IntegerField(verbose_name='rc', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class ConformationIndexBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_csv = models.FloatField(verbose_name='ebv_csv', null=True, blank=True)
    rel_csv = models.IntegerField(verbose_name='rel_csv', null=True, blank=True)
    ebv_ds = models.FloatField(verbose_name='ebv_ds', null=True, blank=True)
    rel_ds = models.IntegerField(verbose_name='rel_ds', null=True, blank=True)
    ebv_pzkop = models.FloatField(verbose_name='ebv_pzkop', null=True, blank=True)
    rel_pzkop = models.IntegerField(verbose_name='rel_pzkop', null=True, blank=True)
    ebv_rps = models.FloatField(verbose_name='ebv_rps', null=True, blank=True)
    rel_rps = models.IntegerField(verbose_name='rel_rps', null=True, blank=True)
    ebv_pdv = models.FloatField(verbose_name='ebv_pdv', null=True, blank=True)
    rel_pdv = models.IntegerField(verbose_name='rel_pdv', null=True, blank=True)
    ebv_gt = models.FloatField(verbose_name='ebv_gt', null=True, blank=True)
    rel_gt = models.IntegerField(verbose_name='rel_gt', null=True, blank=True)
    ebv_rost = models.FloatField(verbose_name='ebv_rost', null=True, blank=True)
    rel_rost = models.IntegerField(verbose_name='rel_rost', null=True, blank=True)
    ebv_pzkb = models.FloatField(verbose_name='ebv_pzkb', null=True, blank=True)
    rel_pzkb = models.IntegerField(verbose_name='rel_pzkb', null=True, blank=True)
    ebv_gv = models.FloatField(verbose_name='ebv_gv', null=True, blank=True)
    rel_gv = models.IntegerField(verbose_name='rel_gv', null=True, blank=True)
    ebv_szcv = models.FloatField(verbose_name='ebv_szcv', null=True, blank=True)
    rel_szcv = models.IntegerField(verbose_name='rel_szcv', null=True, blank=True)
    ebv_pzkz = models.FloatField(verbose_name='ebv_pzkz', null=True, blank=True)
    rel_pzkz = models.IntegerField(verbose_name='rel_pzkz', null=True, blank=True)
    ebv_rzs = models.FloatField(verbose_name='ebv_rzs', null=True, blank=True)
    rel_rzs = models.IntegerField(verbose_name='rel_rzs', null=True, blank=True)
    ebv_kt = models.FloatField(verbose_name='ebv_kt', null=True, blank=True)
    rel_kt = models.IntegerField(verbose_name='rel_kt', null=True, blank=True)
    ebv_tip = models.FloatField(verbose_name='ebv_tip', null=True, blank=True)
    rel_tip = models.IntegerField(verbose_name='rel_tip', null=True, blank=True)
    ebv_vzcv = models.FloatField(verbose_name='ebv_vzcv', null=True, blank=True)
    rel_vzcv = models.IntegerField(verbose_name='rel_vzcv', null=True, blank=True)
    ebv_shz = models.FloatField(verbose_name='ebv_shz', null=True, blank=True)
    rel_shz = models.IntegerField(verbose_name='rel_shz', null=True, blank=True)
    ebv_sust = models.FloatField(verbose_name='ebv_sust', null=True, blank=True)
    rel_sust = models.IntegerField(verbose_name='rel_sust', null=True, blank=True)
    ebv_pz = models.FloatField(verbose_name='ebv_pz', null=True, blank=True)
    rel_pz = models.IntegerField(verbose_name='rel_pz', null=True, blank=True)
    rbv_tip = models.IntegerField(verbose_name='rbv_tip', null=True, blank=True)
    rbv_kt = models.IntegerField(verbose_name='rbv_kt', null=True, blank=True)
    rbv_rost = models.IntegerField(verbose_name='rbv_rost', null=True, blank=True)
    rbv_gt = models.IntegerField(verbose_name='rbv_gt', null=True, blank=True)
    rbv_pz = models.IntegerField(verbose_name='rbv_pz', null=True, blank=True)
    rbv_shz = models.IntegerField(verbose_name='rbv_shz', null=True, blank=True)
    rbv_pzkb = models.IntegerField(verbose_name='rbv_pzkb', null=True, blank=True)
    rbv_pzkz = models.IntegerField(verbose_name='rbv_pzkz', null=True, blank=True)
    rbv_sust = models.IntegerField(verbose_name='rbv_sust', null=True, blank=True)
    rbv_pzkop = models.IntegerField(verbose_name='rbv_pzkop', null=True, blank=True)
    rbv_gv = models.IntegerField(verbose_name='rbv_gv', null=True, blank=True)
    rbv_pdv = models.IntegerField(verbose_name='rbv_pdv', null=True, blank=True)
    rbv_vzcv = models.IntegerField(verbose_name='rbv_vzcv', null=True, blank=True)
    rbv_szcv = models.IntegerField(verbose_name='rbv_szcv', null=True, blank=True)
    rbv_csv = models.IntegerField(verbose_name='rbv_csv', null=True, blank=True)
    rbv_rps = models.IntegerField(verbose_name='rbv_rps', null=True, blank=True)
    rbv_rzs = models.IntegerField(verbose_name='rbv_rzs', null=True, blank=True)
    rbv_ds = models.IntegerField(verbose_name='rbv_ds', null=True, blank=True)
    rbvt = models.IntegerField(verbose_name='rbvt', null=True, blank=True)
    rbvf = models.IntegerField(verbose_name='rbvf', null=True, blank=True)
    rbvu = models.IntegerField(verbose_name='rbvu', null=True, blank=True)
    rc = models.IntegerField(verbose_name='rc', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class ConformationIndexDiagramBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    rbv_tip = models.IntegerField(verbose_name='rbv_tip', null=True, blank=True)
    rbv_kt = models.IntegerField(verbose_name='rbv_kt', null=True, blank=True)
    rbv_rost = models.IntegerField(verbose_name='rbv_rost', null=True, blank=True)
    rbv_gt = models.IntegerField(verbose_name='rbv_gt', null=True, blank=True)
    rbv_pz = models.IntegerField(verbose_name='rbv_pz', null=True, blank=True)
    rbv_shz = models.IntegerField(verbose_name='rbv_shz', null=True, blank=True)
    rbv_pzkb = models.IntegerField(verbose_name='rbv_pzkb', null=True, blank=True)
    rbv_pzkz = models.IntegerField(verbose_name='rbv_pzkz', null=True, blank=True)
    rbv_sust = models.IntegerField(verbose_name='rbv_sust', null=True, blank=True)
    rbv_pzkop = models.IntegerField(verbose_name='rbv_pzkop', null=True, blank=True)
    rbv_gv = models.IntegerField(verbose_name='rbv_gv', null=True, blank=True)
    rbv_pdv = models.IntegerField(verbose_name='rbv_pdv', null=True, blank=True)
    rbv_vzcv = models.IntegerField(verbose_name='rbv_vzcv', null=True, blank=True)
    rbv_szcv = models.IntegerField(verbose_name='rbv_szcv', null=True, blank=True)
    rbv_csv = models.IntegerField(verbose_name='rbv_csv', null=True, blank=True)
    rbv_rps = models.IntegerField(verbose_name='rbv_rps', null=True, blank=True)
    rbv_rzs = models.IntegerField(verbose_name='rbv_rzs', null=True, blank=True)
    rbv_ds = models.IntegerField(verbose_name='rbv_ds', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class MilkProductionIndex(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_pprc = models.FloatField(verbose_name='ebv_pprc', null=True, blank=True)
    rel_pprc = models.IntegerField(verbose_name='rel_pprc', null=True, blank=True)
    ebv_fkg = models.FloatField(verbose_name='ebv_fkg', null=True, blank=True)
    rel_fkg = models.IntegerField(verbose_name='rel_fkg', null=True, blank=True)
    ebv_pkg = models.FloatField(verbose_name='ebv_pkg', null=True, blank=True)
    rel_pkg = models.IntegerField(verbose_name='rel_pkg', null=True, blank=True)
    ebv_fprc = models.FloatField(verbose_name='ebv_fprc', null=True, blank=True)
    rel_fprc = models.IntegerField(verbose_name='rel_fprc', null=True, blank=True)
    ebv_milk = models.FloatField(verbose_name='ebv_milk', null=True, blank=True)
    rel_milk = models.IntegerField(verbose_name='rel_milk', null=True, blank=True)
    mp_kg = models.FloatField(verbose_name='mp_kg', null=True, blank=True)
    rbv_milk = models.FloatField(verbose_name='rbv_milk', null=True, blank=True)
    rbv_fkg = models.FloatField(verbose_name='rbv_fkg', null=True, blank=True)
    rbv_pkg = models.FloatField(verbose_name='rbv_pkg', null=True, blank=True)
    rbv_fprc = models.FloatField(verbose_name='rbv_fprc', null=True, blank=True)
    rbv_pprc = models.FloatField(verbose_name='rbv_pprc', null=True, blank=True)
    rm = models.IntegerField(verbose_name='rm', null=True, blank=True)

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class MilkProductionIndexBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_pprc = models.FloatField(verbose_name='ebv_pprc', null=True, blank=True)
    rel_pprc = models.IntegerField(verbose_name='rel_pprc', null=True, blank=True)
    ebv_fkg = models.FloatField(verbose_name='ebv_fkg', null=True, blank=True)
    rel_fkg = models.IntegerField(verbose_name='rel_fkg', null=True, blank=True)
    ebv_pkg = models.FloatField(verbose_name='ebv_pkg', null=True, blank=True)
    rel_pkg = models.IntegerField(verbose_name='rel_pkg', null=True, blank=True)
    ebv_fprc = models.FloatField(verbose_name='ebv_fprc', null=True, blank=True)
    rel_fprc = models.IntegerField(verbose_name='rel_fprc', null=True, blank=True)
    ebv_milk = models.FloatField(verbose_name='ebv_milk', null=True, blank=True)
    rel_milk = models.IntegerField(verbose_name='rel_milk', null=True, blank=True)
    mp_kg = models.FloatField(verbose_name='mp_kg', null=True, blank=True)
    rbv_milk = models.FloatField(verbose_name='rbv_milk', null=True, blank=True)
    rbv_fkg = models.FloatField(verbose_name='rbv_fkg', null=True, blank=True)
    rbv_pkg = models.FloatField(verbose_name='rbv_pkg', null=True, blank=True)
    rbv_fprc = models.FloatField(verbose_name='rbv_fprc', null=True, blank=True)
    rbv_pprc = models.FloatField(verbose_name='rbv_pprc', null=True, blank=True)
    rm = models.IntegerField(verbose_name='rm', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class ReproductionIndex(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_crh = models.FloatField(verbose_name='ebv_crh', null=True, blank=True)
    rel_crh = models.IntegerField(verbose_name='rel_crh', null=True, blank=True)
    ebv_ctfi = models.FloatField(verbose_name='ebv_ctfi', null=True, blank=True)
    rel_ctfi = models.IntegerField(verbose_name='rel_ctfi', null=True, blank=True)
    ebv_do = models.FloatField(verbose_name='ebv_do', null=True, blank=True)
    rel_do = models.IntegerField(verbose_name='rel_do', null=True, blank=True)
    rbv_crh = models.IntegerField(verbose_name='rbv_crh', null=True, blank=True)
    rbv_ctfi = models.IntegerField(verbose_name='rbv_ctfi', null=True, blank=True)
    rbv_do = models.IntegerField(verbose_name='rbv_do', null=True, blank=True)
    rf = models.IntegerField(verbose_name='rf', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class ReproductionIndexBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_crh = models.FloatField(verbose_name='ebv_crh', null=True, blank=True)
    rel_crh = models.IntegerField(verbose_name='rel_crh', null=True, blank=True)
    ebv_ctfi = models.FloatField(verbose_name='ebv_ctfi', null=True, blank=True)
    rel_ctfi = models.IntegerField(verbose_name='rel_ctfi', null=True, blank=True)
    ebv_do = models.FloatField(verbose_name='ebv_do', null=True, blank=True)
    rel_do = models.IntegerField(verbose_name='rel_do', null=True, blank=True)
    rbv_crh = models.IntegerField(verbose_name='rbv_crh', null=True, blank=True)
    rbv_ctfi = models.IntegerField(verbose_name='rbv_ctfi', null=True, blank=True)
    rbv_do = models.IntegerField(verbose_name='rbv_do', null=True, blank=True)
    rf = models.IntegerField(verbose_name='rf', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class SomaticCellIndex(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_scs = models.FloatField(verbose_name='ebv_scs', null=True, blank=True)
    rel_scs = models.IntegerField(verbose_name='rel_scs', null=True, blank=True)
    rscs = models.IntegerField(verbose_name='rscs', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class SomaticCellIndexBull(models.Model):
    pk_cattle = models.OneToOneField(PKBull, on_delete=models.CASCADE)
    num_daug_est = models.FloatField(verbose_name='num_daug_est', null=True, blank=True)
    num_herd_est = models.FloatField(verbose_name='num_herd_est', null=True, blank=True)
    ebv_scs = models.FloatField(verbose_name='ebv_scs', null=True, blank=True)
    rel_scs = models.IntegerField(verbose_name='rel_scs', null=True, blank=True)
    rscs = models.IntegerField(verbose_name='rscs', null=True, blank=True)

    def __str__(self):
        return self.pk_cattle

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class Conform(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    tip = models.IntegerField(verbose_name='tip', null=True, blank=True)
    kt = models.IntegerField(verbose_name='kt', null=True, blank=True)
    rost = models.IntegerField(verbose_name='rost', null=True, blank=True)
    gt = models.IntegerField(verbose_name='gt', null=True, blank=True)
    pz = models.IntegerField(verbose_name='pz', null=True, blank=True)
    shz = models.IntegerField(verbose_name='shz', null=True, blank=True)
    pzkb = models.IntegerField(verbose_name='pzkb', null=True, blank=True)
    pzkz = models.IntegerField(verbose_name='pzkz', null=True, blank=True)
    sust = models.IntegerField(verbose_name='sust', null=True, blank=True)
    pzkop = models.IntegerField(verbose_name='pzkop', null=True, blank=True)
    gv = models.IntegerField(verbose_name='gv', null=True, blank=True)
    pdv = models.IntegerField(verbose_name='pdv', null=True, blank=True)
    vzcv = models.IntegerField(verbose_name='vzcv', null=True, blank=True)
    szcv = models.IntegerField(verbose_name='szcv', null=True, blank=True)
    csv = models.IntegerField(verbose_name='csv', null=True, blank=True)
    rps = models.IntegerField(verbose_name='rps', null=True, blank=True)
    rzs = models.IntegerField(verbose_name='rzs', null=True, blank=True)
    ds = models.IntegerField(verbose_name='ds', null=True, blank=True)

    def __str__(self):
        return self.uniq_key

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class Reprod(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    crh = models.FloatField(verbose_name='crh', null=True, blank=True)
    ctfi = models.FloatField(verbose_name='ctfi', null=True, blank=True)
    do = models.FloatField(verbose_name='do', null=True, blank=True)

    def __str__(self):
        return self.uniq_key

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class Milk(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    milk = models.FloatField(verbose_name='milk', null=True, blank=True)
    fkg = models.FloatField(verbose_name='fkg', null=True, blank=True)
    fprc = models.FloatField(verbose_name='fprc', null=True, blank=True)
    pkg = models.FloatField(verbose_name='pkg', null=True, blank=True)
    pprc = models.FloatField(verbose_name='pprc', null=True, blank=True)

    def __str__(self):
        return self.uniq_key

    class Meta:
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'


class Scs(models.Model):
    pk_cattle = models.OneToOneField(PK, on_delete=models.CASCADE)
    scs = models.FloatField(verbose_name='scs', null=True, blank=True)


class Parentage(models.Model):
    uniq_key = models.CharField(max_length=20, verbose_name='uniq_key')
    ukeyo = models.CharField(max_length=20, null=True, blank=True, verbose_name='ukeyo')
    ukeym = models.CharField(max_length=20, null=True, blank=True, verbose_name='ukeym')

    class Meta:
        verbose_name = 'Родословная'
        verbose_name_plural = 'Родословные'


class Farms(models.Model):
    korg = models.IntegerField(verbose_name='korg', null=True, blank=True)
    norg = models.CharField(max_length=30, verbose_name='norg', null=True, blank=True)
    kter = models.IntegerField(verbose_name='kter', null=True, blank=True)
    area = models.CharField(max_length=20, verbose_name='area', null=True, blank=True)
    region = models.CharField(max_length=20, verbose_name='region', null=True, blank=True)


class JsonFarmsData(models.Model):
    pk_farm = models.OneToOneField(Farms, on_delete=models.CASCADE)
    aggregated_data = models.JSONField(verbose_name='Aggregated Data', null=True, blank=True)
    chart_data = models.JSONField(verbose_name='Chart Data', null=True, blank=True)
    parameter_forecasting = models.JSONField(verbose_name='Parameter Forecasting', null=True, blank=True)
    rating_data = models.JSONField(verbose_name='Rating Data', null=True, blank=True)


class Report(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название отчёта")
    path = models.CharField(max_length=255, verbose_name="Путь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports", verbose_name="Создатель")

    def __str__(self):
        return f"{self.title} (создано {self.user.username})"

    class Meta:
        verbose_name = "Отчёт"
        verbose_name_plural = "Отчёты"
        ordering = ['-created_at']


class BookBranches(models.Model):
    branch_name = models.CharField(max_length=40, verbose_name='branch_name')
    abbreviated_branch_name = models.CharField(max_length=20, verbose_name='abbreviated_branch_name')
    branch_code = models.IntegerField(verbose_name='breed_code', null=True, blank=True)
    kompleks = models.IntegerField(verbose_name='kompleks', null=True, blank=True)


class BookBreeds(models.Model):
    breed_name = models.CharField(max_length=20, verbose_name='breed_name')
    breed_code = models.IntegerField(verbose_name='breed_code', null=True, blank=True)
