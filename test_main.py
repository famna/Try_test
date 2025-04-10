import pytest
import logging
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from dotenv import load_dotenv

# Налаштування логування
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("test.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Створюємо директорію для скріншотів
os.makedirs("screenshots", exist_ok=True)

# Завантаження змінних середовища
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://the-internet.herokuapp.com")
TEST_USER = os.getenv("TEST_USER", "tomsmith")
TEST_PASS = os.getenv("TEST_PASS", "SuperSecretPassword!")

@pytest.fixture(scope="class", params=["chrome", "firefox"])
def setup_driver(request):
    """Фікстура для ініціалізації драйвера"""
    logger.info(f"Ініціалізація {request.param}...")
    
    if request.param == "chrome":
        options = Options()
        # options.add_argument("--headless=new")  # Тимчасово відключено для налагодження
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        # Вимкнення виявлення витоку паролів
        options.add_argument("--password-store=basic")
        options.add_experimental_option("excludeSwitches", ["enable-password-leak-detection"])
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    else:
        options = FirefoxOptions()
        # options.add_argument("-headless")  # Тимчасово відключено для налагодження
        driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=options
        )
    
    driver.implicitly_wait(5)
    driver.get(BASE_URL)
    yield driver
    driver.quit()
    logger.info(f"Драйвер {request.param} закрито")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Хук для скріншотів при падінні тестів"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.failed:
        driver = item.funcargs.get("setup_driver")
        if driver:
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{item.name}_failed.png")
            driver.save_screenshot(screenshot_path)
            logger.error(f"Скріншот збережено: {screenshot_path}")

class TestLogin:
    @pytest.mark.flaky(reruns=2, reruns_delay=1)
    @pytest.mark.parametrize("username, password, expected", [
        (TEST_USER, TEST_PASS, "You logged into a secure area!"),
        ("invalid", "invalid", "Your username is invalid!")
    ])
    def test_login(self, setup_driver, username, password, expected):
        """Тест авторизації з явним очікуванням"""
        logger.info(f"Тестування логіну з користувачем: {username}")
        setup_driver.get(f"{BASE_URL}/login")
        
        # Скріншот перед спробою логіну
        screenshot_path = f"screenshots/before_login_{username}.png"
        setup_driver.save_screenshot(screenshot_path)
        logger.info(f"Скріншот перед логіном збережено: {screenshot_path}")
        
        # Заповнення форми
        setup_driver.find_element(By.ID, "username").send_keys(username)
        setup_driver.find_element(By.ID, "password").send_keys(password)
        setup_driver.find_element(By.CSS_SELECTOR, "button.radius").click()

        # Скріншот після спроби логіну
        screenshot_path = f"screenshots/after_login_{username}.png"
        setup_driver.save_screenshot(screenshot_path)
        logger.info(f"Скріншот після логіну збережено: {screenshot_path}")

        # Чекаємо повідомлення або зміни URL
        try:
            WebDriverWait(setup_driver, 15).until(
                EC.any_of(
                    EC.url_contains("/secure"),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.flash"))
                )
            )
            
            # Логуємо поточну URL для налагодження
            logger.info(f"Поточна URL після логіну: {setup_driver.current_url}")
            
            if "invalid" in username:
                message = setup_driver.find_element(By.CSS_SELECTOR, "div.flash.error")
            else:
                message = setup_driver.find_element(By.CSS_SELECTOR, "div.flash.success")
            
            logger.info(f"Отримано повідомлення: {message.text}")
            assert expected in message.text
            
        except Exception as e:
            logger.error(f"Помилка при авторизації: {str(e)}")
            logger.error(f"Поточна URL: {setup_driver.current_url}")
            logger.error(f"HTML сторінки:\n{setup_driver.page_source[:500]}...")  # Логуємо лише перші 500 символів
            raise

    def test_logout(self, setup_driver):
        """Тест виходу з системи"""
        logger.info("Тестування виходу з системи")
        setup_driver.get(f"{BASE_URL}/login")
        
        # Логін
        setup_driver.find_element(By.ID, "username").send_keys(TEST_USER)
        setup_driver.find_element(By.ID, "password").send_keys(TEST_PASS)
        setup_driver.find_element(By.CSS_SELECTOR, "button.radius").click()
        
        # Перевірка успішного входу
        WebDriverWait(setup_driver, 10).until(
            EC.url_contains("/secure")
        )
        
        # Переконуємося, що ми повністю увійшли перед продовженням
        login_message = WebDriverWait(setup_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.flash.success"))
        )
        assert "You logged into a secure area!" in login_message.text
        logger.info("Успішний вхід у систему")
        
        # Скріншот після успішного входу
        setup_driver.save_screenshot("screenshots/after_login_success.png")
        
        # Чекаємо момент перед натисканням кнопки виходу
        time.sleep(1)
        
        # Вихід - переконуємося, що знаходимо правильну кнопку виходу
        logout_button = WebDriverWait(setup_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button[href='/logout']"))
        )
        logger.info(f"Знайдено кнопку виходу: {logout_button.get_attribute('href')}")
        logout_button.click()
        
        # Скріншот після натискання кнопки виходу
        setup_driver.save_screenshot("screenshots/after_logout_click.png")
        
        # Чекаємо перенаправлення після виходу
        WebDriverWait(setup_driver, 10).until(
            EC.url_contains("/login")
        )
        
        # Перевірка повідомлення про вихід
        logout_message = WebDriverWait(setup_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.flash.success"))
        )
        
        logger.info(f"Текст повідомлення після виходу: {logout_message.text}")
        assert "You logged out of the secure area!" in logout_message.text
        logger.info("Успішний вихід із системи")

