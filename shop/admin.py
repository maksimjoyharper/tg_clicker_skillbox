from django.contrib import admin
from shop.models import PlayerProduct, Product, Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели Shop."""
    list_display = ['id', 'name', 'description', 'picture']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели Product."""
    list_display = ['id', 'shop', 'name', 'description', 'price', 'is_active']


@admin.register(PlayerProduct)
class PlayerProductAdmin(admin.ModelAdmin):
    """Регистрация в админ панели модели PlayerProduct."""
    list_display = ['id', 'player', 'product', 'purchased_at', 'is_accessible']

