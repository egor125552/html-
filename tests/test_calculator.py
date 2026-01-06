import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.app = CalculatorApp(master=None)

    def test_addition(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)
        self.assertEqual(self.app.safe_eval("2.5 + 2.5"), 5.0)

    def test_subtraction(self):
        self.assertEqual(self.app.safe_eval("5-3"), 2)
        self.assertEqual(self.app.safe_eval("10 - 5.5"), 4.5)

    def test_multiplication(self):
        self.assertEqual(self.app.safe_eval("3*3"), 9)
        self.assertEqual(self.app.safe_eval("2.5 * 2"), 5.0)

    def test_division(self):
        self.assertEqual(self.app.safe_eval("10/2"), 5)
        self.assertEqual(self.app.safe_eval("5/2"), 2.5)

    def test_division_by_zero(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("10/0")

    def test_invalid_expression(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("2++2")
        with self.assertRaises(ValueError):
            self.app.safe_eval("abc")

if __name__ == '__main__':
    unittest.main()
