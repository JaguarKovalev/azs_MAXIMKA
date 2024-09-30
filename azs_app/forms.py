from django import forms
from .models import FuelType, Customer


class StatisticsForm(forms.Form):
    start_date = forms.DateField(
        label="Начальная дата",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    end_date = forms.DateField(
        label="Конечная дата",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    fuel_type = forms.ModelChoiceField(
        queryset=FuelType.objects.all(), label="Тип топлива", required=False
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(), label="Клиент", required=False
    )


class SQLQueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea, label="SQL Query")
