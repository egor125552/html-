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
        self.assertEqual(self.app.display_var.get(), "")

    def test_number_click(self):
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.assertEqual(self.app.display_var.get(), "12")

    def test_basic_operation(self):
        self.app._on_button_click("7")
        self.app._on_button_click("+")
        self.app._on_button_click("3")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "10")

    def test_clear_buttons(self):
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.app._on_button_click("C")
        self.assertEqual(self.app.display_var.get(), "1")
        self.app._on_button_click("AC")
        self.assertEqual(self.app.display_var.get(), "")

    def test_scientific_input(self):
        self.app._on_button_click("sin(")
        self.app._on_button_click("0")
        self.app._on_button_click(")")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "0")

if __name__ == "__main__":
    unittest.main()
