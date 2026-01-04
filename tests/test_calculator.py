import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = CalculatorApp(self.root)

    def test_safe_eval_addition(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)

    def test_safe_eval_subtraction(self):
        self.assertEqual(self.app.safe_eval("5-3"), 2)

    def test_safe_eval_multiplication(self):
        self.assertEqual(self.app.safe_eval("3*4"), 12)

    def test_safe_eval_division(self):
        self.assertEqual(self.app.safe_eval("10/2"), 5)

    def test_safe_eval_division_by_zero(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("10/0")

    def test_safe_eval_invalid_expression(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("2++2")

    def test_safe_eval_complex_expression(self):
        self.assertEqual(self.app.safe_eval("2+3*4-5/5"), 13)

    def test_calculate_addition(self):
        self.app.display.insert(0, "2+2")
        self.app.calculate()
        self.assertEqual(self.app.display.get(), "4")

    def test_calculate_error(self):
        self.app.display.insert(0, "2++2")
        self.app.calculate()
        self.assertEqual(self.app.display.get(), self.app.ERROR_MSG)

    def tearDown(self):
        self.root.destroy()

if __name__ == '__main__':
    unittest.main()
