import unittest
import sys
import os
import tkinter as tk
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.main import safe_eval, CalculatorApp

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertEqual(safe_eval('2+2'), 4)

    def test_subtract(self):
        self.assertEqual(safe_eval('5-3'), 2)

    def test_multiply(self):
        self.assertEqual(safe_eval('3*4'), 12)

    def test_divide(self):
        self.assertEqual(safe_eval('10/2'), 5)

    def test_invalid_expression(self):
        with self.assertRaises(ValueError):
            safe_eval('2+')

    def test_unsupported_operator(self):
        with self.assertRaises(ValueError):
            safe_eval('2**2')

    def test_divide_by_zero(self):
        # safe_eval uses op.truediv which raises ZeroDivisionError
        with self.assertRaises(ZeroDivisionError):
            safe_eval('1/0')

class TestCalculatorApp(unittest.TestCase):
    def setUp(self):
        # Создаём Tkinter app для каждого теста
        self.root = tk.Tk()
        # Скрываем окно, так как нам не нужен GUI в тестах
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        # Уничтожаем окно после каждого теста
        self.root.destroy()

    def test_number_press(self):
        self.app.on_key_press(SimpleNamespace(keysym='5'))
        self.assertEqual(self.app.display_text.get(), '5')

    def test_operator_press(self):
        self.app.on_key_press(SimpleNamespace(keysym='plus'))
        self.assertEqual(self.app.display_text.get(), '+')

    def test_clear_press(self):
        self.app.display_text.set("123")
        self.app.on_key_press(SimpleNamespace(keysym='Escape'))
        self.assertEqual(self.app.display_text.get(), '')

    def test_calculate_press(self):
        self.app.display_text.set("9*3")
        self.app.on_key_press(SimpleNamespace(keysym='Return'))
        self.assertEqual(self.app.display_text.get(), '27')

    def test_backspace(self):
        self.app.display_text.set("123")
        self.app.on_key_press(SimpleNamespace(keysym='BackSpace'))
        self.assertEqual(self.app.display_text.get(), '12')

if __name__ == '__main__':
    unittest.main()
