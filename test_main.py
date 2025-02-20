from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

class BaseTest:
    def setup_method(self):
        print("Налаштовую драйвер...")
        
        # Налаштування параметрів Chrome
        options = Options()
        # Вимкніть headless для перевірки
        # options.add_argument("--headless")  # Вимкнення headless режиму для відображення браузера
        options.add_argument("--disable-gpu")  # Вимкнення GPU для кращої роботи
        options.add_argument("--window-size=1920,1080")  # Розмір вікна

        # Встановлення драйвера Chrome
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("Драйвер запущено!")
        
        self.driver.implicitly_wait(10)  # Очікування елементів на сторінці
        print("Браузер відкрито!")

    def teardown_method(self):
        print("Закриваю драйвер...")
        self.driver.quit()
        print("Драйвер закрито.")

class LoginTest(BaseTest):
    def test_login(self):
        print("Відкриваю сторінку...")
        self.driver.get("https://the-internet.herokuapp.com/login")
        
        # Знаходимо елементи на сторінці
        username_input = self.driver.find_element(By.ID, "username")
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button.radius")
        
        # Вводимо дані та натискаємо кнопку
        username_input.send_keys("tomsmith")
        password_input.send_keys("SuperSecretPassword!")
        login_button.click()
        
        # Перевіряємо, чи вдалося залогінитись
        \
        success_message = self.driver.find_element(By.ID, "flash")
        assert "You logged into a secure area!" in success_message.text
        
        print("Тест завершено!")

if __name__ == "__main__":
    test = LoginTest()
    test.setup_method()
    test.test_login()
    test.teardown_method()
