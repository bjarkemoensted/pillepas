from unittest import TestCase

from pillepas import config
from pillepas.persistence import data


class TestFormFields(TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.fields_dict = config._read_fields()

        cls.n_form_fields = sum(len(v) for v in cls.fields_dict.values())

        cls.n_parameters = len(data.PARAMETERS)
        cls.n_fields = len(data.FIELDS)

        cls.n_total = cls.n_fields + cls.n_parameters
        
        return super().setUpClass()
    
    def test_read_fields(self):
        self.assertIsInstance(self.fields_dict, dict)
    
    def test_field_container(self):
        self.assertEqual(self.n_fields, len(data.FIELDS.contents))
    
    def test_filtering(self):
        for attr in data.FIELDS.get_distinct_attributes():
            values = data.FIELDS.get_distinct_values(attr)
            for val in values:
                d = {attr: val}
                matches = data.FIELDS.lookup(**d)
                for m in matches:
                    self.assertTrue(m.matches(**d))
                #
            #
        #
    
    def test_iteration(self):
        n = 0
        for thing in (data.FIELDS, data.PARAMETERS):
            for elem in thing:
                n += 1
        self.assertEqual(n, self.n_total)
    #
