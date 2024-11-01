from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException
import time

from pillepas.automation.interactions import Gateway


class FormBot:
    def __init__(
            self,
            target_form_data: dict=None,
            driver: WebDriver=None,
            verbose=False
        ):

        if driver is None:
            driver = webdriver.Chrome()
        self.driver = driver
        
        if target_form_data is None:
            target_form_data = dict()
        self.target_form_data = target_form_data
        self.not_yet_written = set(self.target_form_data.keys())
        
        self.form_id = "formId"
        self.url = config.url
        self.verbose = verbose
        
        self.recorded = dict()
        
        self.form = Gateway(driver=self.driver)
        self.driver.get(self.url)
        
        for name in self.field_names:
            locator_fun = lambda s=name: self.get_input_elements(name=s)
            self.form.add_input(key=name, locator=locator_fun)
        #    
    
    def get_form_element(self) -> WebElement:
        e = self.driver.find_element(By.XPATH, fr"//form")
        return e
    
    def get_input_elements(self, name: str=None):
        """Returns all elements of the form inputs.
        If name is provided, returns only input elements with that name."""

        form = self.get_form_element()
        namepart = "" if name is None else fr"[@Name='{name}']"
        elems = form.find_elements(By.XPATH, fr".//input{namepart}")
        return elems
    
    @property
    def field_names(self):
        """Returns the unique form input field names."""

        seen = set([])
        names_gen = (e.get_property("name") for e in self.get_input_elements())
        res = [name for name in names_gen if not (name in seen or seen.add(name))]
        return res
    
    def decline_cookies(self) -> None:
        self.driver.find_element(By.ID, value="declineButton").click()
    
    def vprint(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
        #
    
    @property
    def current_values(self):
        for name in self.field_names:
            value = self.form[name]
            yield name, value
        #
    
    def record(self):
        for name, value in self.current_values:
            self.recorded[name] = value
        #
    
    def write(self):
        for name, value in self.target_form_data.items():
            
            
            if name in self.not_yet_written and self.form.is_available(name):
                self.form[name] = value
                self.not_yet_written.remove(name)
            #
        #
    #


if __name__ == '__main__':
    from pillepas import config, data_tools
    
    from pillepas.automation.interactions import make_proxy
    
    d = data_tools.load_data()
    
    
    robot = FormBot(verbose=True, target_form_data=d)
    robot.decline_cookies()
    
    robot.write()
        
    keys = ('SelectedPraeperat', 'SelectedPraeperatName')
    
    
    print(d)
    
    while True:
        time.sleep(0.2)