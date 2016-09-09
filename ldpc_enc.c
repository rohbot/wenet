/*

LDPC Encoder, using a 'RA' encoder written by Bill Cowley VK5DSP in March 2016.

Compile with:
gcc -fPIC -shared -o ldpc_enc.so ldpc_enc.c


*/

#include<stdio.h>
#include<stdlib.h>
#define Nibits 2064
#define Npbits 516
#define Nwt     12


unsigned short hrows[] = { 
// read from file created via make_Hrows_txt.m
// use the new code of March 2016 
#include "Hrow2064.txt"
};


void encode(unsigned char *ibits, unsigned char *pbits)   {
  unsigned int   p, i, tmp, par, prev=0;
  char c;  
  for (p=0; p<Npbits; p++)   {
    par =0; 
    for (i=0; i<Nwt; i++)  
      par = par + ibits[hrows[p*Nwt+i]-1];
      // -1 as matlab arrays start from 1, C from 0
    tmp = par + prev;
    //printf(" p ind %d, parity  %d  \n", p, tmp);  
    //c = getchar();  
    tmp &= 1;    // only retain the lsb 
    prev = tmp; 
    pbits[p] =tmp; 
  }
}
