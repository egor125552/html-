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

    def test_number_click(self):
        self.app._on_button_click("7")
        self.assertEqual(self.app.display_var.get(), "7")
        self.app._on_button_click("8")
        self.assertEqual(self.app.display_var.get(), "78")

    def test_clear(self):
        self.app._on_button_click("7")
        self.app._on_button_click("C")
        self.assertEqual(self.app.display_var.get(), "0")

    def test_calculation(self):
        self.app._on_button_click("2")
        self.app._on_button_click("+")
        self.app._on_button_click("3")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "5")

    def test_toggle_sign(self):
        self.app._on_button_click("5")
        self.app._on_button_click("+/-")
        self.assertEqual(self.app.display_var.get(), "(-5)")
        self.app._on_button_click("+/-")
        self.assertEqual(self.app.display_var.get(), "5")

    def test_percent(self):
        self.app._on_button_click("5")
        self.app._on_button_click("0")
        self.app._on_button_click("%")
        self.assertEqual(self.app.display_var.get(), "0.5")

if __name__ == '__main__':
    unittest.main()
