from ..models import PK
from rest_framework import generics
from ..serializers import AnimalCowFindSerializer


class FindCowAnimalListView(generics.ListAPIView):
    serializer_class = AnimalCowFindSerializer

    def get_queryset(self):
        queryset = PK.objects.all()

        search = self.request.query_params.get('search_uniq_key', None)
        search_nomer = self.request.query_params.get('search_nomer', None)

        if search:
            queryset = queryset.filter(uniq_key__istartswith=search).order_by('uniq_key')
        if search_nomer:
            queryset = queryset.filter(nomer__istartswith=search_nomer).order_by('uniq_key')
        if len(queryset) > 2000:
            return queryset[0:2000]
        return queryset
