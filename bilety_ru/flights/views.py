from django.shortcuts import render, get_object_or_404
from .forms import OfferSearchForm
from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from .models import FlightOffer, FlightRequest, FlightSegment
from django.views.generic.edit import CreateView, View, FormView
from django.views.generic import TemplateView
from django.utils import timezone
import amadeus
from django.http import JsonResponse
import datetime
import json
from api.views import get_cities, offer_search_api, create_flight_order


c = amadeus.Client(client_id='1otgEUauKpjxxGPcPxSQvvsRz7o3fxv1',
                   client_secret='VgqvL5c92wzXcPgV')


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
        else:
            initial['departureDate'] = datetime.date.today()
            initial['returnDate'] = datetime.date.today() + datetime.timedelta(days=7)

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
        flight_request.departureDate = timezone.make_aware(datetime.datetime.combine(flight_request.departureDate, datetime.time.min))
        if flight_request.returnDate:
            flight_request.returnDate = timezone.make_aware(datetime.datetime.combine(flight_request.returnDate, datetime.time.min))

        
        # Сохраняем запрос и устанавливаем его ID в сессию
        flight_request.save()
        self.request.session['id_offer_search'] = flight_request.id
        
        # Запускаем поиск предложений через API
        search_success = offer_search_api(flight_request.id)
        # Если запрос AJAX, возвращаем JSON-ответ
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
                    context['offers'] = FlightOffer.objects.filter(flightRequest=flight_req)
                    context['segments'] = FlightSegment.objects.all()
                    context['last_search'] = flight_req
            except Exception as e:
                # Логируем ошибку, но не позволяем ей прервать выполнение
                print(f"Ошибка при получении результатов поиска: {e}")
                # Удаляем некорректный ID из сессии
                if 'id_offer_search' in self.request.session:
                    del self.request.session['id_offer_search']
                    self.request.session.save()
        
        return context


class ClearSearchHistoryView(View):
    """
    Представление для очистки истории поисковых запросов пользователя
    """
    def post(self, request, *args, **kwargs):
        # Проверяем наличие сессии
        if not request.session.session_key:
            request.session.create()
            
        session_key = request.session.session_key
        
        # Удаляем все поисковые запросы для текущей сессии
        FlightRequest.objects.filter(session_key=session_key).delete()
        
        # Если запрос AJAX, возвращаем JSON-ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        # Перенаправляем на главную страницу
        return HttpResponseRedirect(reverse('flights:home'))


class BookingSuccessView(TemplateView):
    template_name = 'flights/booking_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = self.kwargs.get('booking_id')
        
        try:
            from flights.models import Booking
            booking = Booking.objects.get(id=booking_id)
            
            # Добавляем информацию о бронировании в контекст
            context['booking'] = booking
            context['offer'] = booking.offer
            
            # Получаем сегменты рейса
            segments = FlightSegment.objects.filter(offer=booking.offer)
            context['segments'] = segments
            
            # Получаем данные о пассажирах
            context['passengers'] = booking.passenger_data.get('passengers', [])
            
            # Если пользователь авторизован, проверяем, что бронирование принадлежит ему
            if self.request.user.is_authenticated and booking.user and booking.user != self.request.user:
                context['error'] = 'У вас нет доступа к этому бронированию'
                
        except Exception as e:
            context['error'] = f'Бронирование не найдено или произошла ошибка: {str(e)}'
            
        return context
