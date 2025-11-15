def init_exp_log_tables(primitive_polynomial=0x11d, field_size=256):
    gf_exp = [0] * (field_size * 2)
    gf_log = [0] * field_size

    x = 1
    for i in range(field_size - 1):
        gf_exp[i] = x
        gf_log[x] = i
        x <<= 1
        if x & field_size:
            x ^= primitive_polynomial
    for i in range(field_size - 1, field_size * 2 - 2):
        gf_exp[i] = gf_exp[i - (field_size - 1)]

    return gf_exp, gf_log