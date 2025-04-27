import datetime
import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator, Page
from typing import Any, final, Generator, Tuple
import time

from pillepas.automation.utils import WaitForChange

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


def parse_element(element: Locator):
    """Helper method for grabbing a bunch of info on a given element, for debugging etc"""
    attrs = ("id", "value", "name", "class", "type")
    if element:
        d = {attr: element.get_attribute(attr) for attr in attrs}
        d["tag"] = element.evaluate("el => el.tagName")
        d["text"] = element.inner_text()
        return d
    return None


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
    
    def type_(self, s: str):
        self.e.page.keyboard.type(s, delay=50)
    
    def _set(self, value: str):
        self.e.click(force=True)
        self.e.fill(value)
    
    def _get(self):
        res = self.e.get_attribute("value")
        return res

    @final
    def set_value(self, value: Any):
        logger.debug(f"{self} is setting value: {'*'*len(str(value)) if self.sensitive else value}")
        self._set(value=value)
        self.e.dispatch_event('change')
        
    @final
    def get_value(self) -> Any:
        logger.debug(f"{self} is getting value.")
        res = self._get()
        return res
    
    def is_present(self):
        return self.e.count() > 0
    #


class AutocompleteProxy(Proxy):
    def _set(self, value: str):
        self.e.click()
        top = self.e.locator("..").locator("..")
        target = top.get_by_role("option", name=value, exact=True)
        
        for i, char in enumerate(value):
            
            if i < 3:
                self.type_(char)
                continue
            
            with WaitForChange(top.get_by_label("Suggestions")):
                self.type_(char)

            top.get_by_role("option").first.wait_for(state="visible", timeout=3000)
            #top.get_by_label("Suggestions").first.wait_for(state="visible", timeout=3000)
            

            if target.count() > 0:
                break
        
        if target.count() == 1:
            target.click()
            
            #
        #
    #


class DropDownProxy(Proxy):
    def _set(self, value: str):
        select_elem = self.e.locator("..").locator("select").element_handle()
        
        self.e.click(force=True)
        # Select the option with the max value
        select_elem.select_option(label=value)
        select_elem.press("Escape")
    #


class RadioButtonProxy(Proxy):
    def _set(self, value):
        target_button = self.e.locator(f'button[value={value}]')
        target_button.click()
        
    def _get(self):
        selected = self.e.locator('[role="radio"][aria-checked="true"]')
        val = selected.get_attribute('value')
        return val
    #


class DateSelectorProxy(Proxy):
    months = (
        'januar', 'februar', 'marts', 'april', 'maj', 'juni',
        'juli', 'august', 'september', 'oktober', 'november', 'december'
    )
    
    def _month_label_from_date(self, date: datetime.date) -> str:
        """Creates a label like 'april 2025', for locating the correct pane from which to select a date"""
        ind = date.month - 1  # date.month's start at 1, so subtract 1 to get the index
        month_str = self.months[ind]
        res = f"{month_str} {date.strftime("%Y")}"
        return res
    
    @property
    def dialog(self):
        """Locates the dialog box for picking dates"""
        today = datetime.date.today()
        target = self._month_label_from_date(today)
        res = self.e.page.get_by_role('dialog').filter(has_text=target)
        return res
    
    def scroll_to_date(self, date: datetime.date):
        """Scrolls the dialog box forward until the specified month label (e.g. 'april 2025') appears,
        then locates the input date, and clicks it."""

        dia = self.dialog
        target = self._month_label_from_date(date)
        _max = 12  # Something's probably wrong if we need to scroll this long
        pane = dia.get_by_label(target)

        # Keep scrolling until the pana appears
        for _ in range(_max):
            if pane.count() > 0:
                break
            dia.get_by_role("button", name="Go to next month").click()
        
        # Locate date and click it
        date_cell = pane.get_by_role("gridcell", name=str(date.day), exact=True)
        date_cell.click()
    
    def _set(self, value: Tuple[datetime.date]):
        self.e.click()
        
        for date in value:
            self.scroll_to_date(date)
        
        self.dialog.get_by_role("button", name="Gem datoer").click()
    
    def _parse_short_date(self, datestring: str) -> datetime.date:
        """Parses dates represented with abreviated names like '25. apr. 2025' into a date instance."""
        
        date_s, month_s, year_s = datestring.replace(".", "").split()
        # Take the first month which starts with the abreviation
        month_ind = next(i for i, m in enumerate(self.months) if m.startswith(month_s))
        res = datetime.date(int(year_s), month_ind+1, int(date_s))
        return res
    
    def _get(self):
        """The dates are represented with abreviated names like '25. apr. 2025', so we need to parse that back into
        a date."""
        s = self.e.inner_text()
        
        parts = s.strip().split(" - ")
        res = tuple(self._parse_short_date(part) for part in parts)

        return res
    #


