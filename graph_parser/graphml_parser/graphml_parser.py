"""Parser class for parsing OpenVX graphs saved in the yEd graphml format"""

from xml.dom import minidom
import os.path
from function_nodes import FunctionNodes
from image_nodes import ImageNodes
from image_format_checker import ImageNodeFormatChecker
from userdata import Userdata

# The supported OpenVX versions
VX_VERSION_1_0_1 = "1.0.1"
VX_VERSION_1_1 = "1.1"
VX_VERSION_1_2 = "1.2"
VX_VERSIONS = [VX_VERSION_1_0_1, VX_VERSION_1_1, VX_VERSION_1_2]
VX_VERSION_DEFAULT = VX_VERSION_1_2

class GraphParser():
    """OpenVX graph parser class

    Uses a minidom parser to parse the input file specified by the filename argument.

    The first thing that the GraphParser does when it is instansiated is to parse the
    XML file provided in the filename argument.

    Then the GraphParser creates and populates a number of synched lists
    used to store necessary information for the C-code generation

    Global graph information is generated and stored in the arrays set up in the init function.
    Three main things are needed:

    1: Lists of all input/output and internal image nodes id's, where the list indices correspond to
    C-array indices for corresponding C-arrays.

    2: Index-synched lists of all the function nodes and their corresponding OpenVX names
    as well as a node_info object for every function node, containing information
    about all edges (lines) entering or leaving the function nodes and the nodes they connect to.

    3: Separately index-synced lists for all input and output function nodes and
    lists with the corresponding first input and output indices in the parameter list for
    the node create OpenVX function (as defined in the standard). An input function node
    is a function node that has at least one edge connected to an input image node,
    and similarly for the output function nodes. A given function node can technically be present
    both in the input- and output function node lists though usually this is not the case.

    After all lists have been created, no mode parsing should be needed, and the
    C-code can be generated and written to file, using queries to the GraphParser methods and
    its generated lists.

    The GraphParser is mainly intended to provide answers about the graph structure.
    It ideally should not handle the generation of the actual C-code.
    The C-code generating python code uses the Node query methods of the GraphParser
    to make decisions on how to generate the C-code
    based on the global and local graph node information stored in the GraphParser.

    If the verbose flag is set, the GraphParser will print more detailed information
    to the terminal.
    If the debug_mode flag is set, it will print even more information.

    If the strip_mode flag is set, the GraphParser will generate C-code without any
    graphmanager or other libs/vision dependencies.
    Such generated code is typically used for standalone OpenVX tests.
    """

    def __init__(self, verbose, debug_mode, strip_mode=False, strip_io=False, vx_version=VX_VERSION_DEFAULT):
        """Initializes the GraphParser

        Parses the graphml file, then sets up and populates the needed node-related lists.
        """
        #Set general attributes
        self.verbose = verbose
        self.debug_mode = debug_mode
        self.strip_mode = strip_mode
        self.strip_io = strip_io

        if not vx_version in VX_VERSIONS:
            raise RuntimeError('OpenVX version %s is not supported.' % vx_version)
        self.vx_version = vx_version

        self.graph_has_errors = False
        self.image_nodes = ImageNodes(debug_mode)
        self.function_nodes = FunctionNodes(debug_mode)
        self.userdata = Userdata(debug_mode)
        #Format checker only be initialized, NOT run during graphparser initialization time.
        #It can give meaningless results if the graph contains other errors,
        #therefore a dry-run for the code generation should be done first.
        self.image_format_checker = ImageNodeFormatChecker(debug_mode)
        self.validation_output_graph = [None, None]  # Init to a hardcoded empty graph

    def set_io_strip_mode(self):
        """ Set strip mode to also generate code for I/O-image setting"""
        self.strip_io = True

    def set_function_node_library(self, library):
        """Set the function node library to be used.

        The function node library contains necessary parametrization information of the supported function nodes
        """
        self.library = library

    def load_graph(self, file_path):
        """Loads the graph definition from file and processes it.

        Also initializes the image_nodes and function_nodes objects and populates them
        with parsed information from the loaded graph.
        """
        file_name, file_extension = os.path.splitext(file_path)
        self.graphname = os.path.basename(file_name)
        self.graph = minidom.parse(file_path)
        self.validation_output_graph = self.graph.cloneNode(True)
        # Populate all node related lists
        has_errors = self.userdata.populate_userdata(self.graph, self.validation_output_graph)
        self.graph_has_errors |= has_errors

        has_errors = self.image_nodes.populate_image_nodes_lists(self.graph,
                                                                 self.userdata,
                                                                 self.validation_output_graph)
        self.graph_has_errors |= has_errors

        self.function_nodes.populate_function_nodes_indexed_lists(self.graph, self.library, self.image_nodes)

    def verify_graph_image_formats(self):
        has_errors, self.validation_output_graph = self.image_format_checker.check_graph_image_formats(self.graph,
                                                                                                       self.image_nodes,
                                                                                                       self.function_nodes,
                                                                                                       self.library)
        return has_errors

    def function_nodes_list_check(self):
        if not self.function_nodes.lists_populated:
            raise RuntimeError('The FunctionNodes class instance must populate its function node lists before this function is called.')

    def image_nodes_list_check(self):
        if not self.function_nodes.lists_populated:
            raise RuntimeError('The ImageNodes class instance must populate its image node lists before this function is called.')

    # ============================================================
    # Getters
    # ============================================================
    def get_function_node_info(self, node):
        self.function_nodes_list_check()
        return self.function_nodes.get_node_info(node)

    def get_indexed_names(self, node_type_string):
        if node_type_string.endswith('image_nodes'):
            self.image_nodes_list_check()
            if node_type_string == 'uniform_input_image_nodes':
                return self.image_nodes.uniform_input_image_indexed_names
            elif node_type_string == 'input_image_nodes':
                return self.image_nodes.input_nodes_indexed_names
            elif node_type_string == 'output_image_nodes':
                return self.image_nodes.output_nodes_indexed_names
            elif node_type_string == 'virtual_image_nodes':
                return self.image_nodes.virtual_nodes_indexed_names
            elif node_type_string == 'debug_image_nodes':
                return self.image_nodes.debug_nodes_indexed_names
            else:
                raise NameError(node_type_string + ' is not a known image node_type_string.')
        elif node_type_string.endswith('function_nodes'):
            self.function_nodes_list_check()
            if node_type_string == 'function_nodes':
                return self.function_nodes.indexed_function_nodes
            elif node_type_string == 'input_function_nodes':
                return self.function_nodes.input_function_nodes_indexed_names
            elif node_type_string == 'output_function_nodes':
                return self.function_nodes.output_function_nodes_indexed_names
            elif node_type_string == 'debug_input_function_nodes':
                return self.function_nodes.debug_input_function_nodes_indexed_names
            elif node_type_string == 'debug_output_function_nodes':
                return self.function_nodes.debug_output_function_nodes_indexed_names
            else:
                raise NameError(node_type_string + ' is not a known function node_type_string.')
        else:
            raise NameError(node_type_string + ' is not a known node_type_string.')

    def get_dynamic_function_nodes_info(self):
        self.function_nodes_list_check()
        return self.function_nodes.dynamic_nodes_info

    def get_index_for_function_node_in_list(self, node_type_string, node):
        self.function_nodes_list_check()
        if node_type_string == 'input':
            return self.function_nodes.get_input_function_node_index(node)
        elif node_type_string == 'output':
            return self.function_nodes.get_output_function_node_index(node)
        elif node_type_string == 'debug_input':
            return self.function_nodes.get_debug_input_function_node_index(node)
        elif node_type_string == 'debug_output':
            return self.function_nodes.get_debug_output_function_node_index(node)
        else:
            raise NameError(node_type_string + ' is not a known function node_type_string.')

    def get_value_for_attribute(self, node_id, attribute):
        """ Get the value of a specific image attribute.
        :param node_id: The id of the image node.
        :param attribute: The attribute to get.
        :return: A tuple containing (is_userdata, value) where:
        is_userdata is True if value contains reference to userdata
        value is the value of of the attribute or default value if attribute is not set.
        """
        image_attributes = self.image_nodes.get_image_attributes(node_id)
        if image_attributes is None:
            raise RuntimeError("No image attributes could be found for node with id: {}".format(node_id))
        else:
            (is_userdata, value) = image_attributes.get_image_attribute(self.userdata, attribute)
            return is_userdata, value

    def get_image_format(self, node_id):
        """ Get the image format for a specific image node.
        :param node_id: The id of the image node.
        :return: The image format for the image node.
        """
        if node_id not in self.image_format_checker.PIN_ID:
            raise NameError('Image  width_id {} missing in format checker PIN_ID list.'.format(node_id))
        else:
            PIN_index = self.image_format_checker.PIN_ID.index(node_id)
            return self.image_format_checker.PIN_FORMAT[PIN_index]

    def get_uniform_image_value_for_id(self, image_id):
        try:
            index = self.image_nodes.get_uniform_image_index(image_id)
            return self.image_nodes.uniform_input_image_indexed_values[index]
        except:
            print "ERROR: node id is not in uniform image nodes list"
            raise

    def is_function_io_node(self, current_node, node_info):
        return ( any(e in node_info.input_image_node_ids for e in self.get_indexed_names('input_image_nodes')) or \
                 any(e in node_info.output_image_node_ids for e in self.get_indexed_names('output_image_nodes')) or \
                 self.is_function_debug_node(current_node) )

    def is_function_debug_node(self, current_node):
        node_info = self.get_function_node_info(current_node)
        return ( any(e in node_info.input_image_node_ids for e in self.get_indexed_names('debug_image_nodes')) or \
                 any(e in node_info.output_image_node_ids for e in self.get_indexed_names('debug_image_nodes')) )

    def is_function_dynamic_node(self, current_node):
        return any(e[0] == current_node for e in self.get_dynamic_function_nodes_info())

    def using_refcounted_assignment_string(self, current_node):
        if self.is_function_dynamic_node(current_node) or self.is_function_debug_node(current_node):
            return True
        else:
            return False

    def use_any_refcounted_assignment_string(self):
        if self.get_indexed_names('debug_image_nodes') or self.get_dynamic_function_nodes_info():
            return True
        else:
            return False
