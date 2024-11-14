import logging
from asgiref.sync import sync_to_async
from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema_view, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from app_core.models import Player, ReferralSystem
from app_core.serializers import PlayerSerializer, PlayerTaskSerializer
from django.shortcuts import get_object_or_404


@extend_schema_view(
    get=extend_schema(
        tags=["Игрок: информация о пользователе"],
        summary="Получить или создать пользователя",
        description="Получает или создает пользователя по уникальному идентификатору в Telegram и имени пользователя.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram"),
            OpenApiParameter(name="name", type=str, description="Имя пользователя"),
            OpenApiParameter(name="referral_id", type=int, description="Идентификатор реферала (опционально)", required=False)
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: {"description": "Неверные данные"},
            404: {"description": "Реферал не найден"}
        }
    )
)
class PlayerInfo(GenericAPIView):
    """
    Представление для входа/создания пользователя.
    Принимает GET-запрос с идентификатором пользователя (tg_id) и именем пользователя (name).
    Необходимые переменные для корректной работы:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    - `name`: Имя пользователя.
    Возвращает:
    - Информацию о пользователе.
    """
    serializer_class = PlayerSerializer

    async def get(self, request, tg_id: int, name: str, referral_id: int = None):
        # Пытаемся получить игрока или создаем нового
        player, created = await Player.objects.aget_or_create(tg_id=tg_id, defaults={"name": name, "is_new": True})
        # Если игрок только что создан, проверяем реферальную систему
        if created:
            players_count = await Player.objects.аcount()  # Получаем общее количество игроков
            player.rank = players_count + 1  # Новый игрок всегда в конце списка
            if referral_id and referral_id != tg_id:
                referral = await sync_to_async(get_object_or_404)(Player, tg_id=referral_id)
                # Проверяем, что реферальная связь ещё не существует
                exists = await ReferralSystem.objects.filter(referral=referral, new_player=player).aexists()
                if not exists:
                    await ReferralSystem.objects.acreate(referral=referral, new_player=player)
                else:
                    return Response({"Error": "Игрок уже в друзьях у реферала."}, status=status.HTTP_400_BAD_REQUEST)
            elif referral_id == tg_id:
                return Response({"Error": "Нельзя добавить самого себя в друзья!"}, status=status.HTTP_400_BAD_REQUEST)
            # Помечаем игрока как не нового
            player.is_new = False
        if player.daily_bonus_friends != 0:
            player.points += player.daily_bonus_friends
            player.daily_bonus_friends = 0
        # Обновляем ежедневный статус и возвращаем данные игрока
        await player.update_daily_status()
        await player.asave()
        serializer = self.get_serializer(player)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Игрок: друзья"],
        summary="Получить список друзей игрока",
        description="Возвращает список друзей игрока по уникальному идентификатору в Telegram.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram")
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: {"description": "Игрок не найден"}
        }
    )
)
class PlayerFriendsView(GenericAPIView):
    """
    Представление для получения списка друзей игрока.
    Принимает GET-запрос с идентификатором пользователя (tg_id).
    Необходимые переменные для корректной работы:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    Возвращает:
    - Список друзей игрока.
    """
    async def get(self, request, tg_id: int):
        try:
            # Получаем игрока и всех его друзей в одном запросе
            player = await Player.objects.prefetch_related('referral__new_player').aget(tg_id=tg_id)
            # Получаем список друзей
            friends = player.referral.all()  # Получаем все объекты ReferralSystem, связанные с игроком
            # Сериализуем друзей
            friends_data = [{'tg_id': friend.new_player.tg_id, 'name': friend.new_player.name} for friend in friends]
            return Response(friends_data, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({"error": "Игрок не найден."}, status=status.HTTP_404_NOT_FOUND)


# class TakinReferralBonus(GenericAPIView):
#     def post(self, request):
#         person = get_object_or_404(Player, tg_id=request.data['tg_id'])
#         system = get_object_or_404(ReferralSystem, id=request.data['referral_system_id'])
#         if system.referral.lvl < 2 and system.new_player.lvl < 2:
#             return Response({
#                 'Error': 'Оба игрока должны достичь уровня выше 2 для получения бонуса.',
#                 'referral_lvl': system.referral.lvl,
#                 'new_player_lvl': system.new_player.lvl
#             }, status=status.HTTP_400_BAD_REQUEST)
#         if system.referral == person and system.referral_bonus == True:
#             system.referral_bonus = False
#             system.save()
#             person.crystal += 50
#             person.save()
#             return Response({
#                 'referral': 'Получил 50 кристаллов'})
#         if system.new_player == person and system.new_player_bonus == True:
#             system.new_player_bonus = False
#             system.save()
#             system.new_player.crystal += 10
#             system.new_player.save()
#             return Response({
#                 'new_player': 'Получил 10 кристаллов'})
#         else:
#             return Response({'Error': "Вы уже получали бонус"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        tags=["Игрок: реферальная ссылка"],
        summary="Сгенерировать реферальную ссылку",
        description="Генерирует реферальную ссылку для игрока по уникальному идентификатору в Telegram.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram")
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            500: {"description": "Ошибка при генерации ссылки"}
        }
    )
)
class GenerateRefLinkView(GenericAPIView):
    """
    Эндпоинт для генерации реферальной ссылки.
    Принимает GET-запрос с идентификатором пользователя (tg_id).
    Необходимые переменные для корректной работы:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    Возвращает:
    - Реферальную ссылку игрока.
    """
    async def get(self, request, tg_id: int):
        try:
            create_link = f"https://t.me/skillbox_app_bot?start=id_{tg_id}"
        except Exception as e:
            logging.error(f"Error generating referral link: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'ref_link': create_link}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Игрок: задачи"],
        summary="Получить информацию о задачах игрока",
        description="Возвращает информацию о задачах и их статусе у игрока по уникальному идентификатору в Telegram.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram"),
            OpenApiParameter(name="dop_name", type=str, description="Дополнительное имя задачи (опционально)", required=False)
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: {"description": "Задачи не найдены"}
        }
    ),
    post=extend_schema(
        tags=["Игрок: задачи"],
        summary="Обновить статус задачи игрока",
        description="Обновляет статус задачи игрока по уникальному идентификатору в Telegram и дополнительному имени задачи.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram"),
            OpenApiParameter(name="dop_name", type=str, description="Дополнительное имя задачи")
        ],
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: {"description": "Неверные данные"},
            404: {"description": "Задача не найдена"}
        }
    )
)
class TaskPlayerDetailView(GenericAPIView):
    """Информация о задачах и их статусе у игрока."""
    serializer_class = PlayerTaskSerializer

    async def get(self, request, tg_id, dop_name=None):
        # Ищем игрока асинхронно и подгружаем связанные задачи
        person = await Player.objects.prefetch_related('task_player__task').aget(tg_id=tg_id)
        # Фильтруем задачи для игрока, при необходимости применяя доп. фильтр
        if dop_name:
            tasks = person.task_player.filter(task__dop_name=dop_name)
        else:
            tasks = person.task_player.all().order_by('completed', 'id')
        # Если задач нет, возвращаем ошибку
        if not tasks:
            return Response({"detail": "Задачи не найдены"}, status=status.HTTP_404_NOT_FOUND)
        # Сериализуем данные
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, tg_id, dop_name):
        if tg_id and dop_name:
            person = await Player.objects.prefetch_related('task_player__task').aget(tg_id=tg_id)
            tasks = person.task_player.filter(task__dop_name=dop_name)
            # Проверяем, что задача существует
            if not tasks:
                return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
            task = tasks.afirst()
            serializer = self.get_serializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                await serializer.asave()
                await task.check_completion()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'tg_id и dop_name обязательные поля'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        tags=["Игрок: задачи"],
        summary="Запустить таймер задачи",
        description="Запускает таймер задачи после перехода на ссылку по уникальному идентификатору в Telegram и "
                    "дополнительному имени задачи.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram"),
            OpenApiParameter(name="dop_name", type=str, description="Дополнительное имя задачи")
        ],
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: {"description": "Неверные данные"},
            404: {"description": "Задача не найдена"}
        }
    )
)
class StartTaskView(GenericAPIView):
    """Запуск таймера задачи после перехода на ссылку."""
    serializer_class = PlayerTaskSerializer

    async def post(self, request, tg_id, dop_name):
        person = await Player.objects.prefetch_related('task_player__task').aget(tg_id=tg_id)
        tasks = person.task_player.filter(task__dop_name=dop_name)
        # Проверка, если задача уже завершена
        if not tasks:
            return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
        task = tasks.afirst()
        if task.completed:
            return Response({"error": "Задача уже завершена."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            await serializer.asave()
            await task.start_task_player()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        tags=["Игрок: топ-игроки"],
        summary="Получить информацию о топ-игроках и ранге игрока",
        description="Возвращает информацию о топ-100 игроках и ранге текущего игрока по уникальному идентификатору в Telegram.",
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="Уникальный идентификатор пользователя в Telegram", required=True)
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: {"description": "Игрок не найден"}
        }
    )
)
class MonthlyTopPlayersView(GenericAPIView):
    """Топ 100 игроков + ранг текущего игрока"""
    async def get(self, request, tg_id):
        person = await Player.objects.aget(tg_id=tg_id)
        top_players = cache.get("monthly_top_100")
        if not top_players:
            # Если кэша нет, загружаем топ-100 из базы и кэшируем
            top_players_queryset = await Player.objects.order_by('-points').values("tg_id", "name", "points", "rank")[:100]
            top_players = list(top_players_queryset)
            await sync_to_async(cache.set)("monthly_top_100", top_players)
        return Response({'top_players': top_players, 'player_rank': person.rank})

