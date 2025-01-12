from dataclasses import dataclass


@dataclass
class Exchange:
    """Represents an exchange (input/output flow) in a process dataset"""

    flow_name: str
    direction: str
    amount: float
    is_reference_flow: bool = False
