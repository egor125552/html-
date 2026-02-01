import unittest
import math
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), "4")
        self.assertEqual(safe_eval("10-5"), "5")
        self.assertEqual(safe_eval("3*4"), "12")
        self.assertEqual(safe_eval("10/2"), "5")
        self.assertEqual(safe_eval("2+3*4"), "14")
        self.assertEqual(safe_eval("(2+3)*4"), "20")

    def test_power(self):
        self.assertEqual(safe_eval("2^3"), "8")
        self.assertEqual(safe_eval("2**3"), "8")

    def test_math_functions(self):
        self.assertAlmostEqual(float(safe_eval("sin(0)")), 0.0)
        self.assertAlmostEqual(float(safe_eval("cos(0)")), 1.0)
        self.assertAlmostEqual(float(safe_eval("sqrt(16)")), 4.0)
        self.assertAlmostEqual(float(safe_eval("log(e)")), 1.0)

    def test_constants(self):
        self.assertAlmostEqual(float(safe_eval("pi")), math.pi)
        self.assertAlmostEqual(float(safe_eval("e")), math.e)

    def test_errors(self):
        self.assertEqual(safe_eval("1/0"), "Error")
        self.assertEqual(safe_eval("invalid"), "Error")
        self.assertEqual(safe_eval("2+*2"), "Error")

if __name__ == '__main__':
    unittest.main()
