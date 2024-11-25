from django.urls import path
from .views import *


app_name = "shop"

urlpatterns = [
    path('product-list/<int:tg_id>/', ProductListView.as_view(), name='product_list'),

]

