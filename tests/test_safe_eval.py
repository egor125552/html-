import unittest
import sys
import os

# Add the parent directory to the path to allow direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_add(self):
        self.assertEqual(safe_eval('2+2'), 4)
        self.assertEqual(safe_eval('10 + 5'), 15)
        self.assertEqual(safe_eval('0+0'), 0)
        self.assertEqual(safe_eval('-5+5'), 0)
        self.assertAlmostEqual(safe_eval('1.5 + 2.5'), 4.0)

    def test_subtract(self):
        self.assertEqual(safe_eval('10-5'), 5)
        self.assertEqual(safe_eval('5-10'), -5)
        self.assertEqual(safe_eval('0-5'), -5)
        self.assertEqual(safe_eval('-5 - -5'), 0)
        self.assertAlmostEqual(safe_eval('3.5 - 1.5'), 2.0)

    def test_multiply(self):
        self.assertEqual(safe_eval('3*4'), 12)
        self.assertEqual(safe_eval('10 * 0'), 0)
        self.assertEqual(safe_eval('-5 * 5'), -25)
        self.assertEqual(safe_eval('-5 * -5'), 25)
        self.assertAlmostEqual(safe_eval('1.5 * 2'), 3.0)

    def test_divide(self):
        self.assertEqual(safe_eval('10/2'), 5)
        self.assertEqual(safe_eval('5/10'), 0.5)
        self.assertEqual(safe_eval('0/5'), 0)
        self.assertAlmostEqual(safe_eval('5/2'), 2.5)
        self.assertEqual(safe_eval('-10/2'), -5)

    def test_division_by_zero(self):
        self.assertEqual(safe_eval('10/0'), 'Error')
        self.assertEqual(safe_eval('1 / 0'), 'Error')

    def test_order_of_operations(self):
        self.assertEqual(safe_eval('2+3*4'), 14)
        self.assertEqual(safe_eval('10-2*3'), 4)
        self.assertEqual(safe_eval('10/2-3'), 2)
        self.assertEqual(safe_eval('(2+3)*4'), 20)

    def test_unary_minus(self):
        self.assertEqual(safe_eval('-5'), -5)
        self.assertEqual(safe_eval('- 5'), -5)
        self.assertEqual(safe_eval('2+-3'), -1)

    def test_user_friendly_operators(self):
        self.assertEqual(safe_eval('5×2'), 10)
        self.assertEqual(safe_eval('10÷2'), 5)
        self.assertEqual(safe_eval('5 × 2 + 10 ÷ 5'), 12)

    def test_invalid_expressions(self):
        self.assertEqual(safe_eval(''), 'Error')
        self.assertEqual(safe_eval('2++2'), 'Error')
        self.assertEqual(safe_eval('10 5'), 'Error')
        self.assertEqual(safe_eval('abc'), 'Error')
        self.assertEqual(safe_eval('2+'), 'Error')
        self.assertEqual(safe_eval('eval("1+1")'), 'Error')

    def test_unsafe_expressions(self):
        self.assertEqual(safe_eval('__import__("os").system("echo unsafe")'), 'Error')
        self.assertEqual(safe_eval('a=1'), 'Error')
        self.assertEqual(safe_eval('print("hello")'), 'Error')

if __name__ == '__main__':
    unittest.main()
