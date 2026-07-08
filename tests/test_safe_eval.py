import unittest
from calculator.safe_eval import safe_eval
import math

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), 4)
        self.assertEqual(safe_eval("2-2"), 0)
        self.assertEqual(safe_eval("2*3"), 6)
        self.assertEqual(safe_eval("6/2"), 3)
        self.assertEqual(safe_eval("2**3"), 8)
        self.assertEqual(safe_eval("5%2"), 1)

    def test_scientific_functions(self):
        self.assertEqual(safe_eval("sqrt(16)"), 4)
        self.assertAlmostEqual(safe_eval("sin(pi/2)"), 1.0)
        self.assertAlmostEqual(safe_eval("cos(pi)"), -1.0)
        self.assertEqual(safe_eval("log(100)"), 2)
        self.assertEqual(safe_eval("factorial(5)"), 120)
        self.assertEqual(safe_eval("abs(-5)"), 5)

    def test_constants(self):
        self.assertAlmostEqual(safe_eval("pi"), math.pi)
        self.assertAlmostEqual(safe_eval("e"), math.e)

    def test_errors(self):
        self.assertEqual(safe_eval("1/0"), "Error")
        self.assertEqual(safe_eval("invalid"), "Error")
        self.assertEqual(safe_eval("sin(1, 2)"), "Error")

if __name__ == '__main__':
    unittest.main()
