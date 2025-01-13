from dataclasses import dataclass


@dataclass
class Exchange:
    """Represents an exchange (input/output flow) in a process dataset"""

    flow_name: str
    direction: str
    amount: float
    uuid: str
    type: str = ""
    category: str = ""
    unit: str = ""
    is_reference_flow: bool = False
