import unittest
import sys
import os

# Добавляем родительскую директорию в PYTHONPATH, чтобы можно было импортировать 'calculator'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertEqual(safe_eval("1 + 2"), 3)

    def test_subtract(self):
        self.assertEqual(safe_eval("5 - 2"), 3)

    def test_multiply(self):
        self.assertEqual(safe_eval("3 * 4"), 12)

    def test_divide(self):
        self.assertEqual(safe_eval("10 / 2"), 5)

    def test_precedence(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)

    def test_parentheses(self):
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval("-5 + 10"), 5)

    def test_float_numbers(self):
        self.assertAlmostEqual(safe_eval("1.5 + 2.5"), 4.0)

    def test_division_by_zero(self):
        self.assertEqual(safe_eval("1 / 0"), "Деление на ноль")

    def test_invalid_expression(self):
        self.assertEqual(safe_eval("1 +"), "Ошибка ввода")

    def test_invalid_characters(self):
        self.assertEqual(safe_eval("a + b"), "Ошибка ввода")

    def test_power(self):
        self.assertEqual(safe_eval("2**3"), 8)

if __name__ == "__main__":
    unittest.main()
