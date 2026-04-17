import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Deal, DealSection, DealEquipmentItem,
    PartialReturn, PartialReturnItem, DealStatusHistory,
    DEAL_STATUS_CHOICES, CITY_CHOICES, VAT_CHOICES,
)
from clients.models import Client
from equipment.models import EquipmentType, WarehouseStock, EquipmentMovement
from pricing.models import EquipmentCategory
from pricing.calculator import get_city_coefficients, get_scaffolding_default_coeffs, TOWER_HEIGHT_SECTIONS
from documents.models import OurLegalEntity


# ---------------------------------------------------------------------------
# Warehouse mechanics helpers
# ---------------------------------------------------------------------------

def _get_stock_safe(equipment_type):
    stock, _ = WarehouseStock.objects.get_or_create(
        equipment_type=equipment_type,
        defaults={'quantity_total': 0},
    )
    return stock


def _reserve_equipment(deal):
    for item in deal.equipment_items.select_related('equipment_type'):
        stock = _get_stock_safe(item.equipment_type)
        stock.quantity_reserved += item.quantity
        stock.save()
        EquipmentMovement.objects.create(
            equipment_type=item.equipment_type,
            movement_type='out_reserve',
            quantity=item.quantity,
            deal=deal,
            notes=f'Резерв — сделка №{deal.number}',
        )


def _cancel_reserve(deal):
    for item in deal.equipment_items.select_related('equipment_type'):
        stock = _get_stock_safe(item.equipment_type)
        stock.quantity_reserved = max(0, stock.quantity_reserved - item.quantity)
        stock.save()
        EquipmentMovement.objects.create(
            equipment_type=item.equipment_type,
            movement_type='cancel_reserve',
            quantity=item.quantity,
            deal=deal,
            notes=f'Снятие резерва — отмена сделки №{deal.number}',
        )


def _issue_equipment(deal):
    for item in deal.equipment_items.select_related('equipment_type'):
        stock = _get_stock_safe(item.equipment_type)
        stock.quantity_reserved = max(0, stock.quantity_reserved - item.quantity)
        stock.quantity_rented += item.quantity
        stock.save()
        EquipmentMovement.objects.create(
            equipment_type=item.equipment_type,
            movement_type='out_rent',
            quantity=item.quantity,
            deal=deal,
            notes=f'Выдача — сделка №{deal.number}',
        )


def _return_equipment_qty(deal, equipment_type, qty, notes=''):
    stock = _get_stock_safe(equipment_type)
    stock.quantity_rented = max(0, stock.quantity_rented - qty)
    stock.save()
    EquipmentMovement.objects.create(
        equipment_type=equipment_type,
        movement_type='return',
        quantity=qty,
        deal=deal,
        notes=notes,
    )


def _already_returned_qty(deal, equipment_type):
    return (
        PartialReturnItem.objects
        .filter(partial_return__deal=deal, equipment_type=equipment_type)
        .aggregate(total=Sum('quantity_returned'))
        .get('total') or 0
    )


def _return_all_remaining(deal):
    for item in deal.equipment_items.select_related('equipment_type'):
        already = _already_returned_qty(deal, item.equipment_type)
        remaining = item.quantity - already
        if remaining > 0:
            _return_equipment_qty(
                deal, item.equipment_type, remaining,
                notes=f'Полный возврат — сделка №{deal.number}',
            )


def _days_for_period(start_date, end_date):
    if not start_date or not end_date:
        return 0
    delta = (end_date - start_date).days
    return max(delta, 0)


def _build_items_with_remaining(deal):
    rows = []
    equipment_items = list(deal.equipment_items.select_related('equipment_type'))
    for item in equipment_items:
        returned = _already_returned_qty(deal, item.equipment_type)
        remaining = max(item.quantity - returned, 0)
        rows.append({
            'item': item,
            'already_returned': returned,
            'remaining': remaining,
            'in_rent_now': remaining,
            'current_daily_cost': remaining * float(item.daily_rental_rate or 0),
        })
    return rows


def _current_daily_rent_total(items_with_remaining):
    return sum(row['current_daily_cost'] for row in items_with_remaining)


