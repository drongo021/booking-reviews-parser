"""
Flask Backend API для парсинга отзывов Booking.com
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from scrapers.booking_reviews import parse_booking_reviews
import logging
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/api/parse-reviews', methods=['POST'])
def parse_reviews():
    """
    POST /api/parse-reviews
    Парсит последние 10 отзывов из Booking.com
    
    Request body:
    {
        "booking_url": "https://www.booking.com/hotel/...",
        "hotel_id": "hotel-1"  // опционально
    }
    
    Response:
    {
        "status": "success",
        "reviews_found": 10,
        "reviews": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        booking_url = data.get('booking_url')
        hotel_id = data.get('hotel_id', 'unknown')
        
        if not booking_url:
            return jsonify({"error": "booking_url is required"}), 400
        
        # Валидация URL
        if not booking_url.startswith('https://www.booking.com'):
            return jsonify({"error": "Invalid booking.com URL"}), 400
        
        logger.info(f"Parsing reviews for hotel_id: {hotel_id}, URL: {booking_url}")
        
        # Парсинг отзывов
        reviews = parse_booking_reviews(booking_url, max_reviews=10)
        
        return jsonify({
            "status": "success",
            "reviews_found": len(reviews),
            "reviews": reviews
        })
        
    except Exception as e:
        logger.error(f"Error in parse_reviews endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "service": "Booking.com Reviews Parser",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/parse-reviews": "Parse reviews from Booking.com",
            "GET /health": "Health check"
        }
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

