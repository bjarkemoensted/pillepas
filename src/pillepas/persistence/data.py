from __future__ import annotations
import dataclasses
from typing import Any, Dict, List, Optional, Type

from pillepas import config


@dataclasses.dataclass
class FieldBase:
    key: str
    
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
            try:
                attr_val = getattr(self, k)
            except AttributeError:
                return False
            
            if isinstance(attr_val, (list, tuple)):
                # If lookup attribute, all specified values must be contained
                lookfor_vals = v if isinstance(v, (list, tuple)) else [v]
                if not all(val in attr_val for val in lookfor_vals):
                    return False
                #
            else:
                # Otherwise, the attribute must match the specified one
                if attr_val != v:
                    return False
                #
            #
        
        return True
    #


@dataclasses.dataclass
class FormField(FieldBase):
    category: str
    name: str
    label: str
    tags: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Parameter(FieldBase):
    valid_values: Optional[List[Any]] = None



def _iter_form_fields():
    """Iterate over the form fields"""
    fields = config._read_fields()
    for category, entries in fields.items():
        for data in entries:
            try:
                data["tags"] = [s.strip() for s in data["tags"].split(",")]
            except KeyError:
                pass

            form_field = FormField(category=category, **data)
            yield form_field
        #
    #


# Parameters determining behavior
PARAMETERS = (
    Parameter("save_sensitive", valid_values=[True, False]),
)


@dataclasses.dataclass
class FieldContainer:

    contents: Dict[str, FieldBase] = dataclasses.field(default_factory=dict)
    
    def register_field(self, field: FieldBase):
        if not isinstance(field, FieldBase):
            raise TypeError

        k = field.key
        if k in self.contents:
            raise RuntimeError(f"Attempted to double register")
    
        self.contents[k] = field

    def add_new_field(self, class_: Type[FieldBase], *args, **kwargs):
        field = class_(*args, **kwargs)
        self.register_field(field)

    def lookup(self, **kwargs):
        """Lookup fields matching the specified criteria"""
        res = [d for d in self if d.matches(**kwargs)]
        return res
    
    def get_distinct_attributes(self):
        attrs = {attr for field in self for attr in field.__dataclass_fields__}
        res = sorted(attrs)
        return res

    def get_distinct_values(self, attr: str):
        """Returns all unique values of a given attribute.
        If the attribute is multi-valued (e.g. 'tags'), a list of each individual value
        is returned.
        Values are returned in the order encountered."""

        seen = set([])
        res = []
        for field in self:
            if not hasattr(field, attr):
                continue

            val = getattr(field, attr)
            it = val if isinstance(val, (list, tuple)) else (val,)
            for v in it:
                if v not in seen:
                    seen.add(v)
                    res.append(v)
                #
            #
        
        return res
    
    def __iter__(self):
        return iter(self.contents.values())
    #

    @classmethod
    def create(cls) -> FieldContainer:
        res = cls()
        fields = list(PARAMETERS) + list(_iter_form_fields())
        for field in fields:
            res.register_field(field)
        
        return res
    #


FIELDS = FieldContainer.create()
