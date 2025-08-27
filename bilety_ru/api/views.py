from django.shortcuts import render
import amadeus
from django.http import JsonResponse
from django.forms.models import model_to_dict
from .models import IATA
from flights.models import FlightRequest, FlightOffer, FlightSegment
import isodate
import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
#import requests
import datetime
# Create your views here.

c = amadeus.Client(client_id='1otgEUauKpjxxGPcPxSQvvsRz7o3fxv1',
                   client_secret='VgqvL5c92wzXcPgV')


def get_cities(request):
    query = request.GET.get("query", None)  # Получаем введённый текст
    data = c.reference_data.locations.get(keyword=query, subType=amadeus.Location.ANY).data
    result = []
    for i, val in enumerate(data):
        result.append(data[i]['iataCode']+', '+data[i]['name'])
    return JsonResponse(result, safe=False)


def offer_search_api(flight_req_id):
    """
    Функция для поиска предложений авиабилетов через API Amadeus
    и сохранения их в базу данных
    """
    try:
        # Проверяем существование запроса
        flight_req = FlightRequest.objects.get(id=flight_req_id)

        # Преобразуем модель в словарь для передачи в API
        kwargs = model_to_dict(flight_req)
        d = {}
        for key in kwargs.keys():
           if kwargs[key] is not None and key not in ['id', 'user', 'session_key', 'created_at']:
              d[key] = kwargs[key]
        
        # Ограничиваем количество результатов
        d['max'] = 6

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
                dep_duration=segment1['departure']['at'],
                arr_duration=segment_last['arrival']['at'],
                duration=duration,
                currencyCode=flight['price']['currency'],
                totalPrice=flight['price']['total'],
                data=flight,
            )
            # Проверяем наличие атрибутов children и infants у объекта flight_req
            if hasattr(flight_req, 'children') and flight_req.children is not None:
                offer.children_count = flight_req.children
            if hasattr(flight_req, 'infants') and flight_req.infants is not None:
                offer.infants_count = flight_req.infants
            offer.save()
            
            # Обрабатываем каждый сегмент рейса
            for segment in flight['itineraries'][0]['segments']:
                # Получаем информацию о аэропортах отправления и прибытия
                dep_iata = segment['departure']['iataCode']
                dep_airoport = IATA.objects.get(iata=dep_iata).city

                arr_iata = segment['arrival']['iataCode']
                arr_airoport = IATA.objects.get(iata=arr_iata).city
                
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
                
                # Создаем сегмент рейса
                FlightSegment(
                    offer=offer,
                    dep_iataCode=dep_iata,
                    dep_airport=dep_airoport,
                    dep_dateTime=segment['departure']['at'],
                    arr_iataCode=arr_iata,
                    arr_airport=arr_airoport,
                    arr_dateTime=segment['arrival']['at'],
                    carrierCode=segment['carrierCode'],
                    duration=duration_seg
                ).save()
        
        return True
    except FlightRequest.DoesNotExist:
        print(f"FlightRequest with ID {flight_req_id} does not exist")
        return False
    except Exception as e:
        print(f"Error in offer_search_api: {e}")
        return False


