#!/usr/bin/env python2.7
#
# LDPC Encoder based on C code from Bill Cowley in March 2016
# Author: Mark Jessop <vk5qi@rfhead.net>
#
import numpy as np

#
# ORIGINAL C CODE FOLLOWS
#

# #define Nibits 2064
# #define Npbits 516
# #define Nwt     12


# unsigned short hrows[] = { 
# // read from file created via make_Hrows_txt.m
# // use the new code of March 2016 
# #include "Hrow2064.txt"
# };

# unsigned char  ibits[Nibits];    // info array 
# unsigned char  pbits[Npbits];    // parity array 

# void encode()   {
#   unsigned int   p, i, tmp, par, prev=0;
#   char c;  
#   for (p=0; p<Npbits; p++)   {
#     par =0; 
#     for (i=0; i<Nwt; i++)  
#       par = par + ibits[hrows[p*Nwt+i]-1];
#       // -1 as matlab arrays start from 1, C from 0
#     tmp = par + prev;
#     // printf(" p ind %d, parity  %d  \n", p, tmp);  
#     //c = getchar();  
#     tmp &= 1;    // only retain the lsb 
#     prev = tmp; 
#     pbits[p] =tmp; 
#   }
# }


# Load Parity table upon load of this library.
hrows_2064 = np.loadtxt("ldpc_2064.txt",delimiter=',',comments='#').astype(np.int)


# Direct port of encode() above.
# Takes an input array of 0s and 1s.
# Should look at vectorising this somehow.
#@profile
def ldpc_encode(ibits,Nibits=2064,Npbits=516,Nwt=12,hrows=hrows_2064):
    prev = 0
    pbits = np.zeros(Npbits)

    for p in xrange(Npbits):
        #par = 0
        #for i in xrange(Nwt):
        #    par = par + ibits[hrows[p*Nwt+i]-1]
        par = int(np.sum(ibits[hrows[(p*Nwt+np.arange(Nwt))]-1])) # Some vectorisation of the above.

        tmp = (par + prev)&1
        prev = tmp
        pbits[p] = tmp

    return pbits

# Wrapper function for the above, allowing LDPC coding of a 258 byte long string.
def ldpc_encode_string(payload,Nibits=2064,Npbits=516,Nwt=12,hrows=hrows_2064):
    if len(payload) != 258:
        raise TypeError("Payload MUST be 258 bytes in length! (2064 bit codeword)")

    # Convert to bits.
    raw_data = np.array([],dtype=np.uint8)
    ibits = np.unpackbits(np.fromstring(payload,dtype=np.uint8))

    parity = ldpc_encode(ibits,Nibits,Npbits,Nwt,hrows)

    return np.packbits(parity.astype(np.uint8)).tostring()


#
#   Testing Stuff
#

def generate_dummy_packet():
    payload = np.arange(0,256,1)
    payload = np.append(payload,[0,0]).astype(np.uint8).tostring() # Add on dummy checksum, for a total of 258 bytes.
    return payload

#@profile
def main():
    # Generate a dummy test packet, and convert it to an array of 0 and 1.
    payload = generate_dummy_packet()

    print("Input (hex): %s" % ("".join("{:02x}".format(ord(c)) for c in payload)))

    # Now run ldpc_encode over it X times.
    parity = ""
    for x in xrange(100):
        parity = ldpc_encode_string(payload)

    print("LDPC Parity Bits (hex): %s" % ("".join("{:02x}".format(ord(c)) for c in parity)))
    print("Done!")

# Some basic test code.
if __name__ == "__main__":
    main()