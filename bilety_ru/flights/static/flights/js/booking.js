/**
 * booking.js - Скрипт для страницы бронирования билетов
 * Обрабатывает динамическое обновление цен и взаимодействие с формой бронирования
 */

document.addEventListener('DOMContentLoaded', function() {
    // Получаем ID предложения из URL
    const urlParts = window.location.pathname.split('/');
    const offerId = urlParts[urlParts.indexOf('booking') + 1];
    
    // Элементы для обновления цены
    const totalPriceElement = document.getElementById('totalPrice');
    const originalPriceElement = document.getElementById('originalPrice');
    const priceDifferenceElement = document.getElementById('priceDifference');
    const priceAlertElement = document.getElementById('priceAlert');
    
    // Интервал проверки цены (каждые 60 секунд)
    const priceCheckInterval = 60000; // Увеличиваем до 60 секунд
    let priceCheckTimer;
    
    // Загружаем информацию о рейсе
    function loadFlightDetails() {
        const flightDetailsContainer = document.getElementById('flightDetails');
        
        fetch(`/api/flight-details/${offerId}/`)
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    flightDetailsContainer.innerHTML = `
                        <div class="alert alert-danger">
                            ${data.error || 'Ошибка при загрузке данных о рейсе'}
                        </div>
                    `;
                    return;
                }
                
                const flight = data.flight;
                const segments = flight.itineraries[0].segments;
                
                // Формируем HTML для отображения деталей рейса
                let html = `
                    <div class="row">
                        <div class="col-md-8">
                            <h4>Детали рейса</h4>
                            <div class="flight-route">
                                <span class="h5">${segments[0].departure.city} (${segments[0].departure.iataCode})</span>
                                <span class="flight-arrow">→</span>
                                <span class="h5">${segments[segments.length-1].arrival.city} (${segments[segments.length-1].arrival.iataCode})</span>
                            </div>
                            <div class="flight-duration">
                                <small>Общее время в пути: ${flight.itineraries[0].duration}</small>
                            </div>
                        </div>
                        <div class="col-md-4 text-right">
                            <div class="price-info">
                                <div class="price-alert alert alert-info d-none" id="priceAlert">
                                    <p>Цена изменилась!</p>
                                    <p>Старая цена: <span id="originalPrice"></span></p>
                                    <p>Разница: <span id="priceDifference"></span></p>
                                    <button type="button" class="btn btn-sm btn-primary" id="acceptNewPrice">Продолжить с новой ценой</button>
                                </div>
                                <div class="flight-price">
                                    <span id="totalPrice">${flight.price.total} ${flight.price.currency}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <hr>
                    <div class="segments-container">
                `;
                
                // Добавляем информацию о каждом сегменте
                segments.forEach((segment, index) => {
                    const departureDate = new Date(segment.departure.at);
                    const arrivalDate = new Date(segment.arrival.at);
                    
                    html += `
                        <div class="flight-segment">
                            <div class="row">
                                <div class="col-md-1">
                                    <div class="airline-logo">
                                        <img src="https://pics.avs.io/80/40/${segment.carrierCode}.png" alt="${segment.carrierCode}" class="img-fluid">
                                    </div>
                                </div>
                                <div class="col-md-11">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="departure-info">
                                                <div class="time">${departureDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                                                <div class="date">${departureDate.toLocaleDateString()}</div>
                                                <div class="airport">${segment.departure.city} (${segment.departure.iataCode})</div>
                                                <div class="airport-name">${segment.departure.airport}</div>
                                            </div>
                                        </div>
                                        <div class="col-md-4 text-center">
                                            <div class="flight-duration">
                                                <div class="duration">${segment.duration}</div>
                                                <div class="flight-line">&#8212;&#8212;&#8212;&#9992;&#8212;&#8212;&#8212;</div>
                                                <div class="flight-number">${segment.carrierCode} ${segment.number}</div>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="arrival-info">
                                                <div class="time">${arrivalDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                                                <div class="date">${arrivalDate.toLocaleDateString()}</div>
                                                <div class="airport">${segment.arrival.city} (${segment.arrival.iataCode})</div>
                                                <div class="airport-name">${segment.arrival.airport}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Добавляем разделитель между сегментами, кроме последнего
                    if (index < segments.length - 1) {
                        html += `<div class="connection-info text-center"><small>Пересадка</small></div>`;
                    }
                });
                
                html += `</div>`;
                
                // Обновляем содержимое контейнера
                flightDetailsContainer.innerHTML = html;
                
                // Добавляем обработчик для кнопки "Продолжить с новой ценой"
                const acceptNewPriceBtn = document.getElementById('acceptNewPrice');
                if (acceptNewPriceBtn) {
                    acceptNewPriceBtn.addEventListener('click', function() {
                        document.getElementById('priceAlert').classList.add('d-none');
                    });
                }
            })
            .catch(error => {
                console.error('Error loading flight details:', error);
                flightDetailsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        Ошибка при загрузке данных о рейсе. Пожалуйста, обновите страницу или попробуйте позже.
                    </div>
                `;
            });
    }
    
    // Функция для проверки актуальности цены

    function checkCurrentPrice() {
        // Показываем оверлей загрузки
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
        
        fetch(`/api/check-price/${offerId}/`)
            .then(response => {            
            // Скрываем оверлей загрузки
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
                
                // Проверяем, нужно ли перенаправить пользователя
                if (!response.success && response.redirect) {
                    // Показываем уведомление о том, что рейс не найден
                    alert('Рейс не найден или больше недоступен. Вы будете перенаправлены на страницу поиска.');
                    
                    // Останавливаем таймер проверки цены
                    clearInterval(priceCheckTimer);
                    
                    // Перенаправляем на страницу поиска
                    window.location.href = response.redirect_url || '/';
                    return;
                }
                
                // Обрабатываем ошибки
                if (response.error && !response.redirect) {
                    console.error('Error:', response.error);
                    return;
                }
                
                // Получаем текущую цену из элемента (без валюты)
                const currentPriceText = totalPriceElement.textContent;
                const currentPrice = parseFloat(currentPriceText.replace(/[^0-9.]/g, ''));
                
                // Получаем новую цену
                const newPrice = parseFloat(response.price);
                const currencyCode = response.currency;
                
                // Если цена изменилась, обновляем информацию
                if (newPrice !== currentPrice) {
                    // Сохраняем оригинальную цену
                    originalPriceElement.textContent = `${currentPriceText}`;
                    
                    // Обновляем текущую цену
                    totalPriceElement.textContent = `${newPrice} ${currencyCode}`;
                    
                    // Вычисляем и отображаем разницу
                    const difference = newPrice - currentPrice;
                    const differenceText = difference > 0 ? `+${difference}` : difference;
                    priceDifferenceElement.textContent = `${differenceText} ${currencyCode}`;
                    
                    // Перезагружаем информацию о рейсе, чтобы обновить все данные
                    loadFlightDetails();
                    
                    // Показываем уведомление
                    priceAlertElement.classList.remove('d-none');
                    
                    // Добавляем класс для цветового выделения (зеленый - цена снизилась, красный - повысилась)
                    if (difference > 0) {
                        priceDifferenceElement.classList.add('text-danger');
                        priceDifferenceElement.classList.remove('text-success');
                    } else {
                        priceDifferenceElement.classList.add('text-success');
                        priceDifferenceElement.classList.remove('text-danger');
                    }
                    
                    // Обновляем скрытое поле с актуальной ценой
                    document.getElementById('actualPrice').value = newPrice;
                }
            })
            .catch(error => {
                // Скрываем оверлей загрузки в случае ошибки
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
                console.error('Error checking price:', error);
            });
    }

    // Загружаем информацию о рейсе при загрузке страницы
    loadFlightDetails();
    
    // Запускаем первую проверку цены с задержкой в 3 секунды,
    // чтобы сначала загрузилась информация о рейсе
    setTimeout(checkCurrentPrice, 3000);

    // Устанавливаем интервал для периодической проверки
    priceCheckTimer = setInterval(checkCurrentPrice, priceCheckInterval);
    
    // Валидация формы перед отправкой
    document.getElementById('bookingForm').addEventListener('submit', function(e) {
        // Проверяем заполнение всех обязательных полей
        const requiredFields = document.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Проверяем валидность email
        const emailField = document.getElementById('contactEmail');
        if (emailField && emailField.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailField.value)) {
                isValid = false;
                emailField.classList.add('is-invalid');
                document.getElementById('emailFeedback').textContent = 'Пожалуйста, введите корректный email';
            }
        }
        
        // Проверяем валидность телефона
        const phoneField = document.getElementById('contactPhone');
        if (phoneField && phoneField.value) {
            const phoneRegex = /^[+]?[\d\s()-]{10,20}$/;
            if (!phoneRegex.test(phoneField.value)) {
                isValid = false;
                phoneField.classList.add('is-invalid');
                document.getElementById('phoneFeedback').textContent = 'Пожалуйста, введите корректный номер телефона';
            }
        }
        
        // Если форма не валидна, предотвращаем отправку
        if (!isValid) {
            e.preventDefault();
            // Прокручиваем к первому невалидному полю
            const firstInvalid = document.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
        } else {
            // Показываем загрузчик при отправке формы
            document.getElementById('loadingOverlay').style.display = 'flex';
        }
    });
    
    // Очищаем интервал при уходе со страницы
    window.addEventListener('beforeunload', function() {
        clearInterval(priceCheckTimer);
    });
    
    // Обработчики для полей формы (удаление класса is-invalid при вводе)
    document.querySelectorAll('input, select').forEach(element => {
        element.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    });
    
    // Обработчик для кнопки "Продолжить с новой ценой"
    document.getElementById('acceptNewPrice').addEventListener('click', function() {
        priceAlertElement.classList.add('d-none');
    });
});
