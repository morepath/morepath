class Converter(object):
    def __init__(self, decode, encode=None):
        self.decode = decode
        self.encode = encode or str

    def __eq__(self, other):
        return (self.decode is other.decode and
                self.encode is other.encode)

    def __ne__(self, other):
        return not self == other


IDENTITY_CONVERTER = Converter(lambda s: s, lambda s: s)
