from app_core.models import Player, Task, PlayerTask
from adrf.serializers import ModelSerializer


class PlayerSerializer(ModelSerializer):
    """Сериализатор для модели Player"""
    class Meta:
        model = Player
        fields = ['id', 'tg_id', 'name', 'registration_date', 'points', 'points_all', 'tap_points', 'tickets',
                  'tickets_all', 'premium_tickets', 'premium_tickets_all', 'consecutive_days', 'last_login_date', 'login_today', 'daily_points',
                  'daily_bonus_friends', 'rank', 'league']


class TaskSerializer(ModelSerializer):
    """Сериализатор для модели Task"""

    class Meta:
        model = Task
        fields = ['id', 'name', 'picture', 'dop_name', 'description', 'link', 'reward_currency', 'reward_tickets',
                  'is_active']


class PlayerTaskSerializer(ModelSerializer):
    """Сериализатор для модели PlayerTask"""
    task = TaskSerializer(read_only=True)

    class Meta:
        model = PlayerTask
        fields = ['id', 'task', 'start_time', 'completed']

