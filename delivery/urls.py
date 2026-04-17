from django.urls import path
from . import views

urlpatterns = [
    # Рейсы
    path('', views.delivery_list, name='delivery_list'),
    path('new/<int:deal_pk>/', views.delivery_create, name='delivery_create'),
    path('<int:pk>/', views.delivery_detail, name='delivery_detail'),
    path('<int:pk>/edit/', views.delivery_edit, name='delivery_edit'),
    path('<int:pk>/status/', views.delivery_status_change, name='delivery_status_change'),

    # Водители
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/new/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),

    # Машины
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/new/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
]
