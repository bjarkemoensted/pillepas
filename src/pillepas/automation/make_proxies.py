import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator, Page
from typing import Generator, Tuple

from pillepas.automation.proxy_classes import (
    Proxy,
    AutocompleteProxy,
    DropDownProxy,
    RadioButtonProxy,
    DateSelectorProxy
)

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



def proxy_factory(elem: Page|Locator) -> Generator[Tuple[str, Proxy], None, None]:
    page = elem.page
    dr_css = ':scope[name*="doctor"]'
    nodr_css = ':scope:not([name*="doctor"])'

    d = dict(
        dates = (DateSelectorProxy,
            elem.locator("button[id='date']")
        ),
        medicine = (AutocompleteProxy,
            page.get_by_role("combobox").filter(has=page.locator(':scope[name*="drug"]'))
        ),
        daily_dosis = (Proxy,
            elem.get_by_role("spinbutton", name="Daglig dosis i antal enheder")
        ),
        n_days_with_meds = (DropDownProxy,
            elem.get_by_role("combobox", name="Antal dage med medicin")
        ),

        doctor_first_name = (Proxy,
            elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(dr_css))
        ),
        doctor_last_name = (Proxy,
            elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(dr_css))
        ),
        doctor_address = (Proxy,
            elem.locator('input[name*="address"]').filter(has=page.locator(dr_css))
        ),
        doctor_zipcode = (Proxy,
            elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(dr_css))
        ),
        doctor_city = (Proxy,
            elem.get_by_role("textbox", name="By").filter(has=page.locator(dr_css))
        ),
        doctor_phone = (Proxy,
            elem.get_by_role("textbox", name="telefon").filter(has=page.locator(dr_css))
        ),

        user_first_name = (Proxy,
            elem.get_by_role("textbox", name="Fornavn").filter(has=page.locator(nodr_css))
        ),
        user_last_name = (Proxy,
            elem.get_by_role("textbox", name="Efternavn").filter(has=page.locator(nodr_css))
        ),
        user_address = (Proxy,
            elem.locator("input[name*='address']").filter(has=page.locator(nodr_css))
        ),
        user_zipcode = (Proxy,
            elem.get_by_role("textbox", name="Postnummer").filter(has=page.locator(nodr_css))
        ),
        user_city = (Proxy,
            elem.get_by_role("textbox", name="By", exact=True).filter(has=page.locator(nodr_css))
        ),
        user_passport_number = (Proxy,
            elem.get_by_role("textbox", name="Pasnummer").filter(has=page.locator(nodr_css)),
            dict(sensitive=True)
        ),
        user_birthdate = (Proxy,
            elem.get_by_role("textbox", name="Indtast din fødselsdato (DD-").filter(has=page.locator(nodr_css))
        ),
        user_birth_city = (Proxy,
            elem.get_by_role("textbox", name="Fødeby").filter(has=page.locator(nodr_css))
        ),
        user_nationality = (Proxy,
            elem.get_by_role("textbox", name="Nationalitet").filter(has=page.locator(nodr_css))
        ),
        user_email = (Proxy,
            elem.get_by_role("textbox", name="E-mail").filter(has=page.locator(nodr_css))
        ),
        user_phone_number = (Proxy,
            elem.get_by_role("textbox", name="Telefonnummer").filter(has=page.locator(nodr_css))
        ),
        user_gender = (RadioButtonProxy,
            elem.locator('label', has_text="Køn").locator("..").locator("..")
        ),
        pharmacy_address = (AutocompleteProxy,
            elem.locator("input[placeholder='Indtast apotekets navn']")
        ),
    )

    for key, (cls_, e, *opt) in d.items():
        kwargs = dict(key=key)
        if opt:
            assert len(opt) == 1
            kwargs.update(opt[0])
        proxy = cls_(e, **kwargs)
        yield key, proxy
    #
