from playwright.sync_api import Browser, Page, Playwright, sync_playwright
from playwright._impl._errors import TargetClosedError

import time

from pillepas import config


def _get_data():
    # for testing, delete!!!
    from pillepas.cli.cli import GatewayInterface
    g = GatewayInterface.create_with_prompt()
    
    res = {k: v for k, v in g._data.items()}
    return res


def probe_element(element):
    if element:
        attr_dict = {
            "tag": element.evaluate("el => el.tagName"),
            "id": element.get_attribute("id"),
            "name": element.get_attribute("name"),
            "class": element.get_attribute("class"),
            "type": element.get_attribute("type"),
            "text": element.inner_text(),
        }
        return attr_dict
    return None


def expose(page: Page):
    page.expose_binding("recordInput", lambda source, data: print("User typed:", data))

    # Inject JS to listen for user input changes
    page.add_init_script("""
        document.addEventListener("input", (event) => {
            const target = event.target;
            if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
                const data = {
                    tag: target.tagName,
                    name: target.name,
                    id: target.id,
                    value: target.value,
                };
                window.recordInput(data);
            }
        });
    """)


def on_page_close():
    print("The page has been closed by the user!")
            

class Session:
    url = config.URL
    
    def __init__(self, form_contents: dict):
        self.form_contents = form_contents
        self.read = dict()
        
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
    
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
    
    def fill(self):
        p = sync_playwright()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(self.url)
            
            
            # Locate the form (e.g., first form on the page)
            form = page.query_selector("form")
            
            # Get all input, select, and textarea elements inside the form
            form_elements = form.query_selector_all("input, select, textarea, button")

            # Print out details of each element
            for element in form_elements:
                print(f"Tag: {element.evaluate('el => el.tagName')}, Name: {element.get_attribute('name')}")

            
            while True:
                time.sleep(0.5)

            # # Fill in the username field
            # page.fill('input[name="username"]', 'myUsername')

            # # Optionally, fill in password and submit
            # page.fill('input[name="password"]', 'mySecretPassword')
            # page.click('button[type="submit"]')

        #
    #


if __name__ == '__main__':
    data = _get_data()
    sess = Session(data)
    sess.start()
    
    while True:
        time.sleep(0.1)
        print(sess.is_alive(), int(time.time()))

        
    
    