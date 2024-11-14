from rest_framework import serializers
from app_core.models import Player, Task, PlayerTask


class PlayerSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Player"""
    class Meta:
        model = Player
        fields = ['id', 'tg_id', 'registration_date', 'points', 'points_all', 'tap_points', 'tickets', 'tickets_all',
                  'consecutive_days', 'last_login_date', 'login_today', 'daily_points', 'daily_bonus_friends']


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Task"""

    class Meta:
        model = Task
        fields = ['id', 'name', 'picture', 'dop_name', 'description', 'reward_currency', 'chest',
                  'is_active']


class PlayerTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели PlayerTask"""
    task = TaskSerializer(read_only=True)

    class Meta:
        model = PlayerTask
        fields = ['id', 'task', 'start_time', 'completed']

