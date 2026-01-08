import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Скрываем главное окно во время тестов
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        # Уничтожаем окно после каждого теста
        self.root.destroy()

    def test_safe_eval_addition(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)

    def test_safe_eval_subtraction(self):
        self.assertEqual(self.app.safe_eval("5-3"), 2)

    def test_safe_eval_multiplication(self):
        self.assertEqual(self.app.safe_eval("4*3"), 12)

    def test_safe_eval_division(self):
        self.assertEqual(self.app.safe_eval("10/2"), 5)

    def test_safe_eval_division_by_zero(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("1/0")

    def test_safe_eval_invalid_expression(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("1++2")

    def test_safe_eval_complex_expression(self):
        self.assertEqual(self.app.safe_eval("2+3*4"), 14)

    def test_safe_eval_negative_numbers(self):
        self.assertEqual(self.app.safe_eval("-5+10"), 5)

    def test_on_button_click_number(self):
        self.app.on_button_click('5')
        self.assertEqual(self.app.entry.get(), '5')

    def test_on_button_click_operator(self):
        self.app.on_button_click('7')
        self.app.on_button_click('+')
        self.app.on_button_click('3')
        self.assertEqual(self.app.entry.get(), '7+3')

    def test_on_button_click_clear(self):
        self.app.on_button_click('1')
        self.app.on_button_click('2')
        self.app.on_button_click('C')
        self.assertEqual(self.app.entry.get(), '')

    def test_on_button_click_equals(self):
        self.app.on_button_click('9')
        self.app.on_button_click('*')
        self.app.on_button_click('3')
        self.app.on_button_click('=')
        self.assertEqual(self.app.entry.get(), '27')

if __name__ == "__main__":
    unittest.main()
