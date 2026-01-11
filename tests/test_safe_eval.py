import unittest
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_basic_operations(self):
        self.assertEqual(safe_eval("1 + 2"), 3.0)
        self.assertEqual(safe_eval("10 - 5"), 5.0)
        self.assertEqual(safe_eval("3 * 4"), 12.0)
        self.assertEqual(safe_eval("10 / 2"), 5.0)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval("-5 + 10"), 5.0)
        self.assertEqual(safe_eval("10 * -2"), -20.0)
        self.assertEqual(safe_eval("-5 - -3"), -2.0)

    def test_order_of_operations(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14.0)
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20.0)

    def test_division_by_zero(self):
        self.assertIsNone(safe_eval("1 / 0"))

    def test_invalid_expressions(self):
        self.assertIsNone(safe_eval("1 +"))
        self.assertIsNone(safe_eval("1 ++ 2"))
        self.assertIsNone(safe_eval("import os")) # Проверка безопасности
        self.assertIsNone(safe_eval("a + b"))

if __name__ == '__main__':
    unittest.main()
