from django.contrib import admin
from django.urls import path
from azs_app import views

urlpatterns = [
    path("admin/sql-query/", views.execute_sql_query, name="sql_query"),
    path("admin/", admin.site.urls),
    path("statistics/", views.statistics_view, name="statistics"),
    path("", views.tables_view, name="tables"),
]
