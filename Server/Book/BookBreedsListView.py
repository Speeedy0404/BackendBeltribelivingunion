from ..models import BookBreeds
from rest_framework import generics
from ..serializers import BookBreedsSerializer

class BookBreedsListView(generics.ListAPIView):
    queryset = BookBreeds.objects.all()
    serializer_class = BookBreedsSerializer