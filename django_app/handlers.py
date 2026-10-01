from business_logic.service_layer.services import PlaceOrder
from django_app.django_uow import DjangoUnitOfWork
from django_app.services import DjangoUniqueIdGenerator
from django_app.models import OrderModel


def handler_one(person_id):
    with DjangoUnitOfWork() as uow:
        order = PlaceOrder(
            person_id,
            uow.person_repo,
            uow.cart_repo,
            uow.order_repo,
            uow.inventory_item_repo,
            DjangoUniqueIdGenerator(OrderModel)
        )
        order.place_order()
        uow.commit()