import unittest
import math
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), 4)
        self.assertEqual(safe_eval("10-5"), 5)
        self.assertEqual(safe_eval("3×4"), 12)
        self.assertEqual(safe_eval("10÷2"), 5)
        self.assertEqual(safe_eval("2^3"), 8)
        self.assertEqual(safe_eval("-5+3"), -2)

    def test_scientific_functions(self):
        self.assertAlmostEqual(safe_eval("sin(0)"), 0)
        self.assertAlmostEqual(safe_eval("cos(0)"), 1)
        self.assertAlmostEqual(safe_eval("sqrt(16)"), 4)
        self.assertAlmostEqual(safe_eval("log(100)"), 2)
        self.assertAlmostEqual(safe_eval("ln(e)"), 1)
        self.assertAlmostEqual(safe_eval("exp(1)"), math.e)

    def test_constants(self):
        self.assertAlmostEqual(safe_eval("pi"), math.pi)
        self.assertAlmostEqual(safe_eval("e"), math.e)

    def test_factorial(self):
        self.assertEqual(safe_eval("factorial(5)"), 120)

    def test_errors(self):
        self.assertEqual(safe_eval("1/0"), "Error: Div by 0")
        self.assertEqual(safe_eval("1÷0"), "Error: Div by 0")
        self.assertEqual(safe_eval("abc"), "Error")

if __name__ == "__main__":
    unittest.main()
