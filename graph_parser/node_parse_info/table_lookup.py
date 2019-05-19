"""Class for writing C-code to create a vxTableLookupNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode

# Valid values for the vx_lut parameter, i.e. implemented default LUTs
# TODO: Actually implement the default LUTs
DEFAULT_LUTs = {'LUT_DUMMY': 'vxCreateLUT(graphmanager_get_context(graph_manager), VX_TYPE_UINT8, 256)',
                'LUT_ZERO': 'graphmanager_utils_create_lut_zero()',
                'LUT_IDENTITY': 'graphmanager_utils_create_lut_unity()'}

class TableLookup(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.table_lookup_count = 0

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
            if self.table_lookup_count == 0 and not dry_run:
                self.table_lookup_count += 1
                parsed_string += "    vx_lut lut;\n"

            lut_type = self.parse_single_parameter(graphparser, "vx_lut", current_node)
            if lut_type not in DEFAULT_LUTs:
                err_string = "ERROR: LUT implementation for {} not found\n".format(lut_type)
                self.set_graph_has_errors(graphparser, current_node, err_string)
            else:
                parsed_string += "    lut = " + DEFAULT_LUTs[lut_type] + ";\n"

            parsed_string += "    " + assignment_string + "vxTableLookupNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += ", lut"
            parsed_string += self.parse_output_parameters(graphparser, current_node)
            parsed_string += ");\n"
            parsed_string += "    vxReleaseLUT(&lut);\n"
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string
