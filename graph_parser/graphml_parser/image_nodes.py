"""Image Nodes class
"""
import re
import parse_common

# Dictionary of currently supported image attributes and corresponding valid type and default value
IMAGE_ATTRIBUTES_VALID = {'width': (int, 0),
                          'height': (int, 0),
                          'nodetype': (str, 'virtual_image'),
                          'vx_df_image_e': (str, 'VX_DF_IMAGE_VIRT'),
                          'uniform_value': (int, 0)}

class ImageAttributes:
    """ Class that contains id and explicitly set attributes for an image node.
    Image attributes are specific properties set on images in the graph.
    Image attributes do not include image format and image type (e.g. input or debug image).
    These are currently handled separately.
    NOTE: When values for an attribute are referencing userdata attributes it is assumed that the reference is
    the first thing on the value and that there only is one reference per attribute.
    E.g. [width ref_width/2] is OK whereas [width 0.5*ref_width] is not.

    Examples of how to specify image attributes in graph on an image node's data field:
    [width 100]
    [width ref_value*7] (Assuming ref_value is defined in userdata node)
    """

    def __init__(self, node_id):
        # Node id for the image node corresponding to the image attributes
        self.node_id = node_id
        # Dictionary of image attributes for this node
        # with attribute names mapping to corresponding attribute values.
        self.attributes = {}

    def get_image_attribute(self, userdata, attribute):
        """ Get the value of a specific image attribute.
        :param userdata: The userdata object.
        :param attribute: The attribute to get.
        :return: A tuple containing (is_userdata, value) where:
        is_userdata is True if value contains reference to userdata
        value is the value of of the attribute or default value if attribute is not set.
        """

        if attribute not in self.attributes:
            if attribute not in IMAGE_ATTRIBUTES_VALID:
                raise(RuntimeError, "Unknown image attribute {}".format(attribute))
            return False, IMAGE_ATTRIBUTES_VALID[attribute][1]

        userdata_attributes = self.get_userdata_attributes(userdata)

        if attribute in userdata_attributes:
            return True, userdata_attributes[attribute]
        elif attribute in IMAGE_ATTRIBUTES_VALID:
            value = self.attributes[attribute]
            try:
                # Rough check of the type of attribute literal value by attempting a type conversion to the valid type
                IMAGE_ATTRIBUTES_VALID[attribute][0](value)
                return False, value
            except ValueError:
                print "Invalid image attribute value {} for attribute {}. Expected {}".format(
                    value, attribute, IMAGE_ATTRIBUTES_VALID[attribute][0])
                raise
        else:
            raise(RuntimeError, "Unknown image attribute {}".format(attribute))

    def is_valid_attribute(self, userdata, attribute, value):
        """ Check if attribute,value- combination is valid.
        :param userdata: The userdata object.
        :param attribute:
        :return: A tuple containing (valid, err_string) where:
        valid is True if the combination is valid and False otherwise
        err_string is an error string indicating why combination is invalid if valid is False
        """
        if attribute not in IMAGE_ATTRIBUTES_VALID:
            return False, "Unknown image attribute {}".format(attribute)
        else:
            # Check if value is userdata reference first
            for attribute_userdata in userdata.attributes:
                if attribute_userdata in value:
                    return True, ""
            # Check if value is valid type for attribute
            try:
                # Rough check of the type of attribute literal value by attempting a type conversion to the valid type
                IMAGE_ATTRIBUTES_VALID[attribute][0](value)
            except ValueError:
                return False, "Invalid\nvalue\nfor {}".format(attribute)
            else:
                return True, ""

    def get_userdata_attributes(self, userdata):
        """Filter image attributes to get only those that are referencing userdata attributes. """

        attributes_with_userdata_refs = {}
        for attribute in self.attributes:
            value = self.attributes[attribute]
            for attribute_userdata in userdata.attributes:
                if attribute_userdata in value:
                    attributes_with_userdata_refs[attribute] = value

        return attributes_with_userdata_refs

