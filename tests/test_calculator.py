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
        self.app.press('2')
        self.app.press('+')
        self.app.press('2')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "4.0")

    def test_subtraction(self):
        self.app.press('5')
        self.app.press('-')
        self.app.press('3')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "2.0")

    def test_multiplication(self):
        self.app.press('3')
        self.app.press('*')
        self.app.press('4')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "12.0")

    def test_division(self):
        self.app.press('1')
        self.app.press('0')
        self.app.press('/')
        self.app.press('2')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "5.0")

    def test_division_by_zero(self):
        self.app.press('1')
        self.app.press('/')
        self.app.press('0')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "Ошибка")

    def test_invalid_syntax(self):
        self.app.press('+')
        self.app.press('2')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "Ошибка")

    def test_decimal_input(self):
        self.app.press('2')
        self.app.press('.')
        self.app.press('5')
        self.app.press('+')
        self.app.press('1')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "3.5")

    def test_multiple_decimal_points(self):
        self.app.press('2')
        self.app.press('.')
        self.app.press('5')
        self.app.press('.')
        self.app.press('1')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "Ошибка")

    def test_negative_number(self):
        self.app.press('-')
        self.app.press('5')
        self.app.press('+')
        self.app.press('1')
        self.app.press('0')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "5.0")

    def test_new_calculation_after_equals(self):
        self.app.press('1')
        self.app.press('+')
        self.app.press('1')
        self.app.press('=')
        self.assertEqual(self.app.equation.get(), "2.0")
        self.app.press('3')
        self.assertEqual(self.app.expression, "3")

if __name__ == '__main__':
    unittest.main()
