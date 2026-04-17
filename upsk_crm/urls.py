from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('dashboard'), name='home'),
    path('', include('pricing.urls')),
    path('clients/', include('clients.urls')),
    path('equipment/', include('equipment.urls')),
    path('deals/', include('deals.urls')),
    path('billing/', include('billing.urls')),
    path('documents/', include('documents.urls')),
    path('delivery/', include('delivery.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
