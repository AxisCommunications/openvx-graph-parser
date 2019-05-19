#!/usr/bin/env python

"""OpenVX Graph Code Generator

Submodules used by parse_graph script
-------------------------------------
The parsing framework uses several files for the generic parsing
to build up global lists of node dependencies etc.
For the specific parsing of the individual function nodes,
parser files are located in the folder node_parse_info

The parsing framework makes use of a GraphParser class instance,
which is defined in the file graphml_parser.py.
The GraphParser creates a set of global lists of id's for nodes of different fundamental types,
for instance input image nodes, or function nodes connected to an output node.
It also handles the graph logic needed to be able to autogenerate the OpenVX compliant C-code.

The GraphParser also makes use of the class NodeInfo (defined in graphml_parser.py), which stores
information about edges connected to a particular node,
their edge labels and the neighboring nodes connected by these edges.

A diagram of how the individual function node parameters are accessed and parsed from this top script can be seen
in the call diagram below. Note that only ``graph_create_function.parse`` calls the individual node functions even
though the scripts calls functions from several other submodules in the ``code_generation`` subpackage.

.. figure:: ../graph_parser/parse_graph_call_diagram.png

   Call sequence diagram schematic

The script calls in turn the following submodules:

  1. ``graph_headerfile.py``: Generates a C-header file for the graph.
  2. ``graph_sourcefile_beginning.py``: Generates the beginning of the source file and the graph registration function.
  3. ``graph_create_function.py``: Generates the function that creates the graph skeleton (the graph without input and output images).
     It also calls all the necessary node implementation files in the package ``node_parse_info``.
  4. ``graph_set_io_function.py``: Generates the function used to set new input and output images between each graph processing.
"""
# We use a different documentation format from the other modules here to enable
# adding the image of call sequence (requires docutils-common package or similar)
__docformat__ = "restructuredtext en"
import os.path
import subprocess
import argparse
import logging

# Shared common functionality
from graphml_parser import graphml_parser
from node_parse_info import function_node_library

# Code generating modules for the separate parts of the h- and c-files
from code_generation import graph_headerfile
from code_generation import graph_sourcefile_beginning
from code_generation import graph_create_function
from code_generation import graph_set_io_images_function
from code_generation import graph_set_debug_images_function

