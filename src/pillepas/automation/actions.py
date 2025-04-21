import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator, Page
from typing import Callable, Dict


def _add_filter(fun: Callable[[Locator], Locator], filter_: Callable[[Locator], bool]) -> Callable[[Locator], Locator]:
    def f(element) -> Locator:
        matches = fun(element)
        candidates = matches.all()
        candidates = [c for c in candidates if filter_(c)]
        
        if len(candidates) == 1:
            return candidates[0]
        #
    
    return f


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
    def __init__(
        self,
        role: str=None,
        finder: Callable[[Locator], Locator]=None,
        filter_: Callable[[Locator], bool]=None,
        **role_kwargs
        ):
        
        if role:
            assert finder is None
            finder = lambda e: e.get_by_role(role, **role_kwargs)
        
        if filter_:
            finder = _add_filter(finder, filter_=filter_)
            
        
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

def _doc(element: Locator) -> bool:
    """For filtering 'doctor' in name attribute (doctor's name field is like firstName.doctor or something)"""
    res = "doctor" in element.get_attribute("name").lower()
    return res

# For spotting non-doctor attributes
_nodoc = lambda e: not _doc(e)



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
    doctor_address = "Amerikavej",
    doctor_zipcode = "2200",
    doctor_city = "Kbh",
    doctor_phone="123213123",
    user_firstname="bjarke",
    user_lastname="monsted",
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

PROXIES = dict(
    medicine = AutocompleteProxy(finder=lambda loc: loc.get_by_placeholder("Skriv navnet på din medicin")),
    daily_dosis = Proxy("spinbutton", name="Daglig dosis i antal enheder"),
    n_days_with_meds = DropDownProxy("combobox", name="Antal dage med medicin"),
    doctor_first_name = Proxy("textbox", name="Fornavn", filter_=_doc),
    doctor_last_name = Proxy("textbox", name="Efternavn", filter_=_doc),
    doctor_address = Proxy(finder=lambda e: e.locator("input[name*='address']"), filter_=_doc),
    doctor_zipcode = Proxy("textbox", name="Postnummer", filter_=_doc),
    doctor_city = Proxy("textbox", name="By", filter_=_doc),
    doctor_phone = Proxy("textbox", name="telefon", filter_=_doc),
    user_firstname=Proxy("textbox", name="Fornavn", filter_= _nodoc),
    user_lastname=Proxy("textbox", name="Efternavn", filter_= _nodoc),
    
    # TODO click the autocomplete thingy!!!
    user_address=Proxy(finder=lambda e: e.locator("input[name*='address']"), filter_= lambda e: not _doc(e)),
    user_zipcode = Proxy("textbox", name="Postnummer", filter_= _nodoc),
    user_city = Proxy("textbox", name="By", exact=True, filter_= _nodoc),
    user_passport_number = Proxy("textbox", name="Pasnummer"),
    user_birthdate = Proxy("textbox", name="Indtast din fødselsdato (DD-"),
    user_birth_city = Proxy("textbox", name="Fødeby"),
    user_nationality = Proxy("textbox", name="Nationalitet"),
    user_email = Proxy("textbox", name="E-mail"),
    user_phone_number = Proxy("textbox", name="Telefonnummer", filter_= _nodoc),
    user_gender = RadioButtonProxy(label="Køn")
    #pharmacy_name=Proxy("placeholder", value="Indtast apotekets navn")
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
    
    def is_sensitive(self, key):
        return self.proxies[key].sensitive
    
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
        logger.debug(f"{repr(self)} is setting key: '{key}'")
        proxy = self.proxies[key]
        proxy.set_value(element=self.element, value=value)
        logger.debug(f"Proxy set {key} = {value}")
    
    def __getitem__(self, key: str):
        logger.debug(f"{repr(self)} is getting key: '{key}'")
        proxy = self.proxies[key]
        res = proxy.get_value(element=self.element)
        return res
    #
    
    def signature(self) -> int:
        """Returns a distinct integer which depends on the combination of fields that are currently visible.
        This can be used as a kind of signature, to differentiate between the various pages of a form"""
        
        bits = []
        for k, v in sorted(self.proxies.items()):
            logger.debug(f"Signature check for presence: {k}")
            present = v.is_present(self.element)
            bits.append(present)
        
        bin_str = "".join((str(int(p)) for p in bits))
        res = int(bin_str, 2)
        return res
    #


if __name__ == '__main__':
    fg = FormGateway(element=None)
    print(fg.proxies)
