"""
Pricing algorithm classes. Each algorithm tied to an EquipmentCategory.
Unified interface: .calculate(pricing_params, deal_context, equipment_items) → result dict.
"""
from .calculator import (
    calculate_scaffolding as _calc_scaffolding,
    calculate_tower as _calc_tower,
    roundup,
    CITY_COEFFICIENTS,
    TOWER_HEIGHT_SECTIONS,
)


class AreaBasedAlgorithm:
    """Scaffolding: area-based pricing from rate table. Auto-generates BOM."""
    code = 'area_based'
    name = 'По площади (строительные леса)'

    def calculate(self, pricing_params, deal_context, equipment_items=None):
        sides = pricing_params.get('sides', [])
        raw = _calc_scaffolding(
            sides=sides,
            days=deal_context['days'],
            city=deal_context.get('city', 'Екатеринбург'),
            season_coeff=pricing_params.get('season_coeff', 1.2),
            diagonal_mode=pricing_params.get('diagonal_mode', 'every'),
            planks_qty=pricing_params.get('planks_qty', 4),
            deposit_pct=deal_context.get('deposit_pct', 10),
            delivery_cost=deal_context.get('delivery_cost', 0),
            vat_mode=deal_context.get('vat_mode', 'no_vat'),
            price_coeff=pricing_params.get('price_coeff', 1.15),
            bracket_qty=pricing_params.get('bracket_qty', 0),
            base_plate_qty=pricing_params.get('base_plate_qty', 0),
        )
        # Normalize equipment_items: 'price' → 'unit_price'
        for item in raw['equipment_items']:
            item.setdefault('unit_price', item.get('price', 0))
        return raw


class TowerAlgorithm:
    """Tower-scaffold: per-unit pricing with height-based rate table."""
    code = 'tower'
    name = 'Вышки-туры'

    def calculate(self, pricing_params, deal_context, equipment_items=None):
        height = float(pricing_params.get('height', 3.89))
        qty_towers = int(pricing_params.get('qty_towers', 1))
        model = pricing_params.get('model', 'ПСРВ-21')

        raw = _calc_tower(
            height=height,
            days=deal_context['days'],
            qty_towers=qty_towers,
            model=model,
            city=deal_context.get('city', 'Екатеринбург'),
            deposit_pct=deal_context.get('deposit_pct', 10),
            delivery_cost=deal_context.get('delivery_cost', 0),
            vat_mode=deal_context.get('vat_mode', 'no_vat'),
        )
        # Normalize to standard interface
        result = dict(raw)
        result['daily_cost'] = raw['daily_cost_per_tower'] * qty_towers
        result['deposit_amount'] = raw['deposit_total']
        result['market_value'] = raw['market_value_total']
        result['total_area'] = 0

        tower_code = 'tower_psrv21' if model == 'ПСРВ-21' else 'tower_psrv22'
        sections = raw['sections']
        result['equipment_items'] = [{
            'code': tower_code,
            'name': f'Вышка-тура {model} h={height}м ({sections} сек.)',
            'qty': qty_towers,
            'unit_price': raw['market_value_per_tower'],
            'total': raw['market_value_total'],
        }]
        return result


class DailyRateAlgorithm:
    """Simple per-unit per-day pricing for any equipment (excavators, cranes, etc.)."""
    code = 'daily_rate'
    name = 'Посуточная (любая техника)'

    def calculate(self, pricing_params, deal_context, equipment_items=None):
        days = int(deal_context['days'])
        deposit_pct = float(deal_context.get('deposit_pct', 10))
        delivery_cost = float(deal_context.get('delivery_cost', 0))
        vat_mode = deal_context.get('vat_mode', 'no_vat')
        city = deal_context.get('city', 'Екатеринбург')
        city_coeff = CITY_COEFFICIENTS.get(city, 1.0)

        items_out = []
        market_value = 0.0
        daily_cost = 0.0

        for item in (equipment_items or []):
            qty = int(item.get('qty', 0))
            if qty <= 0:
                continue
            daily_rate = float(item.get('daily_rate', 0))
            unit_price = float(item.get('unit_price', 0))

            item_daily = qty * daily_rate * city_coeff
            item_market = qty * unit_price
            daily_cost += item_daily
            market_value += item_market
            items_out.append({
                'code': item['code'],
                'name': item['name'],
                'qty': qty,
                'unit_price': unit_price,
                'daily_rate': daily_rate,
                'total': item_market,
            })

        total_rental = daily_cost * days
        deposit = int(roundup(market_value * deposit_pct / 100, -2))
        delivery_roundtrip = delivery_cost * 2
        grand_total = total_rental + deposit + delivery_roundtrip

        if vat_mode == 'with_vat':
            vat_amount = round(grand_total * 0.20, 2)
            grand_total_final = round(grand_total + vat_amount, 2)
        else:
            vat_amount = 0.0
            grand_total_final = grand_total

        return {
            'total_area': 0,
            'daily_cost': daily_cost,
            'rental_days': days,
            'total_rental': total_rental,
            'market_value': market_value,
            'deposit_pct': deposit_pct,
            'deposit_amount': deposit,
            'delivery_cost': delivery_cost,
            'delivery_roundtrip': delivery_roundtrip,
            'grand_total': grand_total,
            'vat_amount': vat_amount,
            'grand_total_final': grand_total_final,
            'equipment_items': items_out,
            'city_coeff': city_coeff,
        }


ALGORITHM_REGISTRY = {
    AreaBasedAlgorithm.code: AreaBasedAlgorithm,
    TowerAlgorithm.code: TowerAlgorithm,
    DailyRateAlgorithm.code: DailyRateAlgorithm,
}

ALGORITHM_CHOICES = [
    ('area_based', 'По площади (строительные леса)'),
    ('tower', 'Вышки-туры'),
    ('daily_rate', 'Посуточная (любая техника)'),
]


def get_algorithm(code):
    cls = ALGORITHM_REGISTRY.get(code)
    if not cls:
        raise ValueError(f'Unknown pricing algorithm: {code!r}')
    return cls()
