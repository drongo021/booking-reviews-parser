"""
Booking.com Reviews Parser
Парсит последние отзывы из Booking.com используя Selenium
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import platform
import time
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def _setup_driver():
    """Настройка Selenium WebDriver с headless Chrome"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Определение ОС
    is_windows = platform.system() == 'Windows'
    
    # Использовать Chrome binary из env или системный (только для Linux)
    chrome_binary = os.getenv('CHROME_BINARY')
    if chrome_binary and os.path.exists(chrome_binary):
        options.binary_location = chrome_binary
        logger.info(f"Using Chrome binary from env: {chrome_binary}")
    elif not is_windows:
        # Для Linux по умолчанию
        default_chrome = '/usr/bin/chromium'
        if os.path.exists(default_chrome):
            options.binary_location = default_chrome
            logger.info(f"Using default Chrome binary: {default_chrome}")
    
    # ChromeDriver - webdriver-manager автоматически скачает и установит драйвер
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
    if chromedriver_path and os.path.exists(chromedriver_path):
        logger.info(f"Using ChromeDriver from env: {chromedriver_path}")
        service = Service(chromedriver_path)
    else:
        logger.info("Installing ChromeDriver via webdriver-manager...")
        try:
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver installed at: {driver_path}")
            service = Service(driver_path)
        except Exception as e:
            logger.error(f"Error installing ChromeDriver: {e}")
            raise Exception(f"Не удалось установить ChromeDriver. Убедитесь, что Chrome установлен на вашей системе. Ошибка: {e}")
    
    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Error initializing Chrome WebDriver: {e}")
        if is_windows:
            raise Exception(f"Не удалось запустить Chrome. Убедитесь, что Google Chrome установлен на вашей системе. Ошибка: {e}")
        else:
            raise


def _close_cookie_banner(driver):
    """Закрывает cookie баннер если он есть"""
    try:
        cookie_selectors = [
            "button[id*='onetrust']",
            "button[class*='cookie']",
            "button[id*='cookie']",
            "#onetrust-accept-btn-handler",
            "button[aria-label*='Accept']",
            "button[aria-label*='Принять']",
            "button:contains('Accept')",
            "button:contains('Принять')"
        ]
        for selector in cookie_selectors:
            try:
                cookie_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if cookie_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", cookie_btn)
                    time.sleep(1)
                    logger.info("Cookie banner closed")
                    break
            except:
                continue
    except Exception as e:
        logger.debug(f"Cookie banner not found or error: {e}")


def _navigate_to_reviews(driver, booking_url):
    """Навигация к разделу отзывов"""
    try:
        # Попытка перейти напрямую на вкладку отзывов
        reviews_url = booking_url.split('#')[0] + '#tab-reviews'
        driver.get(reviews_url)
        time.sleep(3)
        logger.info("Navigated to reviews tab")
    except Exception as e:
        logger.warning(f"Could not navigate to reviews tab directly: {e}")
    
    # Попытка найти и кликнуть на ссылку "Reviews"
    try:
        reviews_selectors = [
            "a[href*='reviews']",
            "a[href*='#tab-reviews']",
            "button[data-tab='reviews']",
            "a:contains('Reviews')",
            "a:contains('Отзывы')"
        ]
        for selector in reviews_selectors:
            try:
                reviews_link = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].scrollIntoView(true);", reviews_link)
                driver.execute_script("arguments[0].click();", reviews_link)
                time.sleep(3)
                logger.info("Clicked on reviews link")
                break
            except:
                continue
    except Exception as e:
        logger.debug(f"Could not click reviews link: {e}")


def _find_review_elements(driver):
    """Находит элементы отзывов используя различные селекторы"""
    review_selectors = [
        "div[data-testid='review']",
        "div[data-testid='review-item']",
        "div.review-item",
        "div.c-review",
        "div[class*='review']",
        "div[class*='Review']",
        "article[data-testid='review']",
        "li[data-testid='review']",
        "div.review_list_item",
        "div.review_item",
        "div.review-block",
        "div.review-item-block",
        "div[itemprop='review']",
        "div.review_body",
    ]
    
    for selector in review_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0:
                logger.info(f"Found {len(elements)} reviews using selector: {selector}")
                return elements
        except:
            continue
    
    return []

