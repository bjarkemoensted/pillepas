from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
from typing import Callable

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
        
        self.url = config.url
        self.verbose = verbose
        
        self.recorded = dict()
        
        self.form = Gateway(driver=self.driver)
        
        self.setup()
    
    def setup(self):
        self.driver.get(self.url)
        
        for name in self.field_names:
            locator_fun = lambda s=name: self.get_input_elements(name=s)
            self.form.add_input(key=name, locator=locator_fun)
        #

    @property
    def form_element(self) -> WebElement:
        e = self.driver.find_element(By.XPATH, fr"//form")
        return e
    
    def get_input_elements(self, name: str=None):
        """Returns all elements of the form inputs.
        If name is provided, returns only input elements with that name."""

        form = self.form_element
        namepart = "" if name is None else fr"[@Name='{name}']"
        input_tags = ("input", "select", "textarea")
        xpath = " | ".join([fr".//{input_tag}{namepart}" for input_tag in input_tags])
        elems = form.find_elements(By.XPATH, xpath)
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
        """Iterates over the names and values as they currently appear in the form"""
        for name in self.field_names:
            value = self.form[name]
            yield name, value
        #
    
    def _get_next_prev_buttons(self):
        """Gets the buttons under the form element. The 'next' and 'previous' buttons are among these."""
        res = self.form_element.find_elements(By.CSS_SELECTOR, r"a[class^='button']")
        return res
    
    def click_next(self):
        """Clicks the 'next' button to proceed to the next part of the form"""
        form_buttons = self._get_next_prev_buttons()
        candidates = [e for e in form_buttons if e.text == "Næste"]
        
        if len(candidates) == 1:
            # Record values before clicking to make sure we don't miss any changes
            self.record()
            try:
                candidates[0].click()
                return True
            except ElementClickInterceptedException:
                return False
            #
        #
    
    def record(self):
        for name, value in self.current_values:
            oldval = self.recorded.get(name, "")
            if oldval != value:
                self.recorded[name] = value
                self.vprint(f"Recorded {name} = {value}")
            #
        #
    
    def write(self):
        for name, value in self.target_form_data.items():
            if name in self.not_yet_written and self.form.is_available(name):
                self.form[name] = value
                self.not_yet_written.remove(name)
                self.vprint(f"Wrote {value} to input field '{name}'.")
            #
        #
    
    def tick(self, retry=True):
        try:
            self.record()
            self.write()
        except (StaleElementReferenceException, RuntimeError):
            if retry:
                return self.tick(retry=False)
            raise
    
    def loop(self, constant_condition: Callable, try_click_next=False):
        """Loops until the provided callable takes a value different from its initial value.
        if try_click_next is True, will attempt to click the next-button in each iteration."""

        # Determine initial value
        const = constant_condition()
        
        while True:
            self.tick()
            if try_click_next:
                self.click_next()
            
            # Check and break if the value changed
            try:
                if constant_condition() != const:
                    break
                #
            except:
                break
            
            
        #
            
    def loop_form_page(self, try_click_next=False):
        """Loops until we leave the current page of the form"""
        cond = lambda: tuple(int(e.is_displayed()) for e in self._get_next_prev_buttons())
        self.loop(constant_condition=cond, try_click_next=try_click_next)
    
    def loop_form(self, try_click_next=False):
        """Loops until we're done with the entire form"""
        cond = lambda: self.form_element.get_attribute("id")
        self.loop(constant_condition=cond, try_click_next=try_click_next)
    
    def wrap_up(self):
        print(self.recorded)


if __name__ == '__main__':
    from pillepas import config, data_tools
    
    from pillepas.automation.interactions import make_proxy
    
    d = data_tools.load_data()
    del d["FormId"]
    
    
    robot = FormBot(verbose=True, target_form_data=d)
    robot.decline_cookies()
    
    
    robot.loop_form(try_click_next=True)
    