b32 = 0xFFFFFFFF
b64 = 0xFFFFFFFFFFFFFFFF


class PRNGTable:
    def __init__(
        self,
        value1,
        value2,
    ):
        self.value1 = value1
        self.value2 = value2

    def next(self):
        value1 = self.value1
        temp = (self.value2 - value1) & b64
        self.value1 = (self.value2 * 0xD3833E804F4C574B) & b64
        self.value2 = ((temp * 0x8000000) | (temp >> 0x25)) & b64
        return value1

    def next_int(self):
        return self.next() & b32

    def next_chance(self, chance):
        return (self.next_int() * chance) >> 0x20


class PRNG:
    def __init__(
        self,
        seed,
    ):
        self.tables = []
        seed = seed ^ (seed >> 0x20)

        v1 = seed & b32
        v1 = (1 if v1 == 0 else -v1) & b64
        v1 = v1 * 0x9E6C63D0676A9A99 & b64
        v1 = (((v1 >> 0x33) ^ v1) ^ (v1 >> 0x17)) & b64
        v2 = (v1 * 0x9E6C63D0676A9A99) & b64
        seed1 = ((v2 * 0x8000000) | (v2 >> 0x25)) & b64
        seed1 = (seed1 * 0x9E6C63D0676A9A99) & b64
        seed2 = (((v2 >> 0x33) ^ v2) ^ (v2 >> 0x17)) & b64

        for _ in range(10):
            v1 = seed1 & b32
            v1 = (1 if v1 == 0 else -v1) & b64
            v1 = v1 * 0x9E6C63D0676A9A99 & b64
            v1 = (((v1 >> 0x33) ^ v1) ^ (v1 >> 0x17)) & b64
            v2 = (v1 * 0x9E6C63D0676A9A99) & b64

            prng1 = ((v2 * 0x8000000) | (v2 >> 0x25)) & b64
            prng1 = (prng1 * 0x9E6C63D0676A9A99) & b64
            prng2 = (((v2 >> 0x33) ^ v2) ^ (v2 >> 0x17)) & b64
            self.tables.insert(0, PRNGTable(prng1, prng2))

            temp = (seed2 - seed1) & b64
            seed1 = (seed2 * 0xD3833E804F4C574B) & b64
            seed2 = ((temp * 0x8000000) | (temp >> 0x25)) & b64

        self.level_gen = self.tables[0]
        self.entity_behavior = self.tables[5]

    # def level_gen(self):
    #     return self.tables[0]

    # def entity_behavior(self):
    #     return self.tables[5]


class Seed:
    def __init__(
        self,
        seed,
    ):
        seed = seed & b32
        v1 = (1 if seed == 0 else -seed) & b64
        v1 = v1 * 0x9E6C63D0676A9A99 & b64
        v1 = (((v1 >> 0x33) ^ v1) ^ (v1 >> 0x17)) & b64
        v2 = (v1 * 0x9E6C63D0676A9A99) & b64
        v3 = (((v2 >> 0x33) ^ v2) ^ (v2 >> 0x17)) & b64
        # self.iterator = (((((v1 * 0x8000000) & b64) | (v2 >> 0x25)) * 0x9E6C63D0676A9A99) & b64) | 1
        self.iterator = ((v2 * 0x8000000) | (v2 >> 0x25)) & b64
        self.iterator = (self.iterator * 0x9E6C63D0676A9A99) & b64
        self.iterator |= 1
        # self.iterator = (((((v1 * 0x8000000) & b64) | (v2 >> 0x25)) * 0x9E6C63D0676A9A99) & b64) | 1
        v4 = (v3 * 0xD3833E804F4C574B) & b64
        v3 = (1 if v4 == 0 else -v4) & b64
        v3 = (v3 * 0x9E6C63D0676A9A99) & b64
        v3 = (((v3 >> 0x33) ^ v3) ^ (v3 >> 0x17)) & b64
        v3 = (v3 * 0x9E6C63D0676A9A99) & b64
        self.generator = ((v3 * 0x8000000) | (v3 >> 0x25)) & b64
        self.generator = (self.generator * 0x9E6C63D0676A9A99) & b64
        self.initial_generator = self.generator

    def next_level_prng(self):
        self.generator = (self.generator + self.iterator) & b64
        return PRNG(self.generator)

    def current_level_prng(self):
        return PRNG(self.generator)

    def level_prng(self, level):
        return PRNG((self.generator + self.iterator * level) & b64)
