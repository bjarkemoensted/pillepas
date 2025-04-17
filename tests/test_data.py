from unittest import TestCase

from pillepas import config
from pillepas.persistence import data


class TestFormFields(TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.fields_dict = config._read_fields()
        cls.n_fields = sum(len(v) for v in cls.fields_dict.values())
        
        # The attributes we can look up on a field
        cls.attrs = data.Field.__dataclass_fields__.keys()
        
        
        
        
        return super().setUpClass()
    
    def test_read_fields(self):
        self.assertIsInstance(self.fields_dict, dict)
    
    def test_field_container(self):
        self.assertIsInstance(data.form_fields, data.FieldContainer)
        self.assertEqual(self.n_fields, len(data.form_fields.contents))
    
    def test_filtering(self):
        for attr in self.attrs:
            values = data.form_fields.get_distinct_values(attr)
            for val in values:
                d = {attr: val}
                matches = data.form_fields.lookup(**d)
                for m in matches:
                    self.assertTrue(m.matches(**d))
                #
            #
        #
    
    def test_iteration(self):
        elems = [e for e in data.form_fields]
        self.assertEqual(len(elems), len(data.form_fields.contents))
    #