def _last_partial_return_date(deal):
    last_pr = deal.partial_returns.order_by('-return_date', '-created_at').first()
    return last_pr.return_date if last_pr else None


def _factual_rental_snapshot(deal, items_with_remaining):
    total_realized = float(
        deal.partial_returns.aggregate(total=Sum('amount_paid')).get('total') or 0
    )
    current_daily = _current_daily_rent_total(items_with_remaining)
    today = timezone.now().date()
    period_start = _last_partial_return_date(deal) or deal.start_date or deal.created_at.date()
    ongoing_days = _days_for_period(period_start, today) if deal.status in _STATUSES_ACTIVE_RENT else 0
    ongoing_amount = current_daily * ongoing_days
    return {
        'period_start': period_start,
        'ongoing_days': ongoing_days,
        'current_daily': current_daily,
        'realized_amount': total_realized,
        'ongoing_amount': ongoing_amount,
        'factual_total': total_realized + ongoing_amount,
    }


def _check_stock_issues(deal):
    issues = []
    for item in deal.equipment_items.select_related('equipment_type'):
        stock = _get_stock_safe(item.equipment_type)
        if stock.quantity_available < item.quantity:
            issues.append({
                'name': item.equipment_type.name,
                'required': item.quantity,
                'available': stock.quantity_available,
                'shortage': item.quantity - stock.quantity_available,
            })
    return issues


def _aggregate_deal_financials(deal):
    """Sum section financials into deal fields + apply delivery/VAT at deal level."""
    agg = deal.sections.aggregate(
        sum_area=Sum('total_area'),
        sum_daily=Sum('daily_cost'),
        sum_rental=Sum('total_rental'),
        sum_market=Sum('market_value'),
        sum_deposit=Sum('deposit_amount'),
    )
    deal.total_area = agg['sum_area'] or 0
    deal.daily_cost = agg['sum_daily'] or 0
    deal.total_rental = agg['sum_rental'] or 0
    deal.market_value = agg['sum_market'] or 0
    deal.deposit_amount = agg['sum_deposit'] or 0

    delivery_roundtrip = float(deal.delivery_cost) * 2
    grand_total = float(deal.total_rental) + float(deal.deposit_amount) + delivery_roundtrip
    if deal.vat_mode == 'with_vat':
        grand_total = round(grand_total * 1.20, 2)
    deal.grand_total = grand_total
    deal.save()


# ---------------------------------------------------------------------------
# AJAX: calculate (per-section)
# ---------------------------------------------------------------------------

@require_POST
def calculate_ajax(request):
    try:
        data = json.loads(request.body)
        category = get_object_or_404(EquipmentCategory, pk=data['category_id'])
        deal_context = data.get('deal_context', {})
        pricing_params = data.get('pricing_params', {})
        equipment_items = data.get('equipment_items', [])

        algo = category.get_algorithm()
        result = algo.calculate(pricing_params, deal_context, equipment_items)
        return JsonResponse({'ok': True, 'result': result})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ---------------------------------------------------------------------------
# AJAX: stock check
# ---------------------------------------------------------------------------

@require_POST
def stock_check_ajax(request):
    try:
        data = json.loads(request.body)
        result = []
        for entry in data.get('items', []):
            code = entry.get('code')
            qty = int(entry.get('qty', 0))
            if qty <= 0:
                continue
            try:
                et = EquipmentType.objects.get(code=code)
                stock = _get_stock_safe(et)
                available = stock.quantity_available
                result.append({
                    'code': code,
                    'name': et.name,
                    'required': qty,
                    'available': available,
                    'ok': available >= qty,
                    'shortage': max(0, qty - available),
                })
            except EquipmentType.DoesNotExist:
                result.append({
                    'code': code, 'name': code,
                    'required': qty, 'available': 0,
                    'ok': False, 'shortage': qty,
                })
        return JsonResponse({'ok': True, 'items': result})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ---------------------------------------------------------------------------
# Deal list
# ---------------------------------------------------------------------------