class TestFileUpload:
    def test_upload(self, setup_driver):
        """Тест завантаження файлу з перевіркою заголовка"""
        logger.info("Тестування завантаження файлу")
        temp_file = "test_file.txt"
        with open(temp_file, "w") as f:
            f.write("Тестовий вміст")
        
        try:
            setup_driver.get(f"{BASE_URL}/upload")
            
            # Скріншот перед завантаженням
            setup_driver.save_screenshot("screenshots/before_upload.png")
            
            # Завантаження файлу
            file_input = setup_driver.find_element(By.ID, "file-upload")
            file_input.send_keys(os.path.abspath(temp_file))
            setup_driver.find_element(By.ID, "file-submit").click()
            
            # Скріншот після завантаження
            setup_driver.save_screenshot("screenshots/after_upload.png")
            
            # Перевірка результату
            header = WebDriverWait(setup_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h3"))
            )
            assert "File Uploaded!" in header.text
            logger.info("Файл успішно завантажено")
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.info(f"Тимчасовий файл {temp_file} видалено")

class TestDynamicElements:
    def test_dynamic_loading(self, setup_driver):
        """Тест динамічного завантаження елементів"""
        logger.info("Тестування динамічного завантаження")
        setup_driver.get(f"{BASE_URL}/dynamic_loading/1")
        
        # Натискаємо кнопку Start
        setup_driver.find_element(By.CSS_SELECTOR, "div#start button").click()
        
        # Чекаємо поки елемент з'явиться
        text_element = WebDriverWait(setup_driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div#finish h4"))
        )
        
        assert "Hello World!" in text_element.text
        logger.info("Динамічний елемент успішно завантажено")
        
    def test_dynamic_controls(self, setup_driver):
        """Тест динамічних елементів керування"""
        logger.info("Тестування динамічних елементів керування")
        setup_driver.get(f"{BASE_URL}/dynamic_controls")
        
        # Видалення чекбокса
        setup_driver.find_element(By.CSS_SELECTOR, "button[onclick='swapCheckbox()']").click()
        
        # Чекаємо повідомлення про видалення
        message = WebDriverWait(setup_driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "p#message"))
        )
        
        assert "gone" in message.text.lower()
        logger.info("Чекбокс успішно видалено")
        
        # Додавання чекбокса назад
        setup_driver.find_element(By.CSS_SELECTOR, "button[onclick='swapCheckbox()']").click()
        
        # Чекаємо повідомлення про додавання
        message = WebDriverWait(setup_driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "p#message"))
        )
        
        assert "back" in message.text.lower()
        logger.info("Чекбокс успішно додано назад")

class TestAPI:
    def test_mocked_api(self, requests_mock):
        """Тест API з мокованим запитом"""
        logger.info("Тестування API з мокованим запитом")
        requests_mock.get("https://api.example.com/data", json={"id": 1})
        response = requests.get("https://api.example.com/data")
        assert response.status_code == 200
        assert response.json()["id"] == 1
        logger.info("API тест успішно пройдено")

if __name__ == "__main__":
    pytest.main([
        "-v",
        "--alluredir=allure-results",
        "--clean-alluredir",
        "--html=report.html",
        "--self-contained-html"
    ])