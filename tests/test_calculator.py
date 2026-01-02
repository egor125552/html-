import unittest
import tkinter as tk
from calculator.main import CalculatorApp

class TestCalculatorApp(unittest.TestCase):
    def setUp(self):
        """
        Настройка тестового окружения.
        """
        self.root = tk.Tk()
        # Скрываем окно Tkinter во время тестов
        self.root.withdraw()
        self.app = CalculatorApp(self.root)

    def tearDown(self):
        """
        Очистка после каждого теста.
        """
        self.root.destroy()

    def test_safe_eval_addition(self):
        """
        Тестирование сложения.
        """
        self.assertEqual(self.app.safe_eval("2+3"), 5)

    def test_safe_eval_subtraction(self):
        """
        Тестирование вычитания.
        """
        self.assertEqual(self.app.safe_eval("5-3"), 2)

    def test_safe_eval_multiplication(self):
        """
        Тестирование умножения.
        """
        self.assertEqual(self.app.safe_eval("2*3"), 6)

    def test_safe_eval_division(self):
        """
        Тестирование деления.
        """
        self.assertEqual(self.app.safe_eval("6/3"), 2)

    def test_safe_eval_invalid_expression(self):
        """
        Тестирование некорректного выражения.
        """
        with self.assertRaises(ValueError):
            self.app.safe_eval("2++3")

    def test_safe_eval_disallowed_function(self):
        """
        Тестирование запрещенной функции.
        """
        with self.assertRaises(ValueError):
            self.app.safe_eval("abs(-1)")

    def test_safe_eval_empty_expression(self):
        """
        Тестирование пустого выражения.
        """
        with self.assertRaises(ValueError):
            self.app.safe_eval("")

if __name__ == '__main__':
    unittest.main()
