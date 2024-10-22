from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pillepas.automation import base
from pillepas.automation.interactions import make_proxy


class Robot:
    def __init__(self, driver: WebDriver=None, values: dict=None):
        if driver is None:
            driver = webdriver.Chrome()
        if values is None:
            values = dict()
        
        self.values = values
        self.driver = driver
        self.proxies = dict()
        for id_ in self.values.keys():
            e = self.driver.find_element(By.ID, id_)
            self.proxies[id_] = make_proxy(driver=self.driver, e=e)
        
        self.recorded = dict()
    
    
    
        
        
    
    