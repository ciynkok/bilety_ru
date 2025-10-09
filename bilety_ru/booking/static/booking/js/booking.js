/**
 * booking.js - Скрипт для страницы бронирования билетов
 * Обрабатывает динамическое обновление цен и взаимодействие с формой бронирования
 */
let adults_count = document.getElementById('adults_count').value;
let childs_count = document.getElementById('children_count').value;
let infants_count = document.getElementById('infants_count').value;
const arr_n = [adults_count, childs_count, infants_count];
const types = ['adult', 'child', 'infant'];


for (let i = 0; i < 3; i++)
{
    console.log(arr_n[i])
    for (let j = 0; j < arr_n[i]; j++)
    {
        //console.log(j)
        let index = j + 1;
        console.log(`${types[i]}_${j}_document_type`)
        document.getElementById(`${types[i]}_${index}_document_type`).addEventListener('change', function() {
            showDynamicFields(this.value, i, index);
        });
    }
}

function showDynamicFields(selectedValue, i, j) {
    const dynamicFields = document.getElementById(`${types[i]}_${j}_document_data`);
    console.log(`${types[i]}_${j}_document_data`);
    // Очищаем предыдущие поля
    dynamicFields.innerHTML = '';
    
    // В зависимости от выбранного значения показываем соответствующие поля
    switch(selectedValue) {
        case 'PASSPORT':
            dynamicFields.innerHTML = `
                <label for="${types[i]}_${j}_document_number">Номер документа</label>
                <input type="text" class="form-control" id="${types[i]}_${j}_document_number" name="${types[i]}_${j}_document_number" required>
            `;
            break;
        
        case 'ID_CARD':
            dynamicFields.innerHTML = `
            <div class="col-md-4 form-group">
                <label for="${types[i]}_${j}_document_series">Серия</label>
                <input type="text" class="form-control" id="${types[i]}_${j}_document_series" name="${types[i]}_${j}_document_series" required style="width:10em;">
            </div>
            <div class="col-md-4 form-group">
                <label for="${types[i]}_${j}_two_letters">2 буквы</label>
                <input type="text" class="form-control" id="${types[i]}_${j}_two_letters" name="${types[i]}_${j}_two_letters" required>
            </div>
            <div class="col-md-4 form-group">
                <label for="child_{{ i }}_document_number">Номер документа</label>
                <input type="text" class="form-control" id="${types[i]}_${j}_document_number" name="${types[i]}_${j}_document_number" required style="width:10em;">
            </div>
            `;
            break;
        default:
            dynamicFields.innerHTML = ``
            break;
    }
}


document.addEventListener('DOMContentLoaded', function() {
    // Получаем ID предложения из URL
    const urlParts = window.location.pathname.split('/');
    const offerId = urlParts[urlParts.indexOf('booking') + 1];
    for (let i = 0; i < 3; i++)
    {
        for (let j = 0; j < arr_n[i]; j++)
        {
            let index = j + 1;
            const initalSelect = document.getElementById(`${types[i]}_${index}_document_type`)
            console.log(`${types[i]}_${index}_document_type`)
            showDynamicFields(initalSelect.value, i, index)
        }
    }
    
    // Элементы для обновления цены
    const totalPriceElement = document.getElementById('totalPrice');
    const originalPriceElement = document.getElementById('originalPrice');
    const priceDifferenceElement = document.getElementById('priceDifference');
    const priceAlertElement = document.getElementById('priceAlert');
    
    // Интервал проверки цены (каждые 60 секунд)
    const priceCheckInterval = 60000; // Увеличиваем до 60 секунд
    let priceCheckTimer;
    

    // Новая версия функции проверки актуальности цены
    function checkCurrentPrice(offerId) {
        fetch(`/api/check-price/${offerId}/`)
            .then(response => response.json())
            .then(data => {
                
                if (!data.success) {
                    // Обработка ошибки (например, показать alert)
                    console.log(data.error || 'Ошибка при проверке цены');
                    return;
                }
                // Получаем текущую цену из DOM
                const totalPriceElement = document.getElementById('totalPrice');
                const currentPriceText = totalPriceElement.textContent;
                const currentPrice = parseFloat(currentPriceText.replace(/[^0-9.]/g, ''));
                // Получаем новую цену из ответа API
                const newPrice = parseFloat(data.price);
                const currency = data.currency;
                //console.log(currentPriceText, currentPrice, newPrice, currency);

                if (newPrice !== currentPrice) {
                    // Обновляем цену на странице
                    totalPriceElement.textContent = `${newPrice} ${currency}`;
                    // Можно добавить уведомление о смене цены
                    alert(`Цена изменилась! Новая цена: ${newPrice} ${currency}`);
                }
            })
            .catch(error => {
                console.error('Ошибка при проверке цены:', error);
            });
    }

    // Загружаем информацию о рейсе при загрузке страницы
    console.log(1);
    //loadFlightDetails();
    console.log(2);
    // Запускаем первую проверку цены с задержкой в 3 секунды,
    // чтобы сначала загрузилась информация о рейсе
    //setTimeout(checkCurrentPrice(offerId), 3000);

    // Устанавливаем интервал для периодической проверки
    //priceCheckTimer = setInterval(checkCurrentPrice, priceCheckInterval);
    
    // Валидация формы перед отправкой
    /*
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
    /*
    document.getElementById('acceptNewPrice').addEventListener('click', function() {
        priceAlertElement.classList.add('d-none');
    });*/
});
