import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculatorLogic(unittest.TestCase):
    def setUp(self):
        # Нам не нужно реальное окно, поэтому создаём временное
        root = tk.Tk()
        self.app = CalculatorApp(root)
        root.destroy() # Уничтожаем его сразу

    def test_safe_eval_addition(self):
        self.assertEqual(self.app.safe_eval("2+2"), 4)

    def test_safe_eval_subtraction(self):
        self.assertEqual(self.app.safe_eval("5-3"), 2)

    def test_safe_eval_multiplication(self):
        self.assertEqual(self.app.safe_eval("3*4"), 12)

    def test_safe_eval_division(self):
        self.assertEqual(self.app.safe_eval("10/2"), 5)

    def test_safe_eval_invalid_expression(self):
        with self.assertRaises(TypeError):
            self.app.safe_eval("__import__('os').system('echo unsafe')")

if __name__ == '__main__':
    unittest.main()
