from gf import GF_CALC


class Poly:
    @staticmethod
    def add(p, q): # Dodaje dwa wielomiany (XOR współczynników).
        # Ustal, który jest dłuższy, aby wynik miał odpowiednią długość
        if len(p) > len(q): # Sprawdzamy długość p
            longer, shorter = p, q # Przypisanie dłuższego i krótszego
        else: # W przeciwnym wypadku
            longer, shorter = q, p # Odwrotne przypisanie
        res = list(longer) # Kopiujemy dłuższy wielomian jako bazę wyniku
        # Dodajemy krótszy do końcówki dłuższego (wyrównanie do prawej - najniższych potęg)
        offset = len(longer) - len(shorter) # Obliczamy przesunięcie
        for i, val in enumerate(shorter): # Iterujemy przez elementy krótszego wielomianu
            res[offset + i] = GF_CALC.add(res[offset + i], val) # Wykonujemy XOR (dodawanie w GF)
        return res # Zwracamy wynik dodawania

    @staticmethod
    def multiply(p, g):
        res = [0] * (len(p) + len(g) - 1)
        for i, a in enumerate(p):
            if a == 0:
                continue
            for j, b in enumerate(g):
                if b == 0:
                    continue
                res[i + j] = GF_CALC.add(res[i + j], GF_CALC.mul(a, b))
        return res

    @staticmethod
    def div_remainder(dividend, divisor): # Dzielenie wielomianów, zwraca tylko resztę (Syndrom wielomianowy).
        # Funkcja kluczowa dla metody Mochnackiego: S(x) = R(x) mod G(x)
        msg_out = list(dividend) # Kopiujemy dzielną (wiadomość) do zmiennej roboczej
        # Normalizujemy długość pętlą dzielenia
        for i in range(len(dividend) - (len(divisor) - 1)): # Iterujemy przez stopnie swobody
            coef = msg_out[i] # Pobieramy współczynnik przy najwyższej potędze
            if coef != 0: # Jeśli współczynnik nie jest zerem, redukujemy
                for j in range(1, len(divisor)): # Pętla po współczynnikach dzielnika (G_X)
                    if divisor[j] != 0: # Optymalizacja dla zer w dzielniku
                        # msg_out[i + j] += -divisor[j] * coef (w GF odejmowanie to dodawanie)
                        val = GF_CALC.mul(divisor[j], coef) # Mnożymy współczynnik dzielnika przez wiodący
                        msg_out[i + j] = GF_CALC.add(msg_out[i + j], val) # Dodajemy (XOR) do reszty

        separator = -(len(divisor) - 1) # Obliczamy miejsce odcięcia reszty
        return msg_out[separator:] # Zwracamy samą resztę z dzielenia

    @staticmethod
    def evaluate(poly, x): # Ewaluacja wielomianu w punkcie x
        y = poly[0] # najwyższy współczynnik
        for i in range(1, len(poly)):
            y = GF_CALC.add(GF_CALC.mul(y, x), poly[i]) # y = y*x + poly[i] #https://www.algorytm.edu.pl/algorytmy-w-python/schemat-hornera-python
        return y # dla syndromów jak da 0 to brak błędów

    @staticmethod
    def scale(poly, x): # Mnoży wielomian przez skalar
        return [GF_CALC.mul(coef, x) for coef in poly]

    @staticmethod
    def derivative(poly): # Oblicza pochodną wielomianu
        # W ciałach GF(2^m):
        # - Składniki o parzystych potęgach znikają (pochodna x^2 to 2x = 0).
        # - Składniki o nieparzystych potęgach stają się stałymi (pochodna x^3 to 3x^2 = x^2).
        if len(poly) == 0: # sprawdza czy wielomian nie jest zerowy
            return []
        res = [] # przechowuje współczynniki pochodnej
        degree = len(poly) - 1 # oblicza stopień wielomianu
        for i in range(len(poly) - 1): # Ostatni element to stała, znika
            power = degree - i # oblicza potęgę dla bieżącego współczynnika
            if power % 2 == 1: # jeśli potęga jest nieparzysta
                res.append(poly[i])# dodaj współczynnik do pochodnej X^2k
            else:
                res.append(0) # X^2k znika w pochodnej
        return res if res else [0] # jeśli pochodna jest pusta, zwróć [0]
