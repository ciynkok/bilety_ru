import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import os
from datetime import datetime
from typing import List, Dict, Optional

class FlightBookingEmailSender:
    def __init__(self):
        # Настройки SMTP для разных почтовых сервисов
        self.smtp_settings = {
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587
            },
            'mail_ru': {
                'server': 'smtp.mail.ru',
                'port': 587
            },
            'yandex': {
                'server': 'smtp.yandex.ru',
                'port': 587
            }
        }
    
    def _get_smtp_config(self, email: str) -> Dict:
        """Определяем SMTP сервер по домену email"""
        if 'gmail.com' in email:
            return self.smtp_settings['gmail']
        elif 'mail.ru' in email or 'bk.ru' in email or 'inbox.ru' in email:
            return self.smtp_settings['mail_ru']
        elif 'yandex.ru' in email or 'yandex.com' in email:
            return self.smtp_settings['yandex']
        else:
            # По умолчанию используем Gmail
            return self.smtp_settings['gmail']
    
    def _create_booking_html_template(self, booking_data: Dict) -> str: 
        # Генерация HTML для каждого пассажира
        passengers_html = ""
        for i, passenger in enumerate(booking_data['passenger_data']['passengers'], 1):
            passengers_html += f"""
            <div class="passenger-card">
                <h4>👤 Пассажир {i}</h4>
                <table>
                    <tr>
                        <th>ФИО</th>
                        <td>{passenger['firstName']} {passenger['lastName']} {passenger['surname']}</td>
                    </tr>
                    <tr>
                        <th>Тип пассажира</th>
                        <td>{passenger['type']}</td>
                    </tr>
                </table>
            </div>
            """
        
        # Генерация информации о стоимости
        #total_price = sum(float(passenger['price'].replace(' ', '')) for passenger in booking_data['passengers'])
        html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Подтверждение бронирования авиабилетов</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 700px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
                text-align: center;
                margin: -30px -30px 20px -30px;
            }}
            .booking-number {{
                background: #ffc107;
                color: #333;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }}
            .flight-info {{
                background: #f8f9fa;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 5px 5px 0;
            }}
            .passengers-section {{
                margin: 25px 0;
            }}
            .passenger-card {{
                background: #e8f5e8;
                border: 1px solid #28a745;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .passenger-card h4 {{
                margin-top: 0;
                color: #155724;
            }}
            .price-summary {{
                background: #fff3cd;
                border: 2px solid #ffc107;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .price-breakdown {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }}
            .qr-code {{
                text-align: center;
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
            .important {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th, td {{
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background: rgba(0,0,0,0.05);
                font-weight: 600;
            }}
            .total-price {{
                font-size: 1.3em;
                font-weight: bold;
                color: #d63384;
                text-align: center;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .segment-divider {{
                border-left: 3px dashed #007bff;
                height: 40px;
                margin: 10px 0 10px 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✈️ Подтверждение бронирования</h1>
                <div class="booking-number">Номер бронирования: {booking_data['order_id']}</div>
                <p>Количество пассажиров: {len(booking_data['passenger_data']['passengers'])}</p>
            </div>
            
            <!-- Информация о рейсе -->
            <div class="flight-info">
                <h3>📅 Информация о рейсе</h3>
                <table>
                    <tr>
                        <th>Маршрут</th>
                        <td>{booking_data['departure_city']} → {booking_data['arrival_city']}</td>
                    </tr>
                    <tr>
                        <th>Авиакомпания</th>
                        <td>{booking_data['airline']}</td>
                    </tr>
                    <tr>
                        <th>Номер самолёта</th>
                        <td>{booking_data['flight_number']}</td>
                    </tr>
                    <tr>
                        <th>Терминал</th>
                        <td>{booking_data['terminal']}</td>
                    </tr>
                    <tr>
                        <th>Дата вылета</th>
                        <td>{booking_data['departure_date'].strftime('%Y-%m-%d')} в {booking_data['departure_date'].strftime('%H:%m')}</td>
                    </tr>
                    <tr>
                        <th>Дата прибытия</th>
                        <td>{booking_data['arrival_date'].strftime('%Y-%m-%d')} в {booking_data['arrival_date'].strftime('%H:%m')}</td>
                    </tr>
                    {f"<tr><th>Обратный рейс</th><td>{booking_data['r_departure_date'].strftime('%Y-%m-%d')} в {booking_data['r_departure_date'].strftime('%H:%m')}</td></tr>" if 'r_departure_date' in booking_data else ""}
                </table>
            </div>
            
            <!-- Секция с пассажирами -->
            <div class="passengers-section">
                <h3>👥 Информация о пассажирах</h3>
                {passengers_html}
            </div>
            
            <div class="important">
                <h3>⚠️ Важная информация бронирования</h3>
                <ul>
                    <li>Все пассажиры должны прибыть в аэропорт за 2.5 часа до вылета</li>
                    <li>При регистрации предъявите этот документ и удостоверения личности всех пассажиров</li>
                    <li>Регистрация группы заканчивается за 50 минут до вылета</li>
                    <li>Рекомендуем пройти онлайн-регистрацию за 24 часа до вылета</li>
                    <li>Места пассажиров будут расположены рядом, где это возможно</li>
                </ul>
            </div>
            
            <p>Спасибо, что выбрали наш сервис! Желаем приятного полета! ✈️</p>
        </div>
    </body>
    </html>
        """
        return html_template
    
    def _create_plain_text_template(self, booking_data: Dict) -> str:
        """Создание текстовой версии письма"""
        passengers_text = ""
        for i, passenger in enumerate(booking_data['passenger_data']['passengers'], 1):
            passengers_text += f"""
Пассажир {i}:
  ФИО: {passenger['firstName']} {passenger['lastName']} {passenger['surname']}
  Тип: {passenger['type']}
"""

        text_template = f"""
ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ АВИАБИЛЕТА

Номер бронирования: {booking_data['id']}

Ваше бронирование успешно подтверждено!

ИНФОРМАЦИЯ О РЕЙСЕ:
Маршрут: {booking_data['departure_city']} → {booking_data['arrival_city']}
Авиакомпания: {booking_data['airline']} {booking_data['flight_number']}
Дата вылета: {booking_data['departure_date'].strftime('%Y-%m-%d')} в {booking_data['departure_date'].strftime('%H:%m')}
Дата прибытия: {booking_data['arrival_date'].strftime('%Y-%m-%d')} в {booking_data['arrival_date'].strftime('%H:%m')}

ИНФОРМАЦИЯ О ПАССАЖИРАХ:
{passengers_text}

ВАЖНАЯ ИНФОРМАЦИЯ:
- Прибывайте в аэропорт за 2 часа до вылета
- Имейте при себе документ, удостоверяющий личность
- Регистрация заканчивается за 40 минут до вылета

Спасибо, что выбрали наш сервис!
        """
        return text_template
    
    def send_booking_confirmation(self, 
                                sender_email: str,
                                sender_password: str,
                                recipient_email: str,
                                booking_data: Dict) -> bool:
        """
        Отправка письма с подтверждением бронирования
        
        Args:
            sender_email: Email отправителя
            sender_password: Пароль отправителя
            recipient_email: Email получателя
            booking_data: Данные о бронировании
        
        Returns:
            bool: Успешность отправки
        """
        
        try:
            # Получаем настройки SMTP
            print(1)
            smtp_config = self._get_smtp_config(sender_email)
            print(2)
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f'Подтверждение бронирования #{booking_data["id"]}'
            msg['Date'] = formatdate(localtime=True)
            
            # Добавляем текстовую и HTML версии
            print(3)
            text_part = MIMEText(self._create_plain_text_template(booking_data), 'plain', 'utf-8')
            print('11')
            html_part = MIMEText(self._create_booking_html_template(booking_data), 'html', 'utf-8')
            print(4)
            msg.attach(text_part)
            msg.attach(html_part)
            print(smtp_config)
            # Устанавливаем соединение и отправляем
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            print(6)
            server.starttls()
            print(7)
            server.login(sender_email, sender_password)
            print(8)
            server.send_message(msg)
            server.quit()
            
            print(f"Письмо с подтверждением бронирования #{booking_data['id']} отправлено на {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Ошибка при отправке письма: {e}")
            return False

# Создаем экземпляр класса для использования