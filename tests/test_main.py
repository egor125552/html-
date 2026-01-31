import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need a display for tkinter. In headless it might fail if xvfb is not used.
        try:
            cls.root = tk.Tk()
            cls.root.withdraw() # Hide window
        except Exception:
            raise unittest.SkipTest("Tkinter not available or no display")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root'):
            cls.root.destroy()

    def setUp(self):
        self.app = CalculatorApp(self.root)

    def test_initial_state(self):
        self.assertEqual(self.app.display.get(), "")

    def test_button_click(self):
        self.app._on_button_click('1')
        self.assertEqual(self.app.display.get(), "1")
        self.app._on_button_click('2')
        self.assertEqual(self.app.display.get(), "12")
        self.app._on_button_click('+')
        self.app._on_button_click('3')
        self.app._on_button_click('=')
        self.assertEqual(self.app.display.get(), "15")

    def test_clear(self):
        self.app._on_button_click('9')
        self.app._on_button_click('C')
        self.assertEqual(self.app.display.get(), "")

    def test_toggle_sign(self):
        self.app._on_button_click('5')
        self.app._on_button_click('+/-')
        self.assertEqual(self.app.display.get(), "(-5)")
        self.app._on_button_click('+/-')
        self.assertEqual(self.app.display.get(), "5")

if __name__ == "__main__":
    unittest.main()
