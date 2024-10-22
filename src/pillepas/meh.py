from selenium import webdriver
from selenium.webdriver.common.by import By

import time

from pillepas import config

from pillepas.automation.interactions import Gateway
from pillepas.automation.base import fields, get_all_ids


medicine_field_id = "SubmitModel_SelectedPraeperatName"



hmmmm = "SubmitModel_TravelStartDate"


def main():
    driver = webdriver.Chrome()
    
    ids = get_all_ids()
    
    driver.get(config.url)
    nope = driver.find_element(By.ID, value="declineButton")
    print(nope)
    nope.click()
    
    med_elem = driver.find_element(By.ID, value=medicine_field_id)
    print(med_elem)
    print(med_elem.get_attribute('value'))
    
    
    next_ = driver.find_elements(By.XPATH,"//*[@data-id='step2']")
    
    hmm = driver.find_elements(By.CSS_SELECTOR,"[data-id^='step']")
    okokok = driver.find_elements(By.CSS_SELECTOR, "[id^='SubmitModel_']")
    
    
    gateway = Gateway(driver=driver, ids=ids)
    
    
    
    
    
    while True:
        print(med_elem.get_attribute('value'))
        d = {e.get_property("id"): e for e in okokok}
        print(len(okokok))
        for elem in okokok:
            print(elem.id)
        time.sleep(0.1)


if __name__ == '__main__':
    import time
    print("eyy")
    
    main()
    time.sleep(5)