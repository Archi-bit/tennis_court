from rest_framework.routers import SimpleRouter
from .views import NewsViewSet, GalleryImageViewSet

router = SimpleRouter()

router.register('news', NewsViewSet, basename='news')
router.register('gallery', GalleryImageViewSet, basename='gallery')

urlpatterns = router.urls