import unittest
import math
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), 4)
        self.assertEqual(safe_eval("10-5"), 5)
        self.assertEqual(safe_eval("3*4"), 12)
        self.assertEqual(safe_eval("10/2"), 5)
        self.assertEqual(safe_eval("2**3"), 8)
        self.assertEqual(safe_eval("10%3"), 1)

    def test_order_of_operations(self):
        self.assertEqual(safe_eval("2+3*4"), 14)
        self.assertEqual(safe_eval("(2+3)*4"), 20)

    def test_scientific_functions(self):
        self.assertAlmostEqual(safe_eval("sin(0)"), 0)
        self.assertAlmostEqual(safe_eval("cos(0)"), 1)
        self.assertAlmostEqual(safe_eval("tan(0)"), 0)
        self.assertAlmostEqual(safe_eval("sqrt(16)"), 4)
        self.assertAlmostEqual(safe_eval("log(100)"), 2)
        self.assertAlmostEqual(safe_eval("ln(e)"), 1)
        self.assertEqual(safe_eval("factorial(5)"), 120)
        self.assertEqual(safe_eval("factorial(2+3)"), 120)
        self.assertAlmostEqual(safe_eval("exp(1)"), math.e)
        self.assertEqual(safe_eval("abs(-10)"), 10)
        self.assertEqual(safe_eval("abs(5)"), 5)

    def test_constants(self):
        self.assertAlmostEqual(safe_eval("pi"), math.pi)
        self.assertAlmostEqual(safe_eval("e"), math.e)

    def test_unary_minus(self):
        self.assertEqual(safe_eval("-5+3"), -2)
        self.assertEqual(safe_eval("-(5+3)"), -8)

    def test_errors(self):
        self.assertEqual(safe_eval("2/0"), "Error")
        self.assertEqual(safe_eval("invalid"), "Error")
        self.assertEqual(safe_eval("import os"), "Error")

if __name__ == '__main__':
    unittest.main()
