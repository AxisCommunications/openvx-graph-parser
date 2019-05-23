# Embedded Vision Summit 2019 workshop

1. Parse the provided graphs to create the necessary files:

       python graph_parser/parse_graph.py -f workshop/diffdemo1.graphml --strip -ev --output_dir=workshop
       python graph_parser/parse_graph.py -f workshop/diffdemo2.graphml --strip -ev --output_dir=workshop
1. Modify the provided `Makefile` to point to your OpenVX installation directory
1. Compile the demo programs

       make -C workshop diffdemo1 diffdemo2
1. Run the first example with some input images

       (cd workshop && LD_LIBRARY_PATH=$OPENVX_LIB_DIR ./diffdemo1 /path/to/input0.pgm /path/to/input1.pgm 256 256)
1. Run the second example with some input images

       (cd workshop && LD_LIBRARY_PATH=$OPENVX_LIB_DIR ./diffdemo2 /path/to/input0.pgm /path/to/input1.pgm 256 256)
