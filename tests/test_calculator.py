# -*- coding: utf-8 -*-
import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculatorLogic(unittest.TestCase):
    """Тесты для проверки логики калькулятора."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        """Очистка после каждого теста."""
        self.root.destroy()

    def test_addition(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)
        self.assertEqual(self.app.safe_eval("10+5.5"), 15.5)

    def test_subtraction(self):
        self.assertEqual(self.app.safe_eval("10-5"), 5)
        self.assertEqual(self.app.safe_eval("5-10"), -5)

    def test_multiplication(self):
        self.assertEqual(self.app.safe_eval("3*4"), 12)
        self.assertEqual(self.app.safe_eval("2.5*2"), 5.0)

    def test_division(self):
        self.assertEqual(self.app.safe_eval("10/2"), 5.0)
        self.assertEqual(self.app.safe_eval("5/2"), 2.5)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.app.safe_eval("1/0")

    def test_invalid_expression(self):
        with self.assertRaises(SyntaxError):
            self.app.safe_eval("2+*2")

    def test_unsafe_expression(self):
        with self.assertRaises(ValueError):
            self.app.safe_eval("().__class__")
        with self.assertRaises(ValueError):
            self.app.safe_eval("exec('print(1)')")
        with self.assertRaises(ValueError):
            self.app.safe_eval("__import__('os').system('echo pwned')")

class TestCalculatorKeyboard(unittest.TestCase):
    """Тесты для проверки управления с клавиатуры."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def _press_key(self, key, keysym):
        """Имитирует нажатие клавиши."""
        event = tk.Event()
        event.char = key
        event.keysym = keysym
        self.app.on_key_press(event)

    def test_digit_keys(self):
        """Тест на ввод цифр."""
        self._press_key('1', '1')
        self._press_key('2', '2')
        self.assertEqual(self.app.expression, "12")

    def test_operator_keys(self):
        """Тест на ввод операторов."""
        self._press_key('1', '1')
        self._press_key('+', '+')
        self._press_key('2', '2')
        self.assertEqual(self.app.expression, "1+2")

    def test_enter_key(self):
        """Тест на нажатие Enter."""
        self._press_key('1', '1')
        self._press_key('+', '+')
        self._press_key('2', '2')
        self.app.on_button_click("=")
        self.assertEqual(self.app.expression, "3") # Исправлено: 1+2=3, а не 3.0

    def test_escape_key(self):
        """Тест на нажатие Escape."""
        self._press_key('1', '1')
        self._press_key('2', '2')
        self._press_key('', 'Escape')
        self.assertEqual(self.app.expression, "")

    def test_backspace_key(self):
        """Тест на нажатие Backspace."""
        self._press_key('1', '1')
        self._press_key('2', '2')
        self._press_key('3', '3')
        self._press_key('', 'BackSpace')
        self.assertEqual(self.app.expression, "12")

if __name__ == "__main__":
    unittest.main()
