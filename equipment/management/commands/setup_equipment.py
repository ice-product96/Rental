"""
Management command: python manage.py setup_equipment
Creates EquipmentCategory records, then EquipmentType + WarehouseStock records.
"""
from django.core.management.base import BaseCommand
from pricing.models import EquipmentCategory
from equipment.models import EquipmentType, WarehouseStock

CATEGORIES = [
    # (name, algorithm_code, deposit_pct, ordering)
    ('Строительные леса', 'area_based', 10, 1),
    ('Вышки-туры',        'tower',       10, 2),
    ('Прочая техника',    'daily_rate',  15, 3),
]

# code, name, category_name, unit, base_price, price_coeff, daily_rental_rate, weight, volume
EQUIPMENT_DATA = [
    # --- Строительные леса (area_based) ---
    ('frame_std',    'Рама проходная',           'Строительные леса', 'шт', 1210,  1.15, 0,   10.0,  0.1),
    ('frame_ladder', 'Рама с лестницей',          'Строительные леса', 'шт', 1450,  1.15, 0,   11.7,  0.1),
    ('brace_diag',   'Связь диагональная 3,3м',   'Строительные леса', 'шт', 546,   1.15, 0,    5.6,  0.0019),
    ('brace_horiz',  'Связь горизонтальная',       'Строительные леса', 'шт', 272,   1.15, 0,    2.6,  0.0041),
    ('plank',        'Мостки деревянные',          'Строительные леса', 'шт', 390,   1.15, 0,   15.0,  0.068),
    ('purlin',       'Ригель',                     'Строительные леса', 'шт', 970,   1.15, 0,    9.5,  0.0056),
    ('bracket',      'Кронштейн',                  'Строительные леса', 'шт', 200,   1.0,  0,    0.0,  0.0),
    ('base_plate',   'Башмак',                     'Строительные леса', 'шт', 150,   1.0,  0,    0.0,  0.0),
    # --- Вышки-туры (tower) ---
    ('tower_psrv21', 'Вышка-тура ПСРВ-21 (компл)', 'Вышки-туры',       'шт', 15500, 1.0,  0,    0.0,  0.0),
    ('tower_psrv22', 'Вышка-тура ПСРВ-22 (компл)', 'Вышки-туры',       'шт', 21400, 1.0,  0,    0.0,  0.0),
    # --- Прочая техника (daily_rate) — примеры ---
    ('generator_5kw', 'Генератор 5 кВт',           'Прочая техника',   'шт', 25000, 1.0,  500,  0.0,  0.0),
    ('compressor_k25', 'Компрессор К-25',           'Прочая техника',   'шт', 80000, 1.0,  1200, 0.0,  0.0),
]


class Command(BaseCommand):
    help = 'Create initial EquipmentCategory, EquipmentType and WarehouseStock records'

    def handle(self, *args, **options):
        # Step 1: create categories
        cat_map = {}
        for name, algo, deposit_pct, ordering in CATEGORIES:
            cat, created = EquipmentCategory.objects.update_or_create(
                name=name,
                defaults={
                    'algorithm_code': algo,
                    'deposit_pct_default': deposit_pct,
                    'ordering': ordering,
                    'is_active': True,
                }
            )
            cat_map[name] = cat
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action} category: {name}')

        # Step 2: create equipment types
        created_count = updated_count = 0
        for code, name, cat_name, unit, base_price, coeff, daily_rate, weight, volume in EQUIPMENT_DATA:
            et, created = EquipmentType.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': cat_map.get(cat_name),
                    'unit': unit,
                    'base_price': base_price,
                    'price_coefficient': coeff,
                    'daily_rental_rate': daily_rate,
                    'weight_per_unit': weight,
                    'volume_per_unit': volume,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {name}')
            else:
                updated_count += 1

            WarehouseStock.objects.get_or_create(
                equipment_type=et,
                defaults={'quantity_total': 0, 'min_stock_level': 0}
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created_count} created, {updated_count} updated. '
            f'Use admin panel to set warehouse quantities.'
        ))
