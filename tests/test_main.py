import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.app = CalculatorApp(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.app._clear()

    def test_initial_state(self):
        self.assertEqual(self.app.expression, "")
        self.assertEqual(self.app.display_var.get(), "0")

    def test_append(self):
        self.app._on_button_click('1')
        self.app._on_button_click('2')
        self.assertEqual(self.app.expression, "12")
        self.assertEqual(self.app.display_var.get(), "12")

    def test_calculate(self):
        self.app.expression = "2+2"
        self.app._calculate()
        self.assertEqual(self.app.expression, "4")
        self.assertEqual(self.app.display_var.get(), "4")

    def test_clear(self):
        self.app.expression = "123"
        self.app._on_button_click('C')
        self.assertEqual(self.app.expression, "")
        self.assertEqual(self.app.display_var.get(), "0")

    def test_toggle_sign(self):
        self.app.expression = "5"
        self.app._toggle_sign()
        self.assertEqual(self.app.expression, "(-5)")
        self.app._toggle_sign()
        self.assertEqual(self.app.expression, "5")

    def test_percent(self):
        self.app.expression = "50"
        self.app._apply_percent()
        self.assertEqual(self.app.expression, "0.5")

    def test_backspace(self):
        self.app.expression = "123"
        self.app._backspace()
        self.assertEqual(self.app.expression, "12")
        self.app.expression = "sin("
        self.app._backspace()
        self.assertEqual(self.app.expression, "")
        self.app.expression = "pi"
        self.app._backspace()
        self.assertEqual(self.app.expression, "")

    def test_factorial_display(self):
        self.app.expression = "factorial(5)"
        self.app._update_display()
        self.assertEqual(self.app.display_var.get(), "5!")
        self.app.expression = "factorial(factorial(3))"
        self.app._update_display()
        self.assertEqual(self.app.display_var.get(), "3!!")

if __name__ == '__main__':
    unittest.main()
