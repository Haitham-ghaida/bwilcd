"""Fixtures for bwilcd"""

import pytest

@pytest.fixture
def sample_data():
    """Fixture for providing sample test data"""
    return {
        'test_value': 42,
        'test_string': 'hello'
    }
