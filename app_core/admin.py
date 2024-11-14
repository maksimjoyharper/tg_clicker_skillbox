from django.contrib import admin
from app_core.models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели Player."""
    list_display = ['id', 'tg_id', 'registration_date', 'points', 'points_all', 'tap_points', 'tickets', 'tickets_all',
                    'consecutive_days', 'last_login_date', 'login_today', 'is_new', 'daily_points', 'daily_bonus_friends',
                    'rank', 'league']

