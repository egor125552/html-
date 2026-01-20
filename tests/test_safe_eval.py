import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval('2+2'), 4)

    def test_subtraction(self):
        self.assertEqual(safe_eval('5-3'), 2)

    def test_multiplication(self):
        self.assertEqual(safe_eval('3*4'), 12)

    def test_division(self):
        self.assertEqual(safe_eval('10/2'), 5)

    def test_unary_negation(self):
        self.assertEqual(safe_eval('-5'), -5)
        self.assertEqual(safe_eval('2+-3'), -1)

    def test_order_of_operations(self):
        self.assertEqual(safe_eval('2+3*4'), 14)
        self.assertEqual(safe_eval('10-4/2'), 8)

    def test_float_division(self):
        self.assertAlmostEqual(safe_eval('5/2'), 2.5)
        self.assertAlmostEqual(safe_eval('10/3'), 3.3333333333)

    def test_invalid_expressions(self):
        with self.assertRaises(ValueError):
            safe_eval('2+*2')  # Invalid syntax
        with self.assertRaises(ValueError):
            safe_eval('invalid')  # Unsupported node type (Name)
        with self.assertRaises(ValueError):
            safe_eval('a=5')  # Invalid syntax
        with self.assertRaises(ValueError):
            safe_eval('2**3')  # Unsupported operator

    def test_unary_addition(self):
        self.assertEqual(safe_eval('+5'), 5)
        self.assertEqual(safe_eval('2++3'), 5)
        self.assertEqual(safe_eval('2++2'), 4)

if __name__ == '__main__':
    unittest.main()
