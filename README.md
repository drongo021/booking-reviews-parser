# Booking.com Review Parser

Flask backend API для парсинга последних 10 отзывов из Booking.com с использованием Selenium.

## Технологии

- **Flask 3.0.0** - веб-фреймворк
- **Selenium 4.15.2** - автоматизация браузера
- **Gunicorn** - WSGI сервер для production
- **Docker** - контейнеризация

## Структура проекта

```
booking-reviews-parser/
├── app.py                 # Главное Flask приложение
├── scrapers/
│   ├── __init__.py
│   └── booking_reviews.py # Парсер Booking.com
├── requirements.txt
├── .env.example           # Пример переменных окружения
├── .gitignore
├── Dockerfile             # Для Railway deployment
├── Procfile              # Для Railway
└── railway.json          # Railway конфигурация
```

## Установка и запуск

### Локальная разработка

1. Клонировать репозиторий
2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Создать `.env` файл (скопировать из `.env.example`)

4. Запустить приложение:
```bash
python app.py
```

### Docker

```bash
docker build -t booking-parser .
docker run -p 5000:5000 booking-parser
```

## API Endpoints

### POST /api/parse-reviews

Парсит последние 10 отзывов из Booking.com

**Request:**
```json
{
  "booking_url": "https://www.booking.com/hotel/ae/rove-trade-centre.ru.html",
  "hotel_id": "hotel-1"
}
```

**Response:**
```json
{
  "status": "success",
  "reviews_found": 10,
  "reviews": [
    {
      "text": "Отличный отель, чисто, уютно...",
      "rating": 9.0,
      "author": "Иван",
      "country": "Russia",
      "date": "December 2025",
      "room_type": "Standard Double Room",
      "stay_duration": "2 nights"
    }
  ]
}
```

### GET /health

Health check endpoint

### GET /

Информация о сервисе

## Деплой на Railway

1. Создать новый проект на Railway
2. Подключить GitHub репозиторий
3. Railway автоматически обнаружит Dockerfile и задеплоит приложение
4. Переменные окружения настраиваются автоматически (PORT устанавливается Railway)

## Тестирование

```bash
# Локальное тестирование
curl -X POST http://localhost:5000/api/parse-reviews \
  -H "Content-Type: application/json" \
  -d '{"booking_url": "https://www.booking.com/hotel/ae/rove-trade-centre.ru.html"}'
```

## Важные замечания

- Парсер извлекает ровно 10 последних отзывов
- Используется headless Chrome для парсинга
- Обрабатываются cookie баннеры и модальные окна
- Поддерживается lazy loading отзывов

