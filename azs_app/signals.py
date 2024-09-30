from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fuel, Order
from django.utils import timezone

@receiver(post_save, sender=Fuel)
def check_fuel_balance(sender, instance, **kwargs):
    # Проверка, нужно ли создавать новый заказ
    if instance.current_quantity < instance.minimum_balance:
        # Проверяем, есть ли уже незавершенные заказы на это топливо
        existing_orders = Order.objects.filter(fuel=instance, status='pending')
        if not existing_orders.exists():
            # Рассчитываем необходимое количество для заказа
            order_quantity = instance.capacity - instance.current_quantity
            Order.objects.create(
                date=timezone.now(),  # Используем текущее время для создания нового заказа
                fuel=instance,
                quantity=order_quantity,
                status='pending',
            )