def argparse_setup():
    """ Function to set up the argParse object with argument options."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest='filename',
                        help="read graph from FILENAME",
                        required=True)
    parser.add_argument('-v', '--verbose',
                        action='store_true', dest='verbose',
                        help="verbose mode")
    parser.add_argument('-e', '--error',
                        action='store_true', dest='error_graph',
                        help="create an error/validation graphml-file to visualize the success of parsing the graph")
    parser.add_argument('-d', '--debug',
                        action='store_true', dest='debug_mode',
                        help="debug mode, VERY verbose")
    parser.add_argument('-S', '--strip',
                        action='store_true', dest='strip_mode',
                        help="generate OpenVX code stripped from graphmanager usage and other dependencies")
    parser.add_argument('-I', '--strip_io',
                        action='store_true', dest='strip_io',
                        help="also generate stripped code for setting I/O images. Only valid if -S/--strip is also given")
    parser.add_argument('-V', '--openvx-version', dest='vx_version',
                        help="generate OpenVX code for OpenVX version VERSION, default is {}".format(graphml_parser.VX_VERSION_DEFAULT),
                        default=graphml_parser.VX_VERSION_DEFAULT)
    parser.add_argument('-O', '--output_dir', dest='output_dir',
                        help="specify output directory for generated files")

    return parser.parse_args()

def generate_source_code(graphparser, dry_run = False):
    generated_source_code_h = ""
    generated_source_code_c = ""

    if dry_run:
        graph_headerfile.parse(graphparser)
        graph_sourcefile_beginning.parse(graphparser)
        graph_create_function.parse(graphparser, dry_run)
        graph_set_io_images_function.parse(graphparser)
        graph_set_debug_images_function.parse(graphparser)
    else:
        generated_source_code_h +=  graph_headerfile.parse(graphparser)
        generated_source_code_c += graph_sourcefile_beginning.parse(graphparser)
        generated_source_code_c += graph_create_function.parse(graphparser, dry_run)
        generated_source_code_c += graph_set_io_images_function.parse(graphparser)
        generated_source_code_c += graph_set_debug_images_function.parse(graphparser)

    return [generated_source_code_h, generated_source_code_c]

def main():
    """ The main function invoked to run the parser."""

    args = argparse_setup()

    # Initialize the GraphParser.
    graphparser = graphml_parser.GraphParser(args.verbose, args.debug_mode, args.strip_mode, args.strip_io, args.vx_version)

    # File paths for reading and writing to generated c-files
    # and validation/error visualization graph
    file_name, file_extension = os.path.splitext(args.filename)
    graphname = os.path.basename(file_name)
    output_dir = os.path.curdir
    if args.output_dir:
        output_dir = args.output_dir
    graphname = os.path.join(output_dir, graphname)
    c_output_filename = graphname + ".c"
    h_output_filename = graphname + ".h"
    graph_filename_validation = graphname + "_VALIDATION.graphml"

    if graphparser.strip_mode:
        print "NOTE: Strip mode is on! (with IO=" + str(graphparser.strip_io) + ")"
        print "      Generating OpenVX code without other dependencies!"
        if graphparser.strip_io:
            c_output_filename = graphname + "_strip_io.c"
            h_output_filename = graphname + "_strip_io.h"
            graph_filename_validation = graphname + "_strip_io_VALIDATION.graphml"
        else:
            c_output_filename = graphname + "_strip.c"
            h_output_filename = graphname + "_strip.h"
            graph_filename_validation = graphname + "_strip_VALIDATION.graphml"

    if graphparser.debug_mode:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        print "Debug mode on (lots of debug info) \n"

    # Print Console info
    if graphparser.verbose:
        print "*************************************************************"
        print "******** OpenVX Graph Initialization Code Generator *********"
        print "*************************************************************"
        print "Verbose mode on\n"
        print "Generating graph setup code from file: " + args.filename
        print "Writing output to files: " + c_output_filename, h_output_filename
        print "Generated code is compatible with OpenVX version " + graphparser.vx_version
        print str(args) + "\n"

    graphparser.set_function_node_library(function_node_library.Library(vx_version=graphparser.vx_version))
    graphparser.load_graph(args.filename)

    # Open output files
    c_output_file = open(c_output_filename, "w")
    h_output_file = open(h_output_filename, "w")

    # Dry-run is done to ensure that there are no errors when the image format check is done
    # The image format check is done before the actual code-generation
    # which is done on the second parse without dry_run,
    # in particular this is needed for the debug node mode,
    # since it will use the generated explicit image formats
    dry_run = True
    generate_source_code(graphparser, dry_run)

    if not graphparser.graph_has_errors:
        # Run format checker on image nodes only if function nodes have passed their checks
        graphparser.graph_has_errors |= graphparser.verify_graph_image_formats()

    if not graphparser.graph_has_errors:
        # Generate C code files for graph registration
        [source_h, source_c] = generate_source_code(graphparser)
        h_output_file.write(source_h)
        c_output_file.write(source_c)
    else:
        h_output_file.write("AUTOGENERATION CONTAINS ERRORS!!!!")
        c_output_file.write("AUTOGENERATION CONTAINS ERRORS!!!!")

    c_output_file.close()
    h_output_file.close()

    if graphparser.verbose:
        if graphparser.graph_has_errors:
            print "GraphParser verification: FAILURE"
        else:
            print "GraphParser verification: SUCCESS"

    if args.error_graph:
        # Write validation/error graph for visualizing result of parsing
        validation_file = open(graph_filename_validation, "w")
        graphparser.validation_output_graph.writexml(validation_file)
        validation_file.close()
        if graphparser.verbose:
            print "Created verification graph: " + validation_file

if __name__ == "__main__":
    main()
