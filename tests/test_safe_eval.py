import unittest
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(safe_eval("2+2"), 4)
        self.assertEqual(safe_eval("10-5"), 5)
        self.assertEqual(safe_eval("3*4"), 12)
        self.assertEqual(safe_eval("10/2"), 5.0)

    def test_operator_precedence(self):
        self.assertEqual(safe_eval("2+3*4"), 14)
        self.assertEqual(safe_eval("(2+3)*4"), 20)

    def test_floating_point(self):
        self.assertAlmostEqual(safe_eval("1.1+2.2"), 3.3, places=7)

    def test_visual_operators(self):
        self.assertEqual(safe_eval("6×7"), 42)
        self.assertEqual(safe_eval("42÷6"), 7.0)

    def test_unary_minus(self):
        self.assertEqual(safe_eval("-5+3"), -2)

    def test_scientific_functions(self):
        self.assertEqual(safe_eval("2^3"), 8)
        self.assertEqual(safe_eval("√(4)"), 2.0)
        self.assertAlmostEqual(safe_eval("sin(0)"), 0.0)
        self.assertAlmostEqual(safe_eval("cos(0)"), 1.0)
        self.assertAlmostEqual(safe_eval("pi"), 3.141592653589793)

    def test_errors(self):
        self.assertEqual(safe_eval("1/0"), "Error")
        self.assertEqual(safe_eval("abc"), "Error")

if __name__ == "__main__":
    unittest.main()
