from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
import getpass

apollo_account = input('請輸入 Apollo 帳號： ')
apollo_password = getpass.getpass('請輸入 Apollo 密碼： ')
start_date = input('輸入開始打卡日期 (格式：YYYY/MM/DD)： ')
end_date = input('輸入結束打卡日期 (格式：YYYY/MM/DD)： ')

def get_workdays(start_date, end_date):
    # 挑選出 start_date 和 end_date 之間的所有工作日
    
    start = datetime.strptime(start_date, '%Y/%m/%d')
    end = datetime.strptime(end_date, '%Y/%m/%d')
    day = timedelta(days=1)
    workdays = []

    while start <= end:
        if start.weekday() < 5:  # Monday to Friday are 0 to 4
            workdays.append(start.strftime('%Y/%m/%d'))
        start += day

    return workdays

def run_webdriver():
  options = webdriver.ChromeOptions()
  options.add_experimental_option('detach', True)  #不自動關閉視窗
  options.add_argument("--incognito")
  driver = webdriver.Chrome(options=options)

  driver.implicitly_wait(5) # 設定等待時間，讓網頁 load 出來
  driver.get("https://apolloxe.mayohr.com/ta/personal/checkin/checkinrecords/workrecords")
  # 直接進到忘打卡申請的頁面後，會先跳轉去登入頁面，登入完成後會再跳回忘打卡申請的頁面
  

  # 啟動登入流程

  # 帶入帳號
  username = driver.find_element(By.NAME, "userName")
  username.send_keys(apollo_account)

  # 帶入密碼
  password = driver.find_element(By.NAME, "password")
  password.send_keys(apollo_password)

  # 點擊登入
  login_btn = driver.find_element(By.CSS_SELECTOR, ".loginform > .submit-btn")
  login_btn.click()

  try:
    # 等待網頁狀態為 'complete'
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    print("Page fully loaded")
  except TimeoutException:
    print("Timeout while waiting for page to load")  
  
  # 開始申請忘打卡

  dates = get_workdays(start_date, end_date)
  apply_btn = driver.find_element(By.CSS_SELECTOR, ".apply-punchin-bar > .ta_btn")

  for date in dates:
    for punch_type in ['上班', '下班']:
      time.sleep(2)

      # 點擊「忘打卡申請」
      apply_btn.click()


      # 先用 JavaScript 清空輸入框
      max_attempts = 5
      attempts = 0

      # 選取日期
      date_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form.form-horizontal.new.forgetPunch .ta-form__form-group .ta-form__form-control .datePickInputer__container input[placeholder='YYYY/MM/DD']"))
      )  

      # 不斷檢查輸入框是否為空
      while attempts < max_attempts:
        current_value = date_input.get_attribute('value')
        if not current_value:
            break  # 如果輸入框是空的，跳出迴圈
        driver.execute_script("arguments[0].value = '';", date_input)
        time.sleep(1)  # 等待一秒後再次檢查
        attempts += 1

      # 確認是否成功清空輸入框
      if attempts == max_attempts:
        print("Failed to clear the input field.")

      # 修改日期
      # 創建 ActionChains 對象
      actions = ActionChains(driver)

      # 輸入新日期
      actions.move_to_element(date_input)  # 將滑鼠移動到日期輸入框
      actions.click()  # 點擊輸入框
      actions.send_keys(date)  # 輸入新日期
      actions.perform()  # 執行

      # 選取類型（上班/下班）
      type_dropdown = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form.form-horizontal.new.forgetPunch .Select--single.is-searchable"))
      )  
      type_dropdown.click()
      time.sleep(1)

      type_option = driver.find_element(By.XPATH, f"//div[@class='Select-menu-outer']//span[text()='{punch_type}']")
      type_option.click()
      time.sleep(1)

      # 選取地點（又米）
      location_dropdown = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form.form-horizontal.new.forgetPunch div[data-reactid='.0.0.1.3.0.1.1.2:$/=10.0.0.1.0.1.3.0.1.0.0.4.1.0.0.1']"))
      )  
      location_dropdown.click()

      location_option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='Select-menu-outer']//div[contains(@class,'Select-option')][1]"))
      )
      location_option.click()

      # 點選確定，送出申請
      submit_btn = driver.find_element(By.CSS_SELECTOR, "form.form-horizontal.new.forgetPunch .new__btn--fixed-height")
      submit_btn.click()

      # 最終確認
      confirm_btn = driver.find_element(By.CSS_SELECTOR, ".message-box .btn-primary")
      confirm_btn.click()

    print(date, '已經完成上下班補打卡')

if __name__ == '__main__':
    run_webdriver()