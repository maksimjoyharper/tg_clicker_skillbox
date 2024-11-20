import logging
from asgiref.sync import sync_to_async, async_to_sync
from django.core.cache import cache
from django.db.models import Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema_view, extend_schema
from rest_framework import status
from rest_framework.response import Response
from app_core.models import Player, ReferralSystem, League, PlayerTask
from app_core.serializers import PlayerSerializer, PlayerTaskSerializer
from django.shortcuts import get_object_or_404
from adrf.viewsets import GenericAPIView


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
    - `referral_id`: Id-друга который пригласил. (Не обязательный аргумент)
    Возвращает:
    - Информацию о пользователе.
    """
    serializer_class = PlayerSerializer

    async def update_player_status(self, player):
        """Функция для обновления ежедневного бонуса и получение бонусов от друзей 10%"""
        if player.daily_bonus_friends != 0:
            player.points += player.daily_bonus_friends
            player.daily_bonus_friends = 0
        elif player.is_new:
            player.is_new = False
        # Обновляем ежедневный статус
        await player.update_daily_status()
        await player.asave()
        serializer = self.get_serializer(player)
        return await serializer.adata

    async def get(self, request, tg_id: int, name: str, referral_id: int = None):
        # Пытаемся получить игрока или создаем нового
        defaults = {"name": name, "is_new": True}
        # Устанавливаем дефолтную лигу
        default_league = await League.objects.afirst()
        if default_league:
            defaults["league"] = default_league
        player, created = await Player.objects.aget_or_create(tg_id=tg_id, defaults=defaults)
        # Если игрок только что создан, проверяем реферальную систему
        if created:
            players_count = await Player.objects.acount()  # Получаем общее количество игроков
            player.rank = players_count  # Новый игрок всегда в конце списка
            if referral_id and referral_id != tg_id:
                referral = await sync_to_async(get_object_or_404)(Player, tg_id=referral_id)
                # Проверяем, что реферальная связь ещё не существует
                exists = await ReferralSystem.objects.filter(referral=referral, new_player=player).aexists()
                if not exists:
                    await ReferralSystem.objects.acreate(referral=referral, new_player=player)
                else:
                    response_data = await self.update_player_status(player)
                    response_data["Error"] = "Игрок уже в друзьях у реферала."
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            elif referral_id == tg_id:
                response_data = await self.update_player_status(player)
                response_data["Error"] = "Нельзя добавить самого себя в друзья!."
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        # Обновляем ежедневный статус и возвращаем данные игрока
        response_data = await self.update_player_status(player)
        return Response(response_data, status=status.HTTP_200_OK)


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
            friends_data = [{'tg_id': friend.new_player.tg_id, 'name': friend.new_player.name,
                            'referral_bonus': friend.referral_bonus, 'points': friend.new_player.points}
                            for friend in friends]
            return Response(friends_data, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({"error": "Игрок не найден."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    post=extend_schema(
        tags=["Игрок: бонусы"],
        summary="Получить бонус за друга",
        description=(
            "Позволяет игроку получить бонус за привлечение нового игрока. "
            "Если реферальная связь существует и бонус не был получен ранее, "
            "игрок получает бонус и обновляется количество его билетов."
        ),
        parameters=[
            OpenApiParameter(name="tg_id", type=int, description="ID игрока, который привлекает друга (Telegram)."),
            OpenApiParameter(name="new_player_id", type=int, description="ID нового игрока, которого пригласил реферал.")
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: {"description": "Реферальная связь не найдена или бонус уже получен."},
            404: {"description": "Игрок не найден."}
        }
    )
)
class FriendBonusView(GenericAPIView):
    """
    Эндпоинт для получения бонуса за друга.
    Принимает POST-запрос с идентификатором пользователя (tg_id) и идентификатором нового игрока (new_player_id).
    Параметры:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    - `new_player_id`: Уникальный идентификатор нового игрока, за которого начисляется бонус.
    Возвращает:
    - Сообщение о получении бонуса и общее количество билетов.
    - Статус 400, если реферальная связь не найдена или бонус уже получен.
    - Статус 404, если игрок не найден.
    """

    async def post(self, request, tg_id: int, new_player_id: int):
        try:
            # Ищем игрока и его реферальную связь
            referral_relation = await ReferralSystem.objects.select_related('referral', 'new_player').filter(
                referral__tg_id=tg_id, new_player__tg_id=new_player_id).afirst()
            if not referral_relation:
                return Response({"message": "Реферальная связь не найдена."}, status=status.HTTP_400_BAD_REQUEST)
            # Проверка бонуса
            elif not referral_relation.referral_bonus:
                return Response({"message": "Бонус за этого друга уже получен."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Обновляем данные
            referral_relation.referral.tickets += 1
            referral_relation.referral.tickets_all += 1
            await referral_relation.referral.asave(update_fields=["tickets", "tickets_all"])
            referral_relation.referral_bonus = False
            await referral_relation.asave(update_fields=["referral_bonus"])
            return Response({"message": f"Вы получили 1 бонусный билет за друга {referral_relation.new_player.name}!",
                            "total_tickets": referral_relation.referral.tickets}, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({"error": "Игрок не найден."}, status=status.HTTP_404_NOT_FOUND)


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
    """
    Эндпоинт для информации о задачах игрока.
    Принимает GET-запрос с идентификатором пользователя (tg_id) и необязательным параметром dop_name.
    Принимает POST-запрос с идентификатором пользователя (tg_id) и dop_name.
    Параметры:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    - `dop_name`: Дополнительное имя задачи (необязательный параметр).
    Возвращает:
    - Информацию о задачах игрока.
    - Статус 404, если игрок или задачи не найдены.
    - Статус 400, если данные невалидны.
    """
    serializer_class = PlayerTaskSerializer

    async def get(self, request, tg_id, dop_name=None):
        try:
            # Используем prefetch_related для загрузки задач игрока и связанных Task
            player = await (Player.objects.prefetch_related
                            (Prefetch('task_player', queryset=PlayerTask.objects.select_related('task')
                                      .order_by('completed', 'id'))).aget(tg_id=tg_id))
        except Player.DoesNotExist:
            return Response({"detail": "Игрок не найден"}, status=status.HTTP_404_NOT_FOUND)
        # Фильтруем задачи, если передан dop_name
        task_players = player.task_player.all()  # Получаем связанные PlayerTask
        if dop_name:
            task_players = [tp for tp in task_players if tp.task.dop_name == dop_name]
        if not task_players:
            return Response({"detail": "Задачи не найдены"}, status=status.HTTP_404_NOT_FOUND)
        # Сериализуем данные
        serializer = self.get_serializer(task_players, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, tg_id, dop_name):
        if tg_id and dop_name:
            player = await (Player.objects.prefetch_related
                            (Prefetch('task_player', queryset=PlayerTask.objects.select_related('task')))
                            .aget(tg_id=tg_id))
            tasks = player.task_player.filter(task__dop_name=dop_name)
            # Преобразуем QuerySet в список перед проверкой
            tasks_list = await sync_to_async(list)(tasks)
            # Проверяем, что задача существует
            if not tasks_list:
                return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
            task = tasks_list[0]
            serializer = self.get_serializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                await serializer.asave()
                await task.check_completion()
                return Response(await serializer.adata, status=status.HTTP_200_OK)
            return Response(await serializer.aerrors, status=status.HTTP_400_BAD_REQUEST)
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
    """
    Эндпоинт для запуска таймера задачи после перехода на ссылку.
    Принимает POST-запрос с идентификатором пользователя (tg_id) и dop_name.
    Параметры:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    - `dop_name`: Дополнительное имя задачи.
    Возвращает:
    - Информацию о задаче.
    - Статус 404, если задача не найдена.
    - Статус 400, если задача уже завершена или данные невалидны.
    """
    serializer_class = PlayerTaskSerializer

    async def post(self, request, tg_id, dop_name):
        player = await (Player.objects.prefetch_related
                        (Prefetch('task_player', queryset=PlayerTask.objects.select_related('task')))
                        .aget(tg_id=tg_id))
        tasks = player.task_player.filter(task__dop_name=dop_name)
        # Преобразуем QuerySet в список перед проверкой
        tasks_list = await sync_to_async(list)(tasks)
        # Проверяем, что задача существует
        if not tasks_list:
            return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
        task = tasks_list[0]
        if task.completed:
            return Response({"error": "Задача уже завершена."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            await serializer.asave()
            await task.start_task_player()
            return Response(await serializer.adata, status=status.HTTP_200_OK)
        return Response(await serializer.aerrors, status=status.HTTP_400_BAD_REQUEST)


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
    """
    Эндпоинт для получения топ-100 игроков и ранга текущего игрока.
    Принимает GET-запрос с идентификатором пользователя (tg_id).
    Параметры:
    - `tg_id`: Уникальный идентификатор пользователя в Telegram.
    Возвращает:
    - Топ-100 игроков и ранг текущего игрока.
    - Статус 500, если возникла ошибка при работе с Redis или базой данных.
    """
    async def get(self, request, tg_id):
        person = await Player.objects.aget(tg_id=tg_id)
        top_players = cache.get("monthly_top_100")
        if not top_players:
            # Если кэша нет, загружаем топ-100 из базы и кэшируем
            top_players_queryset = await sync_to_async(
                lambda: Player.objects.order_by('-points').values("tg_id", "name", "points", "rank")[:100])()
            top_players = list(top_players_queryset)
            await sync_to_async(cache.set)("monthly_top_100", top_players)
        return Response({'top_players': top_players, 'player_rank': person.rank})

