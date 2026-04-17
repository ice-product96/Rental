from django.urls import path
from . import views

urlpatterns = [
    path('our/', views.our_entity_list, name='documents_our_entity_list'),
    path('our/new/', views.our_entity_create, name='documents_our_entity_create'),
    path('our/<int:pk>/edit/', views.our_entity_edit, name='documents_our_entity_edit'),

    path('templates/', views.document_template_hub, name='documents_template_list'),
    path('templates/contracts/', views.contract_template_list, name='documents_contract_template_list'),
    path('templates/contracts/new/', views.contract_template_create, name='documents_template_create'),
    path('templates/contracts/<int:pk>/edit/', views.contract_template_edit, name='documents_template_edit'),
    path('templates/invoices/', views.invoice_template_list, name='documents_invoice_template_list'),
    path('templates/invoices/new/', views.invoice_template_create, name='documents_invoice_template_create'),
    path('templates/invoices/<int:pk>/edit/', views.invoice_template_edit, name='documents_invoice_template_edit'),
    path('templates/acts/', views.act_template_list, name='documents_act_template_list'),
    path('templates/acts/new/', views.act_template_create, name='documents_act_template_create'),
    path('templates/acts/<int:pk>/edit/', views.act_template_edit, name='documents_act_template_edit'),

    path('contracts/', views.generated_contract_list, name='documents_contract_list'),
    path('contracts/new/', views.generated_contract_create, name='documents_contract_create'),
    path('contracts/<int:pk>/', views.generated_contract_detail, name='documents_contract_detail'),
    path('contracts/<int:pk>/print/', views.generated_contract_print, name='documents_contract_print'),
]
