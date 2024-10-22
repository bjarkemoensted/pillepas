### tools for Doing Stuff, i.e. settings values in various inputs (text fields, radio buttons, etc)

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from typing import final, Iterable


def represent_value_as_js(val) -> str:
    """Prepares a value for injection into a JavaScript snippet for when it's necessary to use JS to
    interact with a page."""

    if isinstance(val, bool):
        if val is True:
            return 'true'
        elif val is False:
            return 'false'
        else:
            raise ValueError  # I dunno
        #
    elif isinstance(val, str):
        return f"'{val}'"
    elif isinstance(val, (int, float)):
        return f'{val}'
    elif val is None:
        return 'null'
    else:
        raise TypeError(f"Can't convert type {type(val)} ({str(val)}) to js.")
    #


def set_property_with_js(driver: WebDriver, e: WebElement, property: str, value):
    """Uses a JS snippet to set a property of an element."""
    value_rep = represent_value_as_js(val=value)
    js = f"arguments[0].{property} = {value_rep};"
    driver.execute_script(js, e)


class ElementProxy:
    """Proxy class for setting/getting values from a form element"""

    @final
    def __init__(self, driver: WebDriver, e: WebElement):
        self.driver = driver
        self.e = e
    
    def get_value(self):
        res = self.e.get_property("value")
        return res
    
    def set_value(self, value):
        set_property_with_js(driver=self.driver, e=self.e, property="value", value=value)
    
    def ready(self):
        return self.e.is_displayed() and self.e.is_enabled()
    #


class RadioProxy(ElementProxy):
    """Proxy class for radio buttons because they behave differently - rather than reading/setting
    a desired value, a radio button has the 'checked' property if true, which needs to be set using javascript
    because the true button is often hidden because frontend stuff is 10^23 bad decisions in a trench coat."""

    def get_value(self):
        res = self.e.is_selected()
        return res
    
    def set_value(self, value: bool):
        set_property_with_js(driver=self.driver, e=self.e, property="checked", value=value)
    #


def make_proxy(driver: WebDriver, e: WebElement) -> ElementProxy:
    match e.get_property("type"):
        case 'radio':
            constructor = RadioProxy
        case _:
            constructor = ElementProxy
        #
    
    proxy = constructor(driver=driver, e=e)
    return proxy


class Gateway:
    """Gateway class for abstracting away interacting with different types of form elements.
    Rather than having to think about how to get Selenium to get/set a specific element in a form,
    this helper class takes a mapping from e.g. IDs to webelements, and provides a unified interface
    with pythonic getters and setters, so e.g.
        gateway_instance["id_of_name_field"] = 'My Name'
        gateway_instance["id_of_some_radio_button"] = True
    should both work."""

    def __init__(self, driver: WebDriver, elements_map: dict):
        self.proxies = dict()
        for key, e in elements_map.items():
            proxy = make_proxy(driver=driver, e=e)
            self.proxies[key] = proxy
        #
    
    def _get_proxy(self, key: str):
        proxy = self.proxies[key]
        return proxy
    
    def __getitem__(self, key: str):
        proxy = self._get_proxy(key=key)
        res = proxy.get_value()
        return res

    def __setitem__(self, key: str, value):
        proxy = self._get_proxy(key=key)
        proxy.set_value(value=value)
    #
