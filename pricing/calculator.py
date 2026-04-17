"""
Pricing calculator based on Excel file "Расчет аренды лесов.xlsx"
All formulas, coefficients and rate tables are taken directly from the Excel model.
"""
import math

# ============================================================
# SCAFFOLDING RATE TABLE (руб./м2/день) — Sheet "Расчет лесов" AG2:AM7
# (area_max, days_max, rate)
# ============================================================
SCAFFOLD_RATES = [
    # До 50 м2
    (50, 3, 10.0), (50, 7, 8.0), (50, 14, 4.5), (50, 30, 3.2), (50, 45, 2.5), (50, 60, 2.0), (50, 9999, 1.6),
    # До 100 м2
    (100, 3, 8.0), (100, 7, 5.0), (100, 14, 3.7), (100, 30, 2.7), (100, 45, 2.0), (100, 60, 1.65), (100, 9999, 1.4),
    # До 300 м2
    (300, 3, 5.0), (300, 7, 4.0), (300, 14, 2.8), (300, 30, 2.1), (300, 45, 1.7), (300, 60, 1.45), (300, 9999, 1.25),
    # До 500 м2
    (500, 7, 3.0), (500, 14, 2.0), (500, 30, 1.65), (500, 45, 1.5), (500, 60, 1.3), (500, 9999, 1.1),
    # До 1000 м2
    (1000, 7, 2.5), (1000, 14, 1.7), (1000, 30, 1.4), (1000, 45, 1.25), (1000, 60, 1.1), (1000, 9999, 1.0),
    # Св 1000 м2
    (9999, 7, 2.0), (9999, 14, 1.5), (9999, 30, 1.25), (9999, 45, 1.1), (9999, 60, 1.0), (9999, 9999, 0.9),
]

# ============================================================
# TOWER RATE TABLE (руб./вышка/день) — Sheet "Вышки туры" T2:Z7
# (height_max, days_max, rate)
# ============================================================
TOWER_RATES = [
    (3.89, 4, 290), (3.89, 7, 230), (3.89, 14, 170), (3.89, 21, 150), (3.89, 30, 130), (3.89, 45, 110), (3.89, 9999, 95),
    (6.29, 4, 400), (6.29, 7, 320), (6.29, 14, 230), (6.29, 21, 210), (6.29, 30, 180), (6.29, 45, 150), (6.29, 9999, 130),
    (8.69, 4, 480), (8.69, 7, 380), (8.69, 14, 270), (8.69, 21, 250), (8.69, 30, 220), (8.69, 45, 180), (8.69, 9999, 160),
    (11.09, 4, 550), (11.09, 7, 440), (11.09, 14, 320), (11.09, 21, 290), (11.09, 30, 260), (11.09, 45, 210), (11.09, 9999, 180),
    (13.49, 4, 630), (13.49, 7, 500), (13.49, 14, 360), (13.49, 21, 330), (13.49, 30, 295), (13.49, 45, 240), (13.49, 9999, 210),
    (14.69, 4, 720), (14.69, 7, 560), (14.69, 14, 410), (14.69, 21, 370), (14.69, 30, 330), (14.69, 45, 270), (14.69, 9999, 240),
    (9999, 4, 1300), (9999, 7, 1300), (9999, 14, 1300), (9999, 21, 1300), (9999, 30, 1300), (9999, 45, 1300), (9999, 9999, 1300),
]

# ============================================================
# CITY COEFFICIENTS — Sheet "Расчет лесов" AG22:AG25 / "Вышки туры" Z14:Z17
# ============================================================
CITY_COEFFICIENTS = {
    'Екатеринбург': 1.0,
    'Пермь': 1.15,
    'Новосибирск': 1.15,
    'Челябинск': 1.4,
}

# ============================================================
# SCAFFOLD BASE EQUIPMENT PRICES (Abris prices, коп. AI30=1.15)
# Sheet "Расчет лесов" AJ32:AJ37
# Our price = ROUNDUP(base * 1.15, -1)
# ============================================================
SCAFFOLD_BASE_PRICES = {
    'frame_std': 1210,      # Рама проходная
    'frame_ladder': 1450,   # Рама с лестницей
    'brace_diag': 546,      # Связь диагональная
    'brace_horiz': 272,     # Связь горизонтальная
    'plank': 390,           # Мостки деревянные
    'purlin': 970,          # Ригель
    'bracket': 200,         # Кронштейн
    'base_plate': 150,      # Башмак
}

