"""Class for writing C-code to create a vxConvertDepthNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode

class ConvertDepth(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.convert_depth_count = 0;

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
            if self.convert_depth_count == 0 and not dry_run:
                self.convert_depth_count += 1
                parsed_string += "    vx_int32 depth_value;\n"
                parsed_string += "    vx_scalar depth_scalar;\n"
            parsed_string += "    depth_value = " + self.parse_single_parameter(graphparser, "vx_int32", current_node) + ";\n"
            parsed_string += "    depth_scalar = vxCreateScalar(graphmanager_get_context(graph_manager), VX_TYPE_INT32, &depth_value);\n"
            parsed_string += "    " + assignment_string + "vxConvertDepthNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += self.parse_output_parameters(graphparser, current_node)
            parsed_string += self.parse_parameter(graphparser, "vx_convert_policy_e", current_node)


            parsed_string += ", depth_scalar);\n"
            parsed_string += "    vxReleaseScalar(&depth_scalar);\n"
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string