def deal_list(request):
    qs = Deal.objects.select_related('client').prefetch_related('sections__category').all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    cat_id = request.GET.get('cat', '')
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(client__name__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if cat_id:
        qs = qs.filter(sections__category_id=cat_id).distinct()
    return render(request, 'deals/list.html', {
        'deals': qs,
        'q': q,
        'status': status,
        'cat': cat_id,
        'status_choices': DEAL_STATUS_CHOICES,
        'categories': EquipmentCategory.objects.filter(is_active=True),
        'page_title': 'Сделки',
    })


# ---------------------------------------------------------------------------
# Deal detail
# ---------------------------------------------------------------------------

_STATUS_TRANSITIONS = {
    'new':             ['calculation', 'confirmed', 'cancelled'],
    'calculation':     ['confirmed', 'cancelled'],
    'confirmed':       ['contract_signed', 'cancelled'],
    'contract_signed': ['invoice_sent', 'cancelled'],
    'invoice_sent':    ['paid', 'cancelled'],
    'paid':            ['delivery'],
    'delivery':        ['rented', 'cancelled'],
    'rented':          ['partial_return', 'returned', 'overdue', 'non_return'],
    'partial_return':  ['returned', 'overdue', 'non_return'],
    'overdue':         ['returned', 'non_return'],
    'returned':        [],
    'cancelled':       [],
    'non_return':      [],
}

_STATUSES_WITH_RESERVE = {'confirmed', 'contract_signed', 'invoice_sent', 'paid', 'delivery'}
_STATUSES_ACTIVE_RENT  = {'rented', 'partial_return', 'overdue'}


def deal_detail(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    history = deal.status_history.all()[:15]
    invoices = deal.invoices.all()
    shipping_docs = deal.shipping_docs.all()
    deliveries = deal.deliveries.select_related('driver', 'vehicle').order_by('-planned_date')
    partial_returns = deal.partial_returns.prefetch_related('items__equipment_type')

    items_with_remaining = _build_items_with_remaining(deal)
    factual_snapshot = _factual_rental_snapshot(deal, items_with_remaining)

    # Build sections data (each section with its equipment items + return status)
    sections_data = []
    for section in deal.sections.select_related('category').prefetch_related('equipment_items__equipment_type'):
        items_data = []
        for item in section.equipment_items.all():
            returned = next(
                (r['already_returned'] for r in items_with_remaining if r['item'].equipment_type_id == item.equipment_type_id),
                0,
            )
            items_data.append({
                'item': item,
                'returned': returned,
                'remaining': max(item.quantity - returned, 0),
            })
        sections_data.append({'section': section, 'items': items_data})

    next_statuses = [
        (s, dict(DEAL_STATUS_CHOICES).get(s, s))
        for s in _STATUS_TRANSITIONS.get(deal.status, [])
    ]

    return render(request, 'deals/detail.html', {
        'deal': deal,
        'sections_data': sections_data,
        'history': history,
        'invoices': invoices,
        'shipping_docs': shipping_docs,
        'partial_returns': partial_returns,
        'items_with_remaining': items_with_remaining,
        'factual_snapshot': factual_snapshot,
        'next_statuses': next_statuses,
        'deliveries': deliveries,
        'page_title': f'Сделка №{deal.number}',
    })


# ---------------------------------------------------------------------------
# Deal create
# ---------------------------------------------------------------------------

def deal_create(request):
    clients = Client.objects.order_by('name')
    categories = EquipmentCategory.objects.filter(is_active=True).prefetch_related('equipment_types')
    cities = list(get_city_coefficients().keys())
    tower_heights = [h for h, s in TOWER_HEIGHT_SECTIONS]

    stock_snapshot = {}
    for ws in WarehouseStock.objects.select_related('equipment_type').all():
        stock_snapshot[ws.equipment_type.code] = ws.quantity_available

    # Build categories JSON for JS
    categories_data = []
    for cat in categories:
        eq_types = []
        for et in cat.equipment_types.filter(is_active=True):
            eq_types.append({
                'code': et.code,
                'name': et.name,
                'unit_price': float(et.base_price) * float(et.price_coefficient),
                'daily_rate': float(et.daily_rental_rate),
                'unit': et.unit,
            })
        categories_data.append({
            'id': cat.id,
            'name': cat.name,
            'algorithm_code': cat.algorithm_code,
            'deposit_pct': float(cat.deposit_pct_default),
            'equipment_types': eq_types,
        })

    if request.method == 'POST':
        return _handle_deal_create_post(request)

    return render(request, 'deals/create.html', {
        'clients': clients,
        'our_entities': OurLegalEntity.objects.order_by('-is_default', 'name'),
        'categories': categories,
        'categories_json': json.dumps(categories_data, ensure_ascii=False),
        'cities': cities,
        'tower_heights': tower_heights,
        'stock_snapshot': json.dumps(stock_snapshot),
        'page_title': 'Новая сделка',
    })


@transaction.atomic
def _handle_deal_create_post(request):
    client = get_object_or_404(Client, pk=request.POST.get('client'))
    our_entity = get_object_or_404(OurLegalEntity, pk=request.POST.get('our_entity'))

    deal = Deal(
        client=client,
        our_entity=our_entity,
        city=request.POST.get('city', 'Екатеринбург'),
        rental_days=int(request.POST.get('rental_days', 30)),
        start_date=request.POST.get('start_date') or None,
        end_date=request.POST.get('end_date') or None,
        delivery_address=request.POST.get('delivery_address', ''),
        delivery_cost=float(request.POST.get('delivery_cost', 0) or 0),
        deposit_pct=float(request.POST.get('deposit_pct', 10)),
        vat_mode=request.POST.get('vat_mode', 'no_vat'),
        notes=request.POST.get('notes', ''),
    )
    deal.save()

    deal_context = {
        'city': deal.city,
        'days': deal.rental_days,
        'deposit_pct': float(deal.deposit_pct),
        'delivery_cost': 0,   # delivery applied at deal level only
        'vat_mode': 'no_vat', # VAT applied at deal level only
    }

    section_count = int(request.POST.get('section_count', 0))
    scaffold_defaults = get_scaffolding_default_coeffs()

    for sec_idx in range(section_count):
        prefix = f's{sec_idx}'
        cat_id = request.POST.get(f'{prefix}_category_id')
        if not cat_id:
            continue
        try:
            category = EquipmentCategory.objects.get(pk=cat_id)
        except EquipmentCategory.DoesNotExist:
            continue

        algo_code = category.algorithm_code
        pricing_params = {}
        equipment_items_for_calc = []

        if algo_code == 'area_based':
            sides = [
                (float(request.POST.get(f'{prefix}_side{i}_length', 0) or 0),
                 float(request.POST.get(f'{prefix}_side{i}_height', 0) or 0))
                for i in range(1, 5)
            ]
            pricing_params = {
                'sides': sides,
                'season_coeff': float(request.POST.get(f'{prefix}_season_coeff', scaffold_defaults['season_coeff'])),
                'diagonal_mode': request.POST.get(f'{prefix}_diagonal_mode', 'every'),
                'planks_qty': int(request.POST.get(f'{prefix}_planks_qty', 4) or 4),
                'price_coeff': float(request.POST.get(f'{prefix}_price_coeff', scaffold_defaults['price_coeff'])),
                'bracket_qty': int(request.POST.get(f'{prefix}_bracket_qty', 0) or 0),
                'base_plate_qty': int(request.POST.get(f'{prefix}_base_plate_qty', 0) or 0),
            }
        elif algo_code == 'tower':
            pricing_params = {
                'height': float(request.POST.get(f'{prefix}_height', 3.89)),
                'qty_towers': int(request.POST.get(f'{prefix}_qty_towers', 1) or 1),
                'model': request.POST.get(f'{prefix}_tower_model', 'ПСРВ-21'),
            }
        elif algo_code == 'daily_rate':
            item_idx = 0
            while True:
                code = request.POST.get(f'{prefix}_dr_code_{item_idx}')
                if code is None:
                    break
                qty = int(request.POST.get(f'{prefix}_dr_qty_{item_idx}', 0) or 0)
                if qty > 0:
                    try:
                        et = EquipmentType.objects.get(code=code)
                        equipment_items_for_calc.append({
                            'code': code,
                            'name': et.name,
                            'qty': qty,
                            'daily_rate': float(et.daily_rental_rate),
                            'unit_price': float(et.base_price) * float(et.price_coefficient),
                        })
                    except EquipmentType.DoesNotExist:
                        pass
                item_idx += 1

        algo = category.get_algorithm()
        calc = algo.calculate(pricing_params, deal_context, equipment_items_for_calc)

        section = DealSection.objects.create(
            deal=deal,
            category=category,
            ordering=sec_idx,
            pricing_params=pricing_params,
            total_area=calc.get('total_area', 0),
            daily_cost=calc.get('daily_cost', 0),
            total_rental=calc.get('total_rental', 0),
            market_value=calc.get('market_value', calc.get('market_value_total', 0)),
            deposit_amount=calc.get('deposit_amount', calc.get('deposit_total', 0)),
        )

        for item_data in calc.get('equipment_items', []):
            if item_data.get('qty', 0) <= 0:
                continue
            code = item_data['code']
            if algo_code in ('area_based', 'tower'):
                qty = int(request.POST.get(f'{prefix}_qty_{code}', item_data['qty']) or item_data['qty'])
            else:
                qty = item_data['qty']
            if qty <= 0:
                continue
            try:
                et = EquipmentType.objects.get(code=code)
                DealEquipmentItem.objects.create(
                    deal=deal,
                    section=section,
                    equipment_type=et,
                    quantity=qty,
                    unit_price=item_data.get('unit_price', item_data.get('price', 0)),
                    daily_rental_rate=item_data.get('daily_rate', 0),
                )
            except EquipmentType.DoesNotExist:
                pass

    _aggregate_deal_financials(deal)
    DealStatusHistory.objects.create(deal=deal, old_status='', new_status='new', notes='Сделка создана')
    messages.success(request, f'Сделка №{deal.number} создана.')
    return redirect('deal_detail', pk=deal.pk)


# ---------------------------------------------------------------------------
# Status change — warehouse-integrated
# ---------------------------------------------------------------------------

@transaction.atomic
def deal_status_change(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method != 'POST':
        return redirect('deal_detail', pk=pk)

    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    old_status = deal.status

    if new_status not in _STATUS_TRANSITIONS.get(old_status, []):
        messages.error(request, 'Недопустимый переход статуса.')
        return redirect('deal_detail', pk=pk)

    if new_status == 'confirmed' and old_status not in _STATUSES_WITH_RESERVE:
        issues = _check_stock_issues(deal)
        if issues and not request.POST.get('force'):
            warn = '; '.join(f"{i['name']}: нужно {i['required']}, доступно {i['available']}" for i in issues)
            messages.warning(request, f'⚠ Нехватка на складе: {warn}. '
                             f'Для принудительного подтверждения используйте кнопку ниже.')
            return redirect('deal_detail', pk=pk)
        _reserve_equipment(deal)

    elif new_status == 'rented':
        if old_status not in _STATUSES_ACTIVE_RENT:
            if old_status not in _STATUSES_WITH_RESERVE:
                _reserve_equipment(deal)
            _issue_equipment(deal)

    elif new_status == 'returned':
        if old_status in _STATUSES_ACTIVE_RENT:
            _return_all_remaining(deal)
        elif old_status in _STATUSES_WITH_RESERVE:
            _cancel_reserve(deal)

    elif new_status == 'cancelled':
        if old_status in _STATUSES_WITH_RESERVE:
            _cancel_reserve(deal)
        elif old_status in _STATUSES_ACTIVE_RENT:
            _return_all_remaining(deal)

    elif new_status == 'non_return':
        if old_status in _STATUSES_ACTIVE_RENT:
            _return_all_remaining(deal)

    DealStatusHistory.objects.create(
        deal=deal, old_status=old_status, new_status=new_status, notes=notes,
    )
    deal.status = new_status
    if new_status == 'rented' and not deal.start_date:
        deal.start_date = timezone.now().date()
    if new_status == 'returned' and not deal.actual_return_date:
        deal.actual_return_date = timezone.now().date()
    deal.save()

    messages.success(request, f'Статус изменён: «{deal.status_label}»')
    return redirect('deal_detail', pk=pk)


# ---------------------------------------------------------------------------
# Partial return
# ---------------------------------------------------------------------------

@transaction.atomic
def partial_return_create(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if deal.status not in _STATUSES_ACTIVE_RENT:
        messages.error(request, 'Частичный возврат доступен только для сделок в аренде/просрочке.')
        return redirect('deal_detail', pk=pk)

    equipment_items = list(deal.equipment_items.select_related('equipment_type'))
    items_with_remaining = _build_items_with_remaining(deal)
    total_issued = sum(i.quantity for i in equipment_items)
    total_returned = sum(r['already_returned'] for r in items_with_remaining)
    total_remaining = sum(r['remaining'] for r in items_with_remaining)
    current_daily_before = _current_daily_rent_total(items_with_remaining)

    if request.method == 'POST':
        return_date = request.POST.get('return_date') or timezone.now().date()
        if isinstance(return_date, str):
            from datetime import date
            try:
                return_date = date.fromisoformat(return_date)
            except ValueError:
                messages.error(request, 'Некорректная дата возврата.')
                return redirect('partial_return_create', pk=pk)

        period_start = _last_partial_return_date(deal) or deal.start_date or deal.created_at.date()
        if return_date < period_start:
            messages.error(
                request,
                f'Дата возврата не может быть раньше контрольной даты {period_start.strftime("%d.%m.%Y")}.'
            )
            return redirect('partial_return_create', pk=pk)

        notes = request.POST.get('notes', '')

        return_lines = []
        validation_errors = []
        for row in items_with_remaining:
            item = row['item']
            raw_qty = request.POST.get(f'qty_{item.pk}', 0) or 0
            try:
                qty = int(raw_qty)
            except (TypeError, ValueError):
                validation_errors.append(f'{item.equipment_type.name}: некорректное количество.')
                continue
            if qty < 0:
                validation_errors.append(f'{item.equipment_type.name}: количество не может быть отрицательным.')
                continue
            if qty > row['remaining']:
                validation_errors.append(
                    f'{item.equipment_type.name}: возвращается {qty}, доступный остаток {row["remaining"]}.'
                )
                continue
            if qty > 0:
                return_lines.append((item, qty))

        if validation_errors:
            for err in validation_errors:
                messages.error(request, err)
            return redirect('partial_return_create', pk=pk)

        if not return_lines:
            messages.error(request, 'Укажите количество возвращаемого оборудования.')
            return redirect('partial_return_create', pk=pk)

        pr = PartialReturn.objects.create(
            deal=deal, return_date=return_date, amount_paid=0, notes=notes,
        )
        period_days = _days_for_period(period_start, return_date)
        period_charge = current_daily_before * period_days
        returned_value = 0
        returned_qty_now = 0
        for item, qty in return_lines:
            PartialReturnItem.objects.create(
                partial_return=pr,
                equipment_type=item.equipment_type,
                quantity_returned=qty,
            )
            returned_qty_now += qty
            returned_value += float(item.unit_price) * qty
            _return_equipment_qty(
                deal, item.equipment_type, qty,
                notes=f'Частичный возврат {return_date} — сделка №{deal.number}',
            )
        pr.amount_paid = period_charge
        pr.save(update_fields=['amount_paid'])

        remaining_after = total_remaining - returned_qty_now
        old_status = deal.status
        if remaining_after <= 0:
            deal.status = 'returned'
            deal.actual_return_date = timezone.now().date()
            DealStatusHistory.objects.create(
                deal=deal, old_status=old_status, new_status='returned',
                notes='Всё оборудование возвращено',
            )
        else:
            deal.status = 'partial_return'

        deal.save()
        messages.success(
            request,
            (
                f'Частичный возврат оформлен: {returned_qty_now} ед. '
                f'(остаточная стоимость {returned_value:,.2f} ₽), '
                f'начислено аренды за {period_days} дн.: {period_charge:,.2f} ₽.'
            ).replace(',', ' ')
        )
        return redirect('deal_detail', pk=pk)

    return render(request, 'deals/partial_return.html', {
        'deal': deal,
        'items_with_remaining': items_with_remaining,
        'current_daily_before': current_daily_before,
        'period_start': _last_partial_return_date(deal) or deal.start_date or deal.created_at.date(),
        'total_issued': total_issued,
        'total_returned': total_returned,
        'total_remaining': total_remaining,
        'today': timezone.now().date(),
        'page_title': f'Частичный возврат — сделка №{deal.number}',
    })
