from django.contrib import admin
from app_core.models import *


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели Player."""
    list_display = ['id', 'tg_id', 'name', 'registration_date', 'points', 'points_all', 'tap_points', 'tickets',
                    'tickets_all', 'premium_tickets', 'premium_tickets_all', 'consecutive_days', 'last_login_date',
                    'login_today', 'is_new', 'daily_points', 'daily_bonus_friends', 'rank', 'league']


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели League."""
    list_display = ['id', 'name', 'picture', 'description']


@admin.register(ReferralSystem)
class ReferralSystemAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели ReferralSystem."""
    list_display = ['id', 'referral', 'new_player', 'referral_bonus', 'new_player_bonus']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели Task."""
    list_display = ['id', 'name', 'picture', 'dop_name', 'description', 'link', 'reward_currency', 'reward_tickets', 'is_active']


@admin.register(PlayerTask)
class PlayerTaskAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели PlayerTask."""
    list_display = ['id', 'player', 'task', 'start_time', 'completed', 'add_flag']

