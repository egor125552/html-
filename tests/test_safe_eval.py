import unittest
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы найти модуль calculator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval("10 + 5"), 15)

    def test_subtraction(self):
        self.assertEqual(safe_eval("10 - 5"), 5)

    def test_multiplication(self):
        self.assertEqual(safe_eval("10 * 5"), 50)

    def test_division(self):
        self.assertEqual(safe_eval("10 / 5"), 2)

    def test_float_division(self):
        self.assertAlmostEqual(safe_eval("10 / 3"), 3.3333333333)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval("-10 + 5"), -5)
        self.assertEqual(safe_eval("10 + (-5)"), 5)

    def test_unary_minus(self):
        self.assertEqual(safe_eval("-5"), -5)

    def test_zero_division(self):
        self.assertIn("Ошибка", safe_eval("10 / 0"))

    def test_invalid_syntax(self):
        self.assertIn("Ошибка", safe_eval("10 +"))
        self.assertIn("Ошибка", safe_eval("10 10"))

    def test_unsupported_characters(self):
        self.assertIn("Ошибка", safe_eval("a + 5"))

    def test_malicious_code(self):
        # Убедимся, что функция не выполняет вредоносный код
        self.assertIn("Ошибка", safe_eval("__import__('os').system('echo pwned')"))
        self.assertIn("Ошибка", safe_eval("print('hello')"))

    def test_order_of_operations(self):
        """Проверяет правильный порядок выполнения операций (PEMDAS/BODMAS)."""
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(safe_eval("10 - 2 * 3"), 4)
        self.assertEqual(safe_eval("10 / 2 - 3"), 2)

    def test_parentheses(self):
        """Проверяет правильную обработку выражений в скобках."""
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20)
        self.assertEqual(safe_eval("10 - (2 * 3)"), 4)
        self.assertEqual(safe_eval("10 / (2 - 3)"), -10)
        self.assertEqual(safe_eval("5 * (10 - 2)"), 40)


if __name__ == "__main__":
    unittest.main()
