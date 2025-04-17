import dataclasses
from typing import Dict, List, Iterable, Optional

from pillepas import config


@dataclasses.dataclass
class Field:
    category: str
    key: str
    name: str
    label: str
    tags: list = dataclasses.field(default_factory=list)
    
    @classmethod
    def is_multivalued(cls, attr: str) -> bool:
        """Whether an attribute is a single value, or an iterable of values."""
        field_info = cls.__dataclass_fields__[attr]
        return field_info.type in (list, tuple)
    
    def matches(self, **kwargs) -> bool:
        """Determine whether the field matches input criteriea.
        For example:
        my_field.matches(category='some_category')
        returns all fields with the specified category.
        Properties with multiple values (e.g. 'tags' can be specified as either a single value,
        or a list/tuple of values, i.e.
        my_field.matches(tags='some_tag'))
        or
        my_field.matches(tags=['some_tag', 'some_other_tag']))"""

        for k, v in kwargs.items():
            if self.is_multivalued(k):
                # If lookup attribute, all specified values must be contained
                lookfor_vals = v if isinstance(v, (list, tuple)) else [v]
                has_vals = getattr(self, k)
                if not all(val in has_vals for val in lookfor_vals):
                    return False
                #
            else:
                # Otherwise, the attribute must match the specified one
                if getattr(self, k) != v:
                    return False
                #
            #
        
        return True
    #


@dataclasses.dataclass
class FieldContainer:
    contents: List[Field]
    
    def __init__(self):
        fields = config._read_fields()
        self.contents = []
        for category, entries in fields.items():
            for data in entries:
                
                try:
                    data["tags"] = [s.strip() for s in data["tags"].split(",")]
                except KeyError:
                    pass
                d = Field(category=category, **data)
                self.contents.append(d)
            #
        #
    
    def lookup(self, **kwargs):
        """Lookup fields matching the specified criteria"""
        res = [d for d in self.contents if d.matches(**kwargs)]
        return res
    
    def get_distinct_values(self, attr: str):
        seen = set([])
        res = []
        for field in self.contents:
            val = getattr(field, attr)
            it = val if field.is_multivalued(attr) else (val,)
            for v in it:
                if v not in seen:
                    seen.add(v)
                    res.append(v)
                #
            #
        
        return res
    
    def __iter__(self):
        return iter(self.contents)            
    
form_fields = FieldContainer()
