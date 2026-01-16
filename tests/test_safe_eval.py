import unittest
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertEqual(safe_eval('2 + 3'), 5)

    def test_subtract(self):
        self.assertEqual(safe_eval('10 - 4'), 6)

    def test_multiply(self):
        self.assertEqual(safe_eval('5 * 6'), 30)

    def test_divide(self):
        self.assertEqual(safe_eval('10 / 2'), 5)

    def test_negative_numbers(self):
        self.assertEqual(safe_eval('-5 + 10'), 5)
        self.assertEqual(safe_eval('10 + -5'), 5)

    def test_order_of_operations(self):
        self.assertEqual(safe_eval('2 + 3 * 4'), 14)
        self.assertEqual(safe_eval('10 / 2 - 3'), 2)

    def test_float_numbers(self):
        self.assertAlmostEqual(safe_eval('2.5 + 3.5'), 6.0)
        self.assertAlmostEqual(safe_eval('10.5 / 2'), 5.25)

    def test_zero_division(self):
        self.assertIn('Ошибка', safe_eval('10 / 0'))

    def test_invalid_input(self):
        self.assertIn('Ошибка', safe_eval('10 +'))
        self.assertIn('Ошибка', safe_eval('abc'))
        self.assertIn('Ошибка', safe_eval('10 ** 2')) # Неподдерживаемый оператор

if __name__ == '__main__':
    unittest.main()
