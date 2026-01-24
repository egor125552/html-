import unittest
import sys
import os

# Add the parent directory to the Python path to allow importing 'calculator'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(safe_eval("2 + 3"), 5)
        self.assertEqual(safe_eval("10 + -5"), 5)

    def test_subtraction(self):
        self.assertEqual(safe_eval("10 - 5"), 5)
        self.assertEqual(safe_eval("5 - 10"), -5)

    def test_multiplication(self):
        self.assertEqual(safe_eval("4 * 5"), 20)
        self.assertEqual(safe_eval("-2 * 3"), -6)

    def test_division(self):
        self.assertEqual(safe_eval("10 / 2"), 5)
        self.assertAlmostEqual(safe_eval("1 / 3"), 0.3333333333333333)

    def test_power(self):
        self.assertEqual(safe_eval("2**3"), 8)
        self.assertEqual(safe_eval("4**2"), 16)

    def test_unsupported_operator(self):
        self.assertEqual(safe_eval("4^2"), "Ошибка ввода")

    def test_order_of_operations(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(safe_eval("(2 + 3) * 4"), 20)

    def test_zero_division(self):
        self.assertEqual(safe_eval("10 / 0"), "Деление на ноль")

    def test_invalid_input(self):
        self.assertEqual(safe_eval("a + b"), "Ошибка ввода")
        self.assertEqual(safe_eval("10 +"), "Ошибка ввода")

    def test_malicious_code(self):
        self.assertEqual(safe_eval("__import__('os').system('echo pwned')"), "Ошибка ввода")
        self.assertEqual(safe_eval("print('hello')"), "Ошибка ввода")

if __name__ == '__main__':
    unittest.main()
