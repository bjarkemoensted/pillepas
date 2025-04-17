from unittest import TestCase

from pillepas import config
from pillepas.persistence import data


class TestFormFields(TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.fields_dict = config._read_fields()

        cls.n_form_fields = sum(len(v) for v in cls.fields_dict.values())
        cls.n_parameters = len(data.PARAMETERS)
        cls.n_fields = cls.n_form_fields + cls.n_parameters

        cls.fields = data.FieldContainer.create()
        
        return super().setUpClass()
    
    def test_read_fields(self):
        self.assertIsInstance(self.fields_dict, dict)
    
    def test_field_container(self):
        self.assertIsInstance(self.fields, data.FieldContainer)
        self.assertEqual(self.n_fields, len(self.fields.contents))
    
    def test_filtering(self):
        for attr in self.fields.get_distinct_attributes():
            values = self.fields.get_distinct_values(attr)
            for val in values:
                d = {attr: val}
                matches = self.fields.lookup(**d)
                for m in matches:
                    self.assertTrue(m.matches(**d))
                #
            #
        #
    
    def test_iteration(self):
        elems = [e for e in self.fields]
        total = self.n_form_fields + self.n_parameters
        self.assertEqual(len(elems), total)
    #
