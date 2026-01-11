# Konfiguracja parametrów kodu Reeda-Solomona

P_X = 0x11D     # Wielomian pierwotny (Primitive Polynomial) dla GF(256)
ALPHA = 0x02    # Generator (element prymitywny)
Q = 256         # Rozmiar ciała (2^8)
T = 16          # Liczba symboli korekcyjnych (zdolność naprawy T błędów), 2*T to liczba bajtów nadmiarowych

# N - Długość bloku (maksymalna) w ciele GF(Q)
# Dla standardowego RS w GF(256) wynosi 255 (Q-1)
N = Q - 1