SCAFFOLD_PRICE_COEFF = 1.15  # AI30 — наш коэффициент на цены Абрис

# ============================================================
# SCAFFOLD EQUIPMENT WEIGHTS (kg) and VOLUMES (m3) per unit
# Sheet "Расчет лесов" AI17:AJ22
# ============================================================
SCAFFOLD_WEIGHTS = {
    'frame_std': 10.0,
    'frame_ladder': 11.7,
    'brace_diag': 5.6,
    'brace_horiz': 2.6,
    'plank': 15.0,
    'purlin': 9.5,
}
SCAFFOLD_VOLUMES = {
    'frame_std': 0.1,
    'frame_ladder': 0.1,
    'brace_diag': 0.0019,
    'brace_horiz': 0.0041,
    'plank': 0.068,
    'purlin': 0.0056,
}

# ============================================================
# PLANK DAILY RATES (руб./шт/день) — Sheet "Расчет лесов" AH9:AM9
# ============================================================
PLANK_RATES = [(7, 18), (14, 13), (30, 10), (45, 8), (60, 7), (9999, 5)]

# ============================================================
# DEPRECIATION/RECOVERY % BY DURATION — Sheet "Расчет лесов" L25
# ============================================================
RECOVERY_RATES = [
    (3, 3), (7, 4), (14, 6), (21, 8), (30, 10), (45, 14),
    (60, 17), (90, 22), (120, 27), (180, 32), (9999, 40),
]

# ============================================================
# TOWER MARKET VALUES — Sheet "Вышки туры" X20:X35 (ПСРВ-21) and Лист1 G3:G19 (ПСРВ-22)
# Indexed by section count
# ============================================================
PSRV21_VALUES = {
    1: 15500, 2: 18500, 3: 22000, 4: 26000, 5: 29500, 6: 33000,
    7: 36500, 8: 39500, 9: 43000, 10: 46500, 11: 50000, 12: 53500,
    13: 57000, 14: 60000, 15: 63500, 16: 67000,
}
PSRV22_VALUES = {
    1: 21400, 2: 25140, 3: 28900, 4: 34900, 5: 38500, 6: 42500,
    7: 46300, 8: 50000, 9: 53700, 10: 57700, 11: 61000, 12: 65100,
    13: 69200, 14: 72800, 15: 76500, 16: 80600, 17: 83900,
}

# Tower height (m) → section count mapping — Sheet "Вышки туры" B13:B28
TOWER_HEIGHT_SECTIONS = [
    (2.69, 1), (3.89, 2), (5.09, 3), (6.29, 4), (7.49, 5), (8.69, 6),
    (9.89, 7), (11.09, 8), (12.29, 9), (13.49, 10), (14.69, 11), (15.89, 12),
    (17.09, 13), (18.29, 14), (19.49, 15), (20.69, 16),
]

