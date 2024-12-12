from ..models import Farms
from rest_framework import generics
from ..serializers import BookFarmsSerializer
from django_filters.rest_framework import DjangoFilterBackend


class BookFarmsListView(generics.ListAPIView):
    queryset = Farms.objects.all()
    serializer_class = BookFarmsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'area']
