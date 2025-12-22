from gf import GF
from encoder import GF_CALC as GF_INSTANCE # Używamy tej samej instancji co koder
from encoder import ALPHA, T, G_X # Bierzemy stałe ustawienia: T (korekcja), G_X (wielomian generujący)

### FUNKCJE POMOCNICZE (Operacje na wielomianach dla Half-Decodera)

def poly_add(p, q): # Dodaje dwa wielomiany (XOR współczynników).
    # Ustal, który jest dłuższy, aby wynik miał odpowiednią długość
    if len(p) > len(q): # Sprawdzamy długość p
        longer, shorter = p, q # Przypisanie dłuższego i krótszego
    else: # W przeciwnym wypadku
        longer, shorter = q, p # Odwrotne przypisanie
    res = list(longer) # Kopiujemy dłuższy wielomian jako bazę wyniku
    # Dodajemy krótszy do końcówki dłuższego (wyrównanie do prawej - najniższych potęg)
    offset = len(longer) - len(shorter) # Obliczamy przesunięcie
    for i in range(len(shorter)): # Iterujemy przez elementy krótszego wielomianu
        res[offset + i] = GF_INSTANCE.add(res[offset + i], shorter[i]) # Wykonujemy XOR (dodawanie w GF)
    return res # Zwracamy wynik dodawania

def poly_div_remainder(dividend, divisor): # Dzielenie wielomianów, zwraca tylko resztę (Syndrom wielomianowy).
    # Funkcja kluczowa dla metody Mochnackiego: S(x) = R(x) mod G(x)
    msg_out = list(dividend) # Kopiujemy dzielną (wiadomość) do zmiennej roboczej
    # Normalizujemy długość pętlą dzielenia
    for i in range(len(dividend) - (len(divisor) - 1)): # Iterujemy przez stopnie swobody
        coef = msg_out[i] # Pobieramy współczynnik przy najwyższej potędze
        if coef != 0: # Jeśli współczynnik nie jest zerem, redukujemy
            for j in range(1, len(divisor)): # Pętla po współczynnikach dzielnika (G_X)
                if divisor[j] != 0: # Optymalizacja dla zer w dzielniku
                    # msg_out[i + j] += -divisor[j] * coef (w GF odejmowanie to dodawanie)
                    val = GF_INSTANCE.mul(divisor[j], coef) # Mnożymy współczynnik dzielnika przez wiodący
                    msg_out[i + j] = GF_INSTANCE.add(msg_out[i + j], val) # Dodajemy (XOR) do reszty
    
    separator = -(len(divisor) - 1) # Obliczamy miejsce odcięcia reszty
    return msg_out[separator:] # Zwracamy samą resztę z dzielenia

def hamming_weight(poly): # Oblicza wagę Hamminga (liczbę niezerowych elementów).
    weight = 0 # Licznik wagi
    for coef in poly: # Przeglądamy każdy współczynnik
        if coef != 0: # Jeśli nie jest zerem
            weight += 1 # Inkrementujemy wagę
    return weight # Zwracamy wynik

def cyclic_shift(data, steps): # Przesunięcie cykliczne wektora (niezbędne w Error Trapping).
    arr = list(data) # Kopiujemy dane
    n = len(arr) # Długość wektora
    steps = steps % n # Zabezpieczenie modulo długość
    # Przesuwamy: to co było na końcu idzie na początek (rotacja w prawo)
    return arr[-steps:] + arr[:-steps] # Zwracamy przesuniętą listę

### GŁÓWNA LOGIKA DEKODERA (Half Decoder / Error Trapping)

