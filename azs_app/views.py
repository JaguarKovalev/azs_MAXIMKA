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

    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        selected_fuel_type = form.cleaned_data["fuel_type"]
        selected_customer = form.cleaned_data["customer"]

    sales_query = Sale.objects.filter(date__range=[start_date, end_date])

    if selected_fuel_type:
        sales_query = sales_query.filter(fuel__fuel_type=selected_fuel_type)

    if selected_customer:
        sales_query = sales_query.filter(customer=selected_customer)

    # 1. Количество продаж по месяцам
    sales_over_time = (
        sales_query.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    # 2. Объем продаж по видам топлива
    fuel_sales_by_type = (
        sales_query.values("fuel__fuel_type__type")
        .annotate(total_sold=Sum("fuel_quantity"))
        .order_by("-total_sold")
    )

    # 3. Объем продаж по заправочным станциям
    sales_by_station = (
        sales_query.values("fuel__gas_station__name")
        .annotate(total_sold=Sum("fuel_quantity"))
        .order_by("-total_sold")
    )

    # 4. Суммарная выручка по видам топлива
    revenue_by_fuel_type = (
        sales_query.values("fuel__fuel_type__type")
        .annotate(total_revenue=Sum("fuel_quantity") * Avg("current_price"))
        .order_by("-total_revenue")
    )

    # 5. Топ-5 клиентов по объему покупок
    top_customers_by_volume = (
        sales_query.values("customer__full_name")
        .annotate(total_volume=Sum("fuel_quantity"))
        .order_by("-total_volume")[:5]
    )

    # 6. Средняя выручка за одну продажу
    avg_revenue_per_sale = sales_query.annotate(
        revenue=Sum("fuel_quantity") * Avg("current_price")
    ).aggregate(Avg("revenue"))["revenue__avg"]

    # 7. Анализ продаж по фирме-производителю за последний год
    sales_by_company_last_year = Company.objects.annotate(
        total_sold=Sum(
            "gasstation__fuel__sale__fuel_quantity",
            filter=Q(gasstation__fuel__sale__date__year=datetime.now().year),
        )
    ).order_by("-total_sold")

    context = {
        "form": form,
        "sales_over_time": sales_over_time,
        "fuel_sales_by_type": fuel_sales_by_type,
        "sales_by_station": sales_by_station,
        "revenue_by_fuel_type": revenue_by_fuel_type,
        "top_customers_by_volume": top_customers_by_volume,
        "avg_revenue_per_sale": avg_revenue_per_sale,
        "sales_by_company_last_year": sales_by_company_last_year,
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