class ImageNodes:
    """Class that contains information about the different types of image nodes."""

    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.lists_populated = False

        # These lists contain the graph input and output image nodes,
        # and the virtual (internal) image nodes.
        # The wording "indexedNames" is used to indicate that
        # the parsing assigns a c-array index for each node id to be used consistently
        # in the generated c-code (an index for each list it belongs to)
        self.input_nodes_indexed_names = []
        self.output_nodes_indexed_names = []
        self.virtual_nodes_indexed_names = []
        self.debug_nodes_indexed_names = []
        #A special input node type used as input to some nodes to generate specific behaviours
        self.uniform_input_image_indexed_names = []
        self.uniform_input_image_indexed_values = []
        self.uniform_input_image_indexed_formats = []

        self.nbr_input_images = -1
        self.nbr_output_images = -1
        self.nbr_debug_images = -1

        self.image_attributes = []

    def populate_image_nodes_lists(self, graph, userdata, validation_output_graph):
        graph_has_errors = False

        if(self.populate_image_attributes(graph, userdata, validation_output_graph)):
            graph_has_errors = True
        if(self.populate_uniform_input_image_names_list(graph, validation_output_graph)):
            graph_has_errors = True
        if(self.populate_virtual_nodes_indexed_names_list(graph)):
            graph_has_errors = True
        if(self.populate_input_nodes_indexed_names_list(graph, validation_output_graph)):
            graph_has_errors = True
        if(self.populate_output_nodes_indexed_names_list(graph, validation_output_graph)):
            graph_has_errors = True
        if(self.populate_debug_nodes_indexed_names_list(graph, validation_output_graph)):
            graph_has_errors = True

        self.nbr_input_images = len(self.input_nodes_indexed_names)
        self.nbr_output_images = len(self.output_nodes_indexed_names)
        self.nbr_debug_images = len(self.debug_nodes_indexed_names)

        self.lists_populated = True
        return graph_has_errors

    def populate_input_nodes_indexed_names_list(self, graph, validation_output_graph):
        """Populates the input_nodes_indexed_names list with the graph input images.

        Ordered in increasing array index for the indexed input images in the graph.
        """
        graph_has_errors = False
        current_index = 0
        found = 1
        while found:
            found = 0

            for node in graph.getElementsByTagName('node'):
                datatext = parse_common.get_node_datatext(node)
                # Check for input image with array index = current_index
                if "input_image[" + str(current_index) + "]" in datatext:
                    if "[vx_df_image_e" in datatext:
                        self.input_nodes_indexed_names.append(node.attributes["id"].value)
                    else:
                        graph_has_errors = True
                        parse_common.set_text_on_node(validation_output_graph, node, "Input\nimage\nformat\nmissing", 'Red', False)
                    current_index = current_index + 1
                    found = 1

        return graph_has_errors

    def populate_output_nodes_indexed_names_list(self, graph, validation_output_graph):
        """Populates the output_nodes_indexed_names list with the graph input images."""
        graph_has_errors = False
        current_index = 0
        found = 1
        while found:
            found = 0
            for node in graph.getElementsByTagName('node'):
                datatext = parse_common.get_node_datatext(node)
                 # Check for output image with array index = current_index
                if "output_image[" + str(current_index) + "]" in datatext:
                    if "[vx_df_image_e" in datatext:
                        self.output_nodes_indexed_names.append(node.attributes["id"].value)
                    else:
                        graph_has_errors = True
                        parse_common.set_text_on_node(validation_output_graph, node, "Output\nimage\nformat\nmissing", 'Red', False)
                    current_index = current_index + 1
                    found = 1

        return graph_has_errors

    def populate_virtual_nodes_indexed_names_list(self, graph):
        """Populates the virtual_nodes_indexed_names list with the internal graph images."""
        graph_has_errors = False
        for node in graph.getElementsByTagName('node'):
            for nodeAppearance in node.getElementsByTagName('y:GenericNode'):
                if nodeAppearance.attributes["configuration"].value == "com.yworks.flowchart.process":
                    datatext = parse_common.get_node_datatext(node)
                    if not "input_image[" in datatext and not "output_image[" in datatext:
                        self.virtual_nodes_indexed_names.append(node.attributes["id"].value)

        return graph_has_errors

    def populate_uniform_input_image_names_list(self, graph, validation_output_graph):
        """Populates the uniform_input_image_names list with the graph uniform input images.

        Ordered in increasing array index for the indeed input images in the graph.
        """
        graph_has_errors = False
        for node in graph.getElementsByTagName('node'):
            datatext = parse_common.get_node_datatext(node)
            if "uniform_input_image" in datatext:
                if "[vx_df_image_e" in datatext and "[uniform_value" in datatext:
                    node_id = node.attributes["id"].value
                    self.uniform_input_image_indexed_names.append(node_id)

                    image_attributes = self.get_image_attributes(node_id)
                    self.uniform_input_image_indexed_values.append(image_attributes.attributes.get("uniform_value", "VALUE_ERROR"))
                    self.uniform_input_image_indexed_formats.append(image_attributes.attributes.get("vx_df_image_e", "ERROR"))

                else:
                    graph_has_errors = True
                    parse_common.set_text_on_node(validation_output_graph, node, "Uniform input\nimage\nformat\nmissing", 'Red', False)

        return graph_has_errors

    def populate_debug_nodes_indexed_names_list(self, graph, validation_output_graph):
        """Populates the output_nodes_indexed_names list with the graph input images."""
        graph_has_errors = False
        current_index = 0
        found = 1
        while found:
            found = 0
            for node in graph.getElementsByTagName('node'):
                datatext = parse_common.get_node_datatext(node)
                if "debug_image[" + str(current_index) + "]" in datatext:
                    if "[vx_df_image_e" in datatext:
                        self.debug_nodes_indexed_names.append(node.attributes["id"].value)
                    else:
                        graph_has_errors = True
                        parse_common.set_text_on_node(validation_output_graph, node, "Debug\nimage\nformat\nmissing", 'Red', False)
                    current_index = current_index + 1
                    found = 1

        return graph_has_errors

    def populate_image_attributes(self, graph, userdata, validation_output_graph):
        """Populates the image_attributes list.
        All image nodes will get an ImageAttributes instance even if they have no explicitly set attributes. """
        graph_has_errors = False

        for node in graph.getElementsByTagName('node'):
            image_attributes = ImageAttributes(node.attributes["id"].value)
            datatext = parse_common.get_node_datatext(node)
            for attribute in IMAGE_ATTRIBUTES_VALID:
                values = re.findall('\['+attribute+' (.+)\]', datatext)
                if len(values) > 1:
                    graph_has_errors = True
                    parse_common.set_text_on_node(validation_output_graph, node, "Image\nattribute\nnot unique", 'Red', False)
                elif len(values) == 1:
                    (valid, err_string) = image_attributes.is_valid_attribute(userdata, attribute, values[0])
                    if valid:
                        image_attributes.attributes[attribute] = values[0]
                    else:
                        graph_has_errors = True
                        parse_common.set_text_on_node(validation_output_graph, node, err_string, 'Red', False)

            self.image_attributes.append(image_attributes)

        return graph_has_errors

    def get_image_attributes(self, node_id):
        """ Get the image attributes for a node with specific id.
        :param node_id: The node id
        :return: The ImageAttributes object for the node or None if node has no image attributes set
        """
        for image_attributes in self.image_attributes:
            if image_attributes.node_id == node_id:
                return image_attributes

        return None

    def get_uniform_image_index(self, image_id):
        """Gets the list index in uniform_input_nodes_indexed_names for the image node with id = image_id."""
        try:
            return self.uniform_input_image_indexed_names.index(image_id)
        except:
            print "ERROR: function node is not in input function nodes list"
            raise


