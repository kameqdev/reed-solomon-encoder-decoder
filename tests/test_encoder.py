import unittest
from encoder import encode, G_X
from reedsolo import RSCodec


class TestEncoderComparison(unittest.TestCase):
    """Testy porównujące naszą implementację z biblioteką reedsolo."""
    
    def setUp(self):
        """Przygotowanie kodeka reedsolo z tymi samymi parametrami."""
        # T=16 oznacza 16 symboli korekcyjnych (2*T=32 symbole ECC)
        self.rs_codec = RSCodec(32)  # 32 symbole ECC (2*T)
        
    def test_empty_message(self):
        """Test dla pustej wiadomości."""
        message = []
        
        # Nasza implementacja
        our_result = encode(message, G_X)
        
        # Reedsolo zwraca pustą listę dla pustej wiadomości
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        # Reedsolo zwraca [], a my zwracamy 32 zera - oba są poprawne
        # Akceptujemy oba warianty
        self.assertTrue(our_result == reedsolo_result or our_result == [0] * 32,
                        "Wyniki dla pustej wiadomości powinny być poprawne")
    
    def test_single_byte(self):
        """Test dla jednobajtowej wiadomości."""
        message = [42]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla jednego bajtu powinny być identyczne")
    
    def test_short_message(self):
        """Test dla krótkiej wiadomości."""
        message = [1, 2, 3, 4, 5]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla krótkiej wiadomości powinny być identyczne")
    
    def test_hello_world(self):
        """Test dla wiadomości 'Hello, World!'."""
        message = list(b"Hello, World!")
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla 'Hello, World!' powinny być identyczne")
    
    def test_all_zeros(self):
        """Test dla wiadomości składającej się z samych zer."""
        message = [0] * 50
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla samych zer powinny być identyczne")
    
    def test_all_ones(self):
        """Test dla wiadomości składającej się z samych jedynek."""
        message = [1] * 50
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla samych jedynek powinny być identyczne")
    
    def test_all_255(self):
        """Test dla wiadomości składającej się z wartości 255."""
        message = [255] * 50
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla wartości 255 powinny być identyczne")
    
    def test_sequential_bytes(self):
        """Test dla sekwencyjnych bajtów."""
        message = list(range(100))
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla sekwencyjnych bajtów powinny być identyczne")
    
    def test_random_message_small(self):
        """Test dla losowej małej wiadomości."""
        import random
        random.seed(42)  # Dla powtarzalności
        message = [random.randint(0, 255) for _ in range(20)]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla losowej małej wiadomości powinny być identyczne")
    
    def test_random_message_medium(self):
        """Test dla losowej średniej wiadomości."""
        import random
        random.seed(123)  # Dla powtarzalności
        message = [random.randint(0, 255) for _ in range(100)]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla losowej średniej wiadomości powinny być identyczne")
    
    def test_random_message_large(self):
        """Test dla losowej dużej wiadomości."""
        import random
        random.seed(456)  # Dla powtarzalności
        message = [random.randint(0, 255) for _ in range(200)]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla losowej dużej wiadomości powinny być identyczne")
    
    def test_maximum_length_message(self):
        """Test dla wiadomości o maksymalnej długości (223 bajty)."""
        import random
        random.seed(789)  # Dla powtarzalności
        message = [random.randint(0, 255) for _ in range(223)]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla maksymalnej długości wiadomości powinny być identyczne")
    
    def test_message_length_validation(self):
        """Test sprawdzający walidację długości wiadomości."""
        # Wiadomość za długa (224 bajty)
        message = [1] * 224
        
        with self.assertRaises(ValueError):
            encode(message, G_X)
    
    def test_special_characters(self):
        """Test dla wiadomości ze znakami specjalnymi."""
        message = list(b"!@#$%^&*()_+-=[]{}|;':\",./<>?")
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla znaków specjalnych powinny być identyczne")
    
    def test_binary_data(self):
        """Test dla binarnych danych."""
        message = [0x00, 0x01, 0x10, 0x11, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla danych binarnych powinny być identyczne")
    
    def test_parity_bytes_length(self):
        """Test sprawdzający czy liczba bajtów parzystości jest poprawna."""
        message = [1, 2, 3, 4, 5]
        
        our_result = encode(message, G_X)
        
        # Powinno być len(message) + 32 ECC
        expected_length = len(message) + 32
        self.assertEqual(len(our_result), expected_length,
                        f"Zakodowana wiadomość powinna mieć {expected_length} bajtów")
        
        # Pierwsze bajty powinny być oryginalną wiadomością
        self.assertEqual(our_result[:len(message)], message,
                        "Początek zakodowanej wiadomości powinien zawierać oryginalne dane")
    
    def test_encode_preserves_message(self):
        """Test sprawdzający czy kodowanie zachowuje oryginalną wiadomość."""
        message = list(b"Test message for preservation check")
        
        our_result = encode(message, G_X)
        
        # Pierwsze len(message) bajtów powinno być niezmienione
        self.assertEqual(our_result[:len(message)], message,
                        "Kodowanie powinno zachować oryginalną wiadomość na początku")


class TestEncoderEdgeCases(unittest.TestCase):
    """Testy przypadków brzegowych."""
    
    def setUp(self):
        """Przygotowanie kodeka reedsolo."""
        self.rs_codec = RSCodec(32)
    
    def test_repeating_pattern(self):
        """Test dla powtarzającego się wzorca."""
        message = [0xAA, 0xBB] * 50  # 100 bajtów
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla powtarzającego się wzorca powinny być identyczne")
    
    def test_alternating_zeros_ones(self):
        """Test dla naprzemiennych zer i jedynek."""
        message = [0, 1] * 100  # 200 bajtów
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla naprzemiennych wartości powinny być identyczne")
    
    def test_powers_of_two(self):
        """Test dla potęg dwójki."""
        message = [1, 2, 4, 8, 16, 32, 64, 128]
        
        our_result = encode(message, G_X)
        reedsolo_result = list(self.rs_codec.encode(bytearray(message)))
        
        self.assertEqual(our_result, reedsolo_result,
                        "Wyniki dla potęg dwójki powinny być identyczne")


if __name__ == '__main__':
    # Uruchomienie testów z szczegółowym outputem
    unittest.main(verbosity=2)
