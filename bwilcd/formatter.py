from typing import Dict, Any, List
from .models import Exchange


class ILCDFormatter:
    """Formatter for ILCD dataset information"""

    @staticmethod
    def format_dataset_info(dataset_info: Dict[str, Any]) -> str:
        """Format dataset information into a readable string"""
        output = []

        # Basic information
        output.append(f"\nDataset: {dataset_info.get('name', 'N/A')}")
        output.append(f"UUID: {dataset_info.get('uuid', 'N/A')}")
        output.append(f"Reference Year: {dataset_info.get('reference_year', 'N/A')}")
        output.append(f"Geography: {dataset_info.get('geography', 'N/A')}")
        output.append(f"Functional Unit: {dataset_info.get('functional_unit', 'N/A')}")

        if not dataset_info.get("has_reference_flow"):
            output.append("\nWarning: No reference flow defined for this dataset")

        # Description
        ILCDFormatter._append_text_section(output, "Description", dataset_info.get("description"))

        # Technology description
        ILCDFormatter._append_text_section(output, "Technology Description", dataset_info.get("technology"))

        # Format exchanges
        ILCDFormatter._append_exchanges_section(output, dataset_info)

        return "\n".join(output)

    @staticmethod
    def _append_text_section(output: List[str], title: str, text: str) -> None:
        """Helper method to append a text section with title"""
        if text:
            output.append(f"\n{title}:")
            output.append("-" * 40)
            output.append(
                text[:500] + "..." if len(text) > 500 else text
            )

    @staticmethod
    def _append_exchanges_section(output: List[str], dataset_info: Dict[str, Any]) -> None:
        """Helper method to append exchanges section"""
        if not dataset_info.get("exchanges"):
            return

        # Group exchanges by direction
        inputs = [e for e in dataset_info["exchanges"] if e.direction == "Input"]
        outputs = [e for e in dataset_info["exchanges"] if e.direction == "Output"]

        # Format inputs
        if inputs:
            output.append("\nInputs:")
            output.append("-" * 40)
            for exchange in sorted(inputs, key=lambda x: abs(x.amount), reverse=True):
                output.append(f"  {exchange.flow_name}: {exchange.amount:g}")

        # Format outputs
        if outputs:
            output.append("\nOutputs:")
            output.append("-" * 40)
            ref_found = False
            for exchange in sorted(outputs, key=lambda x: abs(x.amount), reverse=True):
                prefix = "* " if exchange.is_reference_flow else "  "
                output.append(f"{prefix}{exchange.flow_name}: {exchange.amount:g}")
                if exchange.is_reference_flow:
                    ref_found = True

            if not ref_found and dataset_info.get("has_reference_flow"):
                output.append("\nWarning: Reference flow ID found but no matching exchange")
