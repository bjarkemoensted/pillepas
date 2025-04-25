from playwright.sync_api import Locator, Page, TimeoutError


class WaitForChange:
    """Context manager for getting Playwright to wait until Something Changed^tm, e.g. when clicking 'next'
    in a form. Usually, one would simply wait for the required element to appear.
    However, that causes issues if e.g. we're skipping from page 1 to page 2 of a form,
    and a locator matches something on both pages.
    Another approach would be to wait for some present element to disappear after clicking next, but that
    relies on assumptions about which elements exist on the next page.
    
    This class addresses the issue by reading a locator's inner HTML prior to taking an action,
    then after the action, waiting for the HTML to change and the DOM to stabilize.
    
    Example:
    
    with WaitForChange(my_form):
        my_form.get_by_role("button", name="Next").click()
    
    # After de-indenting, the next page should be ready
    """
    
    def __init__(self, locator: Locator):
        self.locator = locator
        self.page = self.locator.page
        self.innerHTML = None
    
    def __enter__(self):
        self.innerHTML = self.locator.inner_html()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.page.wait_for_function(
                expression = "(oldHTML) => document.querySelector('form')?.innerHTML !== oldHTML",
                arg = self.innerHTML,
                timeout=3000
            )
        except TimeoutError:
            pass
        
        self.page.wait_for_load_state("domcontentloaded")
        self.innerHTML = None
    #
