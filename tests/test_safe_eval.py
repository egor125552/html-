import unittest
import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval('2 + 3'), 5)
        self.assertEqual(safe_eval('10 + -5'), 5)

    def test_subtraction(self):
        self.assertEqual(safe_eval('10 - 5'), 5)
        self.assertEqual(safe_eval('5 - 10'), -5)

    def test_multiplication(self):
        self.assertEqual(safe_eval('3 * 4'), 12)
        self.assertEqual(safe_eval('-2 * 5'), -10)

    def test_division(self):
        self.assertEqual(safe_eval('10 / 2'), 5)
        self.assertAlmostEqual(safe_eval('5 / 2'), 2.5)

    def test_power(self):
        self.assertEqual(safe_eval('2 ** 3'), 8)
        self.assertEqual(safe_eval('5 ** 0'), 1)
        self.assertEqual(safe_eval('4 ** -1'), 0.25)

    def test_unary_minus(self):
        self.assertEqual(safe_eval('-5'), -5)
        self.assertEqual(safe_eval('-(-5)'), 5)

    def test_precedence(self):
        self.assertEqual(safe_eval('2 + 3 * 4'), 14)
        self.assertEqual(safe_eval('(2 + 3) * 4'), 20)

    def test_zero_division(self):
        self.assertEqual(safe_eval('1 / 0'), "Деление на ноль")

    def test_invalid_input(self):
        self.assertEqual(safe_eval('1 /'), "Ошибка ввода")
        self.assertEqual(safe_eval('a + b'), "Ошибка ввода")
        self.assertEqual(safe_eval('import os'), "Ошибка ввода")
        self.assertEqual(safe_eval('2 + '), "Ошибка ввода")

if __name__ == '__main__':
    unittest.main()
