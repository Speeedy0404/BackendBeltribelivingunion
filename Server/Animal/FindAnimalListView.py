from ..models import PKBull
from rest_framework import generics
from ..serializers import AnimalFindSerializer


class FindAnimalListView(generics.ListAPIView):
    serializer_class = AnimalFindSerializer

    def get_queryset(self):
        queryset = PKBull.objects.all()

        search = self.request.query_params.get('search_uniq_key', None)
        search_nomer = self.request.query_params.get('search_nomer', None)
        search_klichka = self.request.query_params.get('search_klichka', None)

        if search:
            queryset = queryset.filter(uniq_key__istartswith=search)
        if search_nomer:
            queryset = queryset.filter(nomer__istartswith=search_nomer)
        if search_klichka:
            queryset = queryset.filter(klichka__istartswith=search_klichka)

        return queryset
