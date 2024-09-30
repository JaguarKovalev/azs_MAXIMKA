from django.utils import timezone
from django.db import models, transaction
from django.core.exceptions import ValidationError


class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    telephone = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Customer(models.Model):
    full_name = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15)
    address = models.CharField(max_length=200)
    card_number = models.CharField(max_length=16)
    transport_number = models.CharField(max_length=9)

    def __str__(self):
        return self.full_name


class FuelType(models.Model):
    type = models.CharField(max_length=50)
    unit = models.CharField(max_length=10)

    def __str__(self):
        return self.type


class GasStation(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Fuel(models.Model):
    gas_station = models.ForeignKey(GasStation, on_delete=models.CASCADE)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.CASCADE)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.fuel_type} at {self.gas_station}"


class Order(models.Model):
    date = models.DateField()
    fuel = models.ForeignKey(Fuel, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10)

    def __str__(self):
        return f"Order {self.id}"


class Sale(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    fuel = models.ForeignKey(Fuel, on_delete=models.CASCADE)
    fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        # Проверка, чтобы после продажи количество топлива не стало меньше нуля
        if self.pk:
            original_sale = Sale.objects.get(pk=self.pk)
            quantity_difference = self.fuel_quantity - original_sale.fuel_quantity
            new_quantity = self.fuel.current_quantity - quantity_difference
        else:
            new_quantity = self.fuel.current_quantity - self.fuel_quantity

        if new_quantity < 0:
            raise ValidationError(
                "Продажа невозможна, так как она приведет к отрицательному количеству топлива."
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.clean()  # Проверка перед сохранением

            if self.pk:
                original_sale = Sale.objects.get(pk=self.pk)
                quantity_difference = self.fuel_quantity - original_sale.fuel_quantity
                self.fuel.current_quantity -= quantity_difference
            else:
                self.fuel.current_quantity -= self.fuel_quantity

            self.fuel.save()
            super(Sale, self).save(*args, **kwargs)

            if self.fuel.current_quantity < self.fuel.minimum_balance:
                self.create_order_to_refill()

    def create_order_to_refill(self):
        existing_order = Order.objects.filter(
            fuel=self.fuel, status__in=["pending", "in_progress"]
        ).exists()

        if not existing_order:
            required_quantity = self.fuel.capacity - self.fuel.current_quantity
            Order.objects.create(
                date=timezone.now(),
                fuel=self.fuel,
                quantity=required_quantity,
                status="pending",
            )

    def __str__(self):
        return f"Sale {self.id} by {self.customer}"
