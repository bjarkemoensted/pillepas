import datetime
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


def add_wait(page: Page, button_text: str, user_clicked_next_varname: str, python_done_reading_varname: str):
    """Injects an event listener which delays an event until 'variable_name' has incremented.
    This is useful for delaying navigating away from a form page until any newly entered
    information has been read by python.
    The python method which reads the data must then increment the variable and be run
    repeatedly until the next button is clicked.
    The generated javascript checks if the callback has already been attached,
    so calling it multiple times should cause issues."""
    
    js = f"""
        const button = Array.from(document.querySelectorAll('button')).find(
            el => el.textContent.trim() === '{button_text}'
        );
        
        {user_clicked_next_varname} = false;
        {python_done_reading_varname} = false;
        

        if (button) {{
            const originalClick = button.click.bind(button);
            
            let interval = setInterval(function() {{
                if ({python_done_reading_varname} === true) {{
                    clearInterval(interval);  // Stop polling
                    {user_clicked_next_varname} = false;
                    {python_done_reading_varname} = false;
                    
                    originalClick();
                }}
            }}, 100);  // Check every 100ms

            button.addEventListener('click', function(event) {{
                event.preventDefault();
                {user_clicked_next_varname} = true;
            }}, {{ once: true }});
        }}
    """

    page.evaluate(js)


def make_example_form_values() -> dict:
    today = datetime.date.today()
    travel_start_date = today + datetime.timedelta(days=1)
    travel_end_date = travel_start_date + datetime.timedelta(days=7)
    
    res = dict(
        dates = (travel_start_date, travel_end_date),
        medicine = "Elvanse, kapsler, hårde, 20 mg 'Takeda Pharma'",
        daily_dosis = "1",
        n_days_with_meds = "Alle dage",
        doctor_first_name = "meh",
        doctor_last_name = "meh",
        doctor_address = "Amerikavej 15C, 1",
        doctor_zipcode = "1756",
        doctor_city = "København V",
        doctor_phone="123213123",
        user_first_name="Namey",
        user_last_name="McNameface",
        user_address="Gadevej 20",
        user_zipcode = "1234",
        user_city = "København",
        user_passport_number="123123123",
        user_birthdate="31-01-1990",
        user_birth_city="Hillerød",
        user_nationality="Dansk",
        user_email="user@gdomain.com",
        user_phone_number="12345678",
        user_gender = "Male",
        pharmacy_address="København Hamlets Apotek, København N, 2200"
    )
    
    return res
