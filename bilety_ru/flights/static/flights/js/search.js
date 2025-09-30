// Функция для автозаполнения полей поиска аэропортов
/*
class FlightSearch {
    constructor() {
        this.origin = document.getElementById('id_originLocationCode');
        this.destination = document.getElementById('id_destinationLocationCode');
        this.departureDate = document.getElementById('id_departureDate');
        this.returnDate = document.getElementById('id_returnDate');
        this.departurePrices = document.getElementById('departure-prices');
        this.returnPrices = document.getElementById('return-prices');
        this.flightData = {
            'origin': null,
            'destination': null
        }
        this.initEventListeners();
    }

    initEventListeners() {
        // Запрос цен при фокусе на поле даты вылета
        this.departureDate.addEventListener('focus', () => {
            this.fetchPrices('departure');
        });

        // Запрос цен при фокусе на поле даты возвращения
        this.returnDate.addEventListener('focus', () => {
            this.fetchPrices('return');
        });

        // Обновление цен при изменении городов
        this.origin.addEventListener('change', this.clearPrices.bind(this));
        this.destination.addEventListener('change', this.clearPrices.bind(this));
    }

    async fetchPrices(type) {
        const origin = this.origin.value.trim();
        const destination = this.destination.value.trim();
        const response = {};

        if (!origin || !destination) {
            this.showMessage('Введите города вылета и прилета', type);
            return;
        }

        const requestData = {
            origin: origin,
            destination: destination
        };

        // Добавляем дату только если она выбрана
        if (type === 'departure' && this.departureDate.value) {
            requestData.departure_date = this.departureDate.value;
        } else if (type === 'return' && this.returnDate.value) {
            requestData.return_date = this.returnDate.value;
        }
        
        
        try {
            this.showLoading(type);

            
            $.ajax({
                url: `/api/flight-prices/?origin=${requestData.origin}&destination=${requestData.destination}`,
                type: 'GET',
                dataType: 'json',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }  
            })
            .done(function(data){
                console.log(data.origin, data.destination);
                response.origin = data.origin;
                response.destination = data.destination;
                console.log(response);

                const container = type === 'departure' ? this.departurePrices : this.returnPrices;
                //console.log(flights)
                if (response.length === 0) {
                    container.innerHTML = '<div class="price-item">Рейсов не найдено</div>';
                    return;
                }
                let html = '<div class="prices-container">';
                
                response.forEach(flight => {
                    const departure = flight.itineraries[0];
                    const price = flight.price;
                    
                    html += `
                        <div class="price-item">
                            <div class="price">${price.total} ${price.currency}</div>
                            <div class="route">${departure.segments[0].departure_airport} → ${departure.segments[0].arrival_airport}</div>
                            <div class="time">${formatTime(departure.segments[0].departure_time)}</div>
                        </div>
                    `;
                });
                
                html += '</div>';
                container.innerHTML = html;
            })
            
            //console.log(data)
            //this.displayPrices(data, type);

            const response = await fetch('/api/flight-prices/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (response.ok) {
                this.displayPrices(data, type);
            } else {
                this.showMessage(`Ошибка: ${data.error}`, type);
            }
                
        } catch (error) {
            this.showMessage('Ошибка соединения', type);
            console.error('Error:', error);
        }
    }

    displayPrices(flights, type) {
        const container = type === 'departure' ? this.departurePrices : this.returnPrices;
        //console.log(flights)
        if (flights.length === 0) {
            container.innerHTML = '<div class="price-item">Рейсов не найдено</div>';
            return;
        }

        let html = '<div class="prices-container">';
        
        flights.forEach(flight => {
            const departure = flight.itineraries[0];
            const price = flight.price;
            
            html += `
                <div class="price-item">
                    <div class="price">${price.total} ${price.currency}</div>
                    <div class="route">${departure.segments[0].departure_airport} → ${departure.segments[0].arrival_airport}</div>
                    <div class="time">${this.formatTime(departure.segments[0].departure_time)}</div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    showMessage(message, type) {
        const container = type === 'departure' ? this.departurePrices : this.returnPrices;
        container.innerHTML = `<div class="message">${message}</div>`;
    }

    showLoading(type) {
        const container = type === 'departure' ? this.departurePrices : this.returnPrices;
        container.innerHTML = '<div class="loading">Поиск цен...</div>';
    }

    clearPrices() {
        this.departurePrices.innerHTML = '';
        this.returnPrices.innerHTML = '';
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}
*/
document.addEventListener('DOMContentLoaded', function() {
    //new FlightSearch();
    const originInput = document.getElementById('id_originLocationCode');
    const destinationInput = document.getElementById('id_destinationLocationCode');
    const originList = document.getElementById('originList');
    const destinationList = document.getElementById('destinationList');
    
    // Функция для поиска аэропортов
    function searchAirports(query, resultsList) {
        if (query.length < 2) {
            resultsList.innerHTML = '';
            return;
        }
        
        // Отображаем индикатор загрузки
        const loadingItem = document.createElement('div');
        loadingItem.textContent = 'Поиск аэропортов...';
        loadingItem.className = 'loading-item';
        resultsList.innerHTML = '';
        resultsList.appendChild(loadingItem);
        
        // Используем правильный URL для API поиска аэропортов и jQuery AJAX
        $.ajax({
            url: `/api/airports/?keyword=${encodeURIComponent(query)}`,
            type: 'GET',
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .done(function(data) {
            resultsList.innerHTML = '';

            if (!data.success) {
                console.error('Error:', data.error);
                const errorItem = document.createElement('div');
                errorItem.textContent = 'Ошибка поиска аэропортов';
                errorItem.className = 'error-item';
                resultsList.appendChild(errorItem);
                return;
            }
            
            if (data.airports && data.airports.length > 0) {
                data.airports.forEach(airport => {
                    const item = document.createElement('div');
                    item.className = 'airport-item';
                    const cityInfo = airport.cityName ? `${airport.cityName}, ` : '';
                    item.innerHTML = `<strong>${airport.iataCode}</strong> - ${cityInfo}`;
                    
                    item.addEventListener('click', function() {
                        if (resultsList === originList) {
                            originInput.value = airport.iataCode;
                        } else {
                            destinationInput.value = airport.iataCode;
                        }
                        resultsList.innerHTML = '';
                    });
                    resultsList.appendChild(item);
                });
            } else {
                const item = document.createElement('div');
                item.textContent = 'Аэропорты не найдены';
                item.className = 'no-results';
                resultsList.appendChild(item);
            }
        })
        .fail(function(error) {
            console.error('Error:', error);
            resultsList.innerHTML = '';
            const errorItem = document.createElement('div');
            errorItem.textContent = 'Ошибка соединения с сервером';
            errorItem.className = 'error-item';
            resultsList.appendChild(errorItem);
        });
    }
    
    // Обработчики событий для полей ввода
    if (originInput) {
        originInput.addEventListener('input', function() {
            searchAirports(this.value, originList);
        });
    }
    
    if (destinationInput) {
        destinationInput.addEventListener('input', function() {
            searchAirports(this.value, destinationList);
        });
    }
    
    // Скрытие списков при клике вне полей
    document.addEventListener('click', function(event) {
        if (!originInput.contains(event.target) && !originList.contains(event.target)) {
            originList.innerHTML = '';
        }
        if (!destinationInput.contains(event.target) && !destinationList.contains(event.target)) {
            destinationList.innerHTML = '';
        }
    });
    
    // Функциональность для блока параметров сортировки
    const toggleSortingBtn = document.getElementById('toggleSortingOptions');
    const sortingBody = document.getElementById('sortingBody');
    const applySortingBtn = document.getElementById('applySorting');
    const resetSortingBtn = document.getElementById('resetSorting');
    
    if (toggleSortingBtn && sortingBody) {
        toggleSortingBtn.addEventListener('click', function() {
            if (sortingBody.classList.contains('active')) {
                sortingBody.classList.remove('active');
                toggleSortingBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Показать опции';
            } else {
                sortingBody.classList.add('active');
                toggleSortingBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Скрыть опции';
            }
        });
    }
    
    // Обработчик применения параметров сортировки
    if (applySortingBtn) {
        applySortingBtn.addEventListener('click', function() {
            // Получаем значения параметров сортировки
            const sortBy = document.getElementById('sortBy').value;
            const maxPrice = document.getElementById('maxPrice').value;
            const maxStops = document.getElementById('maxStops').value;
            const airlinesSelect = document.getElementById('airlines');
            const selectedAirlines = Array.from(airlinesSelect.selectedOptions).map(option => option.value);
            
            // Здесь будет логика применения сортировки к результатам
            console.log('Применяем сортировку:', {
                sortBy,
                maxPrice,
                maxStops,
                selectedAirlines
            });
            
            // Пример сортировки результатов (в реальном приложении нужно реализовать полноценную логику)
            sortFlightResults(sortBy, maxPrice, maxStops, selectedAirlines);
        });
    }
    
    // Обработчик сброса параметров сортировки
    if (resetSortingBtn) {
        resetSortingBtn.addEventListener('click', function() {
            // Сбрасываем значения формы сортировки
            document.getElementById('sortingForm').reset();
            
            // Возвращаем исходную сортировку результатов
            console.log('Сбрасываем параметры сортировки');
            resetSortingResults();
        });
    }
    
    // Функция для сортировки результатов поиска
    function sortFlightResults(sortBy, maxPrice, maxStops, selectedAirlines) {
        const flightResults = document.getElementById('flightResults');
        if (!flightResults) return;
        
        const flightCards = Array.from(flightResults.querySelectorAll('.flight-card'));
        
        // Сортировка по выбранному критерию
        flightCards.sort((a, b) => {
            // Получаем данные для сортировки
            const priceA = parseFloat(a.querySelector('.flight-price').textContent.trim().split(' ')[0]);
            const priceB = parseFloat(b.querySelector('.flight-price').textContent.trim().split(' ')[0]);
            
            // Сортировка по цене
            if (sortBy === 'price_asc') {
                return priceA - priceB;
            } else if (sortBy === 'price_desc') {
                return priceB - priceA;
            }
            
            // Здесь можно добавить другие критерии сортировки
            // Например, по длительности, времени вылета и т.д.
            
            return 0;
        });
        
        // Фильтрация по максимальной цене
        let filteredCards = flightCards;
        if (maxPrice && maxPrice > 0) {
            filteredCards = filteredCards.filter(card => {
                const price = parseFloat(card.querySelector('.flight-price').textContent.trim().split(' ')[0]);
                return price <= maxPrice;
            });
        }
        
        // Очищаем и добавляем отсортированные карточки
        flightResults.innerHTML = '';
        filteredCards.forEach(card => {
            flightResults.appendChild(card);
        });
        
        // Если нет результатов после фильтрации
        if (filteredCards.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'col-12 text-center my-4';
            noResults.innerHTML = '<p class="text-muted">Нет результатов, соответствующих выбранным параметрам</p>';
            flightResults.appendChild(noResults);
        }
    }
    
    // Функция для сброса сортировки
    function resetSortingResults() {
        // В реальном приложении здесь можно восстановить исходный порядок результатов
        // или перезагрузить их с сервера
        location.reload(); // Временное решение - перезагрузка страницы
    }
});
