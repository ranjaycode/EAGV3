import pytest
from calc import average

def test_average_standard():
    assert average([1, 2, 3, 4, 5]) == 3.0
    assert average([10, 20]) == 15.0

def test_average_floats():
    assert pytest.approx(average([1.5, 2.5, 3.5]), 0.01) == 2.5

def test_average_empty_list():
    """Empty list should return 0 as specified in docstring."""
    assert average([]) == 0
