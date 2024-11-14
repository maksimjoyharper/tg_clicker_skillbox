from celery import shared_task
from .models import Player
from django.core.cache import cache


@shared_task(acks_late=True, reject_on_worker_lost=True)
async def calculate_daily_referral_bonus():
    """Задача для вычисления суточного бонуса за рефералов + изменение полей."""
    all_players = await Player.objects.prefetch_related('referral__new_player').all()
    players_to_update = []
    async for player in all_players:
        # Рассчитываем бонус для каждого игрока
        total_bonus = sum(ref.new_player.daily_points * 0.1 for ref in player.referral.all())
        player.daily_bonus_friends = int(total_bonus)
        players_to_update.append(player)
    # Массовое обновление daily_bonus_friends у всех игроков
    await Player.objects.abulk_update(players_to_update, fields=['daily_bonus_friends'])
    # Обнуление поля daily_points у всех игроков
    await Player.objects.aupdate(daily_points=0)


@shared_task(acks_late=True, reject_on_worker_lost=True)
async def update_monthly_ranking():
    """Формируем топ 100 игроков и обновляем ранг каждого"""
    # Получаем всех игроков асинхронно, сортируем по баллам
    players = await Player.objects.order_by('-points').all()
    updated_players = []
    rank = 1
    async for player in players:
        player.rank = rank
        updated_players.append(player)
        rank += 1
    # Асинхронно обновляем ранги в базе данных одним запросом
    await Player.objects.abulk_update(updated_players, ['rank'])
    # Кешируем топ-100 игроков асинхронно
    top_100_players = updated_players[:100]
    await cache.aset(
        "monthly_top_100",
        [{"tg_id": player.tg_id, "name": player.name, "points": player.points, "rank": player.rank} for player in top_100_players],
    )
