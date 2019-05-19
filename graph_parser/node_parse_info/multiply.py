"""Class for writing C-code to create a vxMultiplyNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode

class Multiply(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.multiply_count = 0;

    def parse(self, graphparser, current_node, assignment_string, dry_run = False):
        """Parsing of xml and C code for creation of the function node."""
        self.reset_parameters(graphparser, current_node, dry_run)
        parsed_string = ""

        #===============
        # ERROR CHECKING
        #===============
        self.require_nbr_input_edges(graphparser, current_node, 2)
        self.require_nbr_output_edges(graphparser, current_node, 1)
        self.require_2_input_edges_labeled(graphparser, current_node)

        #=================
        # PARSE PARAMETERS
        #=================
        if not self.node_has_errors:
            if self.multiply_count == 0 and not dry_run:
                self.multiply_count += 1
                parsed_string += "    vx_float32 multiply_value;\n"
                parsed_string += "    vx_scalar multiply_scalar;\n"
            parsed_string += "    multiply_value = " + self.parse_single_parameter(graphparser, "vx_float32", current_node) + ";\n"
            parsed_string += "    multiply_scalar = vxCreateScalar(graphmanager_get_context(graph_manager), VX_TYPE_FLOAT32, &multiply_value);\n"
            parsed_string += "    " + assignment_string + "vxMultiplyNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += ", multiply_scalar"
            parsed_string += self.parse_parameter(graphparser, "vx_convert_policy_e", current_node)
            parsed_string += self.parse_parameter(graphparser, "vx_round_policy_e", current_node)
            parsed_string += self.parse_output_parameters(graphparser, current_node)
            parsed_string += ");\n"
            parsed_string += "    vxReleaseScalar(&multiply_scalar);\n"
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string



