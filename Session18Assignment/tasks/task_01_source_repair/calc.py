"""
calc.py - Simple statistical calculations.
"""

def average(numbers):
    """Return the arithmetic mean of a list of numbers. Return 0 for an empty list."""
    # BUG: Raises ZeroDivisionError when numbers is empty
    return sum(numbers) / len(numbers)
