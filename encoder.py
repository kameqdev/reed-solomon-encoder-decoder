from gf import GF
GF = GF(0x11D, 256)

P_X = 0x11D
ALPHA = 0x02
N = 255
T = 16

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
    # poprawny zakres 1-33, poniewarz wzór jest dla(x + α^1)(x + α^2)...(x + α^(32))
    # a nie dla (x + α^0)(x + α^1)...(x + α^(31))
    for i in range(1, 2 * t + 1):
        p = [1, GF.pow(alpha, i)]
        g = poly_multiply(p, g)
    return g

G_X = generate_g(T, ALPHA)

def encode(message, g):
    k = 223
    n_k = N - k
    if(len(message) > k):
        raise ValueError("Message length must be smaller or equal to 223 bytes")
    encoded_message = message + [0] * n_k
    for i in range(k):
        coef = encoded_message[i] # pojedynczy aktualnie  przetwarzany bajt
        if coef != 0:
            for j in range(1, len(g)):
                encoded_message[i + j] = GF.add(encoded_message[i + j], GF.mul(coef, g[j])) # tworzymy nadmiar 
    return encoded_message
    
    
    