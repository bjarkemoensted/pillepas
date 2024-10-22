from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import StaleElementReferenceException

from pillepas.automation import base
from pillepas.automation.interactions import Gateway


class Robot:
    def __init__(self, driver: WebDriver=None, data: dict=None, verbose=False):
        if driver is None:
            driver = webdriver.Chrome()
        if data is None:
            data = dict()
        
        self.verbose = verbose
        self.data = data
        self.ids = tuple(data.keys())
        self.recorded = dict()
        self.first_recorded_values = dict()
        
        self.missing = set(self.ids)
        self.driver = driver
        self.gateway = Gateway(driver=self.driver)
        
        for id_ in self.ids:
            e = self.driver.find_element(By.ID, id_)
            self.gateway.add_element(key=id_, e=e)
        #
    
    def vprint(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
    
    def available_ids(self):
        for id_ in self.ids:
            e = self.gateway.get_element(id_)
            try:
                is_available = e.is_enabled()
                if e.is_displayed():
                    print(f"{id_} is visible")
            except StaleElementReferenceException:
                is_available = False
            if is_available:
                yield id_
            #
        #
    
    def set_values(self):
        for id_ in self.available_ids():
            if id_ in self.missing:
                value = self.data[id_]
                if value is None:
                    continue
                self.gateway[id_] = value
                self.missing.remove(id_)
                self.vprint(f"Set ID {id_} to {value}")
            #
        #
    #
    
    def record_values(self):
        for id_ in self.available_ids():
            value = self.gateway[id_]
            
            # Record initial value if it hasn't been set already
            first_time = id_ not in self.first_recorded_values
            if first_time:
                self.first_recorded_values[id_] = value
            
            previously_recorded = id_ in self.recorded
            recorded_changed = previously_recorded and self.recorded[id_] != value
            
            initial_changed = self.first_recorded_values[id_] != value
            record = False
            if recorded_changed:
                record = True
            else:
                if not previously_recorded and (initial_changed or self.data[id_] is not None):
                    record = True
                #
                
            if record:
                self.recorded[id_] = value
                self.vprint(f"Recorded ID {id_} as {value}")
            #
        #
    #


if __name__ == '__main__':
    robot = Robot()