import pytest 
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@pytest.fixture(scope="class")
def setup_driver():
    logging.info("Налаштовую драйвер...")
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(10)
    logging.info("Браузер відкрито!")
    yield driver
    logging.info("Закриваю драйвер...")
    driver.quit()
    logging.info("Драйвер закрито.")

class TestLogin:
    def test_login_success(self, setup_driver):
        logging.info("Відкриваю сторінку логіну...")
        setup_driver.get("https://the-internet.herokuapp.com/login")
        setup_driver.find_element(By.ID, "username").send_keys("tomsmith")
        setup_driver.find_element(By.ID, "password").send_keys("SuperSecretPassword!")
        setup_driver.find_element(By.CSS_SELECTOR, "button.radius").click()
        assert "You logged into a secure area!" in setup_driver.find_element(By.ID, "flash").text
        logging.info("Успішний логін підтверджено!")

    def test_login_failure(self, setup_driver):
        logging.info("Перевірка некоректного логіну...")
        setup_driver.get("https://the-internet.herokuapp.com/login")
        setup_driver.find_element(By.ID, "username").send_keys("wronguser")
        setup_driver.find_element(By.ID, "password").send_keys("wrongpassword")
        setup_driver.find_element(By.CSS_SELECTOR, "button.radius").click()
        assert "Your username is invalid!" in setup_driver.find_element(By.ID, "flash").text
        logging.info("Перевірка некоректного логіну пройдена!")

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

class TestTable:
    def test_table_content(self, setup_driver):
        logging.info("Перевірка отримання значень із таблиці...")
        setup_driver.get("https://the-internet.herokuapp.com/tables")
        cell_value = setup_driver.find_element(By.XPATH, "//table[1]//tr[2]/td[4]").text
        assert cell_value == "$51.00"
        logging.info("Таблиця містить очікуване значення!")

class TestDragAndDrop:
    def test_drag_and_drop(self, setup_driver):
        logging.info("Перевірка перетягування елементів...")
        setup_driver.get("https://the-internet.herokuapp.com/drag_and_drop")
        source = setup_driver.find_element(By.ID, "column-a")
        target = setup_driver.find_element(By.ID, "column-b")
        ActionChains(setup_driver).drag_and_drop(source, target).perform()
        assert "A" in target.text
        logging.info("Перетягування виконано успішно!")

if __name__ == "__main__":
    pytest.main(["-v", "--html=report.html"])
