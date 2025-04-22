import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator, Page
from typing import Callable, Dict, Type, Generator, Tuple
import time


# add more medzz
# page.get_by_role("button", name="Tilføj mere medicin").click()
# page.locator("input[name=\"medication\\.1\\.drug\"]").click()
# page.locator("input[name=\"medication\\.1\\.drug\"]").fill("elv")
# page.get_by_role("option", name="Elvanse, kapsler, hårde, 20 mg 'Orifarm'").click()
# page.locator("button").filter(has_text="Vælg antallet af dage med").click()
# page.get_by_role("option", name="Alle dage").click()
# page.locator("input[name=\"medication\\.1\\.dailyDose\"]").click()
# page.locator("input[name=\"medication\\.1\\.dailyDose\"]").fill("1")
# page.get_by_role("button", name="Ja").click()
# page.get_by_role("button", name="Næste").click()
# page.get_by_role("button", name="Næste").click()
# page.get_by_role("combobox").filter(has_text="Vælg en læge").click()
# page.get_by_role("option", name="doktorfirstname doctor").click()


# address autocomplete stuff:
# page.get_by_placeholder("Indtast din adresse").click()
# page.get_by_placeholder("Indtast din adresse").fill("tagensvej 98")
# page.get_by_role("option", name="Tagensvej 98, 2200 København N").click()


class Proxy:
    def __init__(
            self, element: Locator, sensitive=False, key: str=None):
        """Proxy for a form element, to harmonize get/set logic. The ideas is to create
        subclasses of this for specific types of inputs (radio buttons, dropdowns, text, etc).
        element: Locator for the topmost element in the form.
        sensitive: Whether the field contains sensitive information (influences whether saved and logged)
        key: Optional key representing the key used for the proxy (useful for debugging etc)"""
        
        self.e = element
        self.sensitive = sensitive
        self.key = key
    
    def __repr__(self):
        s = self.__class__.__name__
        if self.key:
            s = f"{s} <{self.key}>"
        
        return s
    
    def __str__(self):
        return repr(self)
    
    def set_value(self, value: str):
        logger.debug(f"{self} is setting value: {'*'*len(str(value)) if self.sensitive else value}")
        self.e.click(force=True)
        self.e.fill(value)
        self.e.dispatch_event('change')
        
    def get_value(self):
        logger.debug(f"{self} is getting value.")
        res = self.e.get_attribute("value")
        return res
    
    def is_present(self):
        return self.e.count() > 0
    #


class AutocompleteProxy(Proxy):
    def set_value(self, value: str):
        self.e.click()
        top = self.e.locator("..").locator("..")
        target = top.get_by_role("option", name=value)
        
        for char in value:
            if char.isalnum():
                self.e.press(char, delay=50)
            else:
                break
        
        # TODO wait for suggestion list to appear instead!!!
        time.sleep(1.0)
        
        if target.count() == 1:
            target.click()
            
            #
        #
    #


class DropDownProxy(Proxy):
    def set_value(self, value: str):
        select_elem = self.e.locator("..").locator("select").element_handle()
        
        self.e.click(force=True)
        # Select the option with the max value
        select_elem.select_option(label=value)
        select_elem.press("Escape")
    #


class RadioButtonProxy(Proxy):
    
    def __init__(self, label: str):
        self.label = label
        super().__init__(finder=self._finder)  # TODO clumsy. Should init with base element and expose the relevant elem as property!!!
    
    def _finder(self, element: Locator):
        label = element.locator('label', has_text=self.label)
        if label.count() == 0:
            return
        
        id_ = label.get_attribute('for')
        top_elem = element.locator(f'[id="{id_}"]')
        #radio_group = label.locator('..').locator('..').get_by_role('radiogroup')
        return top_elem
    
    def set_value(self, element, value):
        # locate label: e.locator('label', has_text=value).count()
        e = self._finder(element)
        target_button = e.locator(f'button[value={value}]')
        target_button.click()
        
    def get_value(self, element):
        e = self.finder(element)
        selected = e.locator('[role="radio"][aria-checked="true"]')
        val = selected.get_attribute('value')
        return val

# ['Male', 'Female', 'Unspecified']  # gender vals


# page.get_by_text("Kvinde (F)").click()
# page.get_by_text("Uspecificeret (X)").click()
# page.get_by_text("Kvinde (F)").click()
# page.get_by_role("radio", name="Uspecificeret (X)").click()
# page.get_by_role("radio", name="Mand (M)").click()



gender_stuff = ("Kvinde (F)", "Mand (M)", "Uspecificeret (X)")


vals = dict(
    medicine = "Elvanse, kapsler, hårde, 20 mg 'Takeda Pharma'",
    daily_dosis = "1",
    n_days_with_meds = "Alle dage",
    doctor_first_name = "meh",
    doctor_last_name = "meh",
    doctor_address = "Amerikavej 15C, 1",
    doctor_zipcode = "2200",
    doctor_city = "Kbh",
    doctor_phone="123213123",
    user_first_name="bjarke",
    user_last_name="monsted",
    user_address="tagensvej 98",
    user_zipcode = "2200",
    user_city = "kbh",
    user_passport_number="123123123",
    user_birthdate="22-03-1987",
    user_birth_city="Hillerod",
    user_nationality="Dansk",
    user_email="bjarkemoensted@gmail.com",
    user_phone_number="22578098",
    user_gender = "Male",
    pharmacy_name="hamlets"
)


