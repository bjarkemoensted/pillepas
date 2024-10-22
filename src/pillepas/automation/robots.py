from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pillepas.automation import base
from pillepas.automation.interactions import Gateway


class Robot:
    def __init__(self, driver: WebDriver=None, values: dict=None):
        if driver is None:
            driver = webdriver.Chrome()
        if values is None:
            values = dict()
        
        self.values = values
        self.driver = driver
        self.gateway = Gateway(driver=self.driver)
        
        for id_ in self.values.keys():
            e = self.driver.find_element(By.ID, id_)
            self.gateway.add_element(key=id_, e=e)
        
        self.recorded = dict()
    
    def set_values(self):
        for id_, value in self.values.items():
            if value is not None:
                self.gateway[id_] = value
        #
    #
    
    def record_values(self):
        for k in self.values.keys():
            val = self.gateway[k]
            self.recorded[k] = val
        #
    #


if __name__ == '__main__':
    robot = Robot()