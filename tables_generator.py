def init_exp_log_tables(primitive_polynomial=0x11d, field_size=256):
    gf_exp = [0] * (field_size * 2) # tablica potęg
    gf_log = [0] * field_size # tablica logarytmów

    x = 1
    for i in range(field_size - 1):
        gf_exp[i] = x # alpha^i = x
        gf_log[x] = i # log_alpha(x) = i
        x <<= 1 #jezeli liczba przekroczy 8 bitów
        if x & field_size:
            x ^= primitive_polynomial # redukcja modulo wielomianu
    for i in range(field_size - 1, field_size * 2 - 2):
        gf_exp[i] = gf_exp[i - (field_size - 1)]

    return gf_exp, gf_log
