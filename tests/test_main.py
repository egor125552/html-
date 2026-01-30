import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculatorGUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_initial_state(self):
        self.assertEqual(self.app.display_var.get(), "0")
        self.assertEqual(self.app.expression, "")

    def test_digit_input(self):
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.assertEqual(self.app.expression, "12")
        self.assertEqual(self.app.display_var.get(), "12")

    def test_clear(self):
        self.app._on_button_click("1")
        self.app._on_button_click("C")
        self.assertEqual(self.app.expression, "")
        self.assertEqual(self.app.display_var.get(), "0")

    def test_all_clear(self):
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.app._on_button_click("AC")
        self.assertEqual(self.app.expression, "")
        self.assertEqual(self.app.display_var.get(), "0")

    def test_calculation(self):
        self.app.expression = "2+2"
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "4")
        self.assertEqual(self.app.expression, "4")

    def test_toggle_sign(self):
        self.app.expression = "5"
        self.app._on_button_click("+/-")
        self.assertEqual(self.app.expression, "-5")
        self.app._on_button_click("+/-")
        self.assertEqual(self.app.expression, "5")

    def test_percent(self):
        self.app.expression = "50"
        self.app._on_button_click("%")
        self.assertEqual(self.app.expression, "0.5")

    def test_complex_toggle_sign(self):
        self.app.expression = "5+3"
        self.app._on_button_click("+/-")
        self.assertEqual(self.app.expression, "5+-3")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "2")

    def test_scientific_input(self):
        self.app._on_button_click("√")
        self.app._on_button_click("4")
        self.app._on_button_click(")")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "2")

    def test_pow_input(self):
        self.app._on_button_click("2")
        self.app._on_button_click("^")
        self.app._on_button_click("3")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "8")

if __name__ == "__main__":
    unittest.main()
