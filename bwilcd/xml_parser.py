import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
from .models import Exchange


class ILCDXMLParser:
    """Parser for ILCD XML responses"""

    @staticmethod
    def parse_stocks(xml_content: bytes) -> List[Dict]:
        """Parse XML content for data stocks"""
        root = ET.fromstring(xml_content)
        namespaces = [
            {"ns": "http://www.ilcd-network.org/ILCD/ServiceAPI"},
            {"ns": "http://www.ilcd-network.org/ILCD/ServiceAPI/"},
            {},  # No namespace
        ]

        for ns in namespaces:
            stocks = ILCDXMLParser._try_parse_stocks(root, ns)
            if stocks:
                return stocks
        return []

    @staticmethod
    def parse_datasets_search(xml_content: bytes) -> List[Dict]:
        """Parse XML content for dataset search results"""
        root = ET.fromstring(xml_content)
        datasets = []

        namespaces = {
            "sapi": "http://www.ilcd-network.org/ILCD/ServiceAPI",
            "p": "http://www.ilcd-network.org/ILCD/ServiceAPI/Process",
        }

        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        paths = [
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}processDataSet",
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}process",
            ".//processDataSet",
            ".//process",
        ]

        for path in paths:
            processes = root.findall(path)
            if processes:
                for process in processes:
                    dataset = ILCDXMLParser._parse_process_element(process)
                    if dataset.get("uuid") and dataset.get("name"):
                        datasets.append(dataset)

        return datasets

    @staticmethod
    def parse_dataset(xml_content_process: bytes) -> Dict[str, Any]:
        """Parse XML content for a specific dataset"""
        root = ET.fromstring(xml_content_process)
        ns = {
            "": "http://lca.jrc.it/ILCD/Process",
            "common": "http://lca.jrc.it/ILCD/Common",
            "xml": "http://www.w3.org/XML/1998/namespace",
        }

        ref_flow_id = root.find(".//quantitativeReference/referenceToReferenceFlow", ns)
        ref_flow_id = int(ref_flow_id.text) if ref_flow_id is not None else None

        return {
            "name": ILCDXMLParser._get_text(
                root,
                './/processInformation/dataSetInformation/name/baseName[@xml:lang="de"]',
                ns,
            ),
            "uuid": ILCDXMLParser._get_text(
                root, ".//processInformation/dataSetInformation/common:UUID", ns
            ),
            "description": ILCDXMLParser._get_text(
                root,
                './/processInformation/dataSetInformation/common:generalComment[@xml:lang="de"]',
                ns,
            ),
            "exchanges": ILCDXMLParser._parse_exchanges(root, ns, ref_flow_id),
            "reference_year": ILCDXMLParser._get_text(
                root, ".//processInformation/time/common:referenceYear", ns
            ),
            "geography": ILCDXMLParser._get_geography(root, ns),
            "technology": ILCDXMLParser._get_text(
                root,
                './/processInformation/technology/technologyDescriptionAndIncludedProcesses[@xml:lang="de"]',
                ns,
            ),
            "functional_unit": ILCDXMLParser._get_text(
                root,
                './/quantitativeReference/functionalUnitOrOther[@xml:lang="de"]',
                ns,
            ),
            "has_reference_flow": ref_flow_id is not None,
        }

    @staticmethod
    def _try_parse_stocks(root: ET.Element, ns: Dict[str, str]) -> List[Dict]:
        """Try to parse stocks with given namespace"""
        stocks = []
        try:
            elements = (
                root.findall(".//ns:dataStock", ns)
                if ns
                else root.findall(".//dataStock")
            )
            for stock in elements:
                stock_data = {}
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

    @staticmethod
    def _parse_process_element(process: ET.Element) -> Dict:
        """Parse a process element from search results"""
        dataset = {"dataset_type": "Process"}

        uuid_paths = [
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}uuid",
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}uuid",
            ".//uuid",
        ]
        name_paths = [
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}baseName",
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI}name",
            ".//{http://www.ilcd-network.org/ILCD/ServiceAPI/Process}name",
            ".//baseName",
            ".//name",
        ]

        for uuid_path in uuid_paths:
            uuid_elem = process.find(uuid_path)
            if uuid_elem is not None and uuid_elem.text:
                dataset["uuid"] = uuid_elem.text
                break

        for name_path in name_paths:
            name_elem = process.find(name_path)
            if name_elem is not None and name_elem.text:
                dataset["name"] = name_elem.text
                break

        return dataset

    @staticmethod
    def _parse_exchanges(
        root: ET.Element,
        ns: Dict,
        ref_flow_id: Optional[int] = None,
    ) -> List[Exchange]:
        """Parse exchanges data from XML"""
        exchanges = []
        for exchange in root.findall(".//exchanges/exchange", ns):
            internal_id = int(exchange.get("dataSetInternalID"))
            flow_dataset = exchange.find(".//referenceToFlowDataSet", ns)
            flow_uuid = (
                flow_dataset.get("refObjectId") if flow_dataset is not None else None
            )
            flow = exchange.find(
                ".//referenceToFlowDataSet/common:shortDescription", ns
            )
            direction = exchange.find("exchangeDirection", ns)
            amount = exchange.find("meanAmount", ns)

            if None in (flow, direction, amount):
                continue

            is_ref = internal_id == ref_flow_id if ref_flow_id else False
            exchanges.append(
                Exchange(
                    flow_name=flow.text,
                    direction=direction.text,
                    amount=float(amount.text),
                    is_reference_flow=is_ref,
                    uuid=flow_uuid,
                )
            )
        return exchanges

    @staticmethod
    def parse_flow_info(xml_content: bytes) -> List[Exchange]:
        """Parse flow information from exchanges response"""
        root = ET.fromstring(xml_content)
        ns = {
            "sapi": "http://www.ilcd-network.org/ILCD/ServiceAPI",
            "f": "http://www.ilcd-network.org/ILCD/ServiceAPI/Flow",
        }

        flows = []
        for flow in root.findall(".//f:flow", ns):
            uuid = flow.find("sapi:uuid", ns).text
            name = flow.find("sapi:name", ns).text
            flow_type = flow.find("f:type", ns).text
            categories = flow.findall(".//sapi:category", ns)
            category = next((c.text for c in categories if c.get("level") == "2"), None)
            unit = flow.find(".//f:defaultUnit", ns).text

            flows.append(
                Exchange(
                    flow_name=name,
                    direction="",  # Will be populated from dataset info
                    amount=0.0,  # Will be populated from dataset info
                    uuid=uuid,
                    type=flow_type,
                    category=category,
                    unit=unit,
                )
            )

        return flows

    @staticmethod
    def _get_text(element: ET.Element, xpath: str, ns: Dict) -> Optional[str]:
        """Helper method to safely extract text from XML elements"""
        try:
            result = element.find(xpath, ns)
            return result.text.strip() if result is not None and result.text else None
        except Exception:
            return None

    @staticmethod
    def _get_geography(root: ET.Element, ns: Dict) -> Optional[str]:
        """Extract geography information from XML"""
        geo_elem = root.find(
            ".//processInformation/geography/locationOfOperationSupplyOrProduction",
            ns,
        )
        return geo_elem.get("location") if geo_elem is not None else None
