import unittest
import sys
import os

# Добавляем родительскую директорию в путь, чтобы можно было импортировать calculator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval("1 + 1"), 2)

    def test_subtraction(self):
        self.assertEqual(safe_eval("10 - 5"), 5)

    def test_multiplication(self):
        self.assertEqual(safe_eval("3 * 4"), 12)

    def test_division(self):
        self.assertEqual(safe_eval("10 / 2"), 5)

    def test_order_of_operations(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval("-5 + 10"), 5)
        self.assertEqual(safe_eval("10 + (-5)"), 5)

    def test_floats(self):
        self.assertAlmostEqual(safe_eval("1.5 + 2.5"), 4.0)
        self.assertAlmostEqual(safe_eval("10 / 4"), 2.5)

    def test_zero_division(self):
        self.assertEqual(safe_eval("1 / 0"), "Ошибка")

    def test_invalid_syntax(self):
        self.assertEqual(safe_eval("1 +"), "Ошибка")
        self.assertEqual(safe_eval("1 1"), "Ошибка")

    def test_unsafe_expressions(self):
        self.assertEqual(safe_eval("__import__('os').system('echo unsafe')"), "Ошибка")
        self.assertEqual(safe_eval("print('hello')"), "Ошибка")
        self.assertEqual(safe_eval("[i for i in [1,2]]"), "Ошибка")


if __name__ == '__main__':
    unittest.main()
