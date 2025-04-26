from unittest import TestCase

from pillepas.automation.utils import make_example_form_values
from pillepas.automation.fill_form import Session

class TestFormFill(TestCase):
    headless = True
    
    def setUp(self):
        self.vals = make_example_form_values()
        self.session = Session(self.vals, auto_click_next=True, headless=self.headless)
        self.session.start()
        return super().setUp()

    def tearDown(self):
        self.session.stop()
        return super().tearDown()

    def test_form_read_matches_fill_values(self):
        checked = set([])
        while not self.session.is_last_page():
            self.session.process_current_page()
            for k, v_form in self.session.read_fields.items():
                if k in checked:
                    continue
                
                v_data = self.vals[k]
                msg = f"Compared key={k}, form: {v_form} =? data: {v_data}"
                self.assertEqual(v_data, v_form, msg=msg)
                checked.add(k)
                print(msg)
            #
        #
    #


if __name__ == '__main__':
    tg = TestFormFill()
    tg.setUp()
    res = tg.test_form_read_matches_fill_values()
    tg.tearDown()