def _scroll_to_load_reviews(driver, max_reviews):
    """Прокрутка страницы для загрузки отзывов (lazy loading)"""
    for i in range(8):  # Увеличили количество попыток
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Проверка, сколько отзывов загружено
        reviews = _find_review_elements(driver)
        if len(reviews) >= max_reviews:
            logger.info(f"Loaded {len(reviews)} reviews")
            break
        
        # Дополнительная прокрутка к элементу отзывов
        try:
            review_section_selectors = [
                "[data-testid='reviews']",
                "#review_list_page",
                ".review_list",
                "[id*='review']",
                "[class*='review-list']"
            ]
            for selector in review_section_selectors:
                try:
                    review_section = driver.find_element(By.CSS_SELECTOR, selector)
                    driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass


def _extract_review_data(review_element):
    """Извлекает данные из одного элемента отзыва"""
    review_data = {}
    
    # Текст отзыва
    try:
        text_selectors = [
            "span[data-testid='review-text']",
            "div[data-testid='review-text']",
            "p[class*='review']",
            "div[class*='review-text']",
            "span[class*='review']"
        ]
        for selector in text_selectors:
            try:
                text_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                text = text_elem.text.strip()
                if text:
                    review_data["text"] = text
                    break
            except:
                continue
        if "text" not in review_data:
            # Fallback: получить весь текст элемента
            review_data["text"] = review_element.text.strip()[:500]  # Ограничение длины
    except Exception as e:
        logger.debug(f"Error extracting text: {e}")
        review_data["text"] = ""
    
    # Рейтинг
    try:
        rating_selectors = [
            "[class*='rating']",
            "[class*='score']",
            "[data-testid*='rating']",
            "[aria-label*='rating']"
        ]
        for selector in rating_selectors:
            try:
                rating_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                # Извлечь число из текста (например, "9.0" из "9.0 Excellent")
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating_value = float(rating_match.group(1))
                    # Нормализация рейтинга (если это 5-балльная система, конвертируем в 10-балльную)
                    if rating_value <= 5:
                        rating_value = rating_value * 2
                    review_data["rating"] = rating_value
                    break
            except:
                continue
        # Альтернативный способ: поиск в aria-label
        if "rating" not in review_data:
            try:
                rating_attr = review_element.get_attribute("aria-label")
                if rating_attr:
                    rating_match = re.search(r'(\d+\.?\d*)', rating_attr)
                    if rating_match:
                        rating_value = float(rating_match.group(1))
                        if rating_value <= 5:
                            rating_value = rating_value * 2
                        review_data["rating"] = rating_value
            except:
                pass
    except Exception as e:
        logger.debug(f"Error extracting rating: {e}")
        review_data["rating"] = None
    
    # Автор
    try:
        author_selectors = [
            "[class*='name']",
            "[class*='author']",
            "[data-testid*='author']",
            "span[class*='reviewer']"
        ]
        for selector in author_selectors:
            try:
                author_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                author_text = author_elem.text.strip()
                if author_text and len(author_text) < 100:  # Фильтр слишком длинных текстов
                    review_data["author"] = author_text
                    break
            except:
                continue
    except Exception as e:
        logger.debug(f"Error extracting author: {e}")
        review_data["author"] = ""
    
    # Страна
    try:
        country_selectors = [
            "[class*='country']",
            "[data-testid*='country']",
            "span[title*='country']"
        ]
        for selector in country_selectors:
            try:
                country_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                country_text = country_elem.text.strip()
                if country_text:
                    review_data["country"] = country_text
                    break
            except:
                continue
    except Exception as e:
        logger.debug(f"Error extracting country: {e}")
        review_data["country"] = ""
    
    # Дата
    try:
        date_selectors = [
            "[class*='date']",
            "[data-testid*='date']",
            "time",
            "span[class*='review-date']"
        ]
        for selector in date_selectors:
            try:
                date_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                date_text = date_elem.text.strip()
                if date_text:
                    review_data["date"] = date_text
                    break
            except:
                continue
        # Альтернативный способ: поиск в datetime атрибуте
        if "date" not in review_data:
            try:
                date_attr = review_element.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
                if date_attr:
                    review_data["date"] = date_attr
            except:
                pass
    except Exception as e:
        logger.debug(f"Error extracting date: {e}")
        review_data["date"] = ""
    
    # Тип номера
    try:
        room_type_selectors = [
            "[class*='room']",
            "[class*='accommodation']",
            "[data-testid*='room']"
        ]
        for selector in room_type_selectors:
            try:
                room_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                room_text = room_elem.text.strip()
                if room_text and "room" in room_text.lower():
                    review_data["room_type"] = room_text
                    break
            except:
                continue
    except Exception as e:
        logger.debug(f"Error extracting room_type: {e}")
        review_data["room_type"] = ""
    
    # Длительность проживания
    try:
        duration_selectors = [
            "[class*='stay']",
            "[class*='duration']",
            "[class*='nights']"
        ]
        for selector in duration_selectors:
            try:
                duration_elem = review_element.find_element(By.CSS_SELECTOR, selector)
                duration_text = duration_elem.text.strip()
                if duration_text:
                    review_data["stay_duration"] = duration_text
                    break
            except:
                continue
    except Exception as e:
        logger.debug(f"Error extracting stay_duration: {e}")
        review_data["stay_duration"] = ""
    
    return review_data


