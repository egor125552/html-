import unittest
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertEqual(safe_eval('1 + 2'), 3)

    def test_subtract(self):
        self.assertEqual(safe_eval('10 - 5'), 5)

    def test_multiply(self):
        self.assertEqual(safe_eval('2 * 3'), 6)

    def test_divide(self):
        self.assertEqual(safe_eval('10 / 2'), 5)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval('-5'), -5)
        self.assertEqual(safe_eval('10 + -5'), 5)

    def test_float_numbers(self):
        self.assertAlmostEqual(safe_eval('1.5 + 2.5'), 4.0)
        self.assertAlmostEqual(safe_eval('5.0 / 2.0'), 2.5)

    def test_zero_division(self):
        self.assertEqual(safe_eval('10 / 0'), 'Ошибка')

    def test_invalid_expression(self):
        self.assertEqual(safe_eval('1 +'), 'Ошибка')
        self.assertEqual(safe_eval('++1'), 'Ошибка')

    def test_unsafe_expressions(self):
        self.assertEqual(safe_eval("__import__('os').system('echo pwned')"), 'Ошибка')
        self.assertEqual(safe_eval("print('hello')"), 'Ошибка')
        self.assertEqual(safe_eval("a = 1"), 'Ошибка')

if __name__ == '__main__':
    unittest.main()
