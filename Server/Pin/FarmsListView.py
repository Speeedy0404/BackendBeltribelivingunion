from rest_framework import generics
from ..serializers import FarmsSerializer
from ..models import Farms


class FarmsListView(generics.ListAPIView):
    serializer_class = FarmsSerializer

    def get_queryset(self):
        queryset = Farms.objects.all()
        search = self.request.query_params.get('search', None)
        search_code = self.request.query_params.get('search_code', None)
        if search:
            queryset = queryset.filter(norg__icontains=search)
        if search_code:
            queryset = queryset.filter(korg__istartswith=search_code)
        return queryset
