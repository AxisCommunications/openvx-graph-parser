"""Graph parser package for parsing OpenVX graphs saved in the yEd graphml format

Introduction
============

The yEd graph is expected to contain parser-specific node data for how to set up the
autogenerated OpenVX C-code that handles creating graph skeletons and switching I/O images.

In order for the parser to understand how to generate the graph source code correctly,
a few instructions need to be followed.

Where to add metadata information to nodes
------------------------------------------

To add parameters or other information to any nodes (function nodes and image nodes),
right click on the node, and select "Properties". Select the "Data" tab and enter the
needed data in the "Description" field. All additional information needed to process
nodes is added here except if settings that are global for the whole graph.
(see the UserData object for this exception).

Parameter information in the Data field is given within square brackets,
first specifying the type of information given (nodetype, vx_df_image_e etc.), and after space separation,
giving the value of that parameter (e.g. input_image[3] or VX_DF_IMAGE_U8, DYNAMIC etc.).

Note that if parameters have been added to the Data field of a node,
one can see them as a popup if one hovers with the mouse pointer
over that node in the yEd editor. If no parameters have been added,
the popup only displays the name of the node.

Adding a function node to the graph
-----------------------------------

  1. Function nodes should be flowchart objects of type "Start1" or "Start2"
     (choose the one that fits the diagram best visually)
  2. The function nodes should be named after the OpenVX function they represent,
     but omitting the "vx" and the "Node" part of the node name. E.g. for the function
     node named  "vxHalfScaleGaussianNode" in the standard, one should name the function
     node "HalfScaleGaussianNode". The name is added to the text field of the node.
     The reason to omit the "vx" and "Node" parts is to make names in the graph shorter and easier to read.
  3. We also need to add (to the "Data" tab) any needed parameters as specified in the OpenVX standard.
     They are added with square brackets in the same way as for image nodes.
     For instance, for vxHalfScaleGaussion the OpenVX standard requires the parameter "vx_int32 kernel_size".
     We follow that notation and add the information in the Data field of the function node:
     [vx_int32 5], for a kernel size of 5 pixels.
  4. By writing a I{dynamic_type} followed by a type name within square brackets,
     (e.g. [dynamic_type vx_int32[index]]) the python parser interprets I{dynamic_type} as a directive to the parser
     to treat the named type as a dynamic parameter whose value can be changed between graph executions.
     Indexing should start from 0 and have no "gaps".
     One can still provide an initial value directly in the graph data tab however.
     The parameter is changed at runtime by using the graphmanager function I{graphmanager_set_graph_parameter_by_index}.
     The indexing when using this function should be the same as the indexing that was used in yEd.
     See the graphmanager documentation for further details.
     Note that, except the image parameters, the supported nodes currently never has 2 parameters of the same type, so this
     notation is currently unambiguous. Should there be a need to support multiple parameters
     of the same type in a single node, the parser would need to be updated to handle this.
     Note also that enums should use the specific type and not the generic wrapper name.\n
     E.g. the API for vxConvertDepthNode specifies that the parameter "policy"
     should be of type "vx_enum". However, as is specified in the parameter description,
     "vx_enum" should be of the specific type "vx_convert_policy_e". The graph parser is designed to look
     for the specific type, and not the generic "vx_enum" type.

Adding an image node to the graph
---------------------------------

  1. Image data nodes should be the flowchart object type "Process"
  2. For image nodes that are input nodes or output nodes, we need to add (to the "Data" tab)
     the node type and assign an array index in the corresponding image array,
     e.g. [nodetype input_image[3]] for an input image that is accessed with input_images[3].
     Indexing should start from 0 and have no "gaps".
     We also need to add the image format, e.g. [vx_df_image_e VX_DF_IMAGE_U8], to the data tab.
     If no nodetype is added, the image node will be a virtual image, and the image type will be VX_DF_IMAGE_VIRT,
     which means the OpenVX framework can decide by itself what image format it should have.
     (A technical detail is that before the parser generates the C-code
     it checks that all image formats are consistent throughout the graph,
     and since it has the explicit information, it will actually never use the image format VX_DF_IMAGE_VIRT,
     but instead use the image format it found that the OpenVX framework will have to use.
     However, note that the image node type in this case is still a virtual image.)

See the documentation of the graph manager for information on how to set I/O images
when using the graph in algorithm code.

Connecting nodes in the graph
-----------------------------

  1. The edges (the lines between nodes) should have a target arrow, since we are working with directed graphs,
     The type is arbitrary (one can choose the ones that give the best visual appearance,
     e.g. quadratic, Bezier, polyline etc.)
  2. If a function node has 2 input or 2 output edges,
     they need to be labeled so that the parser can know
     which edge corresponds to which parameter index in the OpenVX API.
     To add a label to an edge, right-click on the edge and choose "Add label".
     The 2 input edges should be labeled "in1" and "in2" respectively (note, no spacing or capital letters)
     The 2 output edges should be labeled "out1" and "out2" respectively.
     Note that for single input or output edges, no labeling is needed.

Userdata objects
----------------

This object should be of the type "User Message" (with an arrow-like right border).
It should not be connected to any other object in the graph.
Furthermore, it is an optional object,
and there should be at most one such object per graph (or subgraph).

To set userdata parameters, right-click on the node and choose "Properties" and the "Data" tab.
Enter any parameters that are global for the whole graph.

The value of such parameters can then be set by the user of the graph
when the graph is registered to the graph manager, by passing in a UserData parameter object.
For instance, if a reference width is needed to be specified, one can add the parameter
[unsigned ref_width] to the UserData object.

See the documentation of the graph manager for further information on how to set the userdata parameter
when registering the graph in the algorithm code.

Debug image nodes
-----------------

These nodes are primarily intended to be used during the design phase when a calculation graph
is constructed and tested e.g. for bitexactness. It allows for the intermediate image data to be saved to
external memory buffers that can be used for testing of the algorithm. They are typically removed before the
production code is released.

Debug nodes should have the following information in the data tab:

  1. An image debug node type should be specified, i.e. [nodetype debug_image[index]].
     Note that it must be indexed, and indexing should start from 0 and have no "gaps".
  2. The debug node image format, e.g. [vx_df_image_e VX_DF_IMAGE_U8].
     Since this is a node with an externally accessed memory buffer, it can not be of type VX_DF_IMAGE_VIRT.

See the documentation of the graph manager for information on how to set debug images
when using the registered graph in algorithm code.

Subgraphs
---------

The graph manager object allows for "chaining" of graphs, where each graph drawn in yEd can be treated as a subgraph.
This is useful for e.g. graphs with repetitive patterns. The chaining is done during registration time,
Therefore nothing needs to be done in yEd in order to later use a particular graph as a subgraph.

See the graphmanager documentation for further details on how to use chaining of subgraphs.

TODO
----
The format of the metadata information for nodes is currently compatible with OpenVX1.0.1.
It should be updated to OpenVX1.1.

For example a border mode can be specified as [vx_border_mode_e VX_BORDER_MODE_CONSTANT] which for OpenVX1.1 would
be [vx_border_e VX_BORDER_CONSTANT].

The code generator will still produce OpenVX code for 1.1 but we should still keep the graph format updated.
This has not been done yet due to lack of time.
"""

#This file also serves as a hook for package-initialization-time actions