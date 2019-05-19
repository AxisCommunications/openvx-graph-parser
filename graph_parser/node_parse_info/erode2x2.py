"""Class for writing C-code to create a vxErode2x2Node object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode
from graphml_parser import graphml_parser

class Erode2x2(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.matrix_count = 0

    def parse(self, graphparser, current_node, assignment_string, dry_run = False):
        """Parsing of xml and C code for creation of the function node."""
        self.reset_parameters(graphparser, current_node, dry_run)
        parsed_string = ""

        #===============
        # ERROR CHECKING
        #===============
        self.require_nbr_input_edges(graphparser, current_node, 1)
        self.require_nbr_output_edges(graphparser, current_node, 1)

        # Early escape if errors
        if self.node_has_errors:
            return parsed_string

        #=================
        # PARSE PARAMETERS
        #=================
        input_image = self.parse_input_parameters(graphparser, current_node)
        output_image = self.parse_output_parameters(graphparser, current_node)

        # If OpenVX version is 1.0.1 we have to rely on our own extension node vxErode2x2Node...
        if graphparser.vx_version == graphml_parser.VX_VERSION_1_0_1:
            parsed_string += "    " + assignment_string + "vxErode2x2Node(graph_skeleton"
            parsed_string += input_image + output_image + ");\n"
        else: # ...otherwise we use the more generic vxNonLinearFilterNode
            # Create the matrix object
            # TODO: Figure out how to change the VX_MATRIX_ORIGIN attribute and use vxCreateMatrixFromPattern instead
            if self.matrix_count == 0 and not dry_run:
                self.matrix_count += 1
                parsed_string += "    vx_matrix matrix_erode2x2;\n"

            parsed_string += "    matrix_erode2x2 = vxCreateMatrix(graphmanager_get_context(graph_manager), VX_TYPE_UINT8, 3, 3);\n"
            parsed_string += "    vx_uint8 buf_erode2x2[9] = { 255, 255, 0,\n"
            parsed_string += "                                 255, 255, 0,\n"
            parsed_string += "                                  0,    0, 0 };\n"
            parsed_string += "    vxCopyMatrix(matrix_erode2x2, buf_erode2x2, VX_WRITE_ONLY, VX_MEMORY_TYPE_HOST);\n"

            # Create the vxNonLinearFilterNode to do erosion with the created matrix
            parsed_string += "    " + assignment_string + "vxNonLinearFilterNode(graph_skeleton"
            parsed_string += ", VX_NONLINEAR_FILTER_MIN"
            parsed_string += input_image
            parsed_string += ", matrix_erode2x2"
            parsed_string += output_image + ");\n"

            # Release the matrix object
            parsed_string += "    vxReleaseMatrix(&matrix_erode2x2);\n"

        parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string



