from rest_framework import generics
from ..serializers import FarmsSerializer
from ..models import Farms


class FarmsListView(generics.ListAPIView):
    serializer_class = FarmsSerializer

    def get_queryset(self):
        queryset = Farms.objects.all()
        name = self.request.query_params.get('name', None)
        code = self.request.query_params.get('code', None)
        if name:
            queryset = queryset.filter(norg__icontains=name)
        elif code:
            queryset = queryset.filter(korg__istartswith=code)
        return queryset
