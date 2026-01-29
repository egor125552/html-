import unittest
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы можно было импортировать calculator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval("1 + 2"), 3)
        self.assertEqual(safe_eval("1 + -2"), -1)

    def test_subtraction(self):
        self.assertEqual(safe_eval("10 - 5"), 5)
        self.assertEqual(safe_eval("5 - 10"), -5)

    def test_multiplication(self):
        self.assertEqual(safe_eval("3 * 4"), 12)
        self.assertEqual(safe_eval("-3 * 4"), -12)

    def test_division(self):
        self.assertEqual(safe_eval("10 / 2"), 5)
        self.assertAlmostEqual(safe_eval("5 / 2"), 2.5)

    def test_division_by_zero(self):
        self.assertEqual(safe_eval("1 / 0"), "Error")

    def test_order_of_operations(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20)

    def test_unary_minus(self):
        self.assertEqual(safe_eval("-5"), -5)
        self.assertEqual(safe_eval("-(5 + 2)"), -7)

    def test_complex_expression(self):
        self.assertAlmostEqual(safe_eval("10 + 2 * 6 - (8 / 4)"), 20)

    def test_invalid_syntax(self):
        self.assertEqual(safe_eval("1 +"), "Error")
        self.assertEqual(safe_eval("1 + * 2"), "Error")

    def test_unsupported_characters(self):
        self.assertEqual(safe_eval("import os"), "Error")
        self.assertEqual(safe_eval("__import__('os').system('ls')"), "Error")
        self.assertEqual(safe_eval("print('hello')"), "Error")
        self.assertEqual(safe_eval("a = 5"), "Error")

if __name__ == '__main__':
    unittest.main()
