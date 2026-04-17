import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .calculator import (
    calculate_scaffolding, calculate_tower,
    DELIVERY_PRICES, TOWER_HEIGHT_SECTIONS,
    get_city_coefficients, get_scaffolding_default_coeffs, get_tower_model_coeffs,
)
from .models import PricingCoefficientSettings


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
    city_coeffs = get_city_coefficients()
    scaffold_defaults = get_scaffolding_default_coeffs()
    tower_coeffs = get_tower_model_coeffs()
    cities = list(city_coeffs.keys())
    tower_heights = [h for h, s in TOWER_HEIGHT_SECTIONS]
    context = {
        'cities': cities,
        'city_coeffs': city_coeffs,
        'scaffold_defaults': scaffold_defaults,
        'tower_coeffs': tower_coeffs,
        'tower_coeff_psrv21': tower_coeffs.get('ПСРВ-21', 0.85),
        'tower_coeff_psrv22': tower_coeffs.get('ПСРВ-22', 1.05),
        'tower_extra_psrv22': tower_coeffs.get('psrv22_extra_charge', 50),
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
            season_coeff=data.get('season_coeff'),
            diagonal_mode=data.get('diagonal_mode', 'every'),
            planks_qty=int(data.get('planks_qty', 4) or 4),
            deposit_pct=float(data.get('deposit_pct', 10)),
            delivery_cost=float(data.get('delivery_cost', 0) or 0),
            vat_mode=data.get('vat_mode', 'no_vat'),
            price_coeff=data.get('price_coeff'),
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


@require_POST
def save_coefficients_ajax(request):
    try:
        data = json.loads(request.body)

        raw_city_coeffs = data.get('city_coefficients', {})
        if not isinstance(raw_city_coeffs, dict):
            raise ValueError('Коэффициенты городов должны быть словарём.')

        city_coeffs = {}
        for city, coeff in raw_city_coeffs.items():
            city_name = str(city).strip()
            if not city_name:
                continue
            city_coeffs[city_name] = float(coeff)

        settings = PricingCoefficientSettings.get_solo()
        settings.city_coefficients = city_coeffs
        settings.scaffold_season_coeff_default = float(data.get('scaffold_season_coeff_default'))
        settings.scaffold_price_coeff_default = float(data.get('scaffold_price_coeff_default'))
        settings.tower_psrv21_model_coeff = float(data.get('tower_psrv21_model_coeff'))
        settings.tower_psrv22_model_coeff = float(data.get('tower_psrv22_model_coeff'))
        settings.tower_psrv22_extra_charge = float(data.get('tower_psrv22_extra_charge'))
        settings.save()

        return JsonResponse({
            'ok': True,
            'coefficients': {
                'city_coefficients': get_city_coefficients(),
                'scaffold_defaults': get_scaffolding_default_coeffs(),
                'tower_coeffs': get_tower_model_coeffs(),
            },
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
