# openvx-graph-parser
Tools for OpenVX C code generation from graphical calculation graph definitions.
Includes a Python based parser which takes graphs defined in graphml format and generates valid OpenVX C code.

## Prerequisites
- [yEd](https://www.yworks.com/products/yed) - A tool to graphically edit the graph definitions
- [Python2.7](https://www.python.org/download/releases/2.7/) - TODO: Update package to Python3

## Example usage as standalone test from graph file
We use `example/threshold_example.graphml` as example graph file. Please open this in yEd and see what it looks like.
This assumes you have an [OpenVX](https://www.khronos.org/openvx/) implementation installed with libraries in environment variables `$OPENVX_LIB_DIR` and headers in `$OPENVX_INCLUDE_DIR`.
Here we have used the [OpenVX 1.2 sample code](https://www.khronos.org/registry/OpenVX/sample/openvx_sample_1.2.tar.bz2).

1. First we generate the necessary stripped OpenVX graph files, note the `--strip` option:
```
python graph_parser/parse_graph.py -f example/threshold_example.graphml --strip
```
   The generator should now have created two new C-files which we can compile.
1. Inspect the generated files and move them to the example directory:
```
mv threshold_example_strip.{c,h} example/
```
1. Compile the dependency for the standalone test, here we call the compiled object file `threshold_example_graph.o`:
```
gcc -c example/threshold_example_strip.c -o example/threshold_example_graph.o -L $OPENVX_LIB_DIR -I $OPENVX_INCLUDE_DIR -lopenvx
```
1. Template code for using the generated graph code is provided at `example/standalone_test_strip_template.c`.
An already modified template can is provided at `example/standalone_test_threshold_example_strip.c`. Compile the standalone test binary into `test_threshold_example` using `threshold_example_graph.o`:
```
gcc example/threshold_example_graph.o example/standalone_test_threshold_example_strip.c -o example/test_threshold_example -L $OPENVX_LIB_DIR -I $OPENVX_INCLUDE_DIR -lopenvx
```
1. Run the created test program `test_threshold_example` using [some](https://people.sc.fsu.edu/~jburkardt/data/pgmb/pgmb.html) input images, e.g. [lena.pgm](https://people.sc.fsu.edu/~jburkardt/data/pgmb/lena.pgm) and [baboon.pgm](https://people.sc.fsu.edu/~jburkardt/data/pgmb/baboon.pgm).
Currently only [PGM images](http://netpbm.sourceforge.net/doc/pgm.html) are supported. The image ordering should correspond to the indexing defined in the graphml and provide the corresponding width and height:
```
(cd example && LD_LIBRARY_PATH=$OPENVX_LIB_DIR ./test_threshold_example ~/Downloads/lena.pgm ~/Downloads/baboon.pgm 512 512)
```
1. Inspect the created outputs.
```
ls example/*.pgm
```

## Documentation for the Python parser
Generated documentation for the Python parser is provided [here](graph_parser/doc/index.html).
### Generating new HTML documentation
1. Install [epydoc](http://epydoc.sourceforge.net/manual-install.html). (On Debian do `apt install python-epydoc`)
1. From the top graph_parser folder, run the following command:
```
epydoc --parse-only --html graph_parser -o graph_parser/doc
```
