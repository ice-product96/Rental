from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('calculator/', views.calculator, name='calculator'),
    path('api/calc/scaffolding/', views.calc_scaffolding_ajax, name='calc_scaffolding_ajax'),
    path('api/calc/tower/', views.calc_tower_ajax, name='calc_tower_ajax'),
]
