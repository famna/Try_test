import pytest 
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os
import time

# Налаштування логування в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_log.log"),
        logging.StreamHandler()
    ]
)

@pytest.fixture(scope="class", params=["chrome", "firefox"])
def setup_driver(request):
    logging.info(f"Налаштовую драйвер для {request.param}...")
    if request.param == "chrome":
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        options = FirefoxOptions()
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    
    driver.implicitly_wait(10)
    logging.info("Браузер відкрито!")
    yield driver
    logging.info("Закриваю драйвер...")
    driver.quit()
    logging.info("Драйвер закрито.")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("setup_driver")
        if driver:
            screenshot_path = f"screenshots/{item.name}.png"
            os.makedirs("screenshots", exist_ok=True)
            driver.save_screenshot(screenshot_path)
            logging.error(f"Тест {item.name} зазнав невдачі. Скріншот збережено: {screenshot_path}")

class TestLogin:
    @pytest.mark.parametrize("username, password, expected_message", [
        ("tomsmith", "SuperSecretPassword!", "You logged into a secure area!"),
        ("wronguser", "wrongpassword", "Your username is invalid!")
    ])
    def test_login(self, setup_driver, username, password, expected_message):
        logging.info("Перевірка логіну з параметризацією...")
        setup_driver.get("https://the-internet.herokuapp.com/login")
        setup_driver.find_element(By.ID, "username").send_keys(username)
        setup_driver.find_element(By.ID, "password").send_keys(password)
        setup_driver.find_element(By.CSS_SELECTOR, "button.radius").click()
        assert expected_message in setup_driver.find_element(By.ID, "flash").text
        logging.info("Перевірка логіну успішна!")

class TestCheckbox:
    def test_checkboxes(self, setup_driver):
        logging.info("Перевірка чекбоксів...")
        setup_driver.get("https://the-internet.herokuapp.com/checkboxes")
        checkboxes = setup_driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes:
            if not checkbox.is_selected():
                checkbox.click()
        assert all(checkbox.is_selected() for checkbox in checkboxes)
        logging.info("Усі чекбокси вибрані!")

class TestAlert:
    def test_alerts(self, setup_driver):
        logging.info("Перевірка спливаючих вікон...")
        setup_driver.get("https://the-internet.herokuapp.com/javascript_alerts")
        setup_driver.find_element(By.XPATH, "//button[text()='Click for JS Alert']").click()
        alert = setup_driver.switch_to.alert
        assert "I am a JS Alert" in alert.text
        alert.accept()
        logging.info("Спливаюче вікно успішно закрито!")

class TestDropdown:
    def test_dropdown(self, setup_driver):
        logging.info("Перевірка випадаючого списку...")
        setup_driver.get("https://the-internet.herokuapp.com/dropdown")
        dropdown = Select(setup_driver.find_element(By.ID, "dropdown"))
        dropdown.select_by_value("2")
        assert dropdown.first_selected_option.text == "Option 2"
        logging.info("Випадаючий список працює коректно!")

class TestFileUpload:
    def test_file_upload(self, setup_driver):
        logging.info("Перевірка завантаження файлу...")
        setup_driver.get("https://the-internet.herokuapp.com/upload")
        file_path = "C:\\Users\\Kirill\\Desktop\\testfile.txt"
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("Test file content")
        file_input = setup_driver.find_element(By.ID, "file-upload")
        file_input.send_keys(file_path)
        setup_driver.find_element(By.ID, "file-submit").click()
        assert "File Uploaded!" in setup_driver.find_element(By.TAG_NAME, "body").text
        logging.info("Файл успішно завантажено!")

class TestInputForm:
    def test_input_form(self, setup_driver):
        logging.info("Перевірка введення тексту у форму...")
        setup_driver.get("https://the-internet.herokuapp.com/inputs")
        input_field = setup_driver.find_element(By.TAG_NAME, "input")
        input_field.clear()
        input_field.send_keys("12345")
        assert input_field.get_attribute("value") == "12345"
        logging.info("Текст успішно введено у форму!")

class TestAPI:
    def test_api_response(self):
        logging.info("Перевірка відповіді API...")
        response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        logging.info("API працює коректно!")

if __name__ == "__main__":
    pytest.main(["-v", "--html=report.html", "--self-contained-html"])