def decode(received_message): # Główna funkcja dekodująca, interfejs zgodny z Twoim kodem
    # 1. PRZYGOTOWANIE I PADDING
    original_len = len(received_message) # Zapamiętujemy oryginalną długość
    nsym = len(G_X) - 1 # Liczba symboli korekcyjnych (stopień G(x))
    # Mochnacki: t = floor(nsym / 2)
    correction_capacity = nsym // 2 # Zdolność korekcyjna t
    
    # Obsługa kodów skróconych (padding zerami do 255)
    if original_len == 255: # Jeśli pełny blok
        padded_msg = list(received_message) # Kopia
        padding_len = 0 # Brak paddingu
    else: # Jeśli kod skrócony
        padding_len = 255 - original_len # Ile zer brakuje
        padded_msg = [0] * padding_len + list(received_message) # Dodajemy zera na początku
        
    n = len(padded_msg) # Długość bloku (powinno być 255)
    current_msg = list(padded_msg) # Kopia robocza do operacji przesuwania
    
    # 2. ALGORYTM "ŁOWIENIA BŁĘDÓW" (Error Trapping)
    # Zamiast skomplikowanego BMA, przesuwamy wiadomość i sprawdzamy wagę reszty.
    
    found_correction = False # Flaga sukcesu
    shifts_performed = 0 # Licznik wykonanych przesunięć
    final_error_count = 0 # Licznik błędów do zwrócenia
    
    for shift in range(n): # Próbujemy każdego z n możliwych przesunięć cyklicznych
        
        # Obliczamy syndrom jako resztę z dzielenia: S(x) = R_przesunięte(x) mod G(x)
        syndrome = poly_div_remainder(current_msg, G_X) # Dzielenie wielomianów
        
        # Sprawdzamy wagę Hamminga syndromu
        w = hamming_weight(syndrome) # Ile jest błędów w obecnej "oknie"
        
        # Warunek z książki Mochnackiego: Jeśli waga(S) <= t, to znaleźliśmy błędy!
        if w <= correction_capacity and w > 0: # Znaleziono naprawialny wzór błędów
            # Naprawa: Dodajemy syndrom do końca wiadomości (tam gdzie jest reszta)
            # W tym stanie przesunięcia, syndrom JEST wektorem błędu.
            current_msg = poly_add(current_msg, syndrome) # Korekcja XOR
            final_error_count = w # Zapisujemy liczbę naprawionych błędów
            found_correction = True # Ustawiamy flagę
            shifts_performed = shift # Zapamiętujemy ile trzeba wrócić
            break # Przerywamy pętlę, naprawione
            
        elif w == 0: # Jeśli waga 0, to brak błędów
            found_correction = True # Uznajemy za sukces
            final_error_count = 0 # Zero błędów
            shifts_performed = shift # Zapamiętujemy przesunięcie
            break # Koniec
            
        # Jeśli nie znaleziono, przesuwamy cyklicznie w prawo o 1 i próbujemy dalej
        current_msg = cyclic_shift(current_msg, 1) # Rotacja wektora
    
    # 3. FINALIZACJA I POWRÓT
    
    if found_correction: # Jeśli udało się naprawić
        # Musimy odkręcić przesunięcia, które wykonaliśmy szukając błędu
        # Przesuwamy w lewo o tyle, ile przesunęliśmy w prawo (czyli -shifts_performed)
        if shifts_performed > 0: # Jeśli były przesunięcia
             fixed_msg_shifted_back = cyclic_shift(current_msg, -shifts_performed) # Powrót
        else: # Jeśli trafiliśmy od razu (shift 0)
             fixed_msg_shifted_back = current_msg # Bez zmian
             
        # Usuwamy padding i parzystość, aby zwrócić czyste dane
        # Uwaga: w Twoim kodzie padding jest na początku, parzystość na końcu
        fixed_msg_with_parity = fixed_msg_shifted_back[padding_len:] # Usuwamy padding z początku
        recovered_data = fixed_msg_with_parity[:-nsym] # Usuwamy parzystość z końca
        
        return recovered_data, final_error_count # Zwracamy dane i liczbę błędów
        
    else: # Jeśli pętla przeszła n razy i waga syndromu zawsze była > t
        # Oznacza to błąd zbyt skomplikowany dla dekodera Error Trapping (Half Decoder)
        # Zachowujemy się jak Twój kod - rzucamy wyjątek (lub można zwrócić krotkę z błędem)
        raise Exception("Dekoder niepełny (Error Trapping) nie znalazł wzorca błędu. Błędy zbyt rozproszone.") # Błąd krytyczny

### TESTY (Dokładnie takie same jak w Twoim kodzie)

