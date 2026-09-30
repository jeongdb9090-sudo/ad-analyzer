import os
import sys

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

STREAMLIT_URL = os.environ.get(
    "STREAMLIT_URL", "https://wlqdprkrhtlvek.streamlit.app/"
)

BUTTON_XPATH = "//button[contains(., 'get this app back up')]"


def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(STREAMLIT_URL)

        try:
            button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, BUTTON_XPATH))
            )
        except TimeoutException:
            print("깨우기 버튼 없음 -> 앱이 이미 깨어 있습니다")
            return

        button.click()
        print("깨우기 버튼 클릭!")

        try:
            WebDriverWait(driver, 120).until(
                EC.invisibility_of_element_located((By.XPATH, BUTTON_XPATH))
            )
            print("앱이 깨어났습니다")
        except TimeoutException:
            print("버튼을 눌렀지만 여전히 슬립 화면입니다")
            sys.exit(1)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