def make_proxies(elem: Page|Locator) -> dict:
    page = elem.page
    dr_css = ':scope[name*="doctor"]'
    nodr_css = ':scope:not([name*="doctor"])'

    d = dict(
        dates=DateSelectorProxy(elem.locator("button[id='date']")),
        medicine=AutocompleteProxy(page.get_by_role("combobox").filter(has=page.locator(':scope[name*="drug"]'))),
        daily_dosis=Proxy(elem.get_by_role("spinbutton", name="Daglig dosis i antal enheder")),
        n_days_with_meds=DropDownProxy(elem.get_by_role("combobox", name="Antal dage med medicin")),

        doctor_first_name=Proxy(elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(dr_css))),
        doctor_last_name=Proxy(elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(dr_css))),
        doctor_address=Proxy(elem.locator('input[name*="address"]').filter(has=page.locator(dr_css))),
        doctor_zipcode=Proxy(elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(dr_css))),
        doctor_city=Proxy(elem.get_by_role("textbox", name="By").filter(has=page.locator(dr_css))),
        doctor_phone=Proxy(elem.get_by_role("textbox", name="telefon").filter(has=page.locator(dr_css))),

        user_first_name=Proxy(elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(nodr_css))),
        user_last_name=Proxy(elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(nodr_css))),
        user_address=Proxy(elem.locator("input[name*='address']").filter(has=page.locator(nodr_css))),
        user_zipcode=Proxy(elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(nodr_css))),
        user_city=Proxy(elem.get_by_role("textbox", name="By", exact=True).filter(has=page.locator(nodr_css))),
        user_passport_number=Proxy(elem.get_by_role("textbox", name="Pasnummer").filter(has=page.locator(nodr_css)), sensitive=True),
        user_birthdate=Proxy(elem.get_by_role("textbox", name="Indtast din fødselsdato (DD-").filter(has=page.locator(nodr_css))),
        user_birth_city=Proxy(elem.get_by_role("textbox", name="Fødeby").filter(has=page.locator(nodr_css))),
        user_nationality=Proxy(elem.get_by_role("textbox", name="Nationalitet").filter(has=page.locator(nodr_css))),
        user_email=Proxy(elem.get_by_role("textbox", name="E-mail").filter(has=page.locator(nodr_css))),
        user_phone_number=Proxy(elem.get_by_role("textbox", name="Telefonnummer").filter(has=page.locator(nodr_css))),
        user_gender=RadioButtonProxy(elem.locator('label', has_text="Køn").locator("..").locator("..")),
        pharmacy_address=AutocompleteProxy(elem.locator("input[placeholder='Indtast apotekets navn']")),
    )
    
    return d


class Proxies(dict[str, Proxy]):
    #doctor_first_name = Element(Locator.get_by_role())
    #page.get_by_role("textbox", name="Fornavn").fill("doktorfirstname")
    
    def __init__(self, element: Locator):
        super().__init__()
        self.element = element
        
        _proxies = make_proxies(element)
        for key, proxy in _proxies.items():
            self[key] = proxy
        #
    #
    
    def present_fields(self):
        for key, proxy in self.items():
            if proxy.is_present():
                logger.debug(f"{repr(self)} detected {key} is present")
                yield key
            #
        #
    
    def __repr__(self):
        return self.__class__.__name__
    
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
