from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright
from playwright._impl._errors import TargetClosedError

import time

from pillepas import config
from pillepas.persistence.data import FIELDS


def _get_data():
    # for testing, delete!!!
    from pillepas.cli.cli import GatewayInterface
    g = GatewayInterface.create_with_prompt()
    
    res = {k: v for k, v in g._data.items()}
    return res


def parse_element(element: Locator):
    attrs = ("id", "value", "name", "class", "type")
    if element:
        d = {attr: element.get_attribute(attr) for attr in attrs}
        d["tag"] = element.evaluate("el => el.tagName")
        d["text"] = element.inner_text()
        return d
    return None

def on_page_close():
    print("The page has been closed by the user!")


def select_max_days(root_elem: Page|Locator):
    """Selects 'all days' option from dropdown with number of days with medication"""
    
    # Discover the element tagged 'days-with-medicine'
    cy_tag="days-with-medicine"
    cy_elem = root_elem.locator(f"[cy-tag={cy_tag}]")
    if cy_elem.count() == 0:
        return False

    # The selector has same parent as the cy-element
    select_elem = cy_elem.locator("..").locator("select")

    # Select the option with the max value
    options = select_elem.locator("option").all()
    choose_val = max((e.get_attribute("value") for e in options), key=int)
    select_elem.select_option(value=choose_val)

    return True



class Session:
    url = config.URL
    
    def __init__(self, fill_data: dict):
        self.fill_data = fill_data
        self.name_to_key = {field.name: field.key for field in FIELDS}
        assert len(self.name_to_key) == len(FIELDS)
        self.read = dict()
        self.already_filled_names = set([])
        
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
    
    def iter_elems(self, query_string="input"):
        self.page.wait_for_load_state("domcontentloaded")
        elems = self.form.locator(query_string)
        for elem in elems.all():
            name = elem.get_attribute("name")
            yield name, elem

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        self.page.goto(self.url)

        self.page.on("close", on_page_close)
        
        #self.page.on("framenavigated", lambda: print("omgomg"))

    def is_alive(self):
        try:
            _ = self.form.count()
            return True
        except TargetClosedError:
            return False
    
    def stop(self):
        self.browser.close()
        self.playwright.stop()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    @property
    def form(self):
        return self.page.locator("form")
    
    # def display_elements(self, q: str):
    #     elems = self.form.locator(q).all()
    #     for elem in elems:
    #         print(probe_element(elem))

    def fill(self):
        for name, elem in self.iter_elems():
            if name in self.already_filled_names:
                continue
            
            key = self.name_to_key.get(name)
            val = self.fill_data.get(key)
            
            if val is None:
                continue
            
            val = self.fill_data[key]
            elem.fill(val)
            self.already_filled_names.add(name)




if __name__ == '__main__':
    data = _get_data()
    data["doctor_first_name"] = "doktormand"  # !!!
    sess = Session(data)
    sess.start()
    