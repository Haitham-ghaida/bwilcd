import pytest
import responses
from bwilcd.client import SodaClient
import xml.etree.ElementTree as ET

# Replace with your actual SODA4LCA server URL and stock ID
SODA_SERVER = "https://data.probas.umweltbundesamt.de"
TEST_STOCK = "ebee4288-5f27-4d18-8e2d-c98e985cda5a"  # Replace with your stock ID


@pytest.fixture
def client():
    return SodaClient(SODA_SERVER)


@pytest.fixture
def auth_client():
    return SodaClient(SODA_SERVER, "username", "password")


@responses.activate
def test_init():
    # Test without auth
    client = SodaClient(SODA_SERVER)
    assert client.base_url == f"{SODA_SERVER}/resource"
    assert client.session.auth is None

    # Test with auth
    client = SodaClient(SODA_SERVER, "user", "pass")
    assert client.session.auth == ("user", "pass")

    # Test invalid auth combination
    with pytest.raises(ValueError):
        SodaClient(SODA_SERVER, "user", None)


@responses.activate
def test_test_connection(client):
    # Test successful connection
    responses.add(
        responses.GET,
        f"{SODA_SERVER}/resource/datastocks",
        status=200,
        content_type="application/xml",
    )
    assert client.test_connection() is True

    # Test failed connection
    responses.reset()
    responses.add(responses.GET, f"{SODA_SERVER}/resource/datastocks", status=404)
    assert client.test_connection() is False


@responses.activate
def test_search_datasets(client):
    # Mock XML response - fixed format
    xml_response = '<?xml version="1.0" encoding="UTF-8"?><processDataSet totalSize="1" xmlns="http://www.ilcd-network.org/ILCD/ServiceAPI"><processDataSet><uuid>test-uuid</uuid><baseName>Test Process</baseName></processDataSet></processDataSet>'
    
    responses.add(
        responses.GET,
        f"{SODA_SERVER}/resource/datastocks/{TEST_STOCK}/processes",
        body=xml_response,
        status=200,
        content_type="application/xml",
    )

    results = client.search_datasets(TEST_STOCK, "test", 0, 20)
    assert len(results) == 1
    assert results[0]["uuid"] == "test-uuid"
    assert results[0]["name"] == "Test Process"


@responses.activate
def test_download_stock(client):
    fake_content = b"fake-zip-content"
    # Mock ZIP response
    responses.add(
        responses.GET,
        f"{SODA_SERVER}/resource/datastocks/{TEST_STOCK}/export",
        body=fake_content,
        status=200,
        content_type="application/zip",
        headers={"content-length": str(len(fake_content))}  # Set correct content length
    )

    # Test without progress callback
    content = client.download_stock(TEST_STOCK)
    assert content == fake_content


@responses.activate
def test_get_stocks(client):
    # Mock XML response - fixed format
    xml_response = '<?xml version="1.0" encoding="UTF-8"?><dataStockList xmlns="http://www.ilcd-network.org/ILCD/ServiceAPI"><dataStock><uuid>stock-uuid</uuid><shortName>Stock Name</shortName><description>Stock Description</description></dataStock></dataStockList>'
    
    responses.add(
        responses.GET,
        f"{SODA_SERVER}/resource/datastocks",
        body=xml_response,
        status=200,
        content_type="application/xml"
    )

    stocks = client.get_stocks()
    assert len(stocks) == 1
    assert stocks[0]["uuid"] == "stock-uuid"
    assert stocks[0]["name"] == "Stock Name"
    assert stocks[0]["description"] == "Stock Description"

    # Test error handling
    responses.reset()
    responses.add(responses.GET, f"{SODA_SERVER}/resource/datastocks", status=500)
    with pytest.raises(Exception):
        client.get_stocks()
