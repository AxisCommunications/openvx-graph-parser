"""Class for writing C-code to create a vxSubtractNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""

from base_node import BaseNode

class Subtract(BaseNode):
    """Class for parsing node with the given class name.

    """

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)

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

        # Maybe check node for existence of parameter vx_convert_policy_e
        # (Create std checker function in nodeParse.py)

        #=================
        # PARSE PARAMETERS
        #=================
        if not self.node_has_errors:
            parsed_string += "    " + assignment_string + "vxSubtractNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += self.parse_parameter(graphparser, "vx_convert_policy_e", current_node)
            parsed_string += self.parse_output_parameters(graphparser, current_node)
            parsed_string += ");\n"
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string


