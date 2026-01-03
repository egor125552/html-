import sys
import os
import unittest
import math

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
from calculator.main import CalculatorApp  # noqa: E402


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.app = CalculatorApp()
        self.app.withdraw()  # Скрываем окно во время тестов

    def tearDown(self):
        self.app.destroy()

    def test_addition(self):
        self.app.display.insert(0, "2+2")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "4.0")

    def test_subtraction(self):
        self.app.display.insert(0, "5-3")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "2.0")

    def test_multiplication(self):
        self.app.display.insert(0, "3*4")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "12.0")

    def test_division(self):
        self.app.display.insert(0, "10/2")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "5.0")

    def test_division_by_zero(self):
        self.app.display.insert(0, "10/0")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "Ошибка")

    def test_invalid_expression(self):
        self.app.display.insert(0, "10++2")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "Ошибка")

    def test_unsafe_expression(self):
        self.app.display.insert(0, "__import__('os').system('echo unsafe')")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "Ошибка")

    def test_sin(self):
        self.app.display.insert(0, "sin(0)")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), str(math.sin(0)))

    def test_cos(self):
        self.app.display.insert(0, "cos(0)")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), str(math.cos(0)))

    def test_log(self):
        self.app.display.insert(0, "log(1)")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), str(math.log(1)))

    def test_sqrt(self):
        self.app.display.insert(0, "sqrt(4)")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "2.0")

    def test_expression_with_parentheses(self):
        self.app.display.insert(0, "(2+3)*4")
        self.app._calculate()
        self.assertEqual(self.app.display.get(), "20.0")


if __name__ == "__main__":
    unittest.main()
