from django import forms
from .models import FlightRequest


class OfferSearchForm(forms.ModelForm):
    CURRENCY_CODES = [('EUR', '€'), ('RUB', '₽'), ('USD', '$')]

    currencyCode = forms.ChoiceField(choices=CURRENCY_CODES, initial='RUB', label='Валюта', widget=forms.Select())
    # returnDate = forms.DateField(required=False)
    
    # Добавляем виджеты для выбора количества пассажиров с ограничениями
    '''
    adults = forms.IntegerField(
        min_value=1, 
        max_value=9, 
        label='Взрослые (от 12 лет)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '9'})
    )
    children = forms.IntegerField(
        min_value=0, 
        max_value=9, 
        required=False,
        label='Дети (от 2 до 12 лет)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '9'})
    )
    infants = forms.IntegerField(
        min_value=0, 
        max_value=9, 
        required=False,
        label='Младенцы (до 2 лет)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '9'})
    )
    '''
    class Meta:
        model = FlightRequest
        fields = '__all__'
        labels = {
            'currencyCode': "Валюта",
            'originLocationCode': 'Аэропорт отправления',
            'destinationLocationCode': 'Аэропорт прибытия',
            'departureDate': 'Дата отправления',
            'returnDate': 'Дата возвращения',
            'maxPrice': 'Максимальная цена',
            'nonStop': 'В первую очередь без пересадок',
            'adults': 'Взрослые от 12',
            'children': 'Дети до 12',
            'infants': 'Младенцы до 2',
            'sortParam': 'Сортировать по'
        }
        widgets = {
            'departureDate': forms.DateInput(attrs={'type': 'date','class': 'form-control', 'style': 'width:10em;'}),
            'returnDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'style': 'width:10em;'}),
            'originLocationCode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например, JFK', }),
            'destinationLocationCode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например, LAX', }),
            'currencyCode': forms.Select(attrs={'class': 'form-control'}),
            'maxPrice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Без ограничений'}),
            'nonStop': forms.CheckboxInput(),
            'adults': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '9', 'size': '1', 'maxlength': '1', 'style': 'width:3em;'}),
            'children': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '9', 'size': '1', 'maxlength': '1', 'style': 'width:3em;'}),
            'infants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '9', 'size': '1', 'maxlength': '1', 'style': 'width:3em;'}),
            'sortParam': forms.Select(attrs={'class': 'form-control'})
        }


# class OfferSearchForm(forms.Form):
#     CURRENCY_CODES = [('EUR', '€'), ('RUB', '₽'), ('USD', '$')]
#
#     currencyCode = forms.ChoiceField(choices=CURRENCY_CODES, label='Валюта', initial='EUR', widget=forms.Select())
#     originLocationCode = forms.CharField(max_length=100)
#     # originLC = forms.ChoiceField(choices=[], label='Выбирете аэропорт отправления')
#     destinationLocationCode = forms.CharField(max_length=100)
#     # destinationLC = forms.ChoiceField(choices=[], label='Выбирете аэропорт прибытия')
#     departureDate = forms.DateField(label='Дата отправления', widget=forms.SelectDateWidget())
#     returnDate = forms.DateField(label='Дата возвращения', widget=forms.SelectDateWidget(), required=False)
#     adults = forms.IntegerField(label='Количество взрослых пассажиров')

