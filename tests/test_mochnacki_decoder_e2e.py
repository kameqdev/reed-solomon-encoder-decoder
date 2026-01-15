import unittest
import random
from encoder import encode, G_X
from mochnacki_decoder import decode as mochnacki_decode
from config import T

class MochnackiDecoderBaseTest(unittest.TestCase):
    """
    Klasa bazowa z metodami pomocniczymi dla testów dekodera Mochnackiego.
    """
    def setUp(self):
        # Ustawiamy seed, aby uniezależnić się od stanu generatora po innych testach
        random.seed(2026)
        
        self.message_str = "Mochnacki Decoder Test Message - 223 bytes payload pattern. " * 4
        self.message_bytes = [ord(c) for c in self.message_str[:223]]
        if len(self.message_bytes) < 223:
            self.message_bytes += [ord('.')] * (223 - len(self.message_bytes))
        
        self.encoded = encode(self.message_bytes, G_X)
        self.packet_len = len(self.encoded)
        self.std_cap = T

    def _corrupt_random_values(self, data, indices):
        corrupted = list(data)
        for idx in indices:
            orig = corrupted[idx]
            while True:
                new_val = random.randint(0, 255)
                if new_val != orig:
                    corrupted[idx] = new_val
                    break
        return corrupted
    
    def _corrupt_negation(self, data, indices):
        """Pomocnicza: neguje bity (XOR 0xFF) na wskazanych pozycjach."""
        corrupted = list(data)
        for idx in indices:
            corrupted[idx] ^= 0xFF
        return corrupted

    def _corrupt_rotated_values(self, data, indices):
        """
        Symuluje błędy poprzez bitową rotację (cykliczne przesunięcie bitów) wartości bajtu.
        """
        corrupted = list(data)
        for idx in indices:
            val = corrupted[idx]
            # Rotacja w lewo o 1 bit: (val << 1) | (val >> 7)
            new_val = ((val << 1) | (val >> 7)) & 0xFF
            # Sytuacja brzegowa: 0x00 i 0xFF się nie zmieniają przy rotacji
            if new_val == val:
                new_val = (val ^ 0b01010101) & 0xFF 
            corrupted[idx] = new_val
        return corrupted


class TestMochnackiDecoderIterative(MochnackiDecoderBaseTest):
    """
    Test iteracyjny sprawdzający możliwości dekodera Mochnackiego.
    Testuje zakres błędów od 0 do 17.
    """

    # Próg błędów rozproszonych, dla którego test MUSI przejść.
    SCATTERED_GUARANTEED_THRESHOLD = 1
    # Próg błędów w ciągu (burst), dla którego test MUSI przejść.
    BURST_GUARANTEED_THRESHOLD = 8

    def test_no_errors(self):
        """Brak błędów - powinien zawsze przejść."""
        decoded, _ = mochnacki_decode(self.encoded)
        self.assertEqual(decoded, self.message_bytes, "Brak błędów: dekoder zawiódł.")

    def test_over_capacity(self):
        """Powyżej 16 błędów - test powinien przejść, jeśli dekoder NIE naprawi błędnie."""
        error_count = 17
        indices = random.sample(range(self.packet_len), error_count)
        corrupted = self._corrupt_random_values(self.encoded, indices)
        
        try:
            decoded, _ = mochnacki_decode(corrupted)
            # Sukces testu to brak fałszywie pozytywnego wyniku.
            self.assertNotEqual(decoded, self.message_bytes,
                "Niespodziewanie naprawił ponad 16 błędów (false positive).")
        except Exception:
            # Wyjątek jest akceptowalny
            pass
        
    def test_max_scatter_distance(self):
        """Test maksymalnej odległości rozproszonych błędów."""
        max_dist_between_errors = self.packet_len - 2
        for dist in range(1, max_dist_between_errors):
            corrupted = self._corrupt_random_values(self.encoded, [0, dist+1])
            
            success = False
            try:
                decoded, _ = mochnacki_decode(corrupted)
                if decoded == self.message_bytes:
                    success = True
            except Exception:
                success = False


            if dist <= 30: # Errors have to be in 32-symbol window to be correctable
                self.assertTrue(success, f"({self.__class__.__name__}.{self._testMethodName}) Failed at distance between errors: {dist}")
            if not success:
                print(f"({self.__class__.__name__}.{self._testMethodName}) Decoder failed at distance between errors: {dist}, stopping further tests.")
                return

    def _run_iterative_test(self, error_generator, min_guaranteed, is_burst):
        test_method = self._testMethodName
        for errors in range(1, 17):
            # Wybieramy indeksy
            if not is_burst:
                indices = random.sample(range(self.packet_len), errors)
            else:
                start_idx = random.randint(0, self.packet_len - errors)
                indices = list(range(start_idx, start_idx + errors))

            corrupted = error_generator(self.encoded, indices)

            success = False
            try:
                decoded, _ = mochnacki_decode(corrupted)
                if decoded == self.message_bytes:
                    success = True
            except Exception:
                success = False

            if errors <= min_guaranteed:
                self.assertTrue(success, f"({self.__class__.__name__}.{test_method}) Failed at {errors} errors (Guaranteed threshold: {min_guaranteed})")
            if not success:
                print(f"({self.__class__.__name__}.{test_method}) Decoder failed at {errors} errors, stopping further tests.")
                return

    def test_iterative_scattered_random(self):
        self._run_iterative_test(self._corrupt_random_values, self.SCATTERED_GUARANTEED_THRESHOLD, is_burst=False)

    def test_iterative_scattered_negation(self):
        self._run_iterative_test(self._corrupt_negation, self.SCATTERED_GUARANTEED_THRESHOLD, is_burst=False)

    def test_iterative_scattered_rotated(self):
        self._run_iterative_test(self._corrupt_rotated_values, self.SCATTERED_GUARANTEED_THRESHOLD, is_burst=False)

    def test_iterative_burst_random(self):
        self._run_iterative_test(self._corrupt_random_values, self.BURST_GUARANTEED_THRESHOLD, is_burst=True)

    def test_iterative_burst_negation(self):
        self._run_iterative_test(self._corrupt_negation, self.BURST_GUARANTEED_THRESHOLD, is_burst=True)

    def test_iterative_burst_rotated(self):
        self._run_iterative_test(self._corrupt_rotated_values, self.BURST_GUARANTEED_THRESHOLD, is_burst=True)

if __name__ == '__main__':
    unittest.main()
