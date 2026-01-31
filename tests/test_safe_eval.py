import unittest
from calculator.safe_eval import safe_eval

class TestSafeEval(unittest.TestCase):
    def test_basic_ops(self):
        self.assertEqual(safe_eval("2+2"), "4")
        self.assertEqual(safe_eval("10-5"), "5")
        self.assertEqual(safe_eval("3*4"), "12")
        self.assertEqual(safe_eval("3×4"), "12")
        self.assertEqual(safe_eval("10/2"), "5")
        self.assertEqual(safe_eval("10÷2"), "5")
        self.assertEqual(safe_eval("2**3"), "8")

    def test_scientific_ops(self):
        self.assertEqual(safe_eval("sqrt(16)"), "4")
        self.assertAlmostEqual(float(safe_eval("sin(0)")), 0.0)
        self.assertAlmostEqual(float(safe_eval("pi")), 3.141592653589793)

    def test_errors(self):
        self.assertEqual(safe_eval("1/0"), "Error")
        self.assertEqual(safe_eval("abc"), "Error")
        self.assertEqual(safe_eval("1++1"), "Error")

if __name__ == "__main__":
    unittest.main()
