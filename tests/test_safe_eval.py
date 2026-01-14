import unittest
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы можно было импортировать 'calculator'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertAlmostEqual(safe_eval("2 + 2"), 4.0)
        self.assertAlmostEqual(safe_eval("10.5 + 3.5"), 14.0)

    def test_subtract(self):
        self.assertAlmostEqual(safe_eval("10 - 4"), 6.0)
        self.assertAlmostEqual(safe_eval("3.5 - 1.2"), 2.3)

    def test_multiply(self):
        self.assertAlmostEqual(safe_eval("3 * 7"), 21.0)
        self.assertAlmostEqual(safe_eval("2.5 * 2.5"), 6.25)

    def test_divide(self):
        self.assertAlmostEqual(safe_eval("10 / 4"), 2.5)
        self.assertAlmostEqual(safe_eval("5 / 2"), 2.5)

    def test_negative_numbers(self):
        self.assertAlmostEqual(safe_eval("-5 + 10"), 5.0)
        self.assertAlmostEqual(safe_eval("10 + -5"), 5.0)
        self.assertAlmostEqual(safe_eval("-3 * -3"), 9.0)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            safe_eval("1 / 0")

    def test_invalid_syntax(self):
        with self.assertRaises(ValueError):
            safe_eval("2 +")
        with self.assertRaises(ValueError):
            safe_eval("1.2.3 + 4")
        with self.assertRaises(ValueError):
            safe_eval("1 ++ 2")

    def test_disallowed_operators(self):
        # Моя функция вызывает ValueError для любых неизвестных бинарных операторов
        with self.assertRaises(ValueError):
            safe_eval("2 ** 3") # Степерь
        with self.assertRaises(ValueError):
            safe_eval("1 << 2") # Битовый сдвиг

    def test_empty_input(self):
        self.assertEqual(safe_eval(""), 0.0)

if __name__ == '__main__':
    unittest.main()
