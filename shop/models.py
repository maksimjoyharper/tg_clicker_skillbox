from django.db import models
from app_core.models import Player


class Shop(models.Model):
    """Модель магазина"""
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(null=True, blank=True, verbose_name="Описание товара")
    picture = models.ImageField(null=True, blank=True, verbose_name='Картинка')

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель продукта в магазине"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products", verbose_name="Магазин")
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(null=True, blank=True, verbose_name="Описание товара")
    price = models.PositiveIntegerField(default=1000, verbose_name="Цена в очках")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Продукт в магазине"
        verbose_name_plural = "Продукты в магазине"

    def __str__(self):
        return self.name


class PlayerProduct(models.Model):
    """Модель продукта у игрока"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="purchases", verbose_name="Покупатель")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    purchased_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата покупки")
    is_accessible = models.BooleanField(default=True, verbose_name="Доступен ли продукт")

    class Meta:
        verbose_name = "Продукт игрока"
        verbose_name_plural = "Продукты игрока"

    def __str__(self):
        return self.player.name


