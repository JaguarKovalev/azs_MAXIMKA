from django.contrib import admin
from django.urls import path
from django import forms
from django.db import connection
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Company, Customer, Fuel, FuelType, GasStation, Order, Sale


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "telephone")
    search_fields = ("name", "address", "telephone")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "telephone",
        "address",
        "card_number",
        "transport_number",
    )
    search_fields = ("full_name", "telephone", "card_number", "transport_number")


@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ("type", "unit")
    search_fields = ("type",)


@admin.register(GasStation)
class GasStationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "company")
    search_fields = ("name", "address")
    list_filter = ("company",)


@admin.register(Fuel)
class FuelAdmin(admin.ModelAdmin):
    list_display = (
        "gas_station",
        "fuel_type",
        "current_quantity",
        "price",
        "capacity",
        "minimum_balance",
    )
    search_fields = ("gas_station__name", "fuel_type__type")
    list_filter = ("gas_station", "fuel_type")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "fuel", "quantity", "status")
    actions = ["mark_as_completed"]

    def mark_as_completed(self, request, queryset):
        for order in queryset:
            if order.status != "completed":
                order.fuel.current_quantity += order.quantity

                if order.fuel.current_quantity > order.fuel.capacity:
                    order.fuel.current_quantity = order.fuel.capacity

                order.fuel.save()
                order.status = "completed"
                order.save()

        self.message_user(
            request,
            "Выбранные заказы были помечены как выполненные и топливо добавлено на АЗС.",
        )

    mark_as_completed.short_description = (
        "Пометить как выполненные и добавить топливо на АЗС"
    )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("date", "customer", "fuel", "fuel_quantity", "current_price")
    search_fields = ("customer__full_name", "fuel__fuel_type__type")
    list_filter = ("fuel__fuel_type", "fuel__gas_station")
