"""Base class for nodes for writing C-code to create a vxXXXNode objects.

Done by parsing the graph parameters of the xml description of the node.
"""
from xml.dom import minidom
import logging
from graphml_parser import parse_common
from graphml_parser import graphml_parser

class BaseNode:
    """Class for parsing node with the given class name.

    """
    # Class-global attributes for all function node instances
    border_mode_count = 0

    def __init__(self):
        """Specified according to the OpenVX standard

        Note that the first index is not counted
        (i.e. the graph index in the node creation function)
        """
        self.node_has_errors = False
        self.dry_run = False
        self.node_info = minidom.Node()

    def reset_parameters(self, graphparser, current_node, dry_run):
        """Used to reset internal parameters before parsing is done in the subclasses"""

        self.node_has_errors = False
        self.dry_run = dry_run
        self.node_info = graphparser.get_function_node_info(current_node)

    def parse(self, graphparser, current_node, assignment_string, dry_run=False):
        """Parsing of xml and creation of dummy function node.

        Note that this function should only be called
        if the graph function node class was not found.
        This might mean that the node name was not found,
        or that the parse function of the subclass has not been implemented.
        """
        self.reset_parameters(graphparser, current_node, dry_run)
        parsed_string = ""

        #===============
        # ERROR CHECKING
        #===============
        # Dummy node only used if something with the naming of a function node went wrong
        self.set_graph_has_errors(graphparser, current_node, "ERROR: Node implementation not found.\nMaybe node name is wrong?\n")

        #=================
        # PARSE PARAMETERS
        #=================
        parsed_string += "ERROR: Node implementation not found. Maybe node name is wrong?"
        parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string

    def parse_border_mode(self, graphparser, current_node, node_ref_string, dry_run=False):
        """Parsing of border mode parameters from xml.
        This functionality lies in base_node bacause it is possible to set border mode for
        all nodes but it might not be supported by a node implementation.
        The function node C-name is given by node_ref_string
        Returns C code for setting the border mode on the function node."""
        parsed_string = ""
        border_mode = parse_common.parse_parameter('vx_border_mode_e', current_node)
        if border_mode and not dry_run:
            logging.debug('border_mode: ' + border_mode)
            if BaseNode.border_mode_count == 0:
                parsed_string += "    {} border_mode;\n".format(get_border_mode_type(graphparser.vx_version))
                BaseNode.border_mode_count += 1

            if border_mode == "VX_BORDER_MODE_CONSTANT" or "VX_BORDER_MODE_REPLICATE" or "VX_BORDER_MODE_UNDEFINED":
                parsed_string += "    border_mode.mode = " + get_border_mode(graphparser.vx_version, border_mode) + ";\n"
                if border_mode == "VX_BORDER_MODE_CONSTANT":
                    constant_value = parse_common.parse_parameter('constant_value', current_node)
                    logging.debug('constant_value: ' + constant_value)
                    if constant_value:
                        parsed_string += "    border_mode" + get_border_constant(graphparser.vx_version, constant_value) + ";\n"
                    else:
                        self.set_graph_has_errors(graphparser, current_node,
                                                  "ERROR: VX_BORDER_MODE_CONSTANT requires a constant_value parameter\n")
            else:
                self.set_graph_has_errors(graphparser, current_node,
                                          "ERROR: Border mode {} not found.\nMaybe spelling is wrong?\n".format(border_mode))

            parsed_string += "    vxSetNodeAttribute({}, {}, &border_mode, " \
                             "sizeof({}));\n".format(node_ref_string,
                                                     get_border_mode_attribute(graphparser.vx_version),
                                                     get_border_mode_type(graphparser.vx_version))

        return parsed_string

    def set_graph_has_errors(self, graphparser, current_node, errorstring):
        """Sets an error text on the given function node."""
        self.node_has_errors = True
        graphparser.graph_has_errors = True
        parse_common.set_text_on_node(graphparser.validation_output_graph, current_node, errorstring, 'Red', True)

    def require_nbr_input_edges(self, graphparser, current_node, nbr_edges):
        if (len(self.node_info.input_image_node_ids) != nbr_edges):
            logging.warning('WARNING: Wrong number of input edges')
            self.set_graph_has_errors(graphparser, current_node, "ERROR: Wrong number of input edges\n")


    def require_nbr_output_edges(self, graphparser, current_node, nbr_edges):
        if (len(self.node_info.output_image_node_ids) != nbr_edges):
            logging.warning('WARNING: Wrong number of output edges')
            self.set_graph_has_errors(graphparser, current_node, "ERROR: Wrong number of output edges\n")

    def require_2_input_edges_labeled(self, graphparser, current_node):
        if not (((self.node_info.input_edge_labels[0] == "in1") and (self.node_info.input_edge_labels[1] == "in2"))
              or ((self.node_info.input_edge_labels[0] == "in2") and (self.node_info.input_edge_labels[1] == "in1"))):
            logging.warning('WARNING: Incorrect naming of input edge labels (in1 and in2 required)')
            self.set_graph_has_errors(graphparser, current_node, "ERROR: Incorrect naming of input edge labels (in1 and in2 required)\n")

    def require_2_output_edges_labeled(self, graphparser, current_node):
        if not (((self.node_info.output_edge_labels[0] == "out1") and (self.node_info.output_edge_labels[1] == "out2"))
              or ((self.node_info.output_edge_labels[0] == "out2") and (self.node_info.output_edge_labels[1] == "out1"))):
            logging.warning('WARNING: Incorrect naming of output edge labels (out1 and out2 required)')
            self.set_graph_has_errors(graphparser, current_node, "ERROR: Incorrect naming of output edge labels (out1 and out2 required)\n")

    def append_to_io_arrays_strip(self, graphparser, current_node):
        """Special version of append_to_io_arrays for strip mode.
        Here we don't use refcounted nodes type, simply save the dynamic nodes to list.

        This function assumes the node lists that current_node is compared against
        can not contain duplicates of nodes (node ids).
        """
        parsed_string = ""

        if graphparser.strip_io: # Also set I/O images
            if any(e in self.node_info.input_image_node_ids for e in
                   graphparser.get_indexed_names('input_image_nodes')):
                parsed_string += "    (io_nodes->input_nodes)[" + \
                                 str(graphparser.get_index_for_function_node_in_list('input',
                                                                                     current_node)) + "] = function_node;\n"
            if any(e in self.node_info.output_image_node_ids for e in
                   graphparser.get_indexed_names('output_image_nodes')):
                parsed_string += "    (io_nodes->output_nodes)[" + \
                                 str(graphparser.get_index_for_function_node_in_list('output',
                                                                                     current_node)) + "] = function_node;\n"

        for idx, itemlist in enumerate(graphparser.get_dynamic_function_nodes_info()):
            if itemlist[0] == current_node:
                parsed_string += "    dynamic_nodes[" + str(idx) + "] = function_node;\n"

        return parsed_string

    def append_to_io_arrays(self, graphparser, current_node):
        """Appends reference to the current node in the corresp. I/O C-array if it is a I/O function node

        This function assumes the node lists that current_node is compared against
        can not contain duplicates of nodes (node ids).
        """

        # Special function if strip_mode
        if graphparser.strip_mode:
            return self.append_to_io_arrays_strip(graphparser, current_node)

        parsed_string = ""

        if graphparser.using_refcounted_assignment_string(current_node):
            parsed_string += "    function_node_rc = node_rc_create(function_node);\n"

        for idx, itemlist in enumerate(graphparser.get_dynamic_function_nodes_info()):
            if itemlist[0] == current_node:
                parsed_string += "    dynamic_nodes[" + str(idx) + "] = node_rc_copy_ref(function_node_rc);\n"

        if any(e in self.node_info.output_image_node_ids for e in graphparser.get_indexed_names('debug_image_nodes')):
            parsed_string += "    (nodes->debug_input_nodes)[" + \
                str(graphparser.get_index_for_function_node_in_list('debug_input', current_node)) + "] = node_rc_copy_ref(function_node_rc);\n"
        if any(e in self.node_info.input_image_node_ids for e in graphparser.get_indexed_names('debug_image_nodes')):
            parsed_string += "    (nodes->debug_output_nodes)[" + \
                str(graphparser.get_index_for_function_node_in_list('debug_output', current_node)) + "] = node_rc_copy_ref(function_node_rc);\n"

        return parsed_string

    def parse_input_parameter(self, graphparser, index, node_info):
        """Creates C-code node input image parameter for a given index in node_info.input_data_node_ids[]."""
        if node_info.input_image_node_ids[index] in graphparser.get_indexed_names('virtual_image_nodes'):
            return ", internal_images[" + str(graphparser.get_indexed_names('virtual_image_nodes').index(node_info.input_image_node_ids[index])) + "]"
        elif node_info.input_image_node_ids[index] in graphparser.get_indexed_names('input_image_nodes'):
            return ", input_images[" + str(graphparser.get_indexed_names('input_image_nodes').index(node_info.input_image_node_ids[index])) + "]"
        elif node_info.input_image_node_ids[index] in graphparser.get_indexed_names('output_image_nodes'):
            return ", output_images[" + str(graphparser.get_indexed_names('output_image_nodes').index(node_info.input_image_node_ids[index])) + "]"
        else:
            return "ERROR: Input parameter missing!!!\n\n"

    def parse_output_parameter(self, graphparser, index, node_info):
        """Creates C-code node output image parameter for a given index in node_info.output_data_node_ids[]."""
        if node_info.output_image_node_ids[index] in graphparser.get_indexed_names('virtual_image_nodes'):
            return ", internal_images[" + str(graphparser.get_indexed_names('virtual_image_nodes').index(node_info.output_image_node_ids[index])) + "]"
        elif node_info.output_image_node_ids[index] in graphparser.get_indexed_names('input_image_nodes'):
            return ", input_images[" + str(graphparser.get_indexed_names('input_image_nodes').index(node_info.output_image_node_ids[index])) + "]"
        elif node_info.output_image_node_ids[index] in graphparser.get_indexed_names('output_image_nodes'):
            return ", output_images[" + str(graphparser.get_indexed_names('output_image_nodes').index(node_info.output_image_node_ids[index])) + "]"
        else:
            return "ERROR: Output parameter missing!!!\n\n"

    def parse_input_parameters(self, graphparser, current_node):
        """Creates the C-code node input image parameters."""
        parsed_string = ""
        if (len(self.node_info.input_image_node_ids) == 1):
            parsed_string += self.parse_input_parameter(graphparser, 0, self.node_info)
        elif (len(self.node_info.input_image_node_ids) == 2):
            if 'in1' in self.node_info.input_edge_labels and 'in2' in self.node_info.input_edge_labels:
                parsed_string += self.parse_input_parameter(graphparser, self.node_info.input_edge_labels.index('in1'), self.node_info)
                parsed_string += self.parse_input_parameter(graphparser, self.node_info.input_edge_labels.index('in2'), self.node_info)
            else:
                logging.warning('WARNING: missing label on input node!\n')

        return parsed_string

    def parse_output_parameters(self, graphparser, current_node):
        """Creates the C-code node input image parameters."""
        parsed_string = ""
        if (len(self.node_info.output_image_node_ids) == 1):
            parsed_string += self.parse_output_parameter(graphparser, 0, self.node_info)
        elif (len(self.node_info.output_image_node_ids) == 2):
            if 'out1' in self.node_info.output_edge_labels and 'out2' in self.node_info.output_edge_labels:
                parsed_string += self.parse_output_parameter(graphparser, self.node_info.output_edge_labels.index('out1'), self.node_info)
                parsed_string += self.parse_output_parameter(graphparser, self.node_info.output_edge_labels.index('out2'), self.node_info)
            else:
                logging.warning('WARNING: missing label on output node!\n')

        return parsed_string

    def parse_parameter(self, graphparser, parameter, current_node):
        """Creates a C-code function node parameter

        Searches for a parameter that matches the given type in parameter.
        The first occurrence found will be used. If the function node creation function has multiple
        parameters of the given type, a more general function must be called.
        """
        parameter_value = parse_common.parse_parameter(parameter, current_node)

        if parameter_value != "":
            parameter_value = ", " + parameter_value

        return parameter_value

    def parse_single_parameter(self, graphparser, parameter, current_node):
        """Creates a C-code function node parameter

        Searches for a parameter that matches the given type in parameter.
        The first occurrence found will be used. If the function node creation function has multiple
        parameters of the given type, a more general function must be called.
        """
        return parse_common.parse_parameter(parameter, current_node)

# Helper functions to generate code for different OpenVX versions
def get_border_mode_type(vx_version):
    if vx_version == graphml_parser.VX_VERSION_1_0_1:
        return "vx_border_mode_t"
    else:
        return "vx_border_t"

def get_border_mode(vx_version, border_mode):
    if vx_version == graphml_parser.VX_VERSION_1_0_1:
        border_modes = {"VX_BORDER_MODE_CONSTANT" : "VX_BORDER_MODE_CONSTANT",
                        "VX_BORDER_MODE_REPLICATE" : "VX_BORDER_MODE_REPLICATE",
                        "VX_BORDER_MODE_UNDEFINED" : "VX_BORDER_MODE_UNDEFINED"}
    else:
        border_modes = {"VX_BORDER_MODE_CONSTANT" : "VX_BORDER_CONSTANT",
                        "VX_BORDER_MODE_REPLICATE" : "VX_BORDER_REPLICATE",
                        "VX_BORDER_MODE_UNDEFINED" : "VX_BORDER_UNDEFINED"}
    return border_modes[border_mode]

def get_border_constant(vx_version, constant_value):
    # TODO: This functions needs to parse the node if we need border modes for non-U8 operations!
    if vx_version is graphml_parser.VX_VERSION_1_0_1:
        return ".constant_value = " + constant_value
    else:
        return ".constant_value.U8 = " + constant_value

def get_border_mode_attribute(vx_version):
    if vx_version == graphml_parser.VX_VERSION_1_0_1:
        return "VX_NODE_ATTRIBUTE_BORDER_MODE"
    else:
        return "VX_NODE_BORDER"
