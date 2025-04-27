import logging
logger = logging.getLogger(__name__)

from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright
from playwright._impl._errors import TargetClosedError
import time

from pillepas.automation.actions import FormGateway
from pillepas.automation.utils import add_wait, WaitForChange
from pillepas import config
from pillepas.persistence.data import FIELDS


def on_page_close():
    print("The page has been closed by the user!")


class Session:
    url = config.URL
    next_button_text = "Næste"
    # javascript variable for indicating whether the 'next' button has been clicked 
    user_clicked_next_var = "window.__userClickedNext"
    # javascript variable for indicating whther python has completed reading
    python_done_reading_var = "window.__pythonDoneReading"
    
    def __init__(self, fill_data: dict, auto_click_next=False, auto_submit=False, headless=False):
        """Creates a session for filling a pillepas form.
        fill_data (dict) - A dictionary containing form data
        auto_click_next (bool, default False) - whether to automatically click 'next' when a page is filled
        auto_submit (bool, default False) - Whether to automatically submit the application after it's been filled
        headless (bool, default True) - whether to run Playwright in headless mode"""

        self.fill_data = fill_data
        self.saved_fields = set([])
        self.read_fields = dict()
        self.n_reads_executed = 0
        self.auto_click_next = auto_click_next
        self.auto_submit=auto_submit
        self.processed_pages_signatures = set([])  # For figuring out if we already did a page
        
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context = None
        self.page: Page | None = None
        self.proxies: FormGateway = None
    
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(color_scheme="dark")
        self.page = self.context.new_page()
        self.page.goto(self.url)

        self.proxies = FormGateway(self.form)

        self.page.on("close", on_page_close)
    
    @property
    def form(self) -> Locator:
        return self.page.locator("form")
    #
    
    @property
    def next_button(self) -> Locator:
        btn = self.form.get_by_role("button", name=self.next_button_text)
        return btn
    
    @property
    def submit_button(self) -> Locator:
        btn = self.form.get_by_role("button", name="Bestil pillepas")
        return btn
    
    def is_last_page(self):
        return self.next_button.count() == 0
    
    def next_page(self):
        """Navigate to the next form page"""
        
        with WaitForChange(self.form):
            self.next_button.click()
        #

    def _log_str(self, key: str, value) -> str:
        """Returns a string for logging a key-value relation, e.g. 'my_key = 'my_value'.
        If the key is marked as sensitive, the value string is replaced by '*' characters."""
        
        valstring = str(value)
        if self.proxies[key].sensitive:
            valstring = "*"*len(valstring)
        
        s = f"{key} = {valstring}"
        return s

    def fill_fields_on_current_page(self):
        """Fills out the fields that are present on the current form page."""
        
        for key in self.proxies.present_fields():
            needs_write = key not in self.saved_fields and key in self.fill_data
            if needs_write:
                try:
                    val = self.fill_data[key]
                    self.proxies[key].set_value(val)
                    logstring = self._log_str(key, val)
                    logger.info(f"Filled form element: {logstring}.")
                except Exception as e:
                    logger.error(f"{self} failed to fill element: {logstring} - {e}")
                
                self.saved_fields.add(key)
            #
        #

    def read_fields_on_current_page(self):
        """Reads field data from all fields present on the current form page."""
        
        logger.debug(f"Reading all present fields")
        for key in self.proxies.present_fields():
            current_val = self.proxies[key].get_value()
            # If we read a new value, store it
            if current_val != self.read_fields.get(key):
                self.read_fields[key] = current_val
                logger.info(f"Read form element: {self._log_str(key, current_val)}.")
            #

    def _current_title(self):
        """Attempts to determine the title of the current form page"""
        headlines_form = self.form.locator("h2").all_text_contents()
        headlines_parent = self.form.locator("..").locator("h2").all_text_contents()
        diff = set(headlines_parent) - set(headlines_form)
        if len(diff) == 1:
            return list(diff)[0]

    def wait_for_user_next(self):
        add_wait(
            page=self.page,
            button_text=self.next_button_text,
            user_clicked_next_varname = self.user_clicked_next_var,
            python_done_reading_varname = self.python_done_reading_var
        )
        
        while self.page.evaluate(f"{self.user_clicked_next_var} === true") is False:
            user_clicked = self.page.evaluate(f"{self.user_clicked_next_var} === true")
            logger.debug(f"User clicked next? {user_clicked}")
            time.sleep(0.2)
        
        logger.debug("Pre-navigation read triggered")
        self.read_fields_on_current_page()
        self.page.evaluate(f"{self.python_done_reading_var} = true")

    def process_current_page(self, force_reprocess=False):
        """Go over all present fields, write any unwritten data, and update read values.
        If the page has already been processed, no action is performed except if
        force_reprocess is True."""
        
        sig = self.proxies.signature()
        if sig in self.processed_pages_signatures and not force_reprocess:
            return
        
        self.processed_pages_signatures.add(sig)
        
        # Print info on current page
        pageno = len(self.processed_pages_signatures)
        title = self._current_title()
        logger.info(f"Processing form page {pageno}{f' "{title}"'if title else ''} (signature {sig})")
        
        if self.is_last_page():
            self.process_submit_page()
            return
        
        self.fill_fields_on_current_page()
        self.read_fields_on_current_page()
        
        page_done = all(field in self.saved_fields for field in self.proxies.present_fields())
        if self.auto_click_next and page_done:
            self.next_page()
            return
        else:
            self.wait_for_user_next()
            
    
    def process_submit_page(self):
        """Processes the final page of the form"""
        
        data_consent_box = self.form.get_by_role(
            "checkbox",
            name="Jeg giver samtykke til, at apoteket behandler mine oplysninger"
        )
        medicine_card_consent_box = self.form.get_by_role(
            "checkbox",
            name="Jeg giver samtykke til, at apoteket må slå op på mit medicinkort"
        )
        
        # Check the data usage consent boxes
        data_consent_box.click()
        medicine_card_consent_box.click()
        
        # If auto-submitting, click the final submit button
        if self.auto_submit:
            self.submit_button.click()
            
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
    

if __name__ == '__main__':
    from pillepas.automation.utils import make_example_form_values
    vals = make_example_form_values()

    HEADLESS = False
    DEBUG_LEVEL = logging.DEBUG
    
    import logging
    
    from pathlib import Path
    path = Path("/tmp/deleteme.json")

    logpath = path.parent / "log.log"
    logpath.unlink(missing_ok=True)
    logging.basicConfig(
        level=DEBUG_LEVEL,
        #filename=str(logpath)
    )
    
    sess = Session(vals, auto_click_next=False, headless=HEADLESS)
    sess.start()
    
    now = time.time()
    
    while True:
        sess.process_current_page()
        print(int(time.time()))
        time.sleep(1)
        
        
    #print(logpath.read_text())
    
    
    