from django.shortcuts import render
from django.apps import apps
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek, TruncHour
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import connection, transaction
from .forms import StatisticsForm, SQLQueryForm
from datetime import datetime, timedelta
import plotly.express as px
from plotly.offline import plot
from django.shortcuts import render
from django.apps import apps
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from .forms import StatisticsForm
from datetime import datetime, timedelta
import plotly.express as px
from plotly.offline import plot
from django.shortcuts import render
from django.apps import apps
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .forms import StatisticsForm
from datetime import datetime, timedelta
import plotly.express as px
from plotly.offline import plot
from time import sleep


def tables_view(request):
    Company = apps.get_model("azs_app", "Company")
    Customer = apps.get_model("azs_app", "Customer")
    Fuel = apps.get_model("azs_app", "Fuel")
    FuelType = apps.get_model("azs_app", "FuelType")
    GasStation = apps.get_model("azs_app", "GasStation")
    Order = apps.get_model("azs_app", "Order")
    Sale = apps.get_model("azs_app", "Sale")

    companies = Company.objects.all()
    customers = Customer.objects.all()
    fuels = Fuel.objects.all()
    fuel_types = FuelType.objects.all()
    gas_stations = GasStation.objects.all()
    orders = Order.objects.all()
    sales = Sale.objects.all()

    context = {
        "companies": companies,
        "customers": customers,
        "fuels": fuels,
        "fuel_types": fuel_types,
        "gas_stations": gas_stations,
        "orders": orders,
        "sales": sales,
    }
    return render(request, "azs_app/tables_view.html", context)


def statistics_view(request):
    Sale = apps.get_model("azs_app", "Sale")
    FuelType = apps.get_model("azs_app", "FuelType")
    GasStation = apps.get_model("azs_app", "GasStation")
    Company = apps.get_model("azs_app", "Company")
    Customer = apps.get_model("azs_app", "Customer")

    form = StatisticsForm(request.GET or None)
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    selected_fuel_type = None
    selected_customer = None

    # Обрабатываем форму
    if form.is_valid():
        start_date = form.cleaned_data.get("start_date", start_date)
        end_date = form.cleaned_data.get("end_date", end_date)
        selected_fuel_type = form.cleaned_data.get("fuel_type")
        selected_customer = form.cleaned_data.get("customer")

    # Фильтруем данные
    sales_query = Sale.objects.filter(date__range=[start_date, end_date])

    if selected_fuel_type:
        sales_query = sales_query.filter(fuel__fuel_type=selected_fuel_type)

    if selected_customer:
        sales_query = sales_query.filter(customer=selected_customer)

    # Готовим данные для графиков, если есть продажи
    sales_over_time_plot = fuel_sales_by_type_plot = sales_by_station_plot = revenue_by_fuel_type_plot = top_customers_by_volume_plot = None

    if sales_query.exists():
        # 1. Количество продаж по месяцам
        sales_over_time = (
            sales_query.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        sales_over_time_fig = px.bar(
            x=[s["month"] for s in sales_over_time],
            y=[s["total"] for s in sales_over_time],
            labels={"x": "Месяц", "y": "Количество продаж"},
            title="Количество продаж по месяцам",
        )
        sales_over_time_plot = plot(sales_over_time_fig, output_type="div")

        # 2. Объем продаж по видам топлива
        fuel_sales_by_type = (
            sales_query.values("fuel__fuel_type__type")
            .annotate(total_sold=Sum("fuel_quantity"))
            .order_by("-total_sold")
        )
        fuel_sales_by_type_fig = px.pie(
            names=[f["fuel__fuel_type__type"] for f in fuel_sales_by_type],
            values=[f["total_sold"] for f in fuel_sales_by_type],
            title="Объем продаж по видам топлива",
        )
        fuel_sales_by_type_plot = plot(fuel_sales_by_type_fig, output_type="div")

        # 3. Объем продаж по заправочным станциям
        sales_by_station = (
            sales_query.values("fuel__gas_station__name")
            .annotate(total_sold=Sum("fuel_quantity"))
            .order_by("-total_sold")
        )
        sales_by_station_fig = px.bar(
            x=[s["fuel__gas_station__name"] for s in sales_by_station],
            y=[s["total_sold"] for s in sales_by_station],
            labels={"x": "Заправочная станция", "y": "Объем продаж"},
            title="Объем продаж по заправочным станциям",
        )
        sales_by_station_plot = plot(sales_by_station_fig, output_type="div")

        # 4. Суммарная выручка по видам топлива
        revenue_by_fuel_type = (
            sales_query.values("fuel__fuel_type__type")
            .annotate(total_revenue=Sum("fuel_quantity") * Avg("current_price"))
            .order_by("-total_revenue")
        )
        revenue_by_fuel_type_fig = px.bar(
            x=[f["fuel__fuel_type__type"] for f in revenue_by_fuel_type],
            y=[f["total_revenue"] for f in revenue_by_fuel_type],
            labels={"x": "Тип топлива", "y": "Выручка"},
            title="Суммарная выручка по видам топлива",
        )
        revenue_by_fuel_type_plot = plot(revenue_by_fuel_type_fig, output_type="div")

        # 5. Топ-5 клиентов по объему покупок
        top_customers_by_volume = (
            sales_query.values("customer__full_name")
            .annotate(total_volume=Sum("fuel_quantity"))
            .order_by("-total_volume")[:5]
        )
        top_customers_by_volume_fig = px.bar(
            x=[c["customer__full_name"] for c in top_customers_by_volume],
            y=[c["total_volume"] for c in top_customers_by_volume],
            labels={"x": "Клиент", "y": "Объем покупок"},
            title="Топ-5 клиентов по объему покупок",
        )
        top_customers_by_volume_plot = plot(top_customers_by_volume_fig, output_type="div")

    context = {
        "form": form,
        "sales_over_time_plot": sales_over_time_plot,
        "fuel_sales_by_type_plot": fuel_sales_by_type_plot,
        "sales_by_station_plot": sales_by_station_plot,
        "revenue_by_fuel_type_plot": revenue_by_fuel_type_plot,
        "top_customers_by_volume_plot": top_customers_by_volume_plot,
    }

    return render(request, "azs_app/statistics_view.html", context)


def execute_sql_query(request):
    error_message = None
    results = None
    columns = []
    form = SQLQueryForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        sql_query = form.cleaned_data["query"]  # Здесь исправлено на "query"

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
        except Exception as e:
            error_message = str(e)

    return render(
        request,
        "azs_app/sql_query.html",
        {
            "form": form,
            "results": results,
            "columns": columns,
            "error_message": error_message,
        },
    )