def parse_booking_reviews(booking_url: str, max_reviews: int = 10) -> List[Dict]:
    """
    Парсит отзывы из Booking.com
    
    Args:
        booking_url: URL страницы отеля на Booking.com
        max_reviews: Максимальное количество отзывов (по умолчанию 10)
    
    Returns:
        Список словарей с данными отзывов
    """
    driver = None
    try:
        logger.info(f"Starting to parse reviews from: {booking_url}")
        driver = _setup_driver()
        driver.get(booking_url)
        time.sleep(5)  # Увеличили время ожидания
        
        # Закрыть cookie баннер
        _close_cookie_banner(driver)
        time.sleep(2)
        
        # Перейти к отзывам
        _navigate_to_reviews(driver, booking_url)
        
        # Дополнительное ожидание после навигации
        time.sleep(3)
        
        # Прокрутить для загрузки
        _scroll_to_load_reviews(driver, max_reviews)
        
        # Найти все отзывы используя различные селекторы
        review_elements = _find_review_elements(driver)
        logger.info(f"Found {len(review_elements)} review elements")
        
        # Если отзывы не найдены, попробуем найти любые элементы с текстом отзывов
        if len(review_elements) == 0:
            logger.warning("No reviews found with standard selectors, trying alternative approach...")
            try:
                # Попробуем найти элементы по классам, содержащим "review"
                all_review_candidates = driver.find_elements(By.XPATH, "//div[contains(@class, 'review') or contains(@class, 'Review')]")
                logger.info(f"Found {len(all_review_candidates)} candidate elements with 'review' in class")
                if len(all_review_candidates) > 0:
                    review_elements = all_review_candidates[:max_reviews * 3]  # Берем больше кандидатов
            except Exception as e:
                logger.debug(f"Alternative search failed: {e}")
        
        reviews = []
        for idx, elem in enumerate(review_elements[:max_reviews * 2]):  # Берем больше, чтобы отфильтровать пустые
            try:
                review_data = _extract_review_data(elem)
                if review_data.get("text") and len(review_data.get("text", "")) > 10:  # Только если есть текст
                    reviews.append(review_data)
                    if len(reviews) >= max_reviews:
                        break
            except Exception as e:
                logger.debug(f"Error extracting review {idx}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(reviews)} reviews")
        return reviews[:max_reviews]
        
    except Exception as e:
        logger.error(f"Error parsing Booking.com reviews: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed")

