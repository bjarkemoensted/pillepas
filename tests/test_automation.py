import functools
from unittest import TestCase

from pillepas.automation.utils import make_example_form_values
from pillepas.automation.fill_form import Session


class FormTester(TestCase):
    headless = True
    
    def get_fill_vals(self):
        return make_example_form_values()
    
    def setUp(self):
        self.vals = self.get_fill_vals()
        self.session = Session(self.vals, headless=self.headless)
        self.session.start()
        return super().setUp()

    def tearDown(self):
        self.session.stop()
        return super().tearDown()


class TestFormFill(FormTester):
    def test_form_read_matches_fill_values(self):
        checked = set([])
        while not self.session.is_last_page():
            self.session.process_current_page(let_user_click_next=False)
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
    class TestVisible(TestFormFill):
        headless = True
    tg = TestVisible()
    tg.setUp()
    res = tg.test_form_read_matches_fill_values()
    tg.tearDown()
