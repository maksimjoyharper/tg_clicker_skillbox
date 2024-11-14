from datetime import timedelta

from django.db import models
from django.utils import timezone


class League(models.Model):
    """Модель лиги"""
    name = models.CharField(max_length=100, verbose_name="Название лиги")
    picture = models.ImageField(null=True, blank=True, verbose_name='Картинка')
    description = models.CharField(max_length=255, verbose_name='Описание задачи', default='')


class Player(models.Model):
    """Модель игрока"""
    tg_id = models.PositiveBigIntegerField(unique=True, verbose_name="Telegram ID")
    name = models.CharField(max_length=50, verbose_name="Имя игрока")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации игрока")
    points = models.IntegerField(default=1000, verbose_name="Текущие баллы игрока")
    points_all = models.IntegerField(default=0, verbose_name="Количество баллов игрока за всё время")
    tap_points = models.IntegerField(default=1, verbose_name="Баллы за 1 тап в игре")
    tickets = models.IntegerField(default=3, verbose_name="Текущее количество билетов игрока")
    tickets_all = models.IntegerField(default=3, verbose_name="Количество билетов игрока за всё время")
    consecutive_days = models.IntegerField(default=0, verbose_name="Количество дней подряд")
    last_login_date = models.DateField(null=True, blank=True, verbose_name="Последний вход для расчёта дней подряд")
    login_today = models.BooleanField(default=False, verbose_name="Входил ли пользователь сегодня")
    is_new = models.BooleanField(default=False, verbose_name='Новый игрок/не новый')
    daily_points = models.IntegerField(default=0, verbose_name="Очки за текущий день")
    daily_bonus_friends = models.IntegerField(default=0, verbose_name="Бонус от рефералов за текущий день")
    rank = models.IntegerField(null=True, blank=True, verbose_name="Место игрока в топ-100")
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="players", verbose_name="Лига игрока")

    async def update_daily_status(self):
        """
        Проверяем вход пользователя, если вход подряд увеличиваем количество дней подряд, проверяем какой день подряд
        вошёл пользователь и начисляем ему билеты, проверяем количество дней подряд и увеличиваем значение тапа.
        """
        today = timezone.now().date()
        # Если пользователь уже заходил сегодня, ничего не делаем
        if self.login_today:
            return
        # Проверка для расчета consecutive_days
        if self.last_login_date:
            days_diff = (today - self.last_login_date).days
            self.consecutive_days = self.consecutive_days + 1 if days_diff == 1 else 1
        else:
            self.consecutive_days = 1

        day_in_cycle = self.consecutive_days % 10
        if day_in_cycle == 0:
            day_in_cycle = 10  # Если остаток 0, это 10-й день в цикле

        self.tickets += day_in_cycle
        self.tickets_all += day_in_cycle  # Увеличиваем общий счетчик билетов
        if 10 < self.consecutive_days < 21:
            self.tap_points = 2
        elif self.consecutive_days > 20:
            self.tap_points = 3
        else:
            self.tap_points = 1

        # Обновляем последний вход
        self.last_login_date = today
        self.login_today = True  # Обновляем флаг, что пользователь зашел сегодня
        await self.asave()

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"

    def __str__(self):
        return f"name:{self.name}, tg_id:{self.tg_id}"


class ReferralSystem(models.Model):
    """Модель реферальной системы"""
    referral = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='referral', verbose_name="Реферал")
    new_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='new_person',
                                   verbose_name="Новый игрок")
    referral_bonus = models.BooleanField(default=True, verbose_name="Бонус реферала")
    new_player_bonus = models.BooleanField(default=True, verbose_name="Бонус нового игрока")

    def __str__(self):
        return f"me:{self.referral.name}___new_player:{self.new_player.name}"


class Task(models.Model):
    """Задания для выполнения."""
    name = models.CharField(max_length=50, verbose_name='Название задачи', default='')
    picture = models.ImageField(null=True, blank=True, verbose_name='Картинка')
    dop_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Доп. название задачи')
    description = models.CharField(max_length=255, verbose_name='Описание задачи', default='')
    reward_currency = models.IntegerField(default=0, verbose_name='Награда (баллы)')
    is_active = models.BooleanField(default=True, verbose_name="Активность задачи")

    def __str__(self):
        return self.name


class PlayerTask(models.Model):
    """Связываем задачи с игроком."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='task_player', verbose_name='Игрок')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='player_tasks', verbose_name='Задача')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='Время начала')
    completed = models.BooleanField(default=False, verbose_name='Выполнено')
    add_flag = models.BooleanField(default=False, verbose_name='Доп. флаг')

    async def check_completion(self):
        """Проверка завершения задачи для одноразовых задач с задержкой 1 час"""
        if not self.completed:
            if self.start_time and timezone.now() >= self.start_time + timedelta(minutes=1):
                self.completed = True
                self.start_time = None
                await self.asave(update_fields=['completed', 'start_time'])
                self.player.points += 1000
                await self.player.asave(update_fields=['points'])

    async def start_task_player(self):
        """При вызове представления, задаём полю значение начало выполнение задачи"""
        self.start_time = timezone.now()
        await self.asave(update_fields=['start_time'])

