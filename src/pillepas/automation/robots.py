from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
from typing import Callable

from pillepas.automation.interactions import Gateway, wait_and_click
from pillepas.config import logger, url


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
        
        self.url = url
        self.verbose = verbose
        
        self.recorded = dict()
        
        self.form = Gateway(driver=self.driver)
        self.field_names = []
        
        self.setup()
    
    def setup(self):
        self.driver.get(self.url)
        self.decline_cookies()
        
        for name, elems in self.get_input_names_and_elements().items():
            self.field_names.append(name)
            self.form.add_input(key=name, elems=elems)
        #

    @property
    def form_element(self) -> WebElement:
        e = self.driver.find_element(By.XPATH, fr"//form")
        return e
    
    def get_input_names_and_elements(self, name=None) -> dict:
        """Returns a dict mapping each input name to a list of elements corresponding to that input.
        We're using a list for consistency, as some input types such as radio buttons might have
        multiple elements tied to the same input.
        name is an optional parameter specifying a particular name to search for. By default, all input names
        are returned, the parameter is mainly used for debugging etc."""
        
        res = dict()
        form = self.form_element
        
        # Construct an xpath locator for html element tags associated with form inputs
        namepart = "" if name is None else fr"[@Name='{name}']"
        input_tags = ("input", "select", "textarea")
        xpath = " | ".join([fr".//{input_tag}{namepart}" for input_tag in input_tags])
        for elem in form.find_elements(By.XPATH, xpath):
            name = elem.get_property("name")
            res[name] = res.get(name, []) + [elem]
        
        return res
    
    def decline_cookies(self) -> None:
        self.driver.find_element(By.ID, value="declineButton").click()
    
    def vprint(self, s: str, **kwargs):
        if self.verbose:
            print(s, **kwargs)
        logger.info(s)
    
    @property
    def current_values(self):
        """Iterates over the names and values as they currently appear in the form"""
        for name in self.field_names:
            value = self.form[name]
            yield name, value
        #
    
    def click_final_submit_button(self):
        """Clicks the submit button. This will cause the form to sent to the selected pharmacy, so use with caution"""
        fe = self.form_element
        btn = fe.find_element(By.XPATH, r".//*[contains(@class, 'submit') and contains(@class, 'button')]")
        wait_and_click(driver=self.driver, e=btn)
    
    def _get_next_prev_buttons(self):
        """Gets the buttons under the form element. The 'next' and 'previous' buttons are among these."""
        res = self.form_element.find_elements(By.CSS_SELECTOR, r"*[class^='button']")
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
    
    @property
    def currently_visible(self):
        res = []
        for fn in self.field_names:
            try:
                if self.form.get_proxy(fn).is_displayed():
                    res.append(fn)
                #
            except StaleElementReferenceException:
                pass
            #

        return res
    
    def get_available_form_fields_missing_from_target(self):
        """Returns a list of the form fields which are currently visible, but are not defined in the
        robot's target data. If any such fields are present, human action is likely required before
        proceeding to the next page of a form."""

        missing = [fn for fn in self.currently_visible if fn not in self.target_form_data]
        return missing
    
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
        if try_click_next is True, will attempt to click the next-button in each iteration (unless
        there are visible form elements we don't have a value for)."""

        # Determine initial value
        const = constant_condition()
        
        while True:
            self.tick()
            
            # If form fields are visible that we don't have a value for, don't click next
            if try_click_next and not self.get_available_form_fields_missing_from_target():
                self.click_next()
            
            # Check and break if the value changed
            try:
                if constant_condition() != const:
                    break
                #
            except:
                break
            #
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
        return self.recorded


if __name__ == '__main__':
    pass
