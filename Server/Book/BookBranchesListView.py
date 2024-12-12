from ..models import BookBranches
from rest_framework import generics
from ..serializers import BookBranchesSerializer

class BookBranchesListView(generics.ListAPIView):
    queryset = BookBranches.objects.all()
    serializer_class = BookBranchesSerializer
