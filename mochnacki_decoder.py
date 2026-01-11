from encoder import G_X # Bierzemy stałe ustawienia: T (korekcja), G_X (wielomian generujący)
from poly import Poly

### FUNKCJE POMOCNICZE (Operacje na wielomianach dla Half-Decodera)

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
        syndrome = Poly.div_remainder(current_msg, G_X) # Dzielenie wielomianów

        # Sprawdzamy wagę Hamminga syndromu
        w = hamming_weight(syndrome) # Ile jest błędów w obecnej "oknie"

        # Warunek z książki Mochnackiego: Jeśli waga(S) <= t, to znaleźliśmy błędy!
        if w <= correction_capacity and w > 0: # Znaleziono naprawialny wzór błędów
            # Naprawa: Dodajemy syndrom do końca wiadomości (tam gdzie jest reszta)
            # W tym stanie przesunięcia, syndrom JEST wektorem błędu.
            current_msg = Poly.add(current_msg, syndrome) # Korekcja XOR
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

        # =================================================================================
        # ZABEZPIECZENIE (WYMÓG PROJEKTOWY)
        # =================================================================================
        # Sprawdzamy, czy "naprawiona" wiadomość jest poprawnym słowem kodowym.
        # Przy dużej liczbie błędów (>t) Error Trapping może znaleźć fałszywego kandydata.
        # Jeśli reszta z dzielenia przez generator nie jest zerem, odrzucamy wynik.
        check_syndrome = Poly.div_remainder(fixed_msg_shifted_back, G_X)
        if max(check_syndrome) != 0:
            raise Exception(f"Weryfikacja nieudana! Znaleziono kandydata, ale syndrom nadal niezerowy. (Zbyt wiele błędów?)")
        # =================================================================================

        # Usuwamy padding i parzystość, aby zwrócić czyste dane
        # Uwaga: w Twoim kodzie padding jest na początku, parzystość na końcu
        fixed_msg_with_parity = fixed_msg_shifted_back[padding_len:] # Usuwamy padding z początku
        recovered_data = fixed_msg_with_parity[:-nsym] # Usuwamy parzystość z końca

        return recovered_data, final_error_count # Zwracamy dane i liczbę błędów

    else: # Jeśli pętla przeszła n razy i waga syndromu zawsze była > t
        # Oznacza to błąd zbyt skomplikowany dla dekodera Error Trapping (Half Decoder)
        # Zachowujemy się jak Twój kod - rzucamy wyjątek (lub można zwrócić krotkę z błędem)
        raise Exception("Dekoder niepełny (Error Trapping) nie znalazł wzorca błędu. Błędy zbyt rozproszone.") # Błąd krytyczny