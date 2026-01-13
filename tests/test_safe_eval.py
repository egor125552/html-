import unittest
import sys
import os

# Add the parent directory to the Python path to allow importing the calculator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_valid_expressions(self):
        self.assertEqual(safe_eval("1 + 1"), 2.0)
        self.assertEqual(safe_eval("10 - 2.5"), 7.5)
        self.assertEqual(safe_eval("2 * 3.0"), 6.0)
        self.assertEqual(safe_eval("10 / 4"), 2.5)
        self.assertEqual(safe_eval("-5"), -5.0)
        self.assertEqual(safe_eval("5 + 2 * 3"), 11.0)
        self.assertEqual(safe_eval("(5 + 2) * 3"), 21.0)
        self.assertAlmostEqual(safe_eval("1 + 2 - 3 * 4 / 5"), 0.6)

    def test_invalid_expressions(self):
        with self.assertRaises(ValueError):
            safe_eval("import os")
        with self.assertRaises(ValueError):
            safe_eval("__import__('os').system('ls')")
        with self.assertRaises(ValueError):
            safe_eval("1 % 2") # Modulo is not allowed
        with self.assertRaises(ValueError):
            safe_eval("abs(-1)")
        with self.assertRaises(ValueError):
            safe_eval("1 & 2")
        with self.assertRaises(ValueError):
            safe_eval("1 +")

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            safe_eval("1 / 0")
        with self.assertRaises(ZeroDivisionError):
            safe_eval("10 / (5 - 5)")

if __name__ == '__main__':
    unittest.main()
