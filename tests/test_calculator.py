
import unittest
import tkinter as tk
from types import SimpleNamespace
from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Hide the window
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_addition(self):
        self.app.on_button_click('1')
        self.app.on_button_click('+')
        self.app.on_button_click('2')
        self.app.on_button_click('=')
        self.assertEqual(self.app.display_var.get(), "3.0")

    def test_keyboard_input(self):
        self.app.on_key_press(SimpleNamespace(keysym='1'))
        self.app.on_key_press(SimpleNamespace(keysym='plus'))
        self.app.on_key_press(SimpleNamespace(keysym='2'))
        self.app.on_key_press(SimpleNamespace(keysym='Return'))
        self.assertEqual(self.app.display_var.get(), "3.0")

    def test_subtraction(self):
        self.app.on_button_click('5')
        self.app.on_button_click('-')
        self.app.on_button_click('3')
        self.app.on_button_click('=')
        self.assertEqual(self.app.display_var.get(), "2.0")

    def test_multiplication(self):
        self.app.on_button_click('3')
        self.app.on_button_click('*')
        self.app.on_button_click('4')
        self.app.on_button_click('=')
        self.assertEqual(self.app.display_var.get(), "12.0")

    def test_division(self):
        self.app.on_button_click('1')
        self.app.on_button_click('0')
        self.app.on_button_click('/')
        self.app.on_button_click('2')
        self.app.on_button_click('=')
        self.assertEqual(self.app.display_var.get(), "5.0")

    def test_clear(self):
        self.app.on_button_click('1')
        self.app.on_button_click('2')
        self.app.on_button_click('3')
        self.app.on_button_click('C')
        self.assertEqual(self.app.expression, "")
        self.assertEqual(self.app.display_var.get(), "")

    def test_error(self):
        self.app.on_button_click('1')
        self.app.on_button_click('/')
        self.app.on_button_click('0')
        self.app.on_button_click('=')
        self.assertEqual(self.app.display_var.get(), "Error")

if __name__ == '__main__':
    unittest.main()
