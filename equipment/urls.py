from django.urls import path
from . import views

urlpatterns = [
    path('', views.warehouse_list, name='warehouse_list'),
    path('types/', views.equipment_list, name='equipment_list'),
    path('types/new/', views.equipment_type_create, name='equipment_type_create'),
    path('types/<int:pk>/edit/', views.equipment_type_edit, name='equipment_type_edit'),
    path('movements/', views.movement_list, name='movement_list'),
    path('adjust/<int:pk>/', views.stock_adjust, name='stock_adjust'),
]