# medication.0.doctorInformation.address

def proxy_factory(elem: Page|Locator) -> Generator[Tuple[str, Proxy], None, None]:
    page = elem.page
    dr_css = ':scope[name*="doctor"]'
    nodr_css = ':not(:scope[name*="doctor"])'

    d = dict(
        medicine = (AutocompleteProxy, page.get_by_role("combobox").filter(has=page.locator(':scope[name*="drug"]'))),
        daily_dosis = (Proxy, elem.get_by_role("spinbutton", name="Daglig dosis i antal enheder")),
        n_days_with_meds = (DropDownProxy, elem.get_by_role("combobox", name="Antal dage med medicin")),
        doctor_first_name = (Proxy, elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(dr_css))),
        doctor_last_name = (Proxy, elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(dr_css))),

        
        doctor_address = (AutocompleteProxy, elem.locator('input[name*="address"]').filter(has=page.locator(dr_css))),
        doctor_zipcode = (Proxy, elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(dr_css))),
        doctor_city = (Proxy, elem.get_by_role("textbox", name="By").filter(has=page.locator(dr_css))),
        doctor_phone = (Proxy, elem.get_by_role("textbox", name="telefon").filter(has=page.locator(dr_css))),

        user_first_name = (Proxy, elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(nodr_css))),
        user_last_name = (Proxy, elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(nodr_css))),

        # TODO click the autocomplete thingy!!!
        user_address = (Proxy, elem.locator("input[name*='address']").filter(has=page.locator(nodr_css))),
        user_zipcode = (Proxy, elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(nodr_css))),
        user_city = (Proxy, elem.get_by_role("textbox", name="By").filter(has=page.locator(nodr_css))),
        user_passport_number = (Proxy, elem.get_by_role("textbox", name="Pasnummer").filter(has=page.locator(nodr_css))),
        user_birthdate = (Proxy, elem.get_by_role("textbox", name="Indtast din fødselsdato (DD-").filter(has=page.locator(nodr_css))),
        user_birth_city = (Proxy, elem.get_by_role("textbox", name="Fødeby").filter(has=page.locator(nodr_css))),
        user_nationality = (Proxy, elem.get_by_role("textbox", name="Nationalitet").filter(has=page.locator(nodr_css))),
        user_email = (Proxy, elem.get_by_role("textbox", name="E-mail").filter(has=page.locator(nodr_css))),
        user_phone_number = (Proxy, elem.get_by_role("textbox", name="Telefonnummer").filter(has=page.locator(nodr_css))),



        #user_gender = RadioButtonProxy(label="Køn"),
        pharmacy_name = (Proxy, elem.locator("input[placeholder='Indtast apotekets navn']"))

        # user_first_name = ProxyFactory(Proxy, role="textbox", name="Fornavn", css=':not([name*="doctor"])'),
        # user_last_name=ProxyFactory(Proxy, role="textbox", name="Efternavn", css=':not([name*="doctor"])'),
        
        # TODO click the autocomplete thingy!!!
        #user_address=Proxy(finder=lambda e: e.locator("input[name*='address']"), filter_= lambda e: not _doc(e)),
        #user_zipcode = Proxy("textbox", name="Postnummer", filter_= _nodoc),
        #user_city = Proxy("textbox", name="By", exact=True, filter_= _nodoc),
        #user_passport_number = Proxy("textbox", name="Pasnummer"),
        #user_birthdate = Proxy("textbox", name="Indtast din fødselsdato (DD-"),
        #user_birth_city = Proxy("textbox", name="Fødeby"),
        #user_nationality = Proxy("textbox", name="Nationalitet"),
        #user_email = Proxy("textbox", name="E-mail"),
        #user_phone_number = Proxy("textbox", name="Telefonnummer", filter_= _nodoc),
        #user_gender = RadioButtonProxy(label="Køn")
        #pharmacy_name=Proxy("placeholder", value="Indtast apotekets navn")
    )

    for key, (cls, elem) in d.items():
        proxy = cls(elem, key=key)
        yield key, proxy
    #


class Proxies(dict[str, Proxy]):
    #doctor_first_name = Element(Locator.get_by_role())
    #page.get_by_role("textbox", name="Fornavn").fill("doktorfirstname")
    
    def __init__(self, element: Locator):
        super().__init__()
        self.element = element

        for key, proxy in proxy_factory(self.element):
            self[key] = proxy
        #
    #
    
    def present_fields(self):
        for key, proxy in self.items():
            if proxy.is_present():
                logger.debug(f"{self} detected {key} is present")
                yield key
            #
        #
    
    def signature(self) -> int:
        """Returns a distinct integer which depends on the combination of fields that are currently visible.
        This can be used as a kind of signature, to differentiate between the various pages of a form"""
        
        bits = []
        for key, proxy in sorted(self.items()):
            logger.debug(f"Signature check for presence: {key}")
            present = proxy.is_present()
            bits.append(present)
        
        bin_str = "".join((str(int(p)) for p in bits))
        res = int(bin_str, 2)
        return res
    #


if __name__ == '__main__':
    pass
