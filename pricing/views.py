import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .calculator import (
    calculate_scaffolding, calculate_tower,
    CITY_COEFFICIENTS, DELIVERY_PRICES, TOWER_HEIGHT_SECTIONS
)


def dashboard(request):
    from deals.models import Deal
    from clients.models import Client
    from billing.models import Invoice
    from django.utils import timezone

    today = timezone.now().date()
    stats = {
        'total_clients': Client.objects.count(),
        'active_deals': Deal.objects.filter(status__in=['rented', 'delivery', 'partial_return']).count(),
        'new_deals': Deal.objects.filter(status='new').count(),
        'overdue_deals': Deal.objects.filter(status__in=['rented', 'partial_return'], end_date__lt=today).count(),
        'unpaid_invoices': Invoice.objects.filter(status__in=['sent', 'draft']).count(),
    }
    recent_deals = Deal.objects.select_related('client').order_by('-created_at')[:8]
    overdue_deals = Deal.objects.select_related('client').filter(
        status__in=['rented', 'partial_return'], end_date__lt=today
    ).order_by('end_date')[:5]

    context = {
        'stats': stats,
        'recent_deals': recent_deals,
        'overdue_deals': overdue_deals,
        'page_title': 'Дашборд',
    }
    return render(request, 'dashboard.html', context)


def calculator(request):
    cities = list(CITY_COEFFICIENTS.keys())
    tower_heights = [h for h, s in TOWER_HEIGHT_SECTIONS]
    context = {
        'cities': cities,
        'tower_heights': tower_heights,
        'delivery_prices': DELIVERY_PRICES,
        'page_title': 'Калькулятор аренды',
    }
    return render(request, 'pricing/calculator.html', context)


@require_POST
def calc_scaffolding_ajax(request):
    try:
        data = json.loads(request.body)
        sides = []
        for i in range(1, 5):
            l = float(data.get(f'side{i}_length', 0) or 0)
            h = float(data.get(f'side{i}_height', 0) or 0)
            sides.append((l, h))

        result = calculate_scaffolding(
            sides=sides,
            days=int(data.get('days', 30)),
            city=data.get('city', 'Екатеринбург'),
            season_coeff=float(data.get('season_coeff', 1.2)),
            diagonal_mode=data.get('diagonal_mode', 'every'),
            planks_qty=int(data.get('planks_qty', 4) or 4),
            deposit_pct=float(data.get('deposit_pct', 10)),
            delivery_cost=float(data.get('delivery_cost', 0) or 0),
            vat_mode=data.get('vat_mode', 'no_vat'),
            price_coeff=float(data.get('price_coeff', 1.15)),
            bracket_qty=int(data.get('bracket_qty', 0) or 0),
            base_plate_qty=int(data.get('base_plate_qty', 0) or 0),
        )
        return JsonResponse({'ok': True, 'result': result})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@require_POST
def calc_tower_ajax(request):
    try:
        data = json.loads(request.body)
        result = calculate_tower(
            height=float(data.get('height', 3.89)),
            days=int(data.get('days', 30)),
            qty_towers=int(data.get('qty_towers', 1) or 1),
            model=data.get('model', 'ПСРВ-21'),
            city=data.get('city', 'Екатеринбург'),
            deposit_pct=float(data.get('deposit_pct', 10)),
            delivery_cost=float(data.get('delivery_cost', 0) or 0),
            vat_mode=data.get('vat_mode', 'no_vat'),
        )
        return JsonResponse({'ok': True, 'result': result})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
