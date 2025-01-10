import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Callable, Any
from urllib.parse import urljoin
import click
import urllib3
import warnings
from dataclasses import dataclass
from functools import lru_cache

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Exchange:
    """Represents an exchange (input/output flow) in a process dataset"""
    flow_name: str
    direction: str
    amount: float
    is_reference_flow: bool = False


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
    def search_datasets(self, stock_uuid: str, query: str = "", page: int = 0, size: int = 20) -> List[Dict]:
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
                root = ET.fromstring(response.content)
                
                # Store total size if available
                total_size = root.get("{http://www.ilcd-network.org/ILCD/ServiceAPI}totalSize")
                if total_size:
                    self.total_size = int(total_size)

                datasets = []
                
                # Try different XML paths and namespaces
                namespaces = {
                    "sapi": "http://www.ilcd-network.org/ILCD/ServiceAPI",
                    "p": "http://www.ilcd-network.org/ILCD/ServiceAPI/Process",
                }

                # Register namespaces
                for prefix, uri in namespaces.items():
                    ET.register_namespace(prefix, uri)

                # Try different paths for process elements
                paths = [
                    ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}processDataSet",
                    ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}process",
                    ".//processDataSet",
                    ".//process"
                ]

                for path in paths:
                    processes = root.findall(path)
                    if processes:
                        for process in processes:
                            dataset = {}

                            # Try different paths for UUID
                            uuid_paths = [
                                ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}uuid",
                                ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}uuid",
                                ".//uuid"
                            ]
                            
                            # Try different paths for name
                            name_paths = [
                                ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}baseName",
                                ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}name",
                                ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}name",
                                ".//baseName",
                                ".//name"
                            ]

                            # Get UUID
                            for uuid_path in uuid_paths:
                                uuid_elem = process.find(uuid_path)
                                if uuid_elem is not None and uuid_elem.text:
                                    dataset["uuid"] = uuid_elem.text
                                    break

                            # Get name
                            for name_path in name_paths:
                                name_elem = process.find(name_path)
                                if name_elem is not None and name_elem.text:
                                    dataset["name"] = name_elem.text
                                    break

                            # Set default type if not found
                            dataset["dataset_type"] = "Process"

                            # Only add if we have both UUID and name
                            if dataset.get("uuid") and dataset.get("name"):
                                datasets.append(dataset)

                        if datasets:
                            return datasets

            return []

        except ET.ParseError:
            return []
        except requests.RequestException:
            return []
    def download_stock(
        self,
        stock_uuid: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """Download a data stock"""
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
            content = bytearray()

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content.extend(chunk)
                    current_size += len(chunk)
                    if progress_callback:
                        progress_callback(current_size, total_size)

            return bytes(content)

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
            # Parse XML response
            root = ET.fromstring(response.content)
            # Try different namespace patterns
            namespaces = [
                {"ns": "http://www.ilcd-network.org/ILCD/ServiceAPI"},
                {"ns": "http://www.ilcd-network.org/ILCD/ServiceAPI/"},
                {},  # No namespace
            ]

            stocks = []
            for ns in namespaces:
                stocks = self._try_parse_stocks(root, ns)
                if stocks:
                    break

            return stocks
        except ET.ParseError as e:
            raise Exception(f"Failed to parse response as XML: {response.text}")

    def _try_parse_stocks(self, root: ET.Element, ns: Dict[str, str]) -> List[Dict]:
        """Try to parse stocks with given namespace"""
        stocks = []
        try:
            # Try with namespace
            if ns:
                elements = root.findall(".//ns:dataStock", ns)
            else:
                # Try without namespace
                elements = root.findall(".//dataStock")

            for stock in elements:
                stock_data = {}

                # Try both with and without namespace
                if ns:
                    uuid = stock.find("ns:uuid", ns)
                    name = stock.find("ns:shortName", ns)
                    description = stock.find("ns:description", ns)
                else:
                    uuid = stock.find("uuid")
                    name = stock.find("shortName")
                    description = stock.find("description")

                if uuid is not None:
                    stock_data["uuid"] = uuid.text
                if name is not None:
                    stock_data["name"] = name.text
                if description is not None:
                    stock_data["description"] = description.text or ""

                if stock_data.get("uuid") and stock_data.get("name"):
                    stocks.append(stock_data)

        except Exception:
            pass

        return stocks

    @lru_cache(maxsize=1000)
    def get_dataset(self, dataset_uuid: str) -> Dict[str, Any]:
        """Fetch and parse a specific dataset by UUID"""
        try:
            url = f"{self.base_url}/processes/{dataset_uuid}/?format=xml&view=overview"
            response = self.session.get(
                url,
                headers={
                    "Accept": "application/xml",
                    "Content-Type": "application/xml"
                },
                verify=False
            )
            response.raise_for_status()
            return self._parse_dataset(response.content)
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch dataset: {str(e)}")

    def _parse_dataset(self, xml_content: bytes) -> Dict[str, Any]:
        """Parse the XML dataset response into a structured dictionary"""
        root = ET.fromstring(xml_content)
        
        # Define XML namespaces
        ns = {
            '': 'http://lca.jrc.it/ILCD/Process',  # Default namespace
            'common': 'http://lca.jrc.it/ILCD/Common',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }
        
        # Get reference flow ID
        ref_flow_id = root.find('.//quantitativeReference/referenceToReferenceFlow', ns)
        ref_flow_id = int(ref_flow_id.text) if ref_flow_id is not None else None
        
        # Extract basic information
        info = {
            'name': self._get_text(root, './/processInformation/dataSetInformation/name/baseName[@xml:lang="de"]', ns),
            'uuid': self._get_text(root, './/processInformation/dataSetInformation/common:UUID', ns),
            'description': self._get_text(root, './/processInformation/dataSetInformation/common:generalComment[@xml:lang="de"]', ns),
            'exchanges': self._parse_exchanges(root, ns, ref_flow_id),
            'reference_year': self._get_text(root, './/processInformation/time/common:referenceYear', ns),
            'geography': root.find('.//processInformation/geography/locationOfOperationSupplyOrProduction', ns).get('location') if root.find('.//processInformation/geography/locationOfOperationSupplyOrProduction', ns) is not None else None,
            'technology': self._get_text(root, './/processInformation/technology/technologyDescriptionAndIncludedProcesses[@xml:lang="de"]', ns),
            'functional_unit': self._get_text(root, './/quantitativeReference/functionalUnitOrOther[@xml:lang="de"]', ns),
            'has_reference_flow': ref_flow_id is not None
        }
        
        return info

    def _parse_exchanges(self, root: ET.Element, ns: Dict, ref_flow_id: Optional[int] = None) -> List[Exchange]:
        """Parse exchanges data from XML"""
        exchanges = []
        
        for exchange in root.findall('.//exchanges/exchange', ns):
            internal_id = int(exchange.get('dataSetInternalID'))
            flow = exchange.find('.//referenceToFlowDataSet/common:shortDescription', ns)
            direction = exchange.find('exchangeDirection', ns)
            amount = exchange.find('meanAmount', ns)
            
            if None in (flow, direction, amount):
                continue
                
            is_ref = internal_id == ref_flow_id if ref_flow_id else False
            
            exchanges.append(Exchange(
                flow_name=flow.text,
                direction=direction.text,
                amount=float(amount.text),
                is_reference_flow=is_ref
            ))
        
        return exchanges

    def _get_text(self, element: ET.Element, xpath: str, ns: Dict) -> Optional[str]:
        """Helper method to safely extract text from XML elements"""
        try:
            result = element.find(xpath, ns)
            return result.text.strip() if result is not None and result.text else None
        except Exception:
            return None

    def format_dataset_info(self, dataset_info: Dict[str, Any]) -> str:
        """Format dataset information into a readable string"""
        output = []
        
        # Basic information
        output.append(f"\nDataset: {dataset_info.get('name', 'N/A')}")
        output.append(f"UUID: {dataset_info.get('uuid', 'N/A')}")
        output.append(f"Reference Year: {dataset_info.get('reference_year', 'N/A')}")
        output.append(f"Geography: {dataset_info.get('geography', 'N/A')}")
        output.append(f"Functional Unit: {dataset_info.get('functional_unit', 'N/A')}")
        
        if not dataset_info.get('has_reference_flow'):
            output.append("\nWarning: No reference flow defined for this dataset")
        
        # Description
        if dataset_info.get('description'):
            output.append("\nDescription:")
            output.append("-" * 40)
            output.append(dataset_info['description'][:500] + "..." if len(dataset_info['description']) > 500 else dataset_info['description'])
        
        # Technology description
        if dataset_info.get('technology'):
            output.append("\nTechnology Description:")
            output.append("-" * 40)
            output.append(dataset_info['technology'][:500] + "..." if len(dataset_info['technology']) > 500 else dataset_info['technology'])
        
        # Format exchanges
        if dataset_info.get('exchanges'):
            # Group exchanges by direction
            inputs = [e for e in dataset_info['exchanges'] if e.direction == 'Input']
            outputs = [e for e in dataset_info['exchanges'] if e.direction == 'Output']
            
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
                
                if not ref_found and dataset_info.get('has_reference_flow'):
                    output.append("\nWarning: Reference flow ID found but no matching exchange")
        
        return "\n".join(output)

    def view_dataset(self, dataset_uuid: str) -> None:
        """Fetch and display formatted information about a dataset"""
        try:
            dataset_info = self.get_dataset(dataset_uuid)
            formatted_info = self.format_dataset_info(dataset_info)
            print(formatted_info)
        except Exception as e:
            print(f"Error viewing dataset: {str(e)}")