def get_structured_flight_offers(request):
    """
    API endpoint для получения структурированных данных о рейсах для фронтенда
    """
    if 'id_offer_search' not in request.session:
        return JsonResponse({'error': 'No flight search in session'}, status=400)
    
    flight_req_id = request.session['id_offer_search']
    try:
        flight_req = FlightRequest.objects.get(id=flight_req_id)
        offers = FlightOffer.objects.filter(flightRequest=flight_req)
        
        structured_offers = []
        for offer in offers:
            # Получаем все сегменты для данного предложения
            segments = FlightSegment.objects.filter(offer=offer)
            
            # Структурируем данные для фронтенда
            offer_data = {
                'id': offer.id,
                'totalPrice': float(offer.totalPrice),
                'currencyCode': offer.currencyCode,
                'duration': offer.duration.strftime('%H:%M'),
                'outbound': [],
                'inbound': [],
                'bookingCode': offer.data.get('id', ''),  # Код бронирования из данных Amadeus
            }
            
            # Добавляем сегменты для полета "туда"
            for segment in segments:
                segment_data = {
                    'departureAirport': segment.dep_iataCode,
                    'departureCity': segment.dep_airport,
                    'departureDateTime': segment.dep_dateTime.strftime('%Y-%m-%d %H:%M'),
                    'arrivalAirport': segment.arr_iataCode,
                    'arrivalCity': segment.arr_airport,
                    'arrivalDateTime': segment.arr_dateTime.strftime('%Y-%m-%d %H:%M'),
                    'duration': segment.duration.strftime('%H:%M'),
                    'airline': segment.carrierCode,
                    'airlineLogo': f"https://s1.apideeplink.com/images/airlines/{segment.carrierCode}.png"
                }
                
                # Определяем, к какому направлению относится сегмент (туда/обратно)
                # Пока что все сегменты считаем как outbound (туда)
                offer_data['outbound'].append(segment_data)
            
            structured_offers.append(offer_data)
        
        return JsonResponse({'offers': structured_offers}, safe=False)
    
    except FlightRequest.DoesNotExist:
        return JsonResponse({'error': 'Flight request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def transform_airport(airport):
    airport = list(airport)
    for i in range(1, len(airport)):
        if airport[i - 1] == ' ':
            continue
        airport[i] = airport[i].lower()
    airport = ''.join(airport)
    return airport


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


def check_flight_price(request, offer_id):
    """
    API для проверки актуальной цены рейса через Amadeus API
    """
    try:
        # Получаем предложение по ID
        offer = FlightOffer.objects.get(id=offer_id)
        print(offer)
        # Формируем параметры для запроса
        #params = {'data': {'type': 'flight-offers-pricing', 'flightOffers': [offer.data]}}
        try:
            response = c.shopping.flight_offers.pricing.post(offer.data)
        except Exception as e:
            print(e)
        # Проверяем статус ответа
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
                
                # Получаем дополнительную информацию о рейсе для корректного отображения карточки
                '''
                segments = FlightSegment.objects.filter(offer=offer)
                segments_data = []
                
                for segment in segments:
                    try:
                        # Получаем информацию об аэропортах
                        departure_airport = get_airport_info(segment.dep_iataCode)
                        arrival_airport = get_airport_info(segment.arr_iataCode)
                        
                        # Форматируем даты
                        departure_at = None
                        arrival_at = None
                        
                        if segment.dep_dateTime:
                            departure_at = segment.dep_dateTime.strftime('%Y-%m-%dT%H:%M:%S')
                        
                        if segment.arr_dateTime:
                            arrival_at = segment.arr_dateTime.strftime('%Y-%m-%dT%H:%M:%S')
                        
                        # Формируем данные о сегменте
                        segment_data = {
                            'id': segment.id,
                            'departure': {
                                'iataCode': segment.dep_iataCode or '',
                                'airport': departure_airport.get('name', segment.dep_airport or 'Неизвестный аэропорт'),
                                'city': departure_airport.get('city', 'Неизвестный город'),
                                'country': departure_airport.get('country', 'Неизвестная страна'),
                                'at': departure_at
                            },
                            'arrival': {
                                'iataCode': segment.arr_iataCode or '',
                                'airport': arrival_airport.get('name', segment.arr_airport or 'Неизвестный аэропорт'),
                                'city': arrival_airport.get('city', 'Неизвестный город'),
                                'country': arrival_airport.get('country', 'Неизвестная страна'),
                                'at': arrival_at
                            },
                            'carrierCode': segment.carrierCode or '',
                            'number': '',  # В модели нет поля number
                            'duration': str(segment.duration) if segment.duration else '00:00',
                            'aircraft': ''  # В модели нет поля aircraft
                        }
                        
                        segments_data.append(segment_data)
                    except Exception as e:
                        print(f"Error processing segment: {e}")
                
                # Формируем полную информацию о рейсе
                flight_data = {
                    'id': offer.id,
                    'price': {
                        'total': current_price,
                        'currency': offer.currencyCode or 'EUR'
                    },
                    'itineraries': [{
                        'segments': segments_data,
                        'duration': str(sum([segment.duration for segment in segments if segment.duration], datetime.timedelta()))
                    }]
                }
                '''
                return JsonResponse({
                    'success': True,
                    'price': current_price,
                    'old_price': old_price,
                    'price_diff': price_diff,
                    'currency': offer.currencyCode or 'EUR',
                })
            else:
                # Если предложений нет, удаляем из кэша и перенаправляем на страницу поиска
                from django.core.cache import cache
                
                # Получаем ключ кэша для этого запроса
                cache_key = f"flight_offers_{flight_request.id}"
                
                # Удаляем предложение из кэша
                cached_offers = cache.get(cache_key, [])
                if offer.id in cached_offers:
                    cached_offers.remove(offer.id)
                    cache.set(cache_key, cached_offers, 60*15)  # Обновляем кэш на 15 минут
                
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


def get_airport_info(iata_code):
    """
    Вспомогательная функция для получения информации об аэропорте по его IATA-коду
    С кэшированием для уменьшения количества запросов к API
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Getting airport info for IATA code: {iata_code}")
    
    from django.core.cache import cache
    
    if not iata_code:
        logger.warning("Empty IATA code provided")
        return {'name': 'Unknown', 'city': 'Unknown', 'country': ''}
    
    # Проверяем наличие в кэше
    cache_key = f"airport_{iata_code}"
    airport_info = cache.get(cache_key)
    
    if airport_info:
        logger.info(f"Found airport info in cache for {iata_code}")
        return airport_info
    
    logger.info(f"Airport info not found in cache for {iata_code}, requesting from API")
    
    # Вместо запроса к API возвращаем базовые данные
    # Это упрощение позволит избежать ошибок при вызове API
    default_info = {
        'name': f"{iata_code} Airport",
        'city': iata_code,
        'country': ''
    }
    
    # Сохраняем в кэш на 24 часа
    cache.set(cache_key, default_info, 60*60*24)
    logger.info(f"Saved default airport info to cache for {iata_code}")
    
    return default_info


def get_flight_details(request, offer_id):
    """
    API для получения подробной информации о рейсе для страницы оформления билета
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Getting flight details for offer_id: {offer_id}")
    
    try:
        # Получаем предложение по ID
        offer = FlightOffer.objects.get(id=offer_id)
        logger.info(f"Found flight offer with ID {offer_id}")
        
        # Получаем сегменты рейса
        segments = FlightSegment.objects.filter(offer=offer)
        logger.info(f"Found {segments.count()} segments for offer {offer_id}")
        
        segments_data = []
        
        # Формируем данные о сегментах
        for segment in segments:
            logger.info(f"Processing segment {segment.id} from {segment.dep_iataCode} to {segment.arr_iataCode}")
            
            try:
                # Получаем информацию об аэропортах
                departure_airport = c.reference_data.locations.get(keyword=segment.dep_iataCode, subType=amadeus.Location.AIRPORT).data[0]
                arrival_airport = c.reference_data.locations.get(keyword=segment.arr_iataCode, subType=amadeus.Location.AIRPORT).data[0]
                
                # Форматируем даты безопасным способом
                departure_at = None
                arrival_at = None
                
                if segment.dep_dateTime:
                    try:
                        departure_at = segment.dep_dateTime.strftime('%Y-%m-%dT%H:%M:%S')
                    except Exception as e:
                        logger.error(f"Error formatting departure time: {e}")
                        departure_at = None
                
                if segment.arr_dateTime:
                    try:
                        arrival_at = segment.arr_dateTime.strftime('%Y-%m-%dT%H:%M:%S')
                    except Exception as e:
                        logger.error(f"Error formatting arrival time: {e}")
                        arrival_at = None
                
                # Формируем данные о сегменте
                segment_data = {
                    'id': segment.id,
                    'departure': {
                        'iataCode': segment.dep_iataCode or '',
                        'airport': departure_airport.name,
                        'city': departure_airport.addresses.cityName,
                        'country': departure_airport.addresses.countryName,
                        'at': departure_at
                    },
                    'arrival': {
                        'iataCode': segment.arr_iataCode or '',
                        'airport': arrival_airport.name,
                        'city': arrival_airport.addresses.cityName,
                        'country': arrival_airport.addresses.countryName,
                        'at': arrival_at
                    },
                    'carrierCode': segment.carrierCode or '',
                    'number': '',  # В модели нет поля number
                    'duration': str(segment.duration) if segment.duration else '00:00',
                    'aircraft': ''  # В модели нет поля aircraft
                }
                
                segments_data.append(segment_data)
                logger.info(f"Successfully processed segment {segment.id}")
                
            except Exception as e:
                logger.error(f"Error processing segment {segment.id}: {e}")
                # Добавляем базовые данные для сегмента в случае ошибки
                segment_data = {
                    'id': segment.id if hasattr(segment, 'id') else 0,
                    'departure': {
                        'iataCode': segment.dep_iataCode if hasattr(segment, 'dep_iataCode') else '',
                        'airport': segment.dep_airport if hasattr(segment, 'dep_airport') else 'Неизвестный аэропорт',
                        'city': 'Неизвестный город',
                        'country': '',
                        'at': None
                    },
                    'arrival': {
                        'iataCode': segment.arr_iataCode if hasattr(segment, 'arr_iataCode') else '',
                        'airport': segment.arr_airport if hasattr(segment, 'arr_airport') else 'Неизвестный аэропорт',
                        'city': 'Неизвестный город',
                        'country': '',
                        'at': None
                    },
                    'carrierCode': segment.carrierCode if hasattr(segment, 'carrierCode') else '',
                    'number': '',
                    'duration': str(segment.duration) if hasattr(segment, 'duration') and segment.duration else '00:00',
                    'aircraft': ''
                }
                segments_data.append(segment_data)
        
        # Формируем данные о рейсе
        try:
            total_price = float(offer.totalPrice) if offer.totalPrice else 0.0
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting price to float: {e}")
            total_price = 0.0
            
        flight_data = {
            'id': offer.id,
            'price': {
                'total': total_price,
                'currency': offer.currencyCode or 'EUR'
            },
            'itineraries': [{
                'duration': str(offer.duration) if offer.duration else '00:00',
                'segments': segments_data
            }]
        }
        
        logger.info(f"Successfully prepared flight data for offer {offer_id}")
        return JsonResponse({
            'success': True,
            'flight': flight_data
        })
    
    except FlightOffer.DoesNotExist:
        logger.error(f"Flight offer with ID {offer_id} not found")
        return JsonResponse({
            'success': False,
            'error': 'Предложение не найдено'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error in get_flight_details for offer {offer_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при получении данных о рейсе: {str(e)}'
        }, status=500)


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
