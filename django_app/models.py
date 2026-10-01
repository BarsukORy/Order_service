from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django_app.services import DjangoUniqueIdGenerator


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.domain_id = DjangoUniqueIdGenerator(self.model).generate_id()
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')
        return self.create_user(email, password, **extra_fields)


class PersonModel(AbstractUser):

    username = None

    domain_id = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class ProductModel(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


class CartModel(models.Model):
    person = models.OneToOneField(PersonModel, on_delete=models.CASCADE)


class CartLineModel(models.Model):
    cart = models.ForeignKey(CartModel, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.IntegerField()


class OrderModel(models.Model):
    domain_id = models.CharField(max_length=255, unique=True)
    person = models.ForeignKey(PersonModel, on_delete=models.CASCADE)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)


class OrderLineModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE)
    product_sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=50)
    quantity = models.IntegerField()
    line_price = models.DecimalField(max_digits=10, decimal_places=2)


class InventoryItemModel(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.IntegerField()