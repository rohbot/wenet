# Build fsk_demod and drs232_ldpc

CC=gcc
CFLAGS= -O3 -Wall

all: fsk_demod drs232_ldpc

fsk_demod: fsk_demod.o fsk.o kiss_fft.o
	gcc  -lm -o fsk_demod fsk_demod.o fsk.o kiss_fft.o

drs232_ldpc: drs232_ldpc.o mpdecode_core.o phi0.o
	gcc -lm -o drs232_ldpc drs232_ldpc.o mpdecode_core.o phi0.o

.c.o:	$(CC)  $(CFLAGS) -c $< -o $@

clean:
	rm -f fsk_demod drs232_ldpc *.o 
