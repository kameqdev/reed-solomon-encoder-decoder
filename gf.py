from tables_generator import init_exp_log_tables

class GF:
    def __init__(self, primitive_polynomial=0x11d, field_size=256):
        self.gf_exp, self.gf_log = init_exp_log_tables(primitive_polynomial, field_size)
        self.primitive_polynomial = primitive_polynomial
        self.field_size = field_size
        self.max_index = field_size - 1

    def add(self, a, b):
        return a ^ b

    def mul(self, a, b):
        if a == 0 or b == 0:
            return 0
        return self.gf_exp[self.gf_log[a] + self.gf_log[b]]

    def pow(self, a, power):
        if a == 0:
            return 0
        if power == 0:
            return 1
        return self.gf_exp[(self.gf_log[a] * power) % self.max_index]

    def inv(self, a):
        if a == 0:
            raise ZeroDivisionError(f'Cannot compute inverse of zero in GF({self.field_size})')
        return self.gf_exp[self.max_index - self.gf_log[a]]