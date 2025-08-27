from django.shortcuts import render, get_object_or_404
from .forms import OfferSearchForm
from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from .models import FlightOffer, FlightRequest, FlightSegment
from django.views.generic.edit import CreateView, View, FormView
from django.views.generic import TemplateView
from django.contrib import messages
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


class BookingView(TemplateView):
    template_name = 'flights/booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer_id = self.kwargs.get('offer_id')
        try:
            offer = FlightOffer.objects.get(id=offer_id)
            context['flight_offer'] = offer
            
            # Получаем сегменты рейса
            segments = FlightSegment.objects.filter(offer=offer)
            context['segments'] = segments
            
            # Получаем информацию о количестве пассажиров
            flight_request = offer.flightRequest
            adults = flight_request.adults
            children = flight_request.children or 0
            infants = flight_request.infants or 0
            
            # Добавляем в контекст количество пассажиров
            context['adults'] = adults
            context['children'] = children
            context['infants'] = infants
            
            # Добавляем диапазоны для циклов в шаблоне
            context['adults_range'] = range(1, adults + 1)
            context['children_range'] = range(1, children + 1)
            context['infants_range'] = range(1, infants + 1)
            
            # Также можно проверить данные о пассажирах в JSON поле data предложения
            if offer.data and 'travelerPricings' in offer.data:
                context['traveler_pricings'] = offer.data['travelerPricings']
                context['traveler_count'] = len(offer.data['travelerPricings'])
            
        except FlightOffer.DoesNotExist:
            context['error'] = 'Предложение не найдено'
        return context
        
    def post(self, request, *args, **kwargs):
        offer_id = self.kwargs.get('offer_id')
        actual_price = request.POST.get('actualPrice')
        
        try:
            offer = FlightOffer.objects.get(id=offer_id)
            
            # Проверяем, изменилась ли цена
            if actual_price and float(actual_price) != float(offer.totalPrice):
                # Обновляем цену в базе данных
                offer.totalPrice = actual_price
                offer.save()
            
            # Обрабатываем данные формы
            form_data = request.POST
            
            # Собираем данные о пассажирах
            passengers = []
            adults_count = int(form_data.get('adults_count', 0))
            children_count = int(form_data.get('children_count', 0))
            infants_count = int(form_data.get('infants_count', 0))
            
            # Проверяем данные о пассажирах в JSON поле data предложения
            traveler_types = {}
            if offer.data and 'travelerPricings' in offer.data:
                for i, traveler in enumerate(offer.data['travelerPricings']):
                    traveler_type = traveler.get('travelerType', '')
                    if traveler_type not in traveler_types:
                        traveler_types[traveler_type] = 0
                    traveler_types[traveler_type] += 1
                
                # Проверяем, что количество пассажиров совпадает
                expected_adults = traveler_types.get('ADULT', 0)
                expected_children = traveler_types.get('CHILD', 0)
                expected_infants = traveler_types.get('HELD_INFANT', 0) + traveler_types.get('SEATED_INFANT', 0)
                
                if adults_count != expected_adults or children_count != expected_children or infants_count != expected_infants:
                    # Если не совпадает, можно логировать или предупредить
                    print(f"Warning: Passenger count mismatch. Form: {adults_count}/{children_count}/{infants_count}, Expected: {expected_adults}/{expected_children}/{expected_infants}")
            
            # Собираем данные о взрослых пассажирах
            for i in range(1, adults_count + 1):
                passenger = {
                    'id': i,
                    'type': 'ADULT',
                    'firstName': form_data.get(f'adult_{i}_first_name', ''),
                    'lastName': form_data.get(f'adult_{i}_last_name', ''),
                    'dateOfBirth': form_data.get(f'adult_{i}_dob', ''),
                    'gender': form_data.get(f'adult_{i}_gender', ''),
                    'documentType': form_data.get(f'adult_{i}_document_type', ''),
                    'documentNumber': form_data.get(f'adult_{i}_document_number', '')
                }
                passengers.append(passenger)
            
            # Собираем данные о детях
            for i in range(1, children_count + 1):
                passenger = {
                    'id': adults_count + i,
                    'type': 'CHILD',
                    'firstName': form_data.get(f'child_{i}_first_name', ''),
                    'lastName': form_data.get(f'child_{i}_last_name', ''),
                    'dateOfBirth': form_data.get(f'child_{i}_dob', ''),
                    'gender': form_data.get(f'child_{i}_gender', '')
                }
                passengers.append(passenger)
            
            # Собираем данные о младенцах
            for i in range(1, infants_count + 1):
                passenger = {
                    'id': adults_count + children_count + i,
                    'type': 'INFANT',
                    'firstName': form_data.get(f'infant_{i}_first_name', ''),
                    'lastName': form_data.get(f'infant_{i}_last_name', ''),
                    'dateOfBirth': form_data.get(f'infant_{i}_dob', ''),
                    'gender': form_data.get(f'infant_{i}_gender', '')
                }
                passengers.append(passenger)
            
            # Получаем контактные данные
            contact_email = form_data.get('contact_email', '')
            contact_phone = form_data.get('contact_phone', '')
            
            # Создаем запись о бронировании
            from flights.models import Booking
            
            booking = Booking(
                offer=offer,
                total_price=offer.totalPrice,
                currency_code=offer.currencyCode,
                passenger_data={'passengers': passengers},
                contact_email=contact_email,
                contact_phone=contact_phone
            )
            
            # Если пользователь авторизован, связываем бронирование с ним
            if request.user.is_authenticated:
                booking.user = request.user
            else:
                # Иначе используем ключ сессии
                booking.session_key = request.session.session_key
            
            booking.save()
            
            # Перенаправляем на страницу успешного бронирования
            from django.urls import reverse
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('flights:booking_success', kwargs={'booking_id': booking.id}))
            
        except FlightOffer.DoesNotExist:
            context = self.get_context_data(**kwargs)
            context['error'] = 'Предложение не найдено'
            return self.render_to_response(context)
        except Exception as e:
            context = self.get_context_data(**kwargs)
            context['error'] = f'Ошибка при обработке бронирования: {str(e)}'
            return self.render_to_response(context)


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
