from gf import GF_CALC
from poly import Poly
from config import ALPHA, N, T


def generate_g(t, alpha):
    g = [1]

    for i in range(0, 2 * t):
        p = [1, GF_CALC.pow(alpha, i)]
        g = Poly.multiply(p, g)
    return g

G_X = generate_g(T, ALPHA)

def encode(message, g):
    k = N - 2 * T
    n_k = N - k
    msg_len = len(message)

    if msg_len > k:
        raise ValueError("Message length must be smaller or equal to 223 bytes")

    encoded_message = message + [0] * n_k

    for i in range(msg_len):
        coef = encoded_message[i] # pojedynczy aktualnie  przetwarzany bajt
        if coef != 0:
            for j in range(1, len(g)):
                encoded_message[i + j] = GF_CALC.add(encoded_message[i + j], GF_CALC.mul(coef, g[j])) # tworzymy nadmiar

    # Przywracamy oryginalną wiadomość (nadpisujemy część z ilorazem)
    encoded_message[:msg_len] = message

    return encoded_message
