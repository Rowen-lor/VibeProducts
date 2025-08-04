import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# This constant can remain at the module level
SUBMITTER_PARAM = "W3sia2V5IjoiUzU2NTQ5IiwibGFiZWwiOiJFbHNhIENoYW5nIn0seyJrZXkiOiJUUjAxMDI3MCIsImxhYmVsIjoiRnJleWEgV3UifSx7ImtleSI6IlRSMDMyMTY4IiwibGFiZWwiOiJOaWwgU2h1YW5nIn0seyJrZXkiOiJUUjAzMzQzMCIsImxhYmVsIjoiSnVzdGluIEx1byJ9LHsia2V5IjoiVFIwNDMzNzYiLCJsYWJlbCI6IktpcmEgWmhhbmcifSx7ImtleSI6IlRSMDQzNTI2IiwibGFiZWwiOiJCcnVjZSBaaGVuZyJ9LHsia2V5IjoiVFIwNDQyOTMiLCJsYWJlbCI6IkFhcm9uIEdvbmcifSx7ImtleSI6IlRSMDQ2ODMwIiwibGFiZWwiOiJBaXNsaW5nIFlhbmcifSx7ImtleSI6IlRSMDQ2ODQ3IiwibGFiZWwiOiJUeXJvbmUgTGl1In0seyJrZXkiOiJUUjA1MDA0NCIsImxhYmVsIjoiQ2hhb3JhbiBHZW5nIn0seyJrZXkiOiJUUjA1MTg5NyIsImxhYmVsIjoiQXlyIE1hbyJ9LHsia2V5IjoiVFIwNTIzMTIiLCJsYWJlbCI6IlJhaW4gUnVhbiJ9LHsia2V5IjoiVFIwNTIzNDUiLCJsYWJlbCI6IkNoZW5rYW5nIFlhbmcifSx7ImtleSI6IlRSMDUzMTU2IiwibGFiZWwiOiJIYW93ZW4gTHVvIn0seyJrZXkiOiJUUjAyMDA5OCIsImxhYmVsIjoiVFJJU1RBTiBNQVRUSEVXIENISU4ifSx7ImtleSI6IlMyMjEyMyIsImxhYmVsIjoiRXZhIFd1In0seyJrZXkiOiJTNzY0MzAiLCJsYWJlbCI6Ik1lbG9keSBIZSJ9LHsia2V5IjoiUzc3ODE2IiwibGFiZWwiOiJKT1NFUEggTEVPTkFSRCBPJ05FSUxMIn0seyJrZXkiOiJUUjAyMDYzOCIsImxhYmVsIjoiUGVhY2ggUG9vbiJ9LHsia2V5IjoiVFIwMjEwMjQiLCJsYWJlbCI6IkppZXlhbiBLYW8ifSx7ImtleSI6IlRSMDI3NDA1IiwibGFiZWwiOiJQb3JudGhpdGEifSx7ImtleSI6IlRSMDMxMjUwIiwibGFiZWwiOiJTYWJyaW5hIEhvIn0seyJrZXkiOiJUUjAzMjgzMyIsImxhYmVsIjoiTWFyZ290IENob2kifSx7ImtleSI6IlRSMDMzNzU4IiwibGFiZWwiOiJBcmllZiBGYWphciBHdW1pbGFyIn0seyJrZXkiOiJUUjAzMzg4MSIsImxhYmVsIjoiU2l0aSBGYXRpbWFoIEFiZHVsIEdoYW5pIn0seyJrZXkiOiJUUjAzNjM5NyIsImxhYmVsIjoiSk9TSFVBIEJFTkpBTUlOIFlBVSBTTk9XREVOIn0seyJrZXkiOiJUUjAzNjYwMyIsImxhYmVsIjoiTGFuaSBPaCJ9LHsia2V5IjoiVFIwNDA4MzIiLCJsYWJlbCI6IkthenVoaXJvIElzaGlrYXdhIn0seyJrZXkiOiJUUjA0MTE3NyIsImxhYmVsIjoiSGl0b21pIEViaWhhcmEifSx7ImtleSI6IlRSMDQ0NjE5IiwibGFiZWwiOiJFZHdhcmQgU3pldG8ifSx7ImtleSI6IlRSMDQ0ODk4IiwibGFiZWwiOiJXYXJpc2FyYSBDaGFuZGhhcmF0aCJ9LHsia2V5IjoiVFIwNDYwMTYiLCJsYWJlbCI6IlNoaW50YXJvaCBZYW1hZGEifSx7ImtleSI6IlRSMDQ2Mjc4IiwibGFiZWwiOiJKaW4gWXUifSx7ImtleSI6IlRSMDQ5MzI0IiwibGFiZWwiOiJKYXNtaW5lIFRzb3UifSx7ImtleSI6IlRSMDUwMjc4IiwibGFiZWwiOiJLcmFpbiBKaWEifSx7ImtleSI6IlRSODQxNjgyIiwibGFiZWwiOiJZYWt1biBXdSJ9LHsia2V5IjoiVFI4NDI0NjkiLCJsYWJlbCI6IkppYXFpIFRhbyJ9LHsia2V5IjoiVFIwMTYwMTkiLCJsYWJlbCI6IkthdHJpbiBMYW1tIn0seyJrZXkiOiJUUjAyMDIyOCIsImxhYmVsIjoiTHVpcyBFbGllemVyIE9qZWRhIFBlZGVtb250ZXMifSx7ImtleSI6IlRSMDM1MzY4IiwibGFiZWwiOiJMYXVyYSBCYXJ0aXJvbW8ifSx7ImtleSI6IlRSMDM1OTAxIiwibGFiZWwiOiJNaW5hIElicmFoaW0ifSx7ImtleSI6IlRSMDM3MTk4IiwibGFiZWwiOiJTYW5kcmEgTcO8bGxlciJ9LHsia2V5IjoiVFIwMzc5MzciLCJsYWJlbCI6IlZpY3Rvci3DiWRvdWFyZCBUaMOpYmF1bHQifSx7ImtleSI6IlRSMDQ3ODIwIiwibGFiZWwiOiJBbmEgR2FicmllbGEgTW9kZXN0byBCcmFnYSJ9LHsia2V5IjoiUzE5NjI5IiwibGFiZWwiOiJTZWxpbmEgR2FvIn0seyJrZXkiOiJUUjAwOTE5NCIsImxhYmVsIjoiSm9zZXBoIFBheW5lIn0seyJrZXkiOiJUUjAwNzAxMCIsImxhYmVsIjoiQWxleCBNb29yZSJ9XQ%3D%3D"

