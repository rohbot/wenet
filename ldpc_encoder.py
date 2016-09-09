#!/usr/bin/env python
#
#   LDPC Encoder Functions.
#   Uses ctypes to call the encode function from ldpc_enc.c
#
#   ldpc_enc.c needs to be compiled to a .so before this will work, with:
#   gcc -fPIC -shared -o ldpc_enc.so ldpc_enc.c
#
#   Mark Jessop <vk5qi@rfhead.net>
#

import ctypes
from numpy.ctypeslib import ndpointer
import numpy as np
import time


# Attempt to load in ldpc_enc.so on startup.
try:
    _ldpc_enc = ctypes.CDLL("./ldpc_enc.so")
    _ldpc_enc.encode.restype = None
    _ldpc_enc.encode.argtypes = (ndpointer(ctypes.c_ubyte, flags="C_CONTIGUOUS"), ndpointer(ctypes.c_ubyte, flags="C_CONTIGUOUS"))
except OSError as e:
    raise OSError("Could not find ldpc_enc.so! Have you compiled ldpc_enc.c?")

#
#   LDPC Encoder.
#   Accepts a 258 byte string as input, returns the LDPC parity bits.
#

def ldpc_encode_string(payload, Nibits = 2064, Npbits = 516):
    if len(payload) != 258:
        raise TypeError("Payload MUST be 258 bytes in length! (2064 bit codeword)")

    # Get input data into the right form (list of 0s and 1s)
    ibits = np.unpackbits(np.fromstring(payload,dtype=np.uint8)).astype(np.uint8)
    pbits = np.zeros(Npbits).astype(np.uint8)

    _ldpc_enc.encode(ibits, pbits)

    return np.packbits(np.array(list(pbits)).astype(np.uint8)).tostring()


# Some testing functions, to time encoding performance.

def generate_dummy_packet():
    payload = np.arange(0,256,1)
    payload = np.append(payload,[0,0]).astype(np.uint8).tostring() # Add on dummy checksum, for a total of 258 bytes.
    return payload

def main():
    # Generate a dummy test packet, and convert it to an array of 0 and 1.
    payload = generate_dummy_packet()

    print("Input (hex): %s" % ("".join("{:02x}".format(ord(c)) for c in payload)))

    # Now run ldpc_encode over it X times.
    parity = ""
    start = time.time()
    for x in xrange(1000):
        #print(x)
        parity = ldpc_encode(payload)

    stop = time.time()
    print("time delta: %.3f" % (stop-start))

    print("LDPC Parity Bits (hex): %s" % ("".join("{:02x}".format(ord(c)) for c in parity)))
    print("Done!")

# Some basic test code.
if __name__ == "__main__":
    main()
