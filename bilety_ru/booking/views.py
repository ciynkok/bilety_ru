from django.shortcuts import render
from django.views.generic import TemplateView
from flights.models import FlightOffer, FlightSegment

# Create your views here.


def index(request, offer_id):
    return render(request, 'booking/booking.html')


class BookingView(TemplateView):
    template_name = 'booking/booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer_id = self.kwargs.get('offer_id')
        try:
            offer = FlightOffer.objects.get(id=offer_id)
            context['offer'] = offer
            
            # Получаем сегменты рейса
            segments = FlightSegment.objects.filter(offer=offer)
            context['segments'] = segments

            print(segments.first().dep_airport)

            context['dep_airport'] = segments.first().dep_airport
            context['dep_iataCode'] = segments.first().dep_iataCode

            context['arr_airport'] = segments.last().arr_airport
            context['arr_iataCode'] = segments.last().arr_iataCode
            
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

