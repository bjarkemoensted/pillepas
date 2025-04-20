import logging
logger = logging.getLogger(__name__)

from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright
from playwright._impl._errors import TargetClosedError
import time

from pillepas.automation.actions import FormGateway
from pillepas.automation.utils import WaitForChange
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


# TODO DELETE!!!!!
def DATESTUFF(page):
    page.get_by_role("button", name="Vælg dato for udrejse og").click()
    page.get_by_label("april").get_by_role("gridcell", name="21").click()
    page.get_by_role("button", name="Go to next month").click()
    page.get_by_role("button", name="Go to previous month").click()
    page.get_by_role("button", name="Go to next month").click()
    page.get_by_label("maj").get_by_role("gridcell", name="9", exact=True).click()
    page.get_by_role("button", name="Gem datoer").click()
    return


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
    
    def __init__(self, fill_data: dict, auto_click_next=False):
        self.fill_data = fill_data
        self.saved_fields = set([])
        self.read_fields = dict()
        self.auto_click_next = auto_click_next
        
        # self.name_to_key = {field.name: field.key for field in FIELDS}
        # assert len(self.name_to_key) == len(FIELDS)
        # self.read = dict()
        # self.already_filled_names = set([])
        
        self.processed_pages_signatures = set([])  # For figuring out if we already did a page
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context = None
        self.page: Page | None = None
        self.form_gateway = None
    
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(color_scheme="dark")
        self.page = self.context.new_page()
        self.page.goto(self.url)
        self.form_gateway = FormGateway(self.form)

        self.page.on("close", on_page_close)
        
        #self.page.on("framenavigated", lambda: print("omgomg"))

    def _click_and_wait(self, button_name: str):
        with WaitForChange(self.page, self.form):
            self.form.get_by_role("button", name=button_name).click()
        #

    def next_page(self):
        page_done = all(field in self.saved_fields for field in self.form_gateway.present_fields())
        if page_done:
            self._click_and_wait(button_name="Næste")

    def process_current_page(self, force_reprocess=False):
        """Go over all present fields, write any unwritten data, and update read values"""
        
        sig = self.form_gateway.signature()
        if sig in self.processed_pages_signatures and not force_reprocess:
            return
        
        self.processed_pages_signatures.add(sig)
        
        for key in self.form_gateway.present_fields():
            
            needs_write = key not in self.saved_fields and key in self.fill_data
            if needs_write:
                try:
                    self.form_gateway[key] = self.fill_data[key]
                except Exception as e:
                    logger.error(f"{self} failed to write field: {key} - {e}")
                
                self.saved_fields.add(key)
            #
            
            current_val = self.form_gateway[key]
            if current_val != self.read_fields.get(key):
                self.read_fields[key] = current_val
                logger.debug(f"Read {len(current_val)} chars from field '{key}'.")
        
        if self.auto_click_next:
            self.next_page()
        
    def is_alive(self) -> bool:
        """Whether the session is alive (to avoid things hanging)"""
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
    #
    

if __name__ == '__main__':
    from pillepas.automation.actions import vals
    import logging
    
    from pathlib import Path
    path = Path("/tmp/deleteme.json")

    logpath = path.parent / "log.log"
    logpath.unlink(missing_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        #filename=str(logpath)
    )
    
    sess = Session(vals, auto_click_next=True)
    sess.start()
    DATESTUFF(sess.page)
    
    while True:
        sess.process_current_page()
        print(int(time.time()))
        time.sleep(1)
        
    #print(logpath.read_text())
    
    
    