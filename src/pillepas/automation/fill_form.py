import logging
logger = logging.getLogger(__name__)

from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright
from playwright._impl._errors import TargetClosedError
import time

from pillepas.automation.actions import Proxies
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
    page.get_by_label("april").get_by_role("gridcell", name="25").click()
    page.get_by_role("button", name="Go to next month").click()
    page.get_by_role("button", name="Go to previous month").click()
    page.get_by_role("button", name="Go to next month").click()
    page.get_by_label("maj").get_by_role("gridcell", name="9", exact=True).click()
    page.get_by_role("button", name="Gem datoer").click()
    return


class Session:
    url = config.URL
    
    def __init__(self, fill_data: dict, auto_click_next=False, headless=False):
        self.fill_data = fill_data
        self.saved_fields = set([])
        self.read_fields = dict()
        self.auto_click_next = auto_click_next
        self.processed_pages_signatures = set([])  # For figuring out if we already did a page
        
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context = None
        self.page: Page | None = None
        self.proxies: Proxies = None
    
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(color_scheme="dark")
        self.page = self.context.new_page()
        self.page.goto(self.url)
        self.proxies = Proxies(self.form)

        self.page.on("close", on_page_close)
        
        #self.page.on("framenavigated", lambda: print("omgomg"))

    def _click_and_wait(self, button_name: str):
        with WaitForChange(self.page, self.form):
            self.form.get_by_role("button", name=button_name).click()
        #

    def next_page(self):
        page_done = all(field in self.saved_fields for field in self.proxies.present_fields())
        if page_done:
            self._click_and_wait(button_name="Næste")

    def _log_str(self, key: str, value):
        valstring = str(value)
        if self.proxies[key].sensitive:
            valstring = "*"*len(valstring)
        
        s = f"{key} = {valstring}"
        return s

    def process_current_page(self, force_reprocess=False):
        """Go over all present fields, write any unwritten data, and update read values"""
        
        sig = self.proxies.signature()
        if sig in self.processed_pages_signatures and not force_reprocess:
            return
        
        logger.info(f"Processing form page with signature {sig}")
        self.processed_pages_signatures.add(sig)
        
        for key in self.proxies.present_fields():
            
            needs_write = key not in self.saved_fields and key in self.fill_data
            if needs_write:
                try:
                    val = self.fill_data[key]
                    
                    self.proxies[key].set_value(val)
                    logger.info(f"Filled form element: {self._log_str(key, val)}.")
                except Exception as e:
                    logger.error(f"{self} failed to fill element: {key} - {e}")
                
                self.saved_fields.add(key)
            #
            
            current_val = self.proxies[key].get_value()
            if current_val != self.read_fields.get(key):
                self.read_fields[key] = current_val
                logger.info(f"Read form element: {self._log_str(key, current_val)}.")
        
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
    HEADLESS = False
    DEBUG_LEVEL = logging.DEBUG
    
    from pillepas.automation.actions import vals
    import logging
    
    from pathlib import Path
    path = Path("/tmp/deleteme.json")

    logpath = path.parent / "log.log"
    logpath.unlink(missing_ok=True)
    logging.basicConfig(
        level=DEBUG_LEVEL,
        #filename=str(logpath)
    )
    
    sess = Session(vals, auto_click_next=True, headless=HEADLESS)
    sess.start()
    DATESTUFF(sess.page)
    
    now = time.time()
    
    while True:
        sess.process_current_page()
        print(int(time.time()))
        time.sleep(1)
        
        
    #print(logpath.read_text())
    
    
    