from gf import GF_CALC # Używamy tej samej instancji co koder
from encoder import G_X
from config import ALPHA, T
from poly import Poly

### 1: Obliczanie Syndromów

def calculate_syndromes(msg, nsym):# sprawdzamy pierwiastki alpha^0, alpha^1 ... alpha^31.
    synd = [0] * nsym # inicjalizacja listy syndromów o dlugosci 32
    for i in range(nsym):
        x = GF_CALC.pow(ALPHA, i) # oblicza alpha^i
        synd[i] = Poly.evaluate(msg, x) # wywołujemy schemat Hornera
    return synd # zwraca liste 32 liczb (syndromy) jezeli same 0 to dobrze  jezeli nie to BMA

### 2: Algorytm Berlekampa-Masseya

def berlekamp_massey(syndromes):#Znajduje wielomian lokatora błędów (Sigma).
    sigma = [1]  # Wielomian lokatora (Sigma)
    prev_sigma = [1]  # Poprzedni lokator
    sigma_degree = 0    # Aktualny stopień wielomianu lokatora
    shift = 1    # Przesunięcie
    prev_delta = 1    # Poprzednia delta (rozbieżność)

    for n, synd_val in enumerate(syndromes):
        # Oblicz rozbieżność (Delta)
        # delta = S_n + sum(sigma_i * S_{n-i})
        delta = synd_val # zaczynamy od S_n
        for i, val in enumerate(sigma[1:], start=1): # pomijamy sigma[0] bo to zawsze 1
            if n - i >= 0: # upewniamy się, że indeks jest poprawny
                delta = GF_CALC.add(delta, GF_CALC.mul(val, syndromes[n - i])) #Sprawdzamy: "Czy nasz obecny wielomian sigma(x) (nasza reguła) poprawnie przewiduje, jaki powinien być ten syndrom ?"
        if delta == 0: # brak błędu
            shift += 1 #zwiększamy licznik
        else:
            # T(x) = sigma(x) - delta * prev_delta^-1 * prev_sigma(x) * x^shift
            # W GF(2^8) odejmowanie to dodawanie (add)
            inv_prev_delta = GF_CALC.inv(prev_delta) # prev_delta^-1
            factor = GF_CALC.mul(delta, inv_prev_delta) # delta * prev_delta^-1
            prev_sigma_scaled = Poly.scale(prev_sigma, factor)# Skalowanie prev_sigma
            # Przesunięcie o shift (dodanie zer na końcu, bo wielomiany zapisujemy [x^n ... x^0])
            #konwencję z poly_add (wyrównanie do prawej)
            #dodajemy zera na początku listy prev_sigma dla operacji dodawania
            prev_sigma_shifted = [0] * shift + prev_sigma_scaled # przesunięcie o shift
            t_old_sigma = list(sigma)# Kopia starego sigma
            len_diff = len(prev_sigma_shifted) - len(sigma) # # Rozszerzamy sigma zerami, jeśli prev_sigma_shifted jest dłuższe
            if len_diff > 0:
                sigma += [0] * len_diff # rozszerzamy sigma jeśli prev_sigma_shifted jest dłuższe

            for i, val in enumerate(prev_sigma_shifted):# XOR element po elemencie
                sigma[i] = GF_CALC.add(sigma[i], val)


            #jeśli jest spełniony, oznacza to, że znaleźliśmy nowy, większy błąd, który wymaga zwiększenia stopnia wielomianu sigma
            if 2 * sigma_degree <= n:
                sigma_degree = n + 1 - sigma_degree
                prev_sigma = t_old_sigma
                prev_delta = delta
                shift = 1
            else:
                shift += 1

    return sigma # zwraca wielomian lokatora błędów Sigma(mape błędów)

### 3: Przeszukiwanie Chiena

def chien_search(sigma):#Znajduje pozycje błędów (pierwiastki Sigmy).
    error_indexes = [] # lista pozycji błędów
    for i in range(255):
        inv_x = GF_CALC.pow(ALPHA, i + 1) # Szukamy miejsc zerowych dla X^-1 = alpha^(255-i)
        if Poly.evaluate(sigma, inv_x) == 0:
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
        for j, sigma_coef in enumerate(sigma_asc):
            # W BMA wygenerowaliśmy C gdzie indeksy rosną wraz z opóźnieniem.
            # Więc C[j] odpowiada x^j.
            if i - j >= 0: # upewniamy się, że indeks jest poprawny
                term = GF_CALC.add(term, GF_CALC.mul(sigma_coef, synd[i - j])) # To jest matematyczny splot: mnożenie Sigma[j] * Syndrom[i-j]
        omega_coeffs[i] = term

    # Omega(x) w postaci listy [w0, w1, ...]
    # Ponieważ poly_eval oczekuje [x^n ... x^0], odwróćmy listę dla poly_eval
    omega_poly = list(reversed(omega_coeffs))
    sigma_desc = list(reversed(sigma_asc)) # odwrócenie Sigmy do postaci [x^n ... x^0]
    sigma_prime = Poly.derivative(sigma_desc)# 2. Pochodna Sigmy
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
        x = GF_CALC.pow(ALPHA, pos)  # X = alpha^(pos)
        x_inv = GF_CALC.pow(ALPHA, 255 - pos) # Punkt ewaluacji X^-1 = alpha^-pos = alpha^(255-pos)
        numerator = Poly.evaluate(omega_poly, x_inv) # Omega(X^-1) licznik
        denominator = Poly.evaluate(sigma_prime, x_inv) # Sigma'(X^-1) mianownik

        if denominator == 0: # Zabezpieczenie, choć nie powinno wystąpić przy poprawnym bloku
            continue

         # (Dla FCR=1 byłoby samo Omega/Sigma')
        # Wzór Forneya dla FCR=0:
        frac = GF_CALC.mul(numerator, GF_CALC.inv(denominator)) # Y = X * (Omega(X^-1) / Sigma'(X^-1))
        y = GF_CALC.mul(x, frac) # Wartość błędu na pozycji 'pos'
        res[pos] = y # Zapisz wartość błędu

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
        padded_msg[idx] = GF_CALC.add(padded_msg[idx], error_vals[pos]) # Naprawa przez XOR

    # --- ZABEZPIECZENIE (DODANE) ---
    # Obliczamy syndromy ponownie dla wiadomości PO naprawie.
    # Jeśli nadal nie są zerami, to znaczy, że naprawa się nie udała (np. za dużo błędów).
    check_synd = calculate_syndromes(padded_msg, nsym)
    if max(check_synd) != 0:
        raise Exception("Weryfikacja nieudana! Wiadomość po naprawie nadal zawiera błędy (przekroczono zdolność korekcyjną).")
    # -------------------------------

    # 7. Zwracanie wyniku: Obcinamy padding i parzystość
    fixed_msg_with_parity = padded_msg[padding_len:] # Usuwamy zera paddingu
    recovered_data = fixed_msg_with_parity[:-nsym]   # Usuwamy parzystość

    return recovered_data, len(error_pos) # zwraca naprawioną wiadomość bez parzystości i liczbę naprawionych błędów