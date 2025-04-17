from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Var:
    s: str
    valid_values: Optional[Any] = None
    category: Optional[str] = None


save_sensitive = Var("save_sensitive", valid_values=[True, False])

