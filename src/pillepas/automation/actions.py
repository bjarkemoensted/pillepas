import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator, Page
from typing import Callable, Dict


def setup_finder(role: str, filter_: Callable[[Locator], bool]=None, **role_kwargs) -> Callable[[Locator], Locator]:
    def f(element: Locator):
        e = element.get_by_role(role, **role_kwargs)
        candidates = e.all()
        if filter_ is not None:
            candidates = [c for c in candidates if filter_(c)]
        
        if len(candidates) == 1:
            return candidates[0]
        #
    
    return f


class Proxy:
    def __init__(self,
                 role: str=None,
                 finder: Callable[[Locator], Locator]=None,
                 filter_: Callable[[Locator], bool]=None,
                 **role_kwargs
            ):
        
        if finder is None:
            finder = setup_finder(role=role, filter_=filter_, **role_kwargs)
        
        self.finder = finder
        self.sensitive = False
    
    def set_value(self, element: Locator, value: str):
        e = self.finder(element)
        e.click(force=True)
        e.fill(value)
        
    def get_value(self, element: Locator):
        e = self.finder(element)
        res = e.get_attribute("value")
        return res
    
    def get_matches(self, element: Locator):
        """Returns list of all matches inside element which match the proxy's finder"""
        elems = self.finder(element)
        if elems is None:
            return []
        return elems.all()
    
    def is_present(self, element: Locator):
        e = self.finder(element)
        return e is not None and e.count() > 0

# form.get_by_role("textbox", name="Fornavn").and_(form.locator('[name*="doctor"]'))


class AutocompleteProxy(Proxy):
    def set_value(self, element, value: str):
        e = self.finder(element)
        e.click()
        e.fill(value[:3])
        element.get_by_role("option", name=value).click()
        return super().set_value(element, value)
    #


class DropDownProxy(Proxy):
    def set_value(self, element: Locator, value: str):
        e = self.finder(element)
        select_elem = e.locator("..").locator("select").element_handle()
        
        e.click(force=True)
        # Select the option with the max value
        select_elem.select_option(label=value)
        element.press("Escape")

def _doctor_filter(element: Locator) -> bool:
    res = "doctor" in element.get_attribute("name").lower()
    return res


vals = dict(
    medicine = "Elvanse, kapsler, hårde, 20 mg 'Takeda Pharma'",
    daily_dosis = "1",
    n_days_with_meds = "Alle dage",
    doctor_first_name = "meh",
    doctor_last_name = "meh",
    doctor_address = "Amerikavej",
    doctor_zipcode = "2200",
    doctor_city = "Kbh",
    doctor_phone="123213123"
)


# medication.0.doctorInformation.address

PROXIES = dict(
    medicine = AutocompleteProxy(finder=lambda loc: loc.get_by_placeholder("Skriv navnet på din medicin")),
    daily_dosis = Proxy("spinbutton", name="Daglig dosis i antal enheder"),
    n_days_with_meds = DropDownProxy("combobox", name="Antal dage med medicin"),
    doctor_first_name = Proxy("textbox", name="Fornavn", filter_=_doctor_filter),
    doctor_last_name = Proxy("textbox", name="Efternavn", filter_=_doctor_filter),
    doctor_address = Proxy(finder=lambda e: e.locator("input[name*='address']"), filter_=_doctor_filter),
    doctor_zipcode = Proxy("textbox", name="Postnummer"),
    doctor_city = Proxy("textbox", name="By"),
    doctor_phone = Proxy("textbox", name="telefon"),
)

class FormGateway:
    #doctor_first_name = Element(Locator.get_by_role())
    #page.get_by_role("textbox", name="Fornavn").fill("doktorfirstname")
    
    def __init__(self, element: Locator):
        self.proxies = {k: v for k, v in PROXIES.items()}
        self.element = element
    
    def is_present(self, key: str):
        proxy = self.proxies[key]
        return proxy.is_present(element=self.element)
    
    def is_present(self, key: str):
        p = self.proxies[key]
        hits = p.get_matches(self.element)
        return len(hits) > 0
    
    def present_fields(self):
        for key in self.proxies.keys():
            if self.is_present(key):
                logger.debug(f"{self} detected {key} is present")
                yield key
            #
        #
    
    def __setitem__(self, key: str, value):
        logger.debug(f"Proxy attempting to set {key} = {value}")
        proxy = self.proxies[key]
        proxy.set_value(element=self.element, value=value)
        logger.debug(f"Proxy set {key} = {value}")
    
    def __getitem__(self, key: str):
        proxy = self.proxies[key]
        res = proxy.get_value(element=self.element)
        return res
    #
    
    def signature(self) -> tuple:
        """Returns a tuple of 0's and 1's indicating whether each field is present.
        This can be used as a kind of signature, to differentiate between the various pages of a form"""
        
        keys = sorted(self.proxies.keys())
        res = tuple(self.proxies[k].is_present(self.element) for k in keys)
        return res
    #


if __name__ == '__main__':
    fg = FormGateway(element=None)
    print(fg.proxies)
