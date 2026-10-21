from django.urls import path, include

urlpatterns = [
    path('', include('apps.core.urls')),
    path('', include('apps.courts.urls')),
    path('', include('apps.coaches.urls')),
    path('', include('apps.services.urls')),
    path('', include('apps.news.urls')),
    path('', include('apps.tournaments.urls')),
]