### tools for Doing Stuff, i.e. settings values in various inputs (text fields, radio buttons, etc)
import abc
import json
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import time
from typing import Callable, Iterable


def _escape(driver: WebDriver):
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()


def _parent(e: WebElement):
    parent = e.find_element(By.XPATH, "./..")
    return parent


def set_property_with_js(driver: WebDriver, e: WebElement, property: str, value):
    """Uses a JS snippet to set a property of an element."""
    value_rep = json.dumps(value)
    js = f"arguments[0].{property} = {value_rep};"
    driver.execute_script(js, e)


class Proxy(abc.ABC):
    """Proxy class for setting/getting values from a form element"""

    def __init__(self, driver: WebDriver, e: WebElement):
        self.driver = driver
        self.e = e
    
    def get_value(self):
        res = self.e.get_property("value")
        return res
    
    @abc.abstractmethod
    def set_value(self, value):
        raise NotImplementedError
    
    def is_available(self):
        return self.e.is_enabled() and self.e.is_displayed()
    #


class TextFill(Proxy):
    def set_value(self, value):
        self.e.send_keys(str(value))
        self.e.send_keys(Keys.TAB)
        _escape(driver=self.driver)
    
    def is_available(self):
        return super().is_available() and self.e.is_displayed()
    #


class AutocompleteField(TextFill):
    def set_value(self, value):
        """Some js validation voodoo is going on here, so incrementally type the value, then look for, and click,
        the target value when it appears in the options."""

        # Options appear at the same level as the input text field, so look for list elements under the input field's parent
        parent = self.e.find_element(By.XPATH, "./..")
        
        # Remove whitespace before matching because options are weirdly formatted
        value = str(value)
        target = value.replace(" ", "")
        
        for char in str(value):
            self.e.send_keys(char)
            
            # Check for suggestions from the options list which match the target value
            children = parent.find_elements(By.TAG_NAME, "li")
            matches = [c for c in children if c.text.replace(" ", "") == target]
            
            # TODO should probably do this instead: https://stackoverflow.com/a/28110129/3752268
            if len(matches) == 1:
                time.sleep(0.5)
                hit = matches[0]
                hit.click()
                return
        #
    #


class Hidden(Proxy):
    def set_value(self, value):
        set_property_with_js(driver=self.driver, e=self.e, property="value", value=value)
    #


class Radio(Proxy):
    def __init__(self, driver: WebDriver, elems: Iterable[WebElement]):
        self.driver = driver
        self.elems = elems
    
    def get_value(self):
        for elem in self.elems:
            if elem.get_property("checked"):
                return elem.get_property("value")
            #
        #
    
    def set_value(self, value):
        for elem in self.elems:
            if elem.get_property("value") == value:
                set_property_with_js(driver=self.driver, e=elem, property="checked", value=True)
                return
            #
        #
    def is_available(self):
        return all(e.is_enabled() for e in self.elems)


def make_proxy(driver: WebDriver, elems: Iterable[WebElement]) -> Proxy:
    if len(elems) == 1:
        e = elems[0]
        kwargs = dict(driver=driver, e=e)
        match e.get_property('type'):
            case 'text' | "number":
                parent = _parent(e)
                if parent.get_attribute("class") == "awesomplete":
                    return AutocompleteField(**kwargs)
                else:
                    return TextFill(**kwargs)
                #
            case 'hidden':
                return Hidden(**kwargs)
            case _:
                raise ValueError(f"No proxy specified for element type: {e.get_property('type')}")
            #
        #
        
    elif len(elems) > 1:
        types = sorted({e.get_property("type") for e in elems})
        if len(types) > 1:
            raise RuntimeError(f"Form elements must have same type, but got: {', '.join(types)}")
        
        type_ = types[0]
        
        match type_:
            case "radio":
                return Radio(driver=driver, elems=elems)
            case _:
                raise RuntimeError
            #
        #
    else:
        raise RuntimeError
    #


class Gateway:
    """Gateway class for abstracting away interacting with different types of form elements.
    Rather than having to think about how to get Selenium to get/set a specific element in a form,
    this helper class maintains a mapping from some key, e.g. names of input elements, to a locator
    function/callable for the corresponding form input elements, and offers a consistent interface for
    getting and setting values regardless of the types of inputs.
    For example setting a value on a radio button type input requires setting
    a 'checked' property on the button with the desired value, whereas for a text input, the value
    property itself must be updated.
    
    This class uses pythonic getters/setters to interact with inputs, like so
        gateway_instance["key_for_name"] = 'My Name'
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self._locators = dict()
    
    def add_input(self, key: str, locator: Callable):
        """Registers an input with the given key and element(s)."""
        
        self._locators[key] = locator
    
    def get_proxy(self, key: str) -> Proxy:
        locator = self._locators[key]
        elems = locator()
        proxy = make_proxy(driver=self.driver, elems=elems)
        return proxy
    
    def __getitem__(self, key: str):
        proxy = self.get_proxy(key=key)
        res = proxy.get_value()
        return res

    def __setitem__(self, key: str, value):
        proxy = self.get_proxy(key=key)
        proxy.set_value(value=value)
    
    def is_available(self, key: str):
        proxy = self.get_proxy(key=key)
        return proxy.is_available()
    #
