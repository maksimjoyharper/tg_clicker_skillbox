# from django.db.models.signals import post_save
# from async_signals import receiver
# from .models import *
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# @receiver(post_save, sender=Player)
# async def assign_existing_tasks_to_player(sender, instance, created, **kwargs):
#     """Асинхронно присваиваем все существующие задачи игроку при создании нового игрока."""
#     if created:
#         tasks = [task async for task in Task.objects.all()]
#         await PlayerTask.objects.bulk_create([PlayerTask(person=instance, task=task) for task in tasks])
#
#
# @receiver(post_save, sender=Task)
# async def assign_task_to_all_players(sender, instance, created, **kwargs):
#     """Асинхронно присваиваем новую задачу всем существующим игрокам."""
#     if created:
#         players = [player async for player in Player.objects.all()]
#         await PlayerTask.objects.bulk_create([PlayerTask(person=player, task=instance) for player in players])
