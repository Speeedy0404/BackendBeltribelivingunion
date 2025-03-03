from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers

from Server.views import *

from Server.Pin.FarmsListView import *
from Server.Pin.IndividualPinView import *
from Server.Pin.ParameterForecastingView import *
from Server.Pin.IndividualBullView import *
from Server.Pin.IndividualCowView import *
from Server.Pin.IndividualYoungView import *
from Server.Pin.ConsolidationView import *

from Server.Animal.FindAnimalListView import *
from Server.Animal.FindCowAnimalListView import *
from Server.Animal.GetInfoView import *
from Server.Animal.GetInfoCowView import *

from Server.Report.ReportView import *
from Server.Report.FarmsReportListView import *
from Server.Report.FarmReportsView import *

from Server.Book.BookFarmsListView import *
from Server.Book.BookBranchesListView import *
from Server.Book.BookBreedsListView import *

urlpatterns = [

    # API для получения списка ферм для закрепления
    path('api/v1/farms/', FarmsListView.as_view(), name='farms-list'),

    # API для получения данных общих данных о ферме
    path('api/v1/individual-pin/', IndividualPinView.as_view(), name='individual-pin'),

    # API для проведения прогнозирования параметров по закреплению сделанных в хоз.
    path('api/v1/parameter-forecasting/', ParameterForecastingView.as_view(), name='parameter-forecasting'),

    # API для получения данных о быках с применением фильтра
    path('api/v1/api/v1/pkbull-individual/', IndividualBullView.as_view(), name='individual-pin-bull'),

    # API для получения данных о коровах с применением фильтра
    path('api/v1/api/v1/pkcow-individual/', IndividualCowView.as_view(), name='individual-pin-cow'),

    # API для получения данных о молодняке с применением фильтра
    path('api/v1/api/v1/young-individual/', IndividualYoungView.as_view(), name='individual-pin-young'),

    # API для проведения закрепления и проверки на инбридинг + кл. родствеников
    path('api/v1/submit-consolidation/', ConsolidationView.as_view(), name='submit-consolidation'),

    # API для получения отчета о закреплении по имени
    path('api/v1/get-report/<str:filename>/', ReportView.as_view(), name='submit-consolidation'),

    # API для общей статистике по всем хоз
    path('api/v1/statistics/', StatisticsListView.as_view(), name='statistics-list'),

    # API для получения рейтинга хоз
    path('api/v1/rating-of-farms/', RatingOfFarms.as_view(), name='rating-of-farms'),

    # API для поиска быка по кличке/номеру/раб. номеру
    path('api/v1/find-animal/', FindAnimalListView.as_view(), name='find-animal'),

    # API для получения информации о быке
    path('api/v1/get-info-animal/', GetInfoView.as_view(), name='get-info-animal'),

    # API для поиска коровы по кличке/номеру/раб. номеру
    path('api/v1/find-cow-animal/', FindCowAnimalListView.as_view(), name='find-animal'),

    # API для получения информации о корове
    path('api/v1/get-info-cow-animal/', GetInfoCowView.as_view(), name='get-info-animal-cow'),

    # API для получения информации о отчетах имеющихся на сервере
    path('api/v1/farms-reports/', FarmsReportListView.as_view(), name='farms-reports'),

    # API для получения отчета по названию хоз
    path('api/v1/farms-reports/<str:farm_name>/', FarmReportsView.as_view(), name='farm-reports'),

    # API для информации о показателях коровы улучшаемых/ухудшаемых/= при закрепелении
    path('api/v1/pkcow-params/<str:uniq_key>/', CowParamsView.as_view(), name='pkcow-params'),

    # API для информации о фермах
    path('api/v1/farms-book/', BookFarmsListView.as_view(), name='farms-list'),

    # API для информации о линиях
    path('api/v1/branches-book/', BookBranchesListView.as_view(), name='branches-list'),

    # API для информации о породах
    path('api/v1/breeds-book/', BookBreedsListView.as_view(), name='breeds-list'),

    path('api/v1/auth', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('admin/', admin.site.urls),
]
