import unittest
import sys
import os

# Add the project root to sys.path to allow importing 'calculator'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):

    def test_addition(self):
        """Tests basic addition."""
        self.assertEqual(safe_eval("1 + 2"), 3)
        self.assertEqual(safe_eval("5 + 5"), 10)
        self.assertEqual(safe_eval("100 + 0"), 100)
        self.assertEqual(safe_eval("-1 + 1"), 0)
        self.assertAlmostEqual(safe_eval("1.5 + 2.5"), 4.0)

    def test_subtraction(self):
        """Tests basic subtraction."""
        self.assertEqual(safe_eval("10 - 5"), 5)
        self.assertEqual(safe_eval("5 - 10"), -5)
        self.assertEqual(safe_eval("0 - 5"), -5)
        self.assertEqual(safe_eval("-1 - 1"), -2)
        self.assertAlmostEqual(safe_eval("5.5 - 2.5"), 3.0)

    def test_combined_operations(self):
        """Tests a combination of addition and subtraction."""
        self.assertEqual(safe_eval("10 + 5 - 3"), 12)
        self.assertEqual(safe_eval("2 - 1 + 8"), 9)

    def test_invalid_input(self):
        """Tests handling of invalid input."""
        self.assertEqual(safe_eval(""), "Error")
        self.assertEqual(safe_eval("1 +"), "Error")
        self.assertEqual(safe_eval("abc"), "Error")
        self.assertEqual(safe_eval("1 +/ 2"), "Error")
        self.assertEqual(safe_eval("1.1.1 + 2"), "Error")

    def test_multiplication(self):
        """Tests multiplication."""
        self.assertEqual(safe_eval("2 * 3"), 6)
        self.assertEqual(safe_eval("-2 * 3"), -6)
        self.assertAlmostEqual(safe_eval("1.5 * 2"), 3.0)

    def test_division(self):
        """Tests division."""
        self.assertEqual(safe_eval("10 / 2"), 5)
        self.assertEqual(safe_eval("-10 / 2"), -5)
        self.assertAlmostEqual(safe_eval("5 / 2"), 2.5)
        self.assertEqual(safe_eval("1 / 0"), "Error")

    def test_unary_minus(self):
        """Tests unary minus."""
        self.assertEqual(safe_eval("-5"), -5)
        self.assertEqual(safe_eval("-(-5)"), 5)
        self.assertEqual(safe_eval("1 + -5"), -4)

    def test_unsupported_operations(self):
        """Tests that unsupported operations return an error."""
        self.assertEqual(safe_eval("2 ** 3"), "Error")
        self.assertEqual(safe_eval("1 % 2"), "Error")
        self.assertEqual(safe_eval("import os"), "Error")
        self.assertEqual(safe_eval("__import__('os').system('echo pwned')"), "Error")

if __name__ == '__main__':
    unittest.main()
