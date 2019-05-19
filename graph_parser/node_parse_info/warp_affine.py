"""Class for writing C-code to create a vxWarpAffineNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode
from graphml_parser import graphml_parser

# Valid values for the vx_matrix parameter, i.e. implemented default matrices
# TODO: Add functionality for specifying a custom matrix in graphml
DEFAULT_MATRIXs = {
    'MATRIX_UNITY': """{
        {1, 0}/* x coefficients */,
        {0, 1}/* y coefficients */,
        {0, 0},/* offsets */
    }""",
    'MATRIX_ROT90CW_REF_HEIGHT': """{
        {0, -1}/* x coefficients */,
        {1, 0}/* y coefficients */,
        {0, opts->ref_height-1},/* offsets */
    }""",
    'MATRIX_ROT90CW_REF_WIDTH': """{
        {0, -1}/* x coefficients */,
        {1, 0}/* y coefficients */,
        {0, opts->ref_width-1},/* offsets */
    }""",
    'MATRIX_ROT90CCW_REF_WIDTH': """{
        {0, 1}/* x coefficients */,
        {-1, 0}/* y coefficients */,
        {opts->ref_width-1, 0},/* offsets */
    }""",
    'MATRIX_ROT90CCW_REF_HEIGHT': """{
        {0, 1}/* x coefficients */,
        {-1, 0}/* y coefficients */,
        {opts->ref_height-1, 0},/* offsets */
    }""",
    'MATRIX_X_Y_SHIFT': """{
        {1, 0}/* x coefficients */,
        {0, 1}/* y coefficients */,
        {opts->x_shift, opts->y_shift},/* offsets */
    }""", }

class WarpAffine(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.mat_count = 0

    def parse(self, graphparser, current_node, assignment_string, dry_run = False):
        """Parsing of xml and C code for creation of the function node."""
        self.reset_parameters(graphparser, current_node, dry_run)
        parsed_string = ""

        #===============
        # ERROR CHECKING
        #===============
        self.require_nbr_input_edges(graphparser, current_node, 1)
        self.require_nbr_output_edges(graphparser, current_node, 1)

        #=================
        # PARSE PARAMETERS
        #=================
        if not self.node_has_errors:
            matrix_type = self.parse_single_parameter(graphparser, "vx_matrix", current_node)
            if matrix_type is "": # Default to unity matrix if vx_matrix is not specified
                matrix_type = 'MATRIX_UNITY'

            if matrix_type not in DEFAULT_MATRIXs:
                err_string = "ERROR: Matrix implementation for {} not found\n".format(matrix_type)
                print err_string
                self.set_graph_has_errors(graphparser, current_node, err_string)
            else:
                matrix_string = DEFAULT_MATRIXs[matrix_type]

            if not dry_run:
                self.mat_count += 1

                parsed_string += """\
    vx_float32 mat%s[3][2] = /*%s*/ %s;
    vx_matrix matrix%s = vxCreateMatrix(graphmanager_get_context(graph_manager), VX_TYPE_FLOAT32, 2, 3);
""" % (str(self.mat_count), matrix_type, matrix_string, str(self.mat_count))

                # Writing to matrix object is different from OpenVX1.1
                if graphparser.vx_version == graphml_parser.VX_VERSION_1_0_1:
                    parsed_string += "    vxWriteMatrix(matrix%s, mat%s);\n" % (str(self.mat_count), str(self.mat_count))
                else:
                    parsed_string += "    vxCopyMatrix(matrix%s, mat%s, VX_WRITE_ONLY, VX_MEMORY_TYPE_HOST);\n" % \
                                     (str(self.mat_count), str(self.mat_count))

            parsed_string += "    " + assignment_string + "vxWarpAffineNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += """, matrix%s""" % (str(self.mat_count))
            parsed_string += self.parse_parameter(graphparser, "vx_interpolation_type_e", current_node)
            parsed_string += self.parse_output_parameters(graphparser, current_node)

            parsed_string += ");\n"
            parsed_string += """    vxReleaseMatrix(&matrix%s);\n""" % (str(self.mat_count))
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string