if __name__ == "__main__":
    from encoder import encode # Importujemy funkcję kodującą
    import random # Do losowania błędów
    
    print("\n" + "="*50) # Linia oddzielająca
    print("   TEST ALGORYTMU MOCHNACKIEGO (HALF DECODER / ERROR TRAPPING)") # Tytuł
    print("="*50) # Linia oddzielająca
    
    # 1. PRZYGOTOWANIE DANYCH
    # Możesz tu wpisać tekst do max 223 znaków
    text = "Witaj Swiecie! Testujemy dekoder Mochnackiego (Error Trapping)." # Tekst testowy
    data = [ord(x) for x in text] # zamiana na listę bajtów (ASCII)
    
    print(f"\n[1] WIADOMOŚĆ ORYGINALNA ({len(data)} bajtów):") # Info o danych
    print(f"    '{text}'") # Wyświetlenie tekstu
    
    # 2. KODOWANIE
    # Encode zwraca listę [dane ... dane, parzystość ... parzystość]
    encoded = encode(data, G_X) # Kodowanie Reed-Solomon
    
    # Rozdzielamy dla czytelności
    nsym_test = len(G_X) - 1 # Obliczamy liczbę symboli parzystości
    data_part = encoded[:-nsym_test] # Część z danymi
    parity_part = encoded[-nsym_test:] # Część z parzystością
    
    print(f"\n[2] ZAKODOWANA WIADOMOŚĆ (Razem {len(encoded)} bajtów):") # Info
    print(f"    Dane:       '{''.join([chr(x) for x in data_part])}'") # Wyświetlenie danych
    # Wyświetlamy parzystość jako liczby HEX
    print(f"    Parzystość: {[hex(x) for x in parity_part]}") # Wyświetlenie ECC
    
    # 3. PSUCIE DANYCH (SYMULACJA BŁĘDÓW)
    corrupted = list(encoded) # Kopia do psucia
    
    # UWAGA: Dekoder Error Trapping najlepiej radzi sobie z błędami skupionymi (burst)
    # Przy błędach losowych (random) jego skuteczność jest niższa niż BMA.
    # Ustawiamy błędy blisko siebie, aby pokazać działanie mechanizmu.
    errors_count = 3 # Ilość błędów
    start_err = 5 # Pozycja startowa błędów
    errors_indices = [start_err + i for i in range(errors_count)] # Błędy obok siebie (burst)
    
    print(f"\n[3] SYMULACJA KANAŁU (Wprowadzanie {errors_count} błędów typu burst):") # Info
    print(f"    Uszkodzone pozycje: {sorted(errors_indices)}") # Gdzie psujemy
    
    for idx in errors_indices: # Pętla psująca
        corrupted[idx] ^= 0xFF # Odwracamy bity (psujemy bajt)
        
    # Podgląd uszkodzonego tekstu
    corrupted_str = "" # String wynikowy
    for byte in corrupted[:-nsym_test]: # Iteracja po danych
        if 32 <= byte <= 126: # Znaki drukowalne ASCII
            corrupted_str += chr(byte) # Dodaj znak
        else: # Niedrukowalne
            corrupted_str += "█" # Znak uszkodzenia
            
    print(f"    Podgląd uszkodzeń:  '{corrupted_str}'") # Wyświetlenie
    
    # 4. DEKODOWANIE (NAPRAWA)
    print(f"\n[4] DEKODOWANIE (Metoda Error Trapping)...") # Info
    try: # Blok try-except
        decoded, corrections = decode(corrupted) # Próba naprawy
        
        # Konwersja na tekst
        decoded_text = "".join([chr(x) for x in decoded]) # Bajty na string
        
        print(f"    Status: SUKCES") # Info sukces
        print(f"    Znaleziono i naprawiono błędów: {corrections}") # Ilość napraw
        print(f"    ODSZYFROWANA WIADOMOŚĆ:") # Wynik
        print(f"    '{decoded_text}'") # Tekst
        
        print("\n" + "-"*50) # Linia
        if decoded[:len(data)] == data: # Porównanie z oryginałem
            print(" >> WERYFIKACJA: ZGODNA Z ORYGINAŁEM <<") # Sukces weryfikacji
        else: # Błąd weryfikacji
            print(" >> WERYFIKACJA: BŁĄD (Różne dane) <<") # Porażka
        print("-"*50) # Linia
            
    except Exception as e: # Przechwycenie błędu dekodowania
        print(f"    Status: BŁĄD KRYTYCZNY (Dekoder niepełny nie dał rady)") # Info
        print(f"    Opis: {e}") # Treść błędu