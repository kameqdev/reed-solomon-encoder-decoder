from gf import GF

P_X = 0x11D
ALPHA = 0x02
Q = 256
N = Q - 1
T = 16

GF = GF(P_X, Q)

def poly_multiply(p, g):
    res = [0] * (len(p) + len(g) - 1)
    for i, a in enumerate(p):
        if a == 0:
            continue
        for j, b in enumerate(g):
            if b == 0:
                continue
            res[i + j] = GF.add(res[i + j], GF.mul(a, b))
    return res

def generate_g(t, alpha):
    g = [1]
    
    for i in range(0, 2 * t):
        p = [1, GF.pow(alpha, i)]
        g = poly_multiply(p, g)
    return g

G_X = generate_g(T, ALPHA)

def encode(message, g):
    k = N - 2 * T
    n_k = N - k
    msg_len = len(message)
    
    if(msg_len > k):
        raise ValueError("Message length must be smaller or equal to 223 bytes")
    
    encoded_message = message + [0] * n_k
    
    for i in range(msg_len):
        coef = encoded_message[i] # pojedynczy aktualnie  przetwarzany bajt
        if coef != 0:
            for j in range(1, len(g)):
                encoded_message[i + j] = GF.add(encoded_message[i + j], GF.mul(coef, g[j])) # tworzymy nadmiar 
    
    # Przywracamy oryginalną wiadomość (nadpisujemy część z ilorazem)
    encoded_message[:msg_len] = message
    
    return encoded_message
