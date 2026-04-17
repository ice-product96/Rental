from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/deal/<int:deal_pk>/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/status/', views.invoice_status_change, name='invoice_status_change'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('shipping/deal/<int:deal_pk>/', views.shipping_doc_create, name='shipping_doc_create'),
    path('shipping/<int:pk>/print/', views.shipping_doc_print, name='shipping_doc_print'),
    path('non-return/deal/<int:deal_pk>/', views.non_return_act_create, name='non_return_act_create'),
    path('non-return/<int:pk>/print/', views.non_return_act_print, name='non_return_act_print'),
]
