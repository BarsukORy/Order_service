from django.contrib import admin
from django_app.models import (PersonModel,
                               ProductModel,
                               CartLineModel,
                               CartModel,
                               OrderLineModel,
                               OrderModel,
                               InventoryItemModel)


@admin.register(PersonModel)
class PersonModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    pass


@admin.register(InventoryItemModel)
class InventoryItemModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CartLineModel)
class CartLineModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CartModel)
class CartModelAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderLineModel)
class OrderLineModelAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderModel)
class OrderModelAdmin(admin.ModelAdmin):
    pass