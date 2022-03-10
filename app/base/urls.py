from django.urls import path

from .views import Home, Settings

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('accounts/profile/', Settings.as_view(), name='settings'),
]
