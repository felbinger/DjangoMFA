from django.urls import path

from .views import Login, Logout, Security

urlpatterns = [
    path('accounts/login/', Login.as_view(), name='login'),
    path('accounts/logout/', Logout.as_view(), name='logout'),
    path('accounts/security/', Security.as_view(http_method_names=['get', 'post']), name='security'),
    path('accounts/security/<uuid:uuid>/', Security.as_view(http_method_names=['put', 'delete']), name='security'),
]
