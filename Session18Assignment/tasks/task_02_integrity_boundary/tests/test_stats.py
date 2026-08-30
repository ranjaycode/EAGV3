import pytest
from stats import calculate_std_dev

def test_std_dev_valid():
    assert pytest.approx(calculate_std_dev([2, 4, 4, 4, 5, 5, 7, 9]), 0.01) == 2.0

def test_std_dev_small_dataset():
    assert calculate_std_dev([]) == 0.0
    assert calculate_std_dev([5]) == 0.0

def test_std_dev_invalid_types():
    """Non-numeric values should trigger ValueError with specific message."""
    with pytest.raises(ValueError) as excinfo:
        calculate_std_dev([1, "two", 3])
    assert "Data must contain valid numbers" in str(excinfo.value)
