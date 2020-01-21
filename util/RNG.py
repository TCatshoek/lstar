''' Format preserving encryption using a Feistel network

    This code is *not* suitable for cryptographic use.

    See https://en.wikipedia.org/wiki/Format-preserving_encryption
    https://en.wikipedia.org/wiki/Feistel_cipher
    http://security.stackexchange.com/questions/211/how-to-securely-hash-passwords

    A Feistel network performs an invertible transformation on its input,
    so each input number produces a unique output number. The netword operates
    on numbers of a fixed bit width, which must be even, i.e., the numbers
    a particular network operates on are in the range(4**k), and it outputs a
    permutation of that range.

    To permute a range of general size we use cycle walking. We set the
    network size to the next higher power of 4, and when we produce a number
    higher than the desired range we simply feed it back into the network,
    looping until we get a number that is in range.

    The worst case is when stop is of the form 4**k + 1, where we need 4
    steps on average to reach a valid n. In the typical case, where stop is
    roughly halfway between 2 powers of 4, we need 2 steps on average.

    Written by PM 2Ring 2016.08.22
'''

# FROM: https://stackoverflow.com/questions/51412182/iteratively-generating-a-permutation-of-natural-numbers/51419335#51419335

from random import Random

# xxhash by Yann Collet. Specialised for a 32 bit number
# See http://fastcompression.blogspot.com/2012/04/selecting-checksum-algorithm.html

def xxhash_num(n, seed):
    n = (374761397 + seed + n * 3266489917) & 0xffffffff
    n = ((n << 17 | n >> 15) * 668265263) & 0xffffffff
    n ^= n >> 15
    n = (n * 2246822519) & 0xffffffff
    n ^= n >> 13
    n = (n * 3266489917) & 0xffffffff
    return n ^ (n >> 16)

class FormatPreserving:
    """ Invertible permutation of integers in range(stop), 0 < stop <= 2**64
        using a simple Feistel network. NOT suitable for cryptographic purposes.
    """
    def __init__(self, stop, keystring):
        if not 0 < stop <= 1 << 64:
            raise ValueError('stop must be <=', 1 << 64)

        # The highest number in the range
        self.maxn = stop - 1

        # Get the number of bits in each part by rounding
        # the bit length up to the nearest even number
        self.shiftbits = -(-self.maxn.bit_length() // 2)
        self.lowmask = (1 << self.shiftbits) - 1
        self.lowshift = 32 - self.shiftbits

        # Make 4 32 bit round keys from the keystring.
        # Create an independent random stream so we
        # don't intefere with the default stream.
        stream = Random()
        stream.seed(keystring)
        self.keys = [stream.getrandbits(32) for _ in range(4)]
        self.ikeys = self.keys[::-1]

    def feistel(self, n, keys):
        # Split the bits of n into 2 parts & perform the Feistel
        # transformation on them.
        left, right = n >> self.shiftbits, n & self.lowmask
        for key in keys:
            left, right = right, left ^ (xxhash_num(right, key) >> self.lowshift)
            #left, right = right, left ^ (hash((right, key)) >> self.lowshift) 
        return (right << self.shiftbits) | left

    def fpe(self, n, reverse=False):
        keys = self.ikeys if reverse else self.keys
        while True:
            # Cycle walk, if necessary, to ensure n is in range.
            n = self.feistel(n, keys)
            if n <= self.maxn:
                return n

