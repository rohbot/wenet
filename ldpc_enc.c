/*

LDPC Encoder, using a 'RA' encoder written by Bill Cowley VK5DSP in March 2016.

Compile with:
gcc -fPIC -shared -o ldpc_enc.so ldpc_enc.c


*/

#include<stdio.h>
#include<string.h>
#include<stdlib.h>

/*

  LDPC Encoder Functions

*/

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


/*

  Diagonal Interleaver Functions

  From fldigi
  Copyright (C) 2006
  Dave Freese, W1HKJ

*/

#define INTERLEAVE_FWD  0
#define INTERLEAVE_REV  1
#define PUNCTURE        0

#define INTERLEAVER_SIZE 256
#define INTERLEAVER_DEPTH 10

int len, interleaver_direction = 0;
unsigned char interleaver_table[INTERLEAVER_SIZE*INTERLEAVER_SIZE*INTERLEAVER_DEPTH];

// Helper function for accessing interleaver table.
unsigned char *tab(int i, int j, int k) {
  return &interleaver_table[(INTERLEAVER_SIZE * INTERLEAVER_SIZE * i) + (INTERLEAVER_SIZE * j) + k];
}

void interleaver_flush(void)
{
// Fill entire RX interleaver with punctures or 0 depending on whether
// Rx or Tx
  if (interleaver_direction == INTERLEAVE_REV)
    memset(interleaver_table, 0, len);
  else
    memset(interleaver_table, PUNCTURE, len);
}

void interleave_symbols(unsigned char *psyms)
{
  int i, j, k;

  for (k = 0; k < INTERLEAVER_DEPTH; k++) {
    for (i = 0; i < INTERLEAVER_SIZE; i++)
      for (j = 0; j < INTERLEAVER_SIZE - 1; j++)
        *tab(k, i, j) = *tab(k, i, j + 1);

    for (i = 0; i < INTERLEAVER_SIZE; i++)
      *tab(k, i, INTERLEAVER_SIZE - 1) = psyms[i];

    for (i = 0; i < INTERLEAVER_SIZE; i++) {
      if (interleaver_direction == INTERLEAVE_FWD)
        psyms[i] = *tab(k, i, INTERLEAVER_SIZE - i - 1);
      else
        psyms[i] = *tab(k, i, i);
    }
  }
}

void init_interleaver(int direction){
  len = INTERLEAVER_SIZE*INTERLEAVER_SIZE*INTERLEAVER_DEPTH;
  interleaver_direction = direction;
  interleaver_flush();
}