def _generate_time_periods():
    """Generates time period configurations."""
    periods = [("20200728", "20201231")]
    now = datetime.now()
    current_year = now.year
    for year in range(2021, current_year + 1):
        start_date_h1 = datetime(year, 1, 1)
        end_date_h1 = datetime(year, 6, 30)
        if now >= start_date_h1:
            actual_end_date_h1 = min(end_date_h1, now)
            periods.append((start_date_h1.strftime("%Y%m%d"), actual_end_date_h1.strftime("%Y%m%d")))
        start_date_h2 = datetime(year, 7, 1)
        end_date_h2 = datetime(year, 12, 31)
        if now >= start_date_h2:
            actual_end_date_h2 = min(end_date_h2, now)
            periods.append((start_date_h2.strftime("%Y%m%d"), actual_end_date_h2.strftime("%Y%m%d")))
    return periods

def _generate_url(start_date, end_date):
    """Generates URL for a given time period."""
    base_url = "http://-report/disposeSituation"
    return f"{base_url}?pid=43&bu=&startTime={start_date}&endTime={end_date}&submitter={SUBMITTER_PARAM}&locale=en-US"

def _export_data(driver, wait, period_desc, log_callback):
    """Handles the data export logic."""
    try:
        try:
            guide_close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div/div[1]/a")))
            guide_close_btn.click()
            log_callback(f"[{period_desc}] 引导弹窗已关闭")
        except TimeoutException:
            log_callback(f"[{period_desc}] 未发现引导弹窗")

        export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/section/section/main/div/div/div[2]/div[1]/div/button[2]')))
        btn_text = export_btn.text.strip().lower()
        if "export" in btn_text or "导 出" in export_btn.text:
            driver.execute_script("arguments[0].click();", export_btn)
            log_callback(f"[{period_desc}] 导出按钮已点击")
            try:
                confirm_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "ant-btn-primary") and contains(@class, "ant-btn-sm")]')))
                confirm_text = confirm_btn.text.strip().lower()
                if "confirm" in confirm_text or "确定" in confirm_btn.text.replace(" ", ""):
                    confirm_btn.click()
                    log_callback(f"[{period_desc}] 确认按钮已点击")
                else:
                    log_callback(f"[{period_desc}] 确认按钮文本不匹配: '{confirm_btn.text.strip()}'")
            except TimeoutException:
                log_callback(f"[{period_desc}] 确认按钮未找到或响应超时")
        else:
            log_callback(f"[{period_desc}] 按钮找到但文本不匹配: '{export_btn.text.strip()}'")
        time.sleep(3)
        log_callback(f"[{period_desc}] 处理完成")
    except (TimeoutException, NoSuchElementException) as e:
        log_callback(f"[{period_desc}] 失败: {e}")

def download_reports(log_callback):
    """Main function to drive the download process."""
    try:
        with open("login_config.json", "r") as f:
            config = json.load(f)
        username = config.get("username")
        password = config.get("password")
    except FileNotFoundError:
        log_callback("错误: 'login_config.json' 文件未找到。请确保该文件与脚本在同一目录下。\n")
        return
    except json.JSONDecodeError:
        log_callback("错误: 'login_config.json' 文件格式不正确。\n")
        return

    periods = _generate_time_periods()
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)
    
    try:
        is_first_run = True
        for start_date, end_date in periods:
            period_desc = f"{start_date}-{end_date}"
            url = _generate_url(start_date, end_date)
            
            log_callback(f"[{period_desc}] 开始处理...")
            driver.get(url)

            if is_first_run:
                wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
                wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password + Keys.RETURN)
                is_first_run = False

            wait.until(EC.presence_of_element_located((By.ID, "__next")))
            _export_data(driver, wait, period_desc, log_callback)
            
            log_callback(f"[{period_desc}] 等待1.5秒后处理下一个时间段...")
            time.sleep(1.5)
    
    finally:
        driver.quit()
    
    log_callback("所有时间段处理完成!\n")

if __name__ == "__main__":
    # Example of how to run this module directly
    # The lambda function will print messages to the console
    download_reports(lambda msg: print(msg))
