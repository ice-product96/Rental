from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import EquipmentType, WarehouseStock, EquipmentMovement
from .forms import EquipmentTypeForm


def warehouse_list(request):
    stocks = WarehouseStock.objects.select_related('equipment_type').all()
    return render(request, 'equipment/warehouse.html', {
        'stocks': stocks, 'page_title': 'Склад',
    })


def equipment_list(request):
    types = EquipmentType.objects.select_related('category').all()
    return render(request, 'equipment/list.html', {
        'types': types, 'page_title': 'Типы оборудования',
    })


def equipment_type_create(request):
    if request.method == 'POST':
        form = EquipmentTypeForm(request.POST)
        if form.is_valid():
            eq_type = form.save()
            # Автоматически создаём запись склада
            WarehouseStock.objects.get_or_create(equipment_type=eq_type)
            messages.success(request, f'Тип оборудования «{eq_type.name}» создан.')
            return redirect('equipment_list')
    else:
        form = EquipmentTypeForm()
    return render(request, 'equipment/type_form.html', {
        'form': form,
        'page_title': 'Новый тип оборудования',
    })


def equipment_type_edit(request, pk):
    eq_type = get_object_or_404(EquipmentType, pk=pk)
    if request.method == 'POST':
        form = EquipmentTypeForm(request.POST, instance=eq_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип оборудования «{eq_type.name}» обновлён.')
            return redirect('equipment_list')
    else:
        form = EquipmentTypeForm(instance=eq_type)
    return render(request, 'equipment/type_form.html', {
        'form': form,
        'eq_type': eq_type,
        'page_title': f'Редактировать: {eq_type.name}',
    })


def movement_list(request):
    movements = EquipmentMovement.objects.select_related('equipment_type', 'deal').order_by('-date')[:100]
    return render(request, 'equipment/movements.html', {
        'movements': movements, 'page_title': 'Движение оборудования',
    })


def stock_adjust(request, pk):
    stock = get_object_or_404(WarehouseStock, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        qty = int(request.POST.get('qty', 0))
        notes = request.POST.get('notes', '')
        if action == 'add':
            stock.quantity_total += qty
            stock.save()
            EquipmentMovement.objects.create(
                equipment_type=stock.equipment_type,
                movement_type='in',
                quantity=qty,
                notes=notes,
            )
            messages.success(request, f'Добавлено {qty} шт. на склад.')
        elif action == 'writeoff':
            stock.quantity_total = max(0, stock.quantity_total - qty)
            stock.save()
            EquipmentMovement.objects.create(
                equipment_type=stock.equipment_type,
                movement_type='writeoff',
                quantity=qty,
                notes=notes,
            )
            messages.success(request, f'Списано {qty} шт.')
        return redirect('warehouse_list')
    return render(request, 'equipment/adjust.html', {
        'stock': stock, 'page_title': f'Корректировка: {stock.equipment_type.name}',
    })
