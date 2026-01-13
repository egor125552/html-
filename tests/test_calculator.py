import unittest
import sys
import os
import tkinter as tk
from types import SimpleNamespace

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator.main import CalculatorApp

class TestCalculatorApp(unittest.TestCase):

    def setUp(self):
        # Set up a root window for the app, but don't run mainloop
        self.root = tk.Tk()
        self.root.withdraw() # Hide the window
        self.app = CalculatorApp()

    def tearDown(self):
        self.app.destroy()
        self.root.destroy()

    def test_button_clicks(self):
        self.app.on_button_click('7')
        self.assertEqual(self.app.display_var.get(), "7")
        self.app.on_button_click('+')
        self.assertEqual(self.app.display_var.get(), "7+")
        self.app.on_button_click('8')
        self.assertEqual(self.app.display_var.get(), "7+8")

    def test_calculation(self):
        self.app.on_button_click('9')
        self.app.on_button_click('*')
        self.app.on_button_click('3')
        self.app.calculate()
        self.assertEqual(self.app.display_var.get(), "27")
        self.assertTrue(self.app.just_calculated)

    def test_clear(self):
        self.app.on_button_click('1')
        self.app.on_button_click('2')
        self.app.clear_display()
        self.assertEqual(self.app.display_var.get(), "")
        self.assertEqual(self.app.expression, "")

    def test_error_handling(self):
        self.app.on_button_click('1')
        self.app.on_button_click('/')
        self.app.on_button_click('0')
        self.app.calculate()
        self.assertEqual(self.app.display_var.get(), "Error")
        self.assertTrue(self.app.just_calculated)

    def test_new_calculation_after_result(self):
        self.app.on_button_click('2')
        self.app.on_button_click('+')
        self.app.on_button_click('2')
        self.app.calculate() # Result is 4
        self.assertEqual(self.app.display_var.get(), "4")

        # Now press a number, should start a new calculation
        self.app.on_button_click('5')
        self.assertEqual(self.app.display_var.get(), "5")
        self.assertFalse(self.app.just_calculated)
        self.assertEqual(self.app.expression, "5")

    def test_operator_after_result(self):
        self.app.on_button_click('3')
        self.app.on_button_click('*')
        self.app.on_button_click('3')
        self.app.calculate() # Result is 9
        self.assertEqual(self.app.display_var.get(), "9")

        # Now press an operator, should continue the calculation
        self.app.on_button_click('-')
        self.assertEqual(self.app.display_var.get(), "9-")
        self.assertFalse(self.app.just_calculated)
        self.assertEqual(self.app.expression, "9-")
        self.app.on_button_click('4')
        self.app.calculate()
        self.assertEqual(self.app.display_var.get(), "5")

    def test_keyboard_bindings(self):
        # Simulate key presses
        self.app.on_button_click('1')
        self.app.on_button_click('+')
        self.app.on_button_click('2')

        # Simulate pressing 'Enter' key
        self.app.calculate()
        self.assertEqual(self.app.display_var.get(), '3')

        # Simulate pressing 'Escape' key
        self.app.clear_display()
        self.assertEqual(self.app.display_var.get(), '')

        # Test backspace
        self.app.on_button_click('1')
        self.app.on_button_click('2')
        self.app.on_button_click('3')
        self.app.handle_backspace()
        self.assertEqual(self.app.display_var.get(), '12')


if __name__ == '__main__':
    unittest.main()
