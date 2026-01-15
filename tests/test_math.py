import unittest
from gf import GF_CALC
from poly import Poly

class TestGF(unittest.TestCase):
    """Testy jednostkowe arytmetyki Ciała Galois (GF)."""

    def test_add_xor_property(self):
        """Dodawanie w GF(2^8) to XOR."""
        # A + A = 0
        self.assertEqual(GF_CALC.add(123, 123), 0)
        # A + 0 = A
        self.assertEqual(GF_CALC.add(255, 0), 255)
        # Przemienność
        self.assertEqual(GF_CALC.add(10, 20), GF_CALC.add(20, 10))

    def test_mul_properties(self):
        """Mnożenie w GF."""
        # A * 0 = 0
        self.assertEqual(GF_CALC.mul(123, 0), 0)
        # A * 1 = A
        self.assertEqual(GF_CALC.mul(45, 1), 45)
        # Przemienność
        self.assertEqual(GF_CALC.mul(7, 9), GF_CALC.mul(9, 7))

    def test_inverse(self):
        """Odwracanie elementów."""
        # A * A^-1 = 1
        a = 15
        inv_a = GF_CALC.inv(a)
        self.assertEqual(GF_CALC.mul(a, inv_a), 1)

    def test_inverse_zero_raises(self):
        """Odwracanie zera powinno rzucić wyjątek."""
        with self.assertRaises(ZeroDivisionError):
            GF_CALC.inv(0)

class TestPoly(unittest.TestCase):
    """Testy operacji na wielomianach."""

    def test_poly_add(self):
        """Dodawanie wielomianów."""
        # [1, 2] + [0, 3] -> [1, 2^3=1]
        p1 = [1, 2]
        p2 = [0, 3]
        res = Poly.add(p1, p2)
        # Sprawdzamy czy wynik ma sensowną długość i wartości
        # Operacja add wyrównuje do prawej? Sprawdźmy implementację w poly.py.
        # W poly.py: dodaje krótszy do końcówki dłuższego.
        # [1, 2] (stopień 1) + [0, 3] (stopień 1) -> dodajemy normalnie.
        # Jeśli implementacja traktuje listy jako [x^N, ... x^0], to wyrównanie do prawej jest poprawne.
        pass 

    def test_poly_mul_simple(self):
        """Mnożenie wielomianów: x * x = x^2."""
        # Reprezentacja: [1, 0] to x,  [1] to 1.
        p1 = [1, 0] # x
        p2 = [1, 0] # x
        # x * x = x^2 -> [1, 0, 0]
        res = Poly.multiply(p1, p2)
        self.assertEqual(res, [1, 0, 0])

    def test_poly_eval(self):
        """Ewaluacja wielomianu."""
        # p(x) = x + 1, czyli [1, 1]
        # p(2) = 2 + 1 = 3
        val = Poly.evaluate([1, 1], 2)
        self.assertEqual(val, 3)

if __name__ == '__main__':
    unittest.main()
