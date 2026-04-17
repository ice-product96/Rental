from django.urls import path
from . import views

urlpatterns = [
    path('', views.deal_list, name='deal_list'),
    path('new/', views.deal_create, name='deal_create'),
    path('<int:pk>/', views.deal_detail, name='deal_detail'),
    path('<int:pk>/status/', views.deal_status_change, name='deal_status_change'),
    path('<int:pk>/return/', views.partial_return_create, name='partial_return_create'),
    path('api/stock-check/', views.stock_check_ajax, name='stock_check_ajax'),
    path('api/calculate/', views.calculate_ajax, name='calculate_ajax'),
]