# ============================================================
# DELIVERY PRICES BY TOWN (min/max) — Sheet "Расчет лесов" B31:C68
# ============================================================
DELIVERY_PRICES = [
    ('По городу', 900, 900),
    ('Арамиль', 1500, 1800),
    ('Балтым', 1000, 1500),
    ('Верхнее Дуброво', 1200, 1200),
    ('Верхняя Пышма', 1300, 1600),
    ('Горный Щит', 1500, 1500),
    ('Сухой лог', 3500, 3500),
    ('Первоуральск', 2000, 2400),
    ('Берёзовский', 1500, 1300),
    ('Каменск-Уральский', 3500, 4000),
    ('Сысерть', 2100, 2500),
    ('Кольцово', 1000, 1200),
    ('Среднеуральск', 1500, 1800),
    ('Реж', 2100, 2500),
    ('Ревда', 2000, 2400),
    ('Новоуральск', 2000, 2500),
    ('Полевской', 2000, 2400),
    ('Нижний Тагил', 3000, 3500),
    ('Заречный', 2000, 2400),
    ('Богданович', 2500, 3000),
    ('Асбест', 2500, 3000),
    ('Красноуфимск', 4000, 4500),
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def roundup(value, decimals=0):
    """Excel ROUNDUP — always rounds away from zero."""
    if decimals >= 0:
        factor = 10 ** decimals
        return math.ceil(float(value) * factor) / factor
    else:
        factor = 10 ** (-decimals)
        return math.ceil(float(value) / factor) * factor


def get_scaffold_rate(area, days):
    """Lookup scaffold rate from rate table."""
    for a_max, d_max, rate in SCAFFOLD_RATES:
        if float(area) <= a_max and int(days) <= d_max:
            return rate
    return SCAFFOLD_RATES[-1][2]


def get_tower_rate(height, days):
    """Lookup tower rate from rate table."""
    for h_max, d_max, rate in TOWER_RATES:
        if float(height) <= h_max and int(days) <= d_max:
            return rate
    return 1300


def get_plank_rate(days):
    """Daily rental rate per plank unit."""
    for d_max, rate in PLANK_RATES:
        if int(days) <= d_max:
            return rate
    return 5


def get_recovery_pct(days):
    """Depreciation recovery % by rental duration."""
    for d_max, pct in RECOVERY_RATES:
        if int(days) <= d_max:
            return pct
    return 40


def get_scaffold_unit_price(item_code, price_coeff=SCAFFOLD_PRICE_COEFF):
    """Our unit price = ROUNDUP(abris_base * coeff, -1)"""
    base = SCAFFOLD_BASE_PRICES.get(item_code, 0)
    return int(roundup(base * price_coeff, -1))


def get_tower_sections(height):
    """Get section count from height."""
    for h, s in TOWER_HEIGHT_SECTIONS:
        if abs(float(height) - h) < 0.01:
            return s
    # find closest
    closest = min(TOWER_HEIGHT_SECTIONS, key=lambda x: abs(x[0] - float(height)))
    return closest[1]


# ============================================================
# MAIN CALCULATORS
# ============================================================

def calculate_scaffolding(sides, days, city='Екатеринбург', season_coeff=1.2,
                          diagonal_mode='every', planks_qty=4, deposit_pct=10,
                          delivery_cost=0, vat_mode='no_vat', price_coeff=1.15,
                          bracket_qty=0, base_plate_qty=0):
    """
    Scaffolding rental calculator.

    sides: list of (length, height) tuples — up to 4 sides
    diagonal_mode: 'every' (В каждую) or 'staggered' (Через секцию)
    vat_mode: 'no_vat' or 'with_vat'
    """
    days = int(days)

    # ----------------------------------------------------------
    # 1. Area calculation: L3=J3*K3, L12=SUM(L3,L5,L7,L9)
    # ----------------------------------------------------------
    total_area = 0.0
    sides_detail = []
    for length, height in sides:
        length, height = float(length), float(height)
        area = length * height
        sides_detail.append({'length': length, 'height': height, 'area': area})
        total_area += area

    # ----------------------------------------------------------
    # 2. Equipment quantities
    # Section = 3m wide, level = 2m tall
    # J4 = J3/3, K4 = K3/2
    # Total frames per side = (sections+1) * levels
    # Ladder frames: K4*1 per stairway bay
    # Horiz: CEILING(sections * levels * horiz_coeff, 1)  AL22
    # Diag:  CEILING(sections * levels / diag_coeff, 1)   AL21
    # ----------------------------------------------------------
    diag_coeff = 1 if diagonal_mode == 'every' else 2      # AL21
    horiz_coeff = 1 if diagonal_mode == 'every' else 1.5   # AL22

    qty_frame_std = 0
    qty_frame_ladder = 0
    qty_brace_diag = 0
    qty_brace_horiz = 0

    for s in sides_detail:
        if s['length'] <= 0 or s['height'] <= 0:
            continue
        sections = s['length'] / 3.0   # J4
        levels = s['height'] / 2.0     # K4

        total_frames = (sections + 1) * levels   # J16
        ladder_frames = levels                   # J17 — 1 ladder column per level-row
        std_frames = total_frames - ladder_frames

        qty_frame_std += std_frames
        qty_frame_ladder += ladder_frames
        qty_brace_horiz += math.ceil(sections * levels * horiz_coeff)   # J18
        qty_brace_diag += math.ceil(sections * levels / diag_coeff)     # J19

    qty_frame_std = max(0, math.ceil(qty_frame_std))
    qty_frame_ladder = max(0, math.ceil(qty_frame_ladder))
    qty_plank = int(planks_qty) * 3    # B12 = J21 * 3
    qty_purlin = int(planks_qty) * 2   # B13 = J21 * 2
    qty_bracket = int(bracket_qty)
    qty_base_plate = int(base_plate_qty)

    # ----------------------------------------------------------
    # 3. Rate lookup — C2 in Excel
    # ----------------------------------------------------------
    rate = get_scaffold_rate(total_area, days)
    city_coeff = CITY_COEFFICIENTS.get(city, 1.0)

    # ----------------------------------------------------------
    # 4. Ladder frame surcharge V2: 1.7 if ALL frames are ladder type
    # ----------------------------------------------------------
    all_ladder = (qty_frame_std == 0 and qty_frame_ladder > 0)
    ladder_ratio_coeff = 1.7 if all_ladder else 1.0

    # ----------------------------------------------------------
    # 5. Plank daily cost: J21 * K21
    # ----------------------------------------------------------
    plank_rate = get_plank_rate(days)
    planks_daily = int(planks_qty) * plank_rate

    # ----------------------------------------------------------
    # 6. Daily rental cost (C3)
    # = ROUNDUP(rate * area * season * city * ladder + planks_daily, -1)
    # ----------------------------------------------------------
    daily_cost = roundup(
        rate * total_area * float(season_coeff) * city_coeff * ladder_ratio_coeff + planks_daily,
        -1
    )

    # ----------------------------------------------------------
    # 7. Total rental for period (D22)
    # ----------------------------------------------------------
    total_rental = daily_cost * days

    # ----------------------------------------------------------
    # 8. Equipment unit prices
    # ----------------------------------------------------------
    prices = {code: get_scaffold_unit_price(code, price_coeff) for code in SCAFFOLD_BASE_PRICES}

    equipment_items = [
        {'code': 'frame_std', 'name': 'Рама проходная', 'unit': 'шт', 'qty': qty_frame_std, 'price': prices['frame_std']},
        {'code': 'frame_ladder', 'name': 'Рама с лестницей', 'unit': 'шт', 'qty': qty_frame_ladder, 'price': prices['frame_ladder']},
        {'code': 'brace_diag', 'name': 'Связь диагональная 3,3м', 'unit': 'шт', 'qty': qty_brace_diag, 'price': prices['brace_diag']},
        {'code': 'brace_horiz', 'name': 'Связь горизонтальная', 'unit': 'шт', 'qty': qty_brace_horiz, 'price': prices['brace_horiz']},
        {'code': 'plank', 'name': 'Мостки деревянные', 'unit': 'шт', 'qty': qty_plank, 'price': prices['plank']},
        {'code': 'purlin', 'name': 'Ригель', 'unit': 'шт', 'qty': qty_purlin, 'price': prices['purlin']},
        {'code': 'bracket', 'name': 'Кронштейн', 'unit': 'шт', 'qty': qty_bracket, 'price': prices['bracket']},
        {'code': 'base_plate', 'name': 'Башмак', 'unit': 'шт', 'qty': qty_base_plate, 'price': prices['base_plate']},
    ]
    for item in equipment_items:
        item['total'] = item['qty'] * item['price']

    # ----------------------------------------------------------
    # 9. Market value (D16)
    # ----------------------------------------------------------
    market_value = sum(item['total'] for item in equipment_items)

    # ----------------------------------------------------------
    # 10. Deposit (D17) = ROUNDUP(market_value * pct / 100, -2)
    # ----------------------------------------------------------
    deposit = int(roundup(market_value * float(deposit_pct) / 100, -2))

    # ----------------------------------------------------------
    # 11. Totals
    # ----------------------------------------------------------
    delivery_roundtrip = float(delivery_cost) * 2   # D18+D19
    grand_total = total_rental + deposit + delivery_roundtrip

    vat_amount = 0.0
    if vat_mode == 'with_vat':
        vat_amount = round(grand_total * 0.20, 2)
        grand_total_final = round(grand_total + vat_amount, 2)
    else:
        grand_total_final = grand_total

    # ----------------------------------------------------------
    # 12. Recovery % and recommended price (L25, L26)
    # ----------------------------------------------------------
    recovery_pct = get_recovery_pct(days)
    recommended_daily = (market_value * recovery_pct / 100) / days if days > 0 else 0

    # ----------------------------------------------------------
    # 13. Weight, volume, logistics (AI/AJ columns)
    # ----------------------------------------------------------
    total_weight = sum(
        qty * SCAFFOLD_WEIGHTS.get(code, 0)
        for code, qty in [
            ('frame_std', qty_frame_std), ('frame_ladder', qty_frame_ladder),
            ('brace_diag', qty_brace_diag), ('brace_horiz', qty_brace_horiz),
            ('plank', qty_plank), ('purlin', qty_purlin),
        ]
    )
    total_volume = sum(
        qty * SCAFFOLD_VOLUMES.get(code, 0)
        for code, qty in [
            ('frame_std', qty_frame_std), ('frame_ladder', qty_frame_ladder),
            ('brace_diag', qty_brace_diag), ('brace_horiz', qty_brace_horiz),
            ('plank', qty_plank), ('purlin', qty_purlin),
        ]
    )
    trucks_needed = math.ceil(total_weight / 400 / 2) * 2 if total_weight > 0 else 0

    return {
        'total_area': round(total_area, 2),
        'rate': rate,
        'city': city,
        'city_coeff': city_coeff,
        'season_coeff': float(season_coeff),
        'ladder_ratio_coeff': ladder_ratio_coeff,
        'plank_rate': plank_rate,
        'planks_daily': planks_daily,
        'daily_cost': daily_cost,
        'rental_days': days,
        'total_rental': total_rental,
        'equipment_items': equipment_items,
        'market_value': market_value,
        'deposit_pct': float(deposit_pct),
        'deposit_amount': deposit,
        'delivery_cost': float(delivery_cost),
        'delivery_roundtrip': delivery_roundtrip,
        'grand_total': grand_total,
        'vat_amount': vat_amount,
        'grand_total_final': grand_total_final,
        'recovery_pct': recovery_pct,
        'recommended_daily': round(recommended_daily, 0),
        'total_weight': round(total_weight, 1),
        'total_volume': round(total_volume, 3),
        'trucks_needed': trucks_needed,
        'vat_mode': vat_mode,
        'diagonal_mode': diagonal_mode,
        'planks_qty': int(planks_qty),
        'bracket_qty': qty_bracket,
        'base_plate_qty': qty_base_plate,
    }


def calculate_tower(height, days, qty_towers=1, model='ПСРВ-21', city='Екатеринбург',
                    deposit_pct=10, delivery_cost=0, vat_mode='no_vat'):
    """
    Tower-scaffold (вышка-тура) rental calculator.
    """
    height = float(height)
    days = int(days)
    qty_towers = int(qty_towers)

    # ----------------------------------------------------------
    # 1. Rate lookup — C3 in "Вышки туры"
    # ----------------------------------------------------------
    rate = get_tower_rate(height, days)
    city_coeff = CITY_COEFFICIENTS.get(city, 1.0)

    # Model coefficient (L5): ПСРВ-21 = 0.85, ПСРВ-22 = 1.05
    if model == 'ПСРВ-21':
        model_coeff = 0.85
        extra_charge = 0
    else:
        model_coeff = 1.05
        extra_charge = 50   # К7: ПСРВ-22 surcharge

    # VAT multiplier (L6=1.2 only if with_vat)
    vat_mult = 1.2 if vat_mode == 'with_vat' else 1.0

    # Daily cost per tower: rate * city_coeff * model_coeff * vat_mult + extra
    daily_cost_per_tower = roundup(rate * city_coeff * model_coeff * vat_mult + extra_charge, 0)

    # ----------------------------------------------------------
    # 2. Total rental
    # ----------------------------------------------------------
    total_rental_per_tower = daily_cost_per_tower * days
    total_rental = total_rental_per_tower * qty_towers

    # ----------------------------------------------------------
    # 3. Market value (tower assembly deposit base)
    # ----------------------------------------------------------
    sections = get_tower_sections(height)
    values_map = PSRV21_VALUES if model == 'ПСРВ-21' else PSRV22_VALUES
    max_sec = max(values_map.keys())
    market_value_per_tower = values_map.get(sections, values_map[max_sec])
    market_value_total = market_value_per_tower * qty_towers

    # ----------------------------------------------------------
    # 4. Deposit: ROUNDUP(value * pct / 100, 0)
    # ----------------------------------------------------------
    deposit_per_tower = int(roundup(market_value_per_tower * float(deposit_pct) / 100, 0))
    deposit_total = deposit_per_tower * qty_towers

    # ----------------------------------------------------------
    # 5. Grand total
    # ----------------------------------------------------------
    delivery_roundtrip = float(delivery_cost) * 2
    grand_total = total_rental + deposit_total + delivery_roundtrip

    if vat_mode == 'with_vat':
        vat_amount = round(grand_total * 0.20, 2)
        grand_total_final = round(grand_total + vat_amount, 2)
    else:
        vat_amount = 0.0
        grand_total_final = grand_total

    # ----------------------------------------------------------
    # 6. Recovery and recommended price (D8, D9)
    # ----------------------------------------------------------
    recovery_pct = get_recovery_pct(days)
    recommended_daily = int(roundup((market_value_per_tower * recovery_pct / 100) / days * 1.2, 0)) if days > 0 else 0

    return {
        'height': height,
        'sections': sections,
        'model': model,
        'qty_towers': qty_towers,
        'rate': rate,
        'city': city,
        'city_coeff': city_coeff,
        'model_coeff': model_coeff,
        'extra_charge': extra_charge,
        'daily_cost_per_tower': daily_cost_per_tower,
        'rental_days': days,
        'total_rental_per_tower': total_rental_per_tower,
        'total_rental': total_rental,
        'market_value_per_tower': market_value_per_tower,
        'market_value_total': market_value_total,
        'deposit_pct': float(deposit_pct),
        'deposit_per_tower': deposit_per_tower,
        'deposit_total': deposit_total,
        'delivery_cost': float(delivery_cost),
        'delivery_roundtrip': delivery_roundtrip,
        'grand_total': grand_total,
        'vat_amount': vat_amount,
        'grand_total_final': grand_total_final,
        'recovery_pct': recovery_pct,
        'recommended_daily': recommended_daily,
        'vat_mode': vat_mode,
    }


def num_to_words_ru(amount):
    """Convert a number to Russian words (сумма прописью)."""
    amount = int(round(float(amount)))
    if amount == 0:
        return 'ноль рублей 00 копеек'

    ones_m = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    ones_f = ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    teens = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
             'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
    tens = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят',
            'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
    hundreds = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
                'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']

    def chunk_to_words(n, feminine=False):
        words = []
        h = n // 100
        t = (n % 100) // 10
        o = n % 10
        if h:
            words.append(hundreds[h])
        if t == 1:
            words.append(teens[o])
        else:
            if t:
                words.append(tens[t])
            if o:
                words.append(ones_f[o] if feminine else ones_m[o])
        return ' '.join(words)

    def rub_suffix(n):
        n = abs(n) % 100
        o = n % 10
        if 11 <= n <= 19:
            return 'рублей'
        if o == 1:
            return 'рубль'
        if 2 <= o <= 4:
            return 'рубля'
        return 'рублей'

    def thou_suffix(n):
        n = abs(n) % 100
        o = n % 10
        if 11 <= n <= 19:
            return 'тысяч'
        if o == 1:
            return 'тысяча'
        if 2 <= o <= 4:
            return 'тысячи'
        return 'тысяч'

    def mil_suffix(n):
        n = abs(n) % 100
        o = n % 10
        if 11 <= n <= 19:
            return 'миллионов'
        if o == 1:
            return 'миллион'
        if 2 <= o <= 4:
            return 'миллиона'
        return 'миллионов'

    parts = []
    millions = amount // 1_000_000
    thousands = (amount % 1_000_000) // 1000
    remainder = amount % 1000

    if millions:
        parts.append(chunk_to_words(millions) + ' ' + mil_suffix(millions))
    if thousands:
        parts.append(chunk_to_words(thousands, feminine=True) + ' ' + thou_suffix(thousands))
    if remainder:
        parts.append(chunk_to_words(remainder) + ' ' + rub_suffix(remainder))
    elif not millions and not thousands:
        parts.append('ноль рублей')
    else:
        parts.append(rub_suffix(0))

    result = ' '.join(parts)
    # capitalize first letter
    return result[0].upper() + result[1:] + ' 00 копеек'
