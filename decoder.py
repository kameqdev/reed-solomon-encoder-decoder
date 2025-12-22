from gf import GF
from encoder import GF_CALC as GF_INSTANCE # Używamy tej samej instancji co koder
from encoder import ALPHA, T, G_X #bierzemy stałe ustawienia

###FUNKCJE POMOCNICZE (Operacje na wielomianach)

def poly_eval(poly, x): # konkrertna wartość x np alpha^i ,Oblicza wartość wielomianu w punkcie x (Schemat Hornera).
    y = poly[0] # najwyższy współczynnik
    for i in range(1, len(poly)):
        y = GF_INSTANCE.add(GF_INSTANCE.mul(y, x), poly[i])# y = y*x + poly[i] #https://www.algorytm.edu.pl/algorytmy-w-python/schemat-hornera-python
    return y # dla syndromów jak da 0 to brak błędów

def poly_scale(p, x):# p, czyli lista współczynników (BMA)
    return [GF_INSTANCE.mul(coef, x) for coef in p] # Mnoży każdy współczynnik wielomianu p przez skalar x.

def poly_add(p, q): #Dodaje dwa wielomiany (XOR współczynników).
    # Ustal, który jest dłuższy, aby wynik miał odpowiednią długość
    if len(p) > len(q):
        longer, shorter = p, q
    else:
        longer, shorter = q, p
    res = list(longer)
    # Dodajemy krótszy do końcówki dłuższego (wyrównanie do prawej - najniższych potęg)
    offset = len(longer) - len(shorter)# Obliczamy, o ile pozycji krótszy wielomian jest przesunięty względem dłuższego
    for i in range(len(shorter)):
        res[offset + i] = GF_INSTANCE.add(res[offset + i], shorter[i]) # XOR
    return res

def poly_derivative(p): # Oblicza pochodną wielomianu.
    # W ciałach GF(2^m): 
    # - Składniki o parzystych potęgach znikają (pochodna x^2 to 2x = 0).
    # - Składniki o nieparzystych potęgach stają się stałymi (pochodna x^3 to 3x^2 = x^2).
    if len(p) == 0: return [] # sprawdza czy wielomian nie jest zerowy
    res = [] # przechowuje współczynniki pochodnej
    degree = len(p) - 1 # oblicza stopień wielomianu
    for i in range(len(p) - 1): # Ostatni element to stała, znika
        power = degree - i # oblicza potęgę dla bieżącego współczynnika
        if power % 2 == 1: # jeśli potęga jest nieparzysta
            res.append(p[i])# dodaj współczynnik do pochodnej X^2k
        else:
            res.append(0) # X^2k znika w pochodnej
    return res if res else [0] # jeśli pochodna jest pusta, zwróć [0]

### 1: Obliczanie Syndromów

def calculate_syndromes(msg, nsym):# sprawdzamy pierwiastki alpha^0, alpha^1 ... alpha^31.
    synd = [0] * nsym # inicjalizacja listy syndromów o dlugosci 32
    for i in range(nsym):
        x = GF_INSTANCE.pow(ALPHA, i) # oblicza alpha^i
        synd[i] = poly_eval(msg, x) # wywołujemy schemat Hornera
    return synd # zwraca liste 32 liczb (syndromy) jezeli same 0 to dobrze  jezeli nie to BMA

### 2: Algorytm Berlekampa-Masseya

