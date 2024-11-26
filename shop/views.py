from django.db.models import Prefetch
from adrf.viewsets import GenericAPIView
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from app_core.models import Player
from shop.models import Product, PlayerProduct
from rest_framework.response import Response


@extend_schema_view(
    get=extend_schema(
        tags=["Продукты"],
        summary="Получить список продуктов игрока",
        description=(
            "Возвращает список всех доступных продуктов для покупки, включая информацию о "
            "том, были ли они приобретены игроком и доступны ли для использования. "
            "Игрок идентифицируется по его tg_id."
        ),
        parameters=[
            OpenApiParameter(
                name="tg_id",
                type=int,
                description="Уникальный идентификатор игрока в Telegram",
                required=True
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: {"description": "Игрок не найден"}
        }
    ),
    post=extend_schema(
        tags=["Продукты"],
        summary="Купить продукт для игрока",
        description=(
            "Покупает указанный продукт для игрока, если у него достаточно баллов. "
            "Продукт идентифицируется по ID, переданному в теле запроса. "
            "Игрок идентифицируется по его tg_id."
        ),
        parameters=[
            OpenApiParameter(
                name="tg_id",
                type=int,
                description="Уникальный идентификатор игрока в Telegram",
                required=True
            )
        ],
        request={
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID продукта, который нужно купить",
                    "example": 1
                }
            },
            "required": ["product_id"]
        },
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "product": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "price": {"type": "number"},
                            "shop": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"}
                                }
                            },
                            "is_accessible": {"type": "boolean"}
                        }
                    },
                    "remaining_points": {"type": "number"}
                }
            },
            400: {"description": "Недостаточно баллов для покупки"},
            404: {"description": "Игрок или продукт не найдены"}
        }
    )
)
class ProductListView(GenericAPIView):
    """
    Эндпоинт для получения списка продуктов и покупки продуктов для игрока.
    GET:
    - Возвращает список всех активных продуктов, включая статус покупки и доступности для игрока.
    POST:
    - Позволяет игроку приобрести продукт, если у него достаточно баллов.
    Параметры:
    - `tg_id`: Уникальный идентификатор игрока в Telegram (передается в URL).
    - `product_id`: ID продукта, который нужно купить (передается в теле POST-запроса).
    Возвращает:
    - Список продуктов (GET).
    - Информацию о купленном продукте и оставшихся баллах игрока (POST).
    - Сообщение об ошибке, если данные неверные или объект не найден.
    """

    async def get(self, request, tg_id):
        try:
            player = await Player.objects.prefetch_related(
                Prefetch('purchases', queryset=PlayerProduct.objects.select_related('product', 'product__shop'))
            ).aget(tg_id=tg_id)
        except Player.DoesNotExist:
            return Response({"error": "Игрок не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Получаем все активные продукты
        products = Product.objects.filter(is_active=True).order_by('id').select_related('shop').aiterator()
        products = [product async for product in products]
        # Собираем список продуктов игрока
        player_products = {pp.product.id: pp for pp in player.purchases.all()}

        response_data = []
        for product in products:
            response_data.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "shop": {
                    "id": product.shop.id,
                    "name": product.shop.name
                },
                "is_purchased": player_products.get(product.id,
                                                    None).purchased_at if product.id in player_products else False,
                "is_accessible": player_products.get(product.id,
                                                     None).is_accessible if product.id in player_products else False
            })

        return Response({"products": response_data}, status=status.HTTP_200_OK)

    async def post(self, request, tg_id):
        product_id = request.data.get('product_id')
        try:
            player = await Player.objects.aget(tg_id=tg_id)
        except Player.DoesNotExist:
            return Response({"error": "Игрок не найден"}, status=status.HTTP_404_NOT_FOUND)
        try:
            product = await Product.objects.select_related('shop').aget(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Продукт не найден или не активен"}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, достаточно ли баллов у игрока для покупки
        if player.points < product.price:
            return Response({"error": "Недостаточно баллов для покупки"}, status=status.HTTP_400_BAD_REQUEST)

        # Уменьшаем количество баллов игрока на цену продукта
        player.points -= product.price
        await player.asave()

        # Создаем запись о покупке продукта для игрока
        player_product = await PlayerProduct.objects.acreate(
            player=player,
            product=product,
            purchased_at=timezone.now(),
            is_accessible=True
        )

        return Response({
            "message": "Продукт успешно куплен",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "shop": {
                    "id": product.shop.id,
                    "name": product.shop.name
                },
                "is_accessible": player_product.is_accessible
            },
            "remaining_points": player.points
        }, status=status.HTTP_201_CREATED)
