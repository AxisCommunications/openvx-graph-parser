"""A Python module for handling parsing of a single OpenVX node.

Adding new node types
=====================

To add support for a new OpenVX function node type to the graph parser, follow these steps:

  1. Look up the name of the calculation node in the OpenVX standard.
     Strip the name from "vx" and "Node". The remaining part is the name
     to be used by the graph parser.\n
     E.g. if the node is named: "vxMyNodeNameNode",
     the graph parser should use the name "MyNodeName".
  2. In the file function_node_library.py, add a new entry for the new node
     in the different dictionaries as follows:

       - B{Dictionary for the constructor name:}
           - NODE_DICTIONARY:                     'MyNodeName' : MyNodeName()

       - B{Dictionaries for I/O image indices:}\n
         Look up the parameter index of the first input and the first output images in the OpenVX API
         Note that the first parameter (the graph object) is not counted,
         and indexing starts from 0.
           - FIRST_INPUT_IMAGE_INDEX_DICT         'MyNodeName' :    0
           - FIRST_OUTPUT_IMAGE_INDEX_DICT        'MyNodeName':    1

       - B{Dictionary for non-image parameters and indices:}\n
         Add an entry for each of the non-image parameters in the node API,
         and add the corresponding parameter indices in the respective dictionaries:
           - PARAMETER_NAMES_DICT                 'MyNodeName':    ["vx_convert_policy_e", "vx_scalar"],
           - PARAMETER_INDICES_DICT               'MyNodeName':    [2, 3]

       - B{Dictionary for I/O image formats:}\n
         Add the allowed input and output image formats as lists of format lists in the respective dictionaries.
         Note that the inputs ans outputs are coupled. So an input list of image formats should
         correspond in index position to the related output list of image formats.
         The Or node is given as an example here:
           - VALID_INPUT_IMAGE_FORMATS            'Or' :[['U8','U8'],['U8','U8']]
           - VALID_OUTPUT_IMAGE_FORMATS           'Or' :[['U8'],['VIRT->U8']]
         If no format is specified in the yEd graph, the image is treated as a virtual image.
         When the parser checks the image formats, it will then look for a match in the valid formats arrays
         containing an entry beginning with I{VIRT} and will generate code with the image having the format
         given after the arrow (i.e. here U8). Other nodes, taking this image as input will then treat the input
         as U8. Thus, the parser never sees virtual input images, only virtual output images.
         See further details about this formatting in function_node_library.py.
  3. Add a class object for the new node. For an example of a simple node, see e.g. the file or_node.py.
     The class object inherits from a base class providing common functionality for all nodes,
     such as parsing for image parameters.The new class node must contain an __init__ function and a parse function.
     The latter is used by the graphml_parser to generate the code for a node creation function
     according to the OpenVX API.
"""
#This file also serves as a hook for package-initialization-time actions