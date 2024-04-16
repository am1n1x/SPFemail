from flask import Flask, request, render_template, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import configparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

def send_mail(receiver_email, spoofed_email, spoofed_name, message, subject):
    try:
        msg = MIMEMultipart("related")
        msg['From'] = f"{spoofed_name} <{spoofed_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = subject
        body = message
        msg.attach(MIMEText(body, 'plain'))

        smtp_host = config.get('SMTP', 'host')
        smtp_port = config.getint('SMTP', 'port')
        smtp_username = config.get('SMTP', 'username')
        smtp_password = config.get('SMTP', 'password')

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(spoofed_email, receiver_email, text)

        return 'Письмо успешно отправлено на ' + receiver_email + ' от ' + spoofed_name
    except Exception as e:
        print(traceback.format_exc())
        return str(e)


def check_dmarc_policy(domain):
    url = f"https://mxtoolbox.com/SuperTool.aspx?action=dmarc%3a{domain}&run=toolpage"

    # Настройка опций для Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск браузера в фоновом режиме

    # Инициализация драйвера
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find_all('td', class_='table-column-Response')
        for result in results:
            text = result.text.strip()
            if "DMARC Quarantine/Reject policy not enabled" in text:
                return "DMARC не подключен"
            elif "DMARC Quarantine/Reject policy enabled" in text:
                return "DMARC подключен"
        return 'Информация о DMARC отсутствует'
    except Exception as e:
        return f'Error: {e}'
    finally:
        driver.quit()  # Закрытие браузера после завершения работы



# Определение маршрута для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Определение маршрута для обработки отправки email
@app.route('/send_email', methods=['POST'])
def handle_send_email():
    try:
        data = request.get_json()  # Получаем данные из JSON
        receiver_email = data['email']  # Извлекаем email из полученных данных
        domain = receiver_email.split('@')[-1]
        spoofed_email = 'support@gosuslugi.ru'
        spoofed_name = 'Госуслуги'
        message = 'Это письмо направлено для проверки безопасности почтового ящика'
        subject = 'Проверка почты'

        send_mail_result = send_mail(receiver_email, spoofed_email, spoofed_name, message, subject)
        dmarc_result = check_dmarc_policy(domain)

        return jsonify({
            'send_mail_result': send_mail_result,
            'dmarc_result': dmarc_result
        })

    except KeyError:
        return 'Ошибка: поле "email" не было отправлено в запросе', 400
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)