def berlekamp_massey(synd):#Znajduje wielomian lokatora błędów (Sigma).
    C = [1]  # Wielomian lokatora (Sigma)
    B = [1]  # Poprzedni lokator
    L = 0    # Aktualny stopień błędów
    m = 1    # Przesunięcie
    b = 1    # Poprzednia delta (rozbieżność)
    
    for n in range(len(synd)):
        # Oblicz rozbieżność (Delta)
        # d = S_n + sum(C_i * S_{n-i})
        d = synd[n] # zaczynamy od S_n
        for i in range(1, len(C)):
            if n - i >= 0: # upewniamy się, że indeks jest poprawny
                d = GF_INSTANCE.add(d, GF_INSTANCE.mul(C[i], synd[n - i])) #Sprawdzamy: "Czy nasz obecny wielomian C(x) (nasza reguła) poprawnie przewiduje, jaki powinien być ten syndrom ?"
        if d == 0: # brak błędu
            m += 1 #zwiększamy licznik
        else:
            # T(x) = C(x) - d * b^-1 * B(x) * x^m
            # W GF(2^8) odejmowanie to dodawanie (add)
            inv_b = GF_INSTANCE.inv(b) # b^-1
            factor = GF_INSTANCE.mul(d, inv_b) # d * b^-1
            B_scaled = poly_scale(B, factor)# Skalowanie B
            # Przesunięcie o m (dodanie zer na końcu, bo wielomiany zapisujemy [x^n ... x^0])
            #konwencję z poly_add (wyrównanie do prawej)
            #dodajemy zera na początku listy B dla operacji dodawania
            B_shifted = [0] * m + B_scaled # przesunięcie o m
            T_old_C = list(C)# Kopia starego C
            len_diff = len(B_shifted) - len(C) # # Rozszerzamy C zerami, jeśli B_shifted jest dłuższe
            if len_diff > 0:
                C += [0] * len_diff # rozszerzamy C jeśli B_shifted jest dłuższe
            
            for i in range(len(B_shifted)):# XOR element po elemencie
                C[i] = GF_INSTANCE.add(C[i], B_shifted[i])
            
            
            #jeśli jest spełniony, oznacza to, że znaleźliśmy nowy, większy błąd, który wymaga zwiększenia stopnia wielomianu C
            if 2 * L <= n:
                L = n + 1 - L
                B = T_old_C
                b = d
                m = 1
            else:
                m += 1
                
    return C # zwraca wielomian lokatora błędów Sigma(mape błędów)

### 3: Przeszukiwanie Chiena

def chien_search(sigma):#Znajduje pozycje błędów (pierwiastki Sigmy).
    error_indexes = [] # lista pozycji błędów
    for i in range(255):
        inv_X = GF_INSTANCE.pow(ALPHA, i + 1) # Szukamy miejsc zerowych dla X^-1 = alpha^(255-i)
        if poly_eval(sigma, inv_X) == 0:
            pos = 254 - i
            error_indexes.append(pos)
    return error_indexes

### 4: Algorytm Forneya

def forney(sigma_asc, synd, error_pos): #Oblicza wartości błędów.
    # 1. Oblicz Omega = (Syndromy * Sigma) mod x^2t
    # Syndromy traktujemy jako wielomian [S0, S1, ...].
    # Aby pasowało to do naszego poly_multiply (gdzie [0] to najwyższa potęga),
    # musimy uważać na kolejność. Najłatwiej zaimplementować splot ręcznie lub odwrócić listy.
    # Tutaj implementacja "na piechotę" dla pewności Omega_i:
    
    nsym = len(synd) # liczba syndromów (2t)
    omega = [] # wielomian Omega
    
    # Mnożenie Sigma * S (obcięte do nsym)
    # Sigma jest [sigma_0, sigma_1...]
    # S jest [S0, S1...]
    
    # Dla uproszczenia użyjmy poly_multiply, ale musimy odwrócić syndromy,
    # aby S_0 było przy najniższej potędze, jeśli tak interpretujemy mnożenie.
    # W standardowym zapisie S(x) = S0 + S1x + ...
    # Sigma(x) = 1 + s1x + ...
    # ręcznie, to najbezpieczniejsze:
    
    omega_coeffs = [0] * nsym # inicjalizacja współczynników Omega
    for i in range(nsym):
        term = 0 # Omega_i
        for j in range(len(sigma_asc)):
            # W BMA wygenerowaliśmy C gdzie indeksy rosną wraz z opóźnieniem.
            # Więc C[j] odpowiada x^j.
            if i - j >= 0: # upewniamy się, że indeks jest poprawny
                term = GF_INSTANCE.add(term, GF_INSTANCE.mul(sigma_asc[j], synd[i - j])) # To jest matematyczny splot: mnożenie Sigma[j] * Syndrom[i-j]
        omega_coeffs[i] = term
        
    # Omega(x) w postaci listy [w0, w1, ...]
    # Ponieważ poly_eval oczekuje [x^n ... x^0], odwróćmy listę dla poly_eval
    omega_poly = list(reversed(omega_coeffs))
    sigma_desc = list(reversed(sigma_asc)) # odwrócenie Sigmy do postaci [x^n ... x^0]
    sigma_prime = poly_derivative(sigma_desc)# 2. Pochodna Sigmy
    res = {} # Miejsce na wartości błędów {pozycja: wartość_błędu}
    for pos in error_pos:
        # X = alpha^(254-pos)  (lokator błędu)
        # X^-1 = alpha^pos     (punkt ewaluacji).
        # Jeśli błąd jest na 'pos', to odpowiada potędze alpha^(255-1-pos).
        
        # Ustalmy X^-1 spójnie z Chien Search:
        # W Chien: inv_X = alpha^(255 - (254-pos)) = alpha^(pos+1)? 
        # Nie, w Chien: inv_X = alpha^(255-i). Pos = 254-i. Czyli i = 254-pos.
        # Więc inv_X = alpha^(255 - (254-pos)) = alpha^(pos+1).
        
        # Sprawdźmy konwencję 'reedsolo' (FCR=0):
        X = GF_INSTANCE.pow(ALPHA, pos)  # X = alpha^(pos)
        X_inv = GF_INSTANCE.pow(ALPHA, 255 - pos) # Punkt ewaluacji X^-1 = alpha^-pos = alpha^(255-pos)
        numerator = poly_eval(omega_poly, X_inv) # Omega(X^-1) licznik
        denominator = poly_eval(sigma_prime, X_inv) # Sigma'(X^-1) mianownik
        
        if denominator == 0: # Zabezpieczenie, choć nie powinno wystąpić przy poprawnym bloku
             continue

         # (Dla FCR=1 byłoby samo Omega/Sigma')
        # Wzór Forneya dla FCR=0:
        frac = GF_INSTANCE.mul(numerator, GF_INSTANCE.inv(denominator)) # Y = X * (Omega(X^-1) / Sigma'(X^-1))
        Y = GF_INSTANCE.mul(X, frac) # Wartość błędu na pozycji 'pos'
        res[pos] = Y # Zapisz wartość błędu
        
    return res # zwraca słownik {pozycja: wartość_błędu}

### MAIN
def decode(received_message):# main
    # 1. PRZYGOTOWANIE I PADDING
    original_len = len(received_message) # <--- POPRAWKA: Definicja
    nsym = 2 * T # 32
    
    # Jeśli wiadomość jest już pełna (RS(255, k)), to nie ma paddingu
    if original_len == 255:
        padded_msg = list(received_message)
        padding_len = 0
    else:
        # Kod skrócony: Dopełniamy zerami do 255
        padding_len = 255 - original_len
        padded_msg = [0] * padding_len + list(received_message) # Dodajemy padding na początku
    # 2. Syndromy (Liczone na pełnym, 255-bajtowym bloku)
    synd = calculate_syndromes(padded_msg, nsym) # lista 32 syndromów
    
    if max(synd) == 0: # Jeśli syndromy to same zera, brak błędów
        return received_message[:original_len-nsym], 0 # Zwracamy oryginał (bez obcinania)
    
    # 3. BMA
    sigma_asc = berlekamp_massey(synd)
    
    # 4. Chien Search (Znajduje pozycje w zakresie 0-254)
    sigma_desc = list(reversed(sigma_asc))
    error_pos = chien_search(sigma_desc)
    
    if not error_pos: # Sprawdzenie czy znaleziono miejsca
        raise Exception("Dekoder wykrył błędy, ale nie mógł znaleźć ich lokalizacji (zbyt wiele błędów?).")
        
    # 5. Forney
    error_vals = forney(sigma_asc, synd, error_pos) 
    
    # 6. Naprawa (Na pełnym bloku z paddingiem)
    for pos in error_pos:
        # Nie musimy sprawdzać if pos < len(msg), bo Chien zwraca pos <= 254, 
        # a padded_msg ma długość 255.
        idx = 254 - pos
        padded_msg[idx] = GF_INSTANCE.add(padded_msg[idx], error_vals[pos]) # Naprawa przez XOR
    # 7. Zwracanie wyniku: Obcinamy padding i parzystość
    fixed_msg_with_parity = padded_msg[padding_len:] # Usuwamy zera paddingu
    recovered_data = fixed_msg_with_parity[:-nsym]   # Usuwamy parzystość
    
    return recovered_data, len(error_pos) # zwraca naprawioną wiadomość bez parzystości i liczbę naprawionych błędów

### TESTY na kodach ASCII


if __name__ == "__main__":
    from encoder import encode
    import random
    
    print("\n" + "="*50)
    print("   TEST ALGORYTMU REED-SOLOMON (RS(255, 223))")
    print("="*50)
    
    # 1. PRZYGOTOWANIE DANYCH
    # Możesz tu wpisać tekst do max 223 znaków
    text = "Witaj Swiecie! To jest test algorytmu Reed-Solomon. Sprawdzamy czy naprawi bledy."
    data = [ord(x) for x in text]# zamiana  na listę bajtów (ASCII)
    
    print(f"\n[1] WIADOMOŚĆ ORYGINALNA ({len(data)} bajtów):")
    print(f"    '{text}'")
    
    # 2. KODOWANIE
    # Encode zwraca listę [dane ... dane, parzystość ... parzystość]
    encoded = encode(data, G_X)
    
    # Rozdzielamy dla czytelności
    data_part = encoded[:-32]
    parity_part = encoded[-32:]
    
    print(f"\n[2] ZAKODOWANA WIADOMOŚĆ (Razem {len(encoded)} bajtów):")
    print(f"    Dane:       '{''.join([chr(x) for x in data_part])}'")
    # Wyświetlamy parzystość jako liczby HEX, bo to nie są litery
    print(f"    Parzystość: {[hex(x) for x in parity_part]}") 
    
    # 3. PSUCIE DANYCH (SYMULACJA BŁĘDÓW)
    corrupted = list(encoded)
    
    #psujemy 10 losowych bajtów (limit to 16)
    errors_count = 10
    #osujemy unikalne indeksy z całego zakresu wiadomości
    errors_indices = random.sample(range(len(encoded)), errors_count)
    
    print(f"\n[3] SYMULACJA KANAŁU (Wprowadzanie {errors_count} błędów):")
    print(f"    Uszkodzone pozycje: {sorted(errors_indices)}")
    
    for idx in errors_indices:
        corrupted[idx] ^= 0xFF # Odwracamy bity (psujemy bajt) #rozbić losowa maske błedów
        
    # Podgląd uszkodzonego tekstu (tylko część danych)
    # Znaki niedrukowalne zamieniamy na kropkę '.' żeby konsola nie zwariowała
    corrupted_str = ""
    for byte in corrupted[:-32]:
        if 32 <= byte <= 126: # Znaki drukowalne ASCII
            corrupted_str += chr(byte)
        else:
            corrupted_str += "█" # Znak uszkodzenia
            
    print(f"    Podgląd uszkodzeń:  '{corrupted_str}'")
    
    # 4. DEKODOWANIE (NAPRAWA)
    print(f"\n[4] DEKODOWANIE...")
    try:
        decoded, corrections = decode(corrupted)
        
        # Konwersja na tekst
        decoded_text = "".join([chr(x) for x in decoded])
        
        print(f"    Status: SUKCES")
        print(f"    Znaleziono i naprawiono błędów: {corrections}")
        print(f"    ODSZYFROWANA WIADOMOŚĆ:")
        print(f"    '{decoded_text}'")
        
        print("\n" + "-"*50)
        if decoded[:len(data)] == data:
            print(" >> WERYFIKACJA: ZGODNA Z ORYGINAŁEM <<")
        else:
            print(" >> WERYFIKACJA: BŁĄD (Różne dane) <<")
        print("-"*50)
            
    except Exception as e:
        print(f"    Status: BŁĄD KRYTYCZNY")
        print(f"    Opis: {e}")