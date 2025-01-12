import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Callable, Any
import urllib3
from functools import lru_cache
from pathlib import Path
from .utils import get_downloads_dir
from .models import Exchange
from .xml_parser import ILCDXMLParser

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SodaClient:
    """Client for interacting with ILCD Network nodes"""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize SODA client with optional authentication

        Args:
            base_url: The base URL of the SODA4LCA server
            username: Optional username for authentication
            password: Optional password for authentication
        """
        # Ensure base URL is properly formatted
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/resource"):
            self.base_url += "/resource"

        self.session = requests.Session()
        # Only set authentication if both username and password are provided
        if username and password:
            self.session.auth = (username, password)
        elif bool(username) != bool(password):
            raise ValueError(
                "Both username and password must be provided for authentication"
            )

    def test_connection(self) -> bool:
        """Test if the connection to the server is working"""
        try:
            # Try to get the datastocks endpoint directly
            headers = {"Accept": "application/xml"}
            response = self.session.get(
                f"{self.base_url}/datastocks", headers=headers, verify=False
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    @lru_cache(maxsize=1000)
    def search_datasets(
        self, stock_uuid: str, query: str = "", page: int = 0, size: int = 20
    ) -> List[Dict]:
        """Search for datasets in a stock"""
        # Calculate start index
        start_index = page * size

        # Build query parameters
        params = {
            "startIndex": start_index,
            "pageSize": size,
        }

        if query:
            params.update({"search": "true", "name": query})

        try:
            response = self.session.get(
                f"{self.base_url}/datastocks/{stock_uuid}/processes",
                params=params,
                headers={"Accept": "application/xml"},
                verify=False,
            )

            if response.status_code == 200:
                return ILCDXMLParser.parse_datasets_search(response.content)
            return []

        except Exception:
            return []

    def download_stock(
        self,
        stock_uuid: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Download a data stock and save it to the downloads directory

        Args:
            stock_uuid: UUID of the stock to download
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded file
        """
        try:
            response = self.session.get(
                f"{self.base_url}/datastocks/{stock_uuid}/export",
                headers={"Accept": "application/zip"},
                stream=True,
                verify=False,
            )
            response.raise_for_status()

            # Get total size for progress bar
            total_size = int(response.headers.get("content-length", 0))
            current_size = 0

            # Create downloads directory and prepare file path
            download_path = get_downloads_dir() / f"{stock_uuid}.zip"

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        current_size += len(chunk)
                        if progress_callback:
                            progress_callback(current_size, total_size)

            return download_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download stock: {str(e)}")

    @lru_cache(maxsize=1000)
    def get_stocks(self) -> List[Dict]:
        """Get list of available data stocks"""
        headers = {"Accept": "application/xml"}
        response = self.session.get(
            f"{self.base_url}/datastocks", headers=headers, verify=False
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to get stocks: {response.status_code}, Response: {response.text}"
            )

        try:
            return ILCDXMLParser.parse_stocks(response.content)
        except Exception as e:
            raise Exception(f"Failed to parse response as XML: {str(e)}")

    @lru_cache(maxsize=1000)
    def get_dataset(self, dataset_uuid: str) -> Dict[str, Any]:
        """Fetch and parse a specific dataset by UUID"""
        try:
            url = f"{self.base_url}/processes/{dataset_uuid}/?format=xml&view=overview"
            response = self.session.get(
                url,
                headers={
                    "Accept": "application/xml",
                    "Content-Type": "application/xml",
                },
                verify=False,
            )
            response.raise_for_status()
            return ILCDXMLParser.parse_dataset(response.content)
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch dataset: {str(e)}")

    def format_dataset_info(self, dataset_info: Dict[str, Any]) -> str:
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
        if dataset_info.get("description"):
            output.append("\nDescription:")
            output.append("-" * 40)
            output.append(
                dataset_info["description"][:500] + "..."
                if len(dataset_info["description"]) > 500
                else dataset_info["description"]
            )

        # Technology description
        if dataset_info.get("technology"):
            output.append("\nTechnology Description:")
            output.append("-" * 40)
            output.append(
                dataset_info["technology"][:500] + "..."
                if len(dataset_info["technology"]) > 500
                else dataset_info["technology"]
            )

        # Format exchanges
        if dataset_info.get("exchanges"):
            # Group exchanges by direction
            inputs = [e for e in dataset_info["exchanges"] if e.direction == "Input"]
            outputs = [e for e in dataset_info["exchanges"] if e.direction == "Output"]

            # Format inputs
            if inputs:
                output.append("\nInputs:")
                output.append("-" * 40)
                for exchange in sorted(
                    inputs, key=lambda x: abs(x.amount), reverse=True
                ):
                    output.append(f"  {exchange.flow_name}: {exchange.amount:g}")

            # Format outputs
            if outputs:
                output.append("\nOutputs:")
                output.append("-" * 40)
                ref_found = False
                for exchange in sorted(
                    outputs, key=lambda x: abs(x.amount), reverse=True
                ):
                    prefix = "* " if exchange.is_reference_flow else "  "
                    output.append(f"{prefix}{exchange.flow_name}: {exchange.amount:g}")
                    if exchange.is_reference_flow:
                        ref_found = True

                if not ref_found and dataset_info.get("has_reference_flow"):
                    output.append(
                        "\nWarning: Reference flow ID found but no matching exchange"
                    )

        return "\n".join(output)

    def view_dataset(self, dataset_uuid: str) -> None:
        """Fetch and display formatted information about a dataset"""
        try:
            dataset_info = self.get_dataset(dataset_uuid)
            formatted_info = self.format_dataset_info(dataset_info)
            print(formatted_info)
        except Exception as e:
            print(f"Error viewing dataset: {str(e)}")
