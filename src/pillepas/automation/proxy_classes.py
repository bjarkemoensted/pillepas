from __future__ import annotations
import datetime
import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator
from typing import Any, Dict, final, Iterable, Tuple

from pillepas.automation.utils import WaitForChange


class Proxy:
    def __init__(
            self, element: Locator, sensitive=False, key: str=None, order: int|float=0):
        """Proxy for a form element, to harmonize get/set logic. The ideas is to create
        subclasses of this for specific types of inputs (radio buttons, dropdowns, text, etc).
        element: Locator for the topmost element in the form.
        sensitive: Whether the field contains sensitive information (influences whether saved and logged)
        key: Optional key representing the key used for the proxy (useful for debugging etc)
        order: Optional int for specifying an order, e.g. to fill elements with order 1 before order 2."""
        
        self.e = element
        self.sensitive = sensitive
        self.key = key
        self.order = order
        # Cache whether element is present, so we can log changes only
        self._present_when_last_checked: bool = None
    
    def copy_for_nth_match(self, i: int) -> Proxy:
        res = self.__class__(element=self.e.nth(i), sensitive=self.sensitive, key=self.key)
        return res
    
    def __repr__(self):
        s = self.__class__.__name__
        if self.key:
            s = f"{s} <{self.key}>"
        
        return s
    
    def __str__(self):
        return repr(self)
    
    def type_(self, s: str):
        """Enters text by simulating keyboard input"""
        self.e.page.keyboard.type(s, delay=50)
    
    def _set(self, value: str):
        self.e.first.click(force=True)
        self.e.first.fill(value)
    
    def _get(self):
        res = self.e.first.get_attribute("value")
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
        present = self.e.count() > 0
        if not (present is self._present_when_last_checked):
            logger.debug(f"{repr(self)} detected as present: {present}.")
            self._present_when_last_checked = present
        return  present
    #


class AutocompleteProxy(Proxy):
    """Proxy for text field where value must be selected from a list of autocompletions, which
    updates as more text is typed.
    Works by repeatedly entering more text, until the required value appears, then selecting it."""
    
    def _set(self, value: str):
        self.e.click()
        # Locator for the desired value in the options
        top = self.e.locator("..").locator("..")
        target = top.get_by_role("option", name=value, exact=True)
        
        for i, char in enumerate(value):
            # It seems a minimum of 3 characters must be entered for options to appear
            if i < 3:
                self.type_(char)
                continue
            
            # Enter the next character and watch for changes in the suggestions
            with WaitForChange(top.get_by_label("Suggestions")):
                self.type_(char)
            top.get_by_role("option").first.wait_for(state="visible", timeout=3000)
            
            # Stop typing if an option has the desired value
            if target.count() > 0:
                break
        
        if target.count() == 1:
            target.click()
            
            #
        #
    #


class DropDownProxy(Proxy):
    """Proxy for text field where an option must be selected from a dropdown with suggestions."""
    def _set(self, value: str):
        # Start by grabbing the select element bc it gets disabled  when we start typing, apparently
        select_elem = self.e.locator("..").locator("select").element_handle()

        self.e.click(force=True)
        select_elem.select_option(label=value)
        select_elem.press("Escape")
    
    def _get(self):
        res = self.e.first.inner_text()
        return res


class RadioButtonProxy(Proxy):
    """Proxy for form radio buttons (multiple select where only one can be selected). Used for e.g. gender."""
    def _set(self, value):
        target_button = self.e.locator(f'button[value={value}]')
        target_button.click()
        
    def _get(self):
        selected = self.e.locator('[role="radio"][aria-checked="true"]')
        val = selected.get_attribute('value')
        return val
    #


class DateSelectorProxy(Proxy):
    """Proxy for picking pairs of dates (start and end of travel) from a date picker."""
    
    # Define Danish month names explicitly so we don't have to rely on any locale stuff being installed
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


class MedicineProxy(Proxy):
    def __init__(self, element, sub_proxies: Dict[str, Proxy], **kwargs):
        self._sub_proxies = sub_proxies
        self.sub_proxies = []
        self._add_sub_proxies()
        super().__init__(element, **kwargs)
    
    def _add_sub_proxies(self):
        i = len(self.sub_proxies)
        new_subs = {k: p.copy_for_nth_match(i) for k, p in self._sub_proxies.items()}
        self.sub_proxies.append(new_subs)
    
    def is_present(self):
        for proxies in self.sub_proxies:
            for proxy in proxies.values():
                if not proxy.is_present():
                    return False
                #
            #
        return True
    
    def get_value(self):
        res = []
        for d in self.sub_proxies:
            val = dict()
            for k, p in d.items():
                thisval = p.get_value()
                val[k] = thisval
            res.append(val)
            
        return res
    
    def _reuse_doctor_info(self):
        page = self.e.page
        
        # Click 'yes' to reuse existing doctor information
        heading = page.get_by_role("heading", name="Information om lægen").nth(-1)
        info_section = heading.locator("..")
        info_section.get_by_role("button", name="Ja").click()
        
        # Choose the existing doctor info from dropdown
        dropdown = info_section.get_by_role("combobox").filter(has_text="Vælg en læge")
        dropdown.click()
        page.keyboard.press("Enter")
    
    def set_value(self, value: Iterable[Dict[str, str]]):
        # Go over all subproxies and use them to set data
        
        for i, d in enumerate(value):
            proxies = self.sub_proxies[i]
            if set(d.keys()) != set(proxies.keys()):
                raise RuntimeError(f"Keys mismatch medicine ({d.keys()}) vs proxies ({self.sub_proxies.keys()})")
        
            for key, proxy in proxies.items():
                val = d[key]
                proxy.set_value(val)
            #
        
            last = i == len(value) - 1
            first = i == 0
            if not first:
                self._reuse_doctor_info()
            if not last:
                self.e.page.get_by_role("button", name="Tilføj mere medicin").click()
                self._add_sub_proxies()
        #
    #


if __name__ == '__main__':
    pass
