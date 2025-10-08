from django.shortcuts import render
import amadeus
from django.http import JsonResponse
from django.utils import timezone
from django.forms.models import model_to_dict
from flights.models import FlightRequest, FlightOffer, FlightSegment
from .models import IATA
import isodate
import datetime
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

c = amadeus.Client(client_id=os.getenv('API_KEY'),
                   client_secret=os.getenv('API_SECRET'))


def get_cities(request):
    query = request.GET.get("query", None)  # Получаем введённый текст
    data = c.reference_data.locations.get(keyword=query, subType=amadeus.Location.ANY).data
    result = []
    for i, val in enumerate(data):
        result.append(data[i]['iataCode']+', '+data[i]['name'])
    return JsonResponse(result, safe=False)


def offer_search_api(flight_req_id):
    
    try:
        # Проверяем существование запроса
        flight_req = FlightRequest.objects.get(id=flight_req_id)

        # Преобразуем модель в словарь для передачи в API
        kwargs = model_to_dict(flight_req)
        d = {}
        for key in kwargs.keys():
           if kwargs[key] is not None and key not in ['id', 'user', 'session_key', 'created_at', 'nonStop', 'sortParam']:
              d[key] = kwargs[key]
        
        # Ограничиваем количество результатов
        d['max'] = 2
        
        # Выполняем поиск рейсов

        search_flights = c.shopping.flight_offers_search.get(**d)

        # Проверяем, есть ли результаты
        if not search_flights.data:
            print(f"No flights found for request ID: {flight_req_id}")
            return False
            
        # Обрабатываем каждый найденный рейс
        for flight in search_flights.data:
            # Получаем первый и последний сегменты для определения общего времени полета
            if not flight.get('itineraries') or not flight['itineraries'][0].get('segments'):
                continue  # Пропускаем рейс без сегментов
                
            segment1 = flight['itineraries'][0]['segments'][0]
            segment_last = flight['itineraries'][0]['segments'][-1]
            
            # Парсим продолжительность полета
            try:
                duration = isodate.parse_duration(flight['itineraries'][0]['duration'])
                duration = datetime.time(hour=duration.seconds//3600, minute=duration.seconds//60 % 60)
            except (ValueError, TypeError) as e:
                print(f"Error parsing duration: {e}")
                duration = datetime.time(0, 0)  # Устанавливаем значение по умолчанию
            
            # Создаем предложение рейса
            
            offer = FlightOffer(
                flightRequest=flight_req,
                adults_count=flight_req.adults,
                dep_duration=isodate.parse_datetime(segment1['departure']['at']),
                arr_duration=isodate.parse_datetime(segment_last['arrival']['at']),
                duration=duration,
                currencyCode=flight['price']['currency'],
                totalPrice=flight['price']['total'],
                oneWay=False if len(flight['itineraries']) > 1 else True,
                data=flight,
            )
            # Проверяем наличие атрибутов children и infants у объекта flight_req
            if hasattr(flight_req, 'children') and flight_req.children is not None:
                offer.children_count = flight_req.children
            if hasattr(flight_req, 'infants') and flight_req.infants is not None:
                offer.infants_count = flight_req.infants
            offer.save()
            
            
            # Обрабатываем каждый сегмент рейса
            for i in range(len(flight['itineraries'])):
                for segment in flight['itineraries'][i]['segments']:
                    # Парсим продолжительность сегмента
                    try:
                        duration_seg = isodate.parse_duration(segment['duration'])
                        duration_seg = datetime.time(
                            hour=duration_seg.seconds // 3600, 
                            minute=duration_seg.seconds // 60 % 60
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing segment duration: {e}")
                        duration_seg = datetime.time(0, 0)  # Устанавливаем значение по умолчанию
                    #print(segment)
                    dep_terminal = '' if not('terminal' in segment['departure']) else segment['departure']['terminal']
                    arr_terminal = '' if not('terminal' in segment['arrival']) else segment['arrival']['terminal'] 
                    FlightSegment(
                        offer=offer,
                        there_seg=True if i == 0 else False,
                        dep_iataCode=segment['departure']['iataCode'],
                        dep_airport=getAirport(segment['departure']['iataCode']),
                        dep_terminal=dep_terminal,
                        dep_dateTime=isodate.parse_datetime(segment['departure']['at']),
                        arr_iataCode=segment['arrival']['iataCode'],
                        arr_airport=getAirport(segment['arrival']['iataCode']),
                        arr_terminal=arr_terminal,
                        arr_dateTime=isodate.parse_datetime(segment['arrival']['at']),
                        carrierCode=segment['carrierCode'],
                        number=segment['number'],
                        aircraftCode=segment['aircraft']['code'],
                        operating=segment['operating']['carrierCode'],
                        duration=duration_seg
                    ).save()
                    #print('success')
        return True
    except FlightRequest.DoesNotExist:
        print(f"FlightRequest with ID {flight_req_id} does not exist")
        return False
    except Exception as e:
        print(f"Error in offer_search_api: {e}")
        return False
    
'''
class Index(APIView):
    def get(self, request):
        origin = request.GET.get('origin', '')
        destination = request.GET.get('destination', '')
        search_params = {
                'origin': origin,
                'destination': destination,
                #'adults': 1,
                #'nonStop': 'false',
                #'currencyCode': 'RUB',
                #'max': 5  # Количество результатов
            }
        
        token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': os.getenv('API_KEY'),
            'client_secret': os.getenv('API_SECRET')
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            return JsonResponse({'error': 'Failed to get API token'}, status=500)
            
        access_token = token_response.json()['access_token']

        # Формируем запрос к Flight Offers Search API
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        search_url = 'https://test.api.amadeus.com/v1/shopping/flight-dates'
        print(1)
        data = requests.get(search_url, headers=headers, params=search_params)
        print(data)
        return JsonResponse({'origin': origin, 'destination': destination, 'data': ''})


def get_flight_prices(request):
    """
    Вьюха для получения цен на перелеты
    Ожидает POST запрос с параметрами:
    - origin: код города вылета (например, 'MOW')
    - destination: код города прилета (например, 'LED')
    - departure_date: дата вылета в формате 'YYYY-MM-DD' (опционально)
    - return_date: дата возвращения в формате 'YYYY-MM-DD' (опционально)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            origin = data.get('origin')
            destination = data.get('destination')
            departure_date = data.get('departure_date')
            return_date = data.get('return_date')

            # Валидация обязательных полей
            if not origin or not destination:
                return JsonResponse({'error': 'Origin and destination are required'}, status=400)

            # Получаем токен Amadeus API
            
            token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': os.getenv('API_KEY'),
                'client_secret': os.getenv('API_SECRET')
            }
            
            token_response = requests.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return JsonResponse({'error': 'Failed to get API token'}, status=500)
                
            access_token = token_response.json()['access_token']

            # Формируем запрос к Flight Offers Search API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Базовые параметры поиска
            search_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'adults': 1,
                'nonStop': 'false',
                'currencyCode': 'RUB',
                'max': 50  # Количество результатов
            }
            
            # Добавляем даты если они есть
            if departure_date:
                search_params['departureDate'] = departure_date
            if return_date:
                search_params['returnDate'] = return_date

            # Если нет конкретных дат, ищем самые дешевые за ближайший месяц

            if not departure_date and not return_date:
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                next_month = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                search_params['departureDate'] = f"{tomorrow},{next_month}"
            search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            response = requests.get(search_url, headers=headers, params=search_params)

            response = c.shopping.flight_dates.get(origin=origin, destination=destination)
            print(response)
            if response.status_code == 200:
                flight_data = response.json()
                processed_data = process_flight_data(flight_data)
                return JsonResponse(processed_data, safe=False)
            else:
                return JsonResponse({'error': 'API request failed'}, status=response.status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)
'''

def process_flight_data(flight_data):
    """
    Обрабатывает сырые данные от API и извлекает нужную информацию
    """
    processed_flights = []
    
    for offer in flight_data.get('data', []):
        # Обрабатываем сегменты перелета
        itineraries = []
        for itinerary in offer['itineraries']:
            segments = []
            for segment in itinerary['segments']:
                segments.append({
                    'departure_airport': segment['departure']['iataCode'],
                    'arrival_airport': segment['arrival']['iataCode'],
                    'departure_time': segment['departure']['at'],
                    'arrival_time': segment['arrival']['at'],
                    'airline': segment['carrierCode'],
                    'flight_number': segment['number']
                })
            
            itineraries.append({
                'duration': itinerary['duration'],
                'segments': segments
            })

        # Информация о цене
        price_info = {
            'total': offer['price']['total'],
            'currency': offer['price']['currency']
        }

        processed_flights.append({
            'itineraries': itineraries,
            'price': price_info,
            'one_way': len(itineraries) == 1
        })
    
    return processed_flights


def transform_airport(airport):
    airport = list(airport)
    for i in range(1, len(airport)):
        if airport[i - 1] == ' ':
            continue
        airport[i] = airport[i].lower()
    airport = ''.join(airport)
    return airport


def getAirport(iataCode):
    data = IATA.objects.get(iata=iataCode)
    return data.city


class SearchAirports(APIView):
    def get(self, request):
        keyword = request.GET.get('keyword', '')
        if not keyword or len(keyword) < 1:
            return JsonResponse({
                'success': False,
                'error': 'Keyword parameter is required'
            }, status=400)
        
        response = c.reference_data.locations.get(keyword=keyword, subType=amadeus.Location.AIRPORT)
        if response.data:
            data = response.data
            airports = []
            if len(data) > 0:
                for item in data:
                    airport = {
                        'iataCode': item['iataCode'],
                        'cityName': transform_airport(item['address']['cityName'])
                    }
                    airports.append(airport)
            return JsonResponse({
                'success': True,
                'airports': airports
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Airports not found'
            }, status=404)


class CheckPriceView(APIView):
    def get(self, request, offer_id):
        offer = FlightOffer.objects.get(id=offer_id)
        try:
            #print(1)
            #print(offer.data)
            response = c.shopping.flight_offers.pricing.post(offer.data)
            #print(response.data)
            #print(response.data['flightOffers'][0]['price']['total'])
            if response and 'flightOffers' in response.data and len(response.data['flightOffers']) > 0:
                current_price = float(response.data['flightOffers'][0]['price']['total'])
                return JsonResponse({
                    'success': True,
                    'price': current_price,
                    'currency': offer.currencyCode or 'EUR'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Flight not found'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

def check_flight_price(request, offer_id):
    """
    API для проверки актуальной цены рейса через Amadeus API
    """
    try:
        # Получаем предложение по ID
        offer = FlightOffer.objects.get(id=offer_id)
        #print(offer.data)
        # Формируем параметры для запроса
        #params = {'data': {'type': 'flight-offers-pricing', 'flightOffers': [offer.data]}}
        try:
            response = c.shopping.flight_offers.pricing.post(offer.data)
        except Exception as e:
            print(e)
        # Проверяем статус ответа
        #print(response.keys())
        #print(response)
        if response:
            # Проверяем, есть ли предложения в ответе
            if 'flightOffers' in response.data and len(response.data['flightOffers']) > 0:
                # Получаем актуальную цену
                current_price = float(response.data['flightOffers'][0]['price']['total'])
                
                # Обновляем цену в базе данных
                old_price = float(offer.totalPrice)
                offer.totalPrice = current_price
                offer.save()
                
                # Возвращаем актуальную цену и разницу с предыдущей
                price_diff = current_price - old_price
                return JsonResponse({
                    'success': True,
                    'price': current_price,
                    'old_price': old_price,
                    'price_diff': price_diff,
                    'currency': offer.currencyCode or 'EUR',
                })
                
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Flight not found',
                    'redirect': True,
                    'redirect_url': '/'
                })
        else:
            # В случае ошибки API, возвращаем текущую цену из базы
            return JsonResponse({
                'success': False,
                'error': f'Amadeus API error: {response.status_code}',
                'price': float(offer.totalPrice),
                'currency': offer.currencyCode or 'EUR'
            })
    
    except FlightOffer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Offer not found',
            'redirect': True,
            'redirect_url': '/'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def create_flight_order(request, offer_id):
    """
    API endpoint для создания заказа через Amadeus Flight Create Orders
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        offer = FlightOffer.objects.get(id=offer_id)
        
        # Подготавливаем данные для запроса к Amadeus API
        order_request = {
            'data': {
                'type': 'flight-order',
                'flightOffers': [offer.data],
                'travelers': data.get('travelers', []),
                'remarks': {
                    'general': [
                        {
                            'subType': 'GENERAL_MISCELLANEOUS',
                            'text': 'ONLINE BOOKING FROM BILETY.RU'
                        }
                    ]
                },
                'ticketingAgreement': {
                    'option': 'DELAY_TO_CANCEL',
                    'delay': '6D'
                },
                'contacts': data.get('contacts', [])
            }
        }
        
        # Выполняем запрос к Amadeus API для создания заказа
        order_response = c.booking.flight_orders.post(order_request)
        
        # Возвращаем данные о созданном заказе
        return JsonResponse({
            'success': True,
            'order': order_response['data']
        })
    
    except FlightOffer.DoesNotExist:
        return JsonResponse({'error': 'Flight offer not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def get_order_info(request, order_id):
    """
    API для получения информации о заказе по его ID
    """
    try:
        # Запрашиваем информацию о заказе через Amadeus API
        order_response = c.booking.flight_orders(order_id).get()
        order_data = order_response['data']
        
        # Извлекаем основную информацию о заказе
        flight_offers = order_data.get('flightOffers', [])
        travelers = order_data.get('travelers', [])
        
        if not flight_offers:
            return JsonResponse({'error': 'No flight offers found in order'}, status=404)
        
        # Получаем информацию о маршруте из первого предложения
        first_offer = flight_offers[0]
        first_segment = first_offer['itineraries'][0]['segments'][0]
        last_segment = first_offer['itineraries'][0]['segments'][-1]
        
        # Получаем названия городов
        try:
            origin_city = c.reference_data.locations.get(
                keyword=first_segment['departure']['iataCode'], 
                subType=amadeus.Location.CITY
            ).data[0]['name']
            
            destination_city = c.reference_data.locations.get(
                keyword=last_segment['arrival']['iataCode'], 
                subType=amadeus.Location.CITY
            ).data[0]['name']
        except Exception:
            # В случае ошибки используем коды IATA
            origin_city = first_segment['departure']['iataCode']
            destination_city = last_segment['arrival']['iataCode']
        
        # Форматируем дату вылета
        departure_datetime = datetime.datetime.fromisoformat(first_segment['departure']['at'].replace('Z', '+00:00'))
        departure_date = departure_datetime.strftime('%d.%m.%Y %H:%M')
        
        # Собираем структурированный ответ
        response_data = {
            'id': order_id,
            'origin': origin_city,
            'destination': destination_city,
            'departureDate': departure_date,
            'passengerCount': len(travelers),
            'totalPrice': first_offer['price']['total'],
            'currencyCode': first_offer['price']['currency'],
            'status': order_data.get('status', 'UNKNOWN')
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
