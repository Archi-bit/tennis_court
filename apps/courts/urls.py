from rest_framework.routers import SimpleRouter
from .views import CourtTypeViewSet, CourtViewSet

router = SimpleRouter()
router.register('courts', CourtViewSet, basename='court')
router.register('court-types', CourtTypeViewSet, basename='court-types')

urlpatterns = router.urls