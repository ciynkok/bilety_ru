// Функция для автозаполнения полей поиска аэропортов
document.addEventListener('DOMContentLoaded', function() {
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
    /*
    // Функция для создания карточки рейса
    function createFlightCard(offer) {
        const card = document.createElement('div');
        card.className = 'col-md-6 mb-4';
        
        let segmentsHtml = '';
        offer.outbound.forEach(segment => {
            segmentsHtml += `
                <div class="flight-segment">
                    <div class="d-flex align-items-center">
                        <img src="${segment.airlineLogo || 'https://via.placeholder.com/30?text=' + segment.airline}" alt="${segment.airline}" class="airline-logo">
                        <div class="w-100">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${segment.departureDateTime.substr(11, 5)}</strong> 
                                    <span class="text-muted">${segment.departureAirport}</span>
                                </div>
                                <div class="flight-duration text-center">
                                    <div class="small text-muted">Длительность</div>
                                    <div>${segment.duration}</div>
                                </div>
                                <div class="text-right">
                                    <strong>${segment.arrivalDateTime.substr(11, 5)}</strong> 
                                    <span class="text-muted">${segment.arrivalAirport}</span>
                                </div>
                            </div>
                            <div class="progress mt-2" style="height: 2px;">
                                <div class="progress-bar bg-primary" role="progressbar" style="width: 100%"></div>
                            </div>
                            <div class="d-flex justify-content-between small text-muted mt-1">
                                <div>${segment.departureCity}</div>
                                <div>${segment.arrivalCity}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        card.innerHTML = `
            <div class="card flight-card h-100">
                <div class="flight-header d-flex justify-content-between align-items-center">
                    <div>
                        <span class="flight-price">${offer.totalPrice} ${offer.currencyCode}</span>
                    </div>
                    <div>
                        <span class="badge badge-info">Общее время: ${offer.duration}</span>
                    </div>
                </div>
                <div class="flight-body">
                    ${segmentsHtml}
                    <div class="text-center mt-3">
                        <a href="/booking/${offer.id}/" class="btn book-button">
                            <i class="fas fa-ticket-alt mr-2"></i>Оформить
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }
    */
    // Функция для получения CSRF-токена из cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Обработчик отправки формы поиска
    /*
    const searchForm = document.getElementById('cityForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            document.getElementById('loadingSpinner').style.display = 'block';
            
            const formData = new FormData(this);
            const csrftoken = getCookie('csrftoken');
            
            // Используем jQuery для отправки запроса, так как в базовом шаблоне мы настроили CSRF для jQuery
            $.ajax({
                url: '/',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .done(function(response) {
                // После успешной отправки формы запрашиваем данные о рейсах
                setTimeout(fetchFlightOffers, 1000); // Даем время на обработку запроса на сервере
            })
            .fail(function(error) {
                console.error('Error:', error);
                document.getElementById('loadingSpinner').style.display = 'none';
            });
        });
    }
    */
    // Проверяем, есть ли результаты поиска в сессии при загрузке страницы
    //if (document.getElementById('flightResults')) {
      //  fetchFlightOffers();
    //}
    
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
