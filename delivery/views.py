from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from deals.models import Deal
from .models import Delivery, Driver, Vehicle, DELIVERY_STATUS_CHOICES
from .forms import DeliveryForm, DriverForm, VehicleForm


# ─── Рейсы ────────────────────────────────────────────────────────────────────

def delivery_list(request):
    qs = Delivery.objects.select_related('deal', 'deal__client', 'driver', 'vehicle')

    status_filter = request.GET.get('status', '')
    direction_filter = request.GET.get('direction', '')
    q = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if direction_filter:
        qs = qs.filter(direction=direction_filter)
    if q:
        qs = qs.filter(
            Q(deal__number__icontains=q) |
            Q(deal__client__name__icontains=q) |
            Q(driver__full_name__icontains=q) |
            Q(vehicle__reg_number__icontains=q)
        )

    return render(request, 'delivery/delivery_list.html', {
        'page_title': 'Рейсы доставки',
        'deliveries': qs,
        'status_choices': DELIVERY_STATUS_CHOICES,
        'status_filter': status_filter,
        'direction_filter': direction_filter,
        'q': q,
    })


def delivery_create(request, deal_pk):
    deal = get_object_or_404(Deal, pk=deal_pk)
    if request.method == 'POST':
        form = DeliveryForm(request.POST, deal=deal)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.deal = deal
            delivery.save()
            messages.success(request, 'Рейс создан.')
            return redirect('deal_detail', pk=deal_pk)
    else:
        form = DeliveryForm(deal=deal)
    return render(request, 'delivery/delivery_form.html', {
        'page_title': f'Новый рейс — сделка №{deal.number}',
        'form': form,
        'deal': deal,
    })


def delivery_detail(request, pk):
    delivery = get_object_or_404(
        Delivery.objects.select_related('deal', 'deal__client', 'driver', 'vehicle'),
        pk=pk,
    )
    return render(request, 'delivery/delivery_detail.html', {
        'page_title': f'Рейс #{delivery.pk}',
        'delivery': delivery,
        'status_choices': DELIVERY_STATUS_CHOICES,
    })


def delivery_edit(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk)
    if request.method == 'POST':
        form = DeliveryForm(request.POST, instance=delivery, deal=delivery.deal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рейс обновлён.')
            return redirect('delivery_detail', pk=pk)
    else:
        form = DeliveryForm(instance=delivery, deal=delivery.deal)
    return render(request, 'delivery/delivery_form.html', {
        'page_title': f'Редактировать рейс #{delivery.pk}',
        'form': form,
        'deal': delivery.deal,
        'delivery': delivery,
    })


def delivery_status_change(request, pk):
    if request.method != 'POST':
        return redirect('delivery_detail', pk=pk)
    delivery = get_object_or_404(Delivery, pk=pk)
    new_status = request.POST.get('status', '')
    valid = [s for s, _ in DELIVERY_STATUS_CHOICES]
    if new_status in valid:
        delivery.status = new_status
        if new_status == 'completed' and not delivery.actual_date:
            from django.utils import timezone
            delivery.actual_date = timezone.now().date()
        delivery.save()
        messages.success(request, f'Статус рейса изменён: {delivery.status_label}')
    return redirect('delivery_detail', pk=pk)


# ─── Водители ─────────────────────────────────────────────────────────────────

def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'delivery/driver_list.html', {
        'page_title': 'Водители',
        'drivers': drivers,
    })


def driver_create(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Водитель добавлен.')
            return redirect('driver_list')
    else:
        form = DriverForm()
    return render(request, 'delivery/driver_form.html', {
        'page_title': 'Новый водитель',
        'form': form,
    })


def driver_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Водитель обновлён.')
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'delivery/driver_form.html', {
        'page_title': f'Редактировать водителя: {driver.full_name}',
        'form': form,
        'driver': driver,
    })


# ─── Машины ───────────────────────────────────────────────────────────────────

def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'delivery/vehicle_list.html', {
        'page_title': 'Транспортные средства',
        'vehicles': vehicles,
    })


def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Транспортное средство добавлено.')
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'delivery/vehicle_form.html', {
        'page_title': 'Новое транспортное средство',
        'form': form,
    })


def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Транспортное средство обновлено.')
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'delivery/vehicle_form.html', {
        'page_title': f'Редактировать: {vehicle}',
        'form': form,
        'vehicle': vehicle,
    })
