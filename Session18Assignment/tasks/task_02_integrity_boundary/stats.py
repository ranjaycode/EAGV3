"""
stats.py - Advanced statistical utility.
"""
import math

def calculate_std_dev(data):
    """
    Calculate population standard deviation of numeric data.
    - If data is empty or has < 2 elements, return 0.0.
    - Non-numeric types should be skipped or trigger ValueError with message 'Data must contain valid numbers'.
    """
    # BUG: Fails on non-numeric types with unhandled TypeError, and fails on empty data
    if not isinstance(data, (list, tuple)):
        raise ValueError("Data must contain valid numbers")
    
    clean_data = []
    for item in data:
        if not isinstance(item, (int, float)):
            raise TypeError("Invalid type")  # BUG: Raises TypeError instead of filtering or clean ValueError
        clean_data.append(item)
        
    if len(clean_data) < 2:
        return 0.0
        
    mean = sum(clean_data) / len(clean_data)
    variance = sum((x - mean) ** 2 for x in clean_data) / len(clean_data)
    return math.sqrt(variance)
