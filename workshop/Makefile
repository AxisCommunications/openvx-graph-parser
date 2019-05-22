# FIXME: Specify your openvx installation directory
OPENVX_INSTALL_DIR = /path/to/openvx
OPENVX_LIB_DIR = $(OPENVX_INSTALL_DIR)/bin
OPENVX_INC_DIR = $(OPENVX_INSTALL_DIR)/include

LIBS=-lopenvx
CC=gcc
CFLAGS=-I$(OPENVX_INC_DIR) -L$(OPENVX_LIB_DIR)

.PHONY: diffdemo1
diffdemo1: diffdemo1_strip.o standalone_diffdemo1_strip.o
	$(CC) -o diffdemo1 diffdemo1_strip.o standalone_diffdemo1_strip.o $(CFLAGS) $(LIBS)

.PHONY: diffdemo2
diffdemo2: diffdemo2_strip.o standalone_diffdemo2_strip.o
	$(CC) -o diffdemo2 diffdemo2_strip.o standalone_diffdemo2_strip.o $(CFLAGS) $(LIBS)

.PHONY: all
all: diffdemo1 diffdemo2

.PHONY: clean
clean:
	$(RM) diffdemo1 diffdemo1_strip.o standalone_diffdemo1_strip.o diffdemo2 diffdemo2_strip.o standalone_diffdemo2_strip.o
