from django.shortcuts import render, get_object_or_404
from .forms import OfferSearchForm
from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from .models import FlightOffer, FlightRequest, FlightSegment, AirLineRaiting
from user_management.models import CustomUser as User
from django.contrib.auth.models import Group
from api.models import IATA
from django.views.generic.edit import CreateView, View, FormView
from django.views.generic import TemplateView
from django.utils import timezone
import amadeus
from django.http import JsonResponse
import datetime
import json
from api.views import get_cities, offer_search_api
import pandas as pd


def index(request):
    #data = pd.read_csv('Airline_review.csv')

    #data['Overall_Rating'] = pd.to_numeric(data['Overall_Rating'], errors='coerce')

    #result = data.groupby('Airline Name')['Overall_Rating'].mean().reset_index()
    #print(result)
    #for index, row in result.iterrows():
        #AirLineRaiting(airline_code=None, airline_name=row['Airline Name'], rating=row['Overall_Rating']).save()
    #print(IATA.objects.get(id=100).iata)
    #IATA.objects.all().delete()
    #iata = IATA.objects.get(city='The Bronx') 
    #IATA.objects.filter(id__lt=9804).delete()
    #for i in range(0, len(data)):
        #IATA(id=i + 1 ,iata=data['IATA'][i], name=data['Airport name'][i], city=data['City'][i], state=data['Country'][i]).save()
    return render(request, 'flights/search.html')

    

class OffersSearch(FormView):
    template_name = 'flights/search.html'
    form_class = OfferSearchForm
    success_url = '/'

    def get_initial(self):
        # Получаем начальные значения для формы из последнего поискового запроса пользователя
        initial = super().get_initial()
    
        # Проверяем наличие сессии
        if not self.request.session.session_key:
            self.request.session.create()
            
        session_key = self.request.session.session_key
        
        # Ищем последний поисковый запрос для текущей сессии
        last_request = FlightRequest.objects.filter(
            session_key=session_key
        ).order_by('-created_at').first()

        if last_request:
            # Заполняем форму данными из последнего запроса
            for field in ['originLocationCode', 'destinationLocationCode', 'departureDate', 
                         'returnDate', 'adults', 'children', 'infants', 'currencyCode',
                         'cabin', 'includedAirlines', 'excludedAirlines', 'travalClass',
                         'nonStop', 'maxPrice']:
                if hasattr(last_request, field) and getattr(last_request, field) is not None:
                    initial[field] = getattr(last_request, field)
        #else:
            #initial['departureDate'] = datetime.date.today()
            #initial['returnDate'] = datetime.date.today() + datetime.timedelta(days=7)

        return initial
    
    def form_valid(self, form):
        flight_request = form.save(commit=False)
        
        # Проверяем наличие сессии

        if not self.request.session.session_key:
            self.request.session.create()
            
        # Сохраняем данные пользователя и сессии
        if self.request.user.is_authenticated:
            flight_request.user = self.request.user
        flight_request.session_key = self.request.session.session_key  # Новое поле
        
        # Обрабатываем коды аэропортов
        flight_request.originLocationCode = flight_request.originLocationCode[:3].upper()
        flight_request.destinationLocationCode = flight_request.destinationLocationCode[:3].upper()

        
        # Сохраняем запрос и устанавливаем его ID в сессию
        flight_request.save()
        self.request.session['id_offer_search'] = flight_request.id
        

        search_success = offer_search_api(flight_request.id)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': search_success})
        
        return HttpResponseRedirect(reverse('flights:home'))

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
        return HttpResponse(form.errors, status=400)#render(self.request, self.template_name, {'form': form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем результаты последнего поиска
        if 'id_offer_search' in self.request.session:
            try:
                flight_req = FlightRequest.objects.filter(id=self.request.session['id_offer_search']).last()
                if flight_req:
                    context['offers'] = get_offers(flight_req)
                    context['segments'] = FlightSegment.objects.filter(there_seg=True)
                    context['return_segments'] = FlightSegment.objects.filter(there_seg=False)
                    context['last_search'] = flight_req
            except Exception as e:
                # Логируем ошибку, но не позволяем ей прервать выполнение
                print(f"Ошибка при получении результатов поиска: {e}")
                # Удаляем некорректный ID из сессии
                if 'id_offer_search' in self.request.session:
                    del self.request.session['id_offer_search']
                    self.request.session.save()
        
        return context


def get_offers(request):
    #request = FlightRequest.objects.filter(id=id_request).last()
    sort_parm = request.sortParam
    match sort_parm:
        case 'price_asc':
            parm = 'totalPrice'
        case 'duration_asc':
            parm = 'duration'
        case 'departure_asc':
            parm = 'dep_duration'
    if request.nonStop:
        return FlightOffer.objects.filter(flightRequest=request).order_by('-oneWay', parm)[:6]
    else:
        return FlightOffer.objects.filter(flightRequest=request).order_by(parm)[:6]

from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.conf import settings
import os

# Adjust the model class import to match your training script's model class
from flights.recsys.predictor import Recommender
# Provide the same model class signature as used during training
from flights.recsys.model_stub import RecModelForInference as ModelClass

# Lazy init (keeps memory in process for faster inference)
RECOMMENDER = None

def get_recommender():
    global RECOMMENDER
    if RECOMMENDER is None:
        model_path = getattr(settings, 'RECSYS_MODEL_PATH', os.path.join(settings.BASE_DIR, 'recsys_model.pth'))
        data_dir = getattr(settings, 'RECSYS_DATA_DIR', os.path.join(settings.BASE_DIR, 'recsys_data'))
        RECOMMENDER = Recommender(ModelClass, model_state_path=model_path, data_dir=data_dir)
    return RECOMMENDER


def recommendations_view(request, user_id):
    # returns JSON list of recommended item IDs
    try:
        rec = get_recommender()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    try:
        top = rec.recommend_for_user(user_id, top_k=10)

        data = []

        for i in top:
            offer = FlightOffer.objects.get(id=i)
            item = {
                'iataCode': FlightSegment.objects.filter(offer=offer).last().dep_iataCode,
                'cityName': FlightSegment.objects.filter(offer=offer).last().dep_airport
            }
            data.append(item)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    # You can also render a template and pass item objects to it
    return JsonResponse({'user_id': user_id, 'data': data})
