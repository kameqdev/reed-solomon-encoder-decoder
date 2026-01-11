import unittest
import random
from encoder import encode, G_X
from decoder import decode
from config import T

class TestDecoderE2E(unittest.TestCase):
    """
    Testy End-to-End dla standardowego dekodera Reeda-Solomona.
    Sprawdzają scenariusze od kodowania, przez symulację błędów, po próbę odzyskania danych.
    """

    def setUp(self):
        # Ustawiamy seed, aby testy dekodera miały własną, powtarzalną losowość
        random.seed(2026)

        # Przygotowanie wiadomości testowej (powtarzalnej, ale zróżnicowanej)
        self.message_str = "To jest testowa wiadomosc o dlugosci 223 bajtow. " * 5
        self.message_bytes = [ord(c) for c in self.message_str[:223]]

        # Kodowanie wiadomości (wzorzec dla testów)
        self.encoded = encode(self.message_bytes, G_X)
        self.packet_len = len(self.encoded)
        self.cap = T # Zdolność korekcyjna (standardowo 16)

    def _corrupt_random_values(self, data, indices):
        """Pomocnicza: losowo zmienia wartości na wskazanych pozycjach."""
        corrupted = list(data)
        for idx in indices:
            # Zmieniamy na losową wartość inna niż oryginał
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

    def test_no_errors(self):
        """Sprawdza czy dekoder działa dla idealnego ciągu."""
        decoded, errors_found = decode(self.encoded)
        self.assertEqual(decoded, self.message_bytes)
        self.assertEqual(errors_found, 0)

    def test_max_capacity_scattered_random(self):
        """
        Sprawdza zdolność korekcyjną dla t=16 błędów rozrzuconych losowo.
        Błędy są losowymi wartościami.
        """
        error_count = self.cap
        indices = random.sample(range(self.packet_len), error_count)

        corrupted = self._corrupt_random_values(self.encoded, indices)

        decoded, errors_found = decode(corrupted)
        self.assertEqual(decoded, self.message_bytes, "Nie udało się naprawić maksymalnej liczby losowych błędów.")
        self.assertEqual(errors_found, error_count)

    def test_max_capacity_scattered_negation(self):
        """
        Sprawdza zdolność korekcyjną dla t=16 błędów rozrzuconych losowo.
        Błędy są negacją bitową.
        """
        error_count = self.cap
        indices = random.sample(range(self.packet_len), error_count)

        corrupted = self._corrupt_negation(self.encoded, indices)

        decoded, errors_found = decode(corrupted)
        self.assertEqual(decoded, self.message_bytes, "Nie udało się naprawić błędów negacji.")
        self.assertEqual(errors_found, error_count)

    def test_max_capacity_scattered_rotated(self):
        """
        Sprawdza zdolność korekcyjną dla t=16 błędów rozrzuconych losowo.
        Błędy są rotacją bitową.
        """
        error_count = self.cap
        indices = random.sample(range(self.packet_len), error_count)

        corrupted = self._corrupt_rotated_values(self.encoded, indices)

        decoded, errors_found = decode(corrupted)
        self.assertEqual(decoded, self.message_bytes, "Nie udało się naprawić błędów rotacji.")
        self.assertEqual(errors_found, error_count)

    def test_max_capacity_burst(self):
        """
        Sprawdza zdolność korekcyjną dla t=16 błędów występujących ciągiem (burst).
        Symuluje dziurę w transmisji.
        """
        error_count = self.cap
        start_idx = random.randint(0, self.packet_len - error_count)
        indices = list(range(start_idx, start_idx + error_count))

        corrupted = self._corrupt_random_values(self.encoded, indices)

        decoded, errors_found = decode(corrupted)
        self.assertEqual(decoded, self.message_bytes, "Nie udało się naprawić ciągu błędów (burst).")
        self.assertEqual(errors_found, error_count)

    def test_over_capacity(self):
        """
        Sprawdza zachowanie dekodera po przekroczeniu zdolności korekcyjnej (t+1 = 17 błędów).
        Oczekujemy rzucenia wyjątku (lub informacji o błędzie), a nie zwrócenia błędnych danych jako poprawnych.
        """
        error_count = self.cap + 1 # 17 błędów
        indices = random.sample(range(self.packet_len), error_count)

        corrupted = self._corrupt_random_values(self.encoded, indices)

        # Oczekujemy wyjątku, ponieważ dekoder powinien wykryć niemożność naprawy
        with self.assertRaises(Exception) as cm:
            decode(corrupted)


if __name__ == '__main__':
    unittest.main()
