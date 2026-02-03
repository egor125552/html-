import unittest
import math
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), "4")
        self.assertEqual(safe_eval("10-5"), "5")
        self.assertEqual(safe_eval("3*4"), "12")
        self.assertEqual(safe_eval("10/2"), "5")
        self.assertEqual(safe_eval("10/4"), "2.5")
        self.assertEqual(safe_eval("2**3"), "8")
        self.assertEqual(safe_eval("10%3"), "1")

    def test_floating_point(self):
        self.assertAlmostEqual(float(safe_eval("2.5+2.5")), 5.0)
        self.assertAlmostEqual(float(safe_eval("1.1*3")), 3.3)

    def test_scientific_functions(self):
        self.assertAlmostEqual(float(safe_eval("sqrt(16)")), 4.0)
        self.assertAlmostEqual(float(safe_eval("sin(0)")), 0.0)
        self.assertAlmostEqual(float(safe_eval("cos(0)")), 1.0)
        # pi
        self.assertAlmostEqual(float(safe_eval("pi")), math.pi)
        # log (base 10)
        self.assertEqual(safe_eval("log(100)"), "2")
        # ln (natural log)
        self.assertAlmostEqual(float(safe_eval("ln(e)")), 1.0)
        # factorial
        self.assertEqual(safe_eval("factorial(5)"), "120")

    def test_complex_expressions(self):
        self.assertEqual(safe_eval("2+3*4"), "14")
        self.assertEqual(safe_eval("(2+3)*4"), "20")
        self.assertAlmostEqual(float(safe_eval("sqrt(9)+2**3")), 11.0)

    def test_error_handling(self):
        self.assertEqual(safe_eval("1/0"), "Error")
        self.assertEqual(safe_eval("sqrt(-1)"), "Error")
        self.assertEqual(safe_eval("invalid"), "Error")
        self.assertEqual(safe_eval("2+"), "Error")
        self.assertEqual(safe_eval(""), "")

    def test_visual_symbols(self):
        self.assertEqual(safe_eval("3×4"), "12")
        self.assertEqual(safe_eval("10÷2"), "5")

if __name__ == "__main__":
    unittest.main()
