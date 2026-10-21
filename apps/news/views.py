from rest_framework import viewsets
from .models import News, GalleryImage
from .serializers import NewsListSerializer, NewsDetailSerializer, GalleryImageSerializer



class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return NewsListSerializer
        
        return super().get_serializer_class()


class GalleryImageViewSet(viewsets.ModelViewSet):
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer