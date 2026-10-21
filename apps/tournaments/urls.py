from rest_framework.routers import SimpleRouter
from .views import TournamentViewSet

router = SimpleRouter()

router.register('tournaments', TournamentViewSet, basename='tournaments')

urlpatterns = router.urls