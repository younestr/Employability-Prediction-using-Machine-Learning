from selenium import webdriver
from selenium.webdriver.chrome.service import Service

url = "about:blank"
# Path to the ChromeDriver executable
service = Service(r'C:\Users\xelor\Downloads\Chromedriver\chromedriver-win64\chromedriver.exe')
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
driver.get(url)