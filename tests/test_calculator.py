import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Скрываем основное окно во время тестов
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_safe_eval_valid(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)
        self.assertEqual(self.app.safe_eval("10-5"), 5)
        self.assertEqual(self.app.safe_eval("3*4"), 12)
        self.assertEqual(self.app.safe_eval("10/2"), 5)
        self.assertEqual(self.app.safe_eval("2**3"), 8)
        self.assertEqual(self.app.safe_eval("10%3"), 1)
        self.assertEqual(self.app.safe_eval("-5"), -5)
        self.assertEqual(self.app.safe_eval("2+3*4"), 14)
        self.assertEqual(self.app.safe_eval("(2+3)*4"), 20)

    def test_safe_eval_invalid(self):
        # `import` - это оператор, а не выражение, поэтому ast.parse вызовет SyntaxError
        with self.assertRaises(SyntaxError):
            self.app.safe_eval("import os")
        # `__import__` - это вызов функции, который должен быть перехвачен _check_nodes
        with self.assertRaises(ValueError):
            self.app.safe_eval("__import__('os')")
        with self.assertRaises(SyntaxError):
            self.app.safe_eval("5+")
        with self.assertRaises(ZeroDivisionError):
            self.app.safe_eval("1/0")

if __name__ == "__main__":
    unittest.main()
