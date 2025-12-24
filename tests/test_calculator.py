import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_addition(self):
        result = self.app._safe_eval("2+2")
        self.assertEqual(result, 4)

    def test_subtraction(self):
        result = self.app._safe_eval("5-3")
        self.assertEqual(result, 2)

    def test_multiplication(self):
        result = self.app._safe_eval("3*4")
        self.assertEqual(result, 12)

    def test_division(self):
        result = self.app._safe_eval("10/2")
        self.assertEqual(result, 5)

    def test_division_by_zero(self):
        with self.assertRaises(Exception):
            self.app._safe_eval("10/0")

    def test_invalid_expression(self):
        with self.assertRaises(Exception):
            self.app._safe_eval("2++2")

    def test_complex_expression(self):
        result = self.app._safe_eval("2+3*4")
        self.assertEqual(result, 14)

    def test_expression_with_parentheses(self):
        result = self.app._safe_eval("(2+3)*4")
        self.assertEqual(result, 20)

    def test_decimal_expression(self):
        result = self.app._safe_eval("2.5+3.5")
        self.assertEqual(result, 6.0)

if __name__ == "__main__":
    unittest.main()
