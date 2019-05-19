"""Function Nodes Class
"""

from xml.dom import minidom
import logging

class NodeInfo:
    """Class that contains information about the neighborhood of a given node.

    input_image_node_ids and output_image_node_ids contain the image node ids
    in the order they were parsed when parsing parameters for a specific node.

    input_edge_labels and output_edge_labels contain the label names in the order they were parsed
    when parsing parameters for a specific node.

    They are used to get the correct input image ordering in the parameter list of the node-creating C-functions.
    """

    def __init__(self):
        self.input_edge_labels = []
        self.output_edge_labels = []
        self.input_image_node_ids = []
        self.output_image_node_ids = []

class IndexLists:
    """Class that is used to store synched index lists used to set new I/O and debug images using vxSetParameterByIndex.

    function_nodes_index_list contains the array indices of the function nodes
    that has an image node that should be swapped for a new image.

    function_param_index_list contains the parameter indices for the image nodes to be swapped.

    images_nodes_index_list contains the array indices of the image nodes to be set
    (stored in the respective image nodes array in the c code).
    """

    def __init__(self):
        self.function_nodes_index_list = []
        self.function_param_index_list = []
        self.images_nodes_index_list = []

    def append_to_index_lists(self, function_node_array_index, function_node_param_index, image_node_array_index):
        self.function_nodes_index_list.append(function_node_array_index)
        self.function_param_index_list.append(function_node_param_index)
        self.images_nodes_index_list.append(image_node_array_index)

class FunctionNodes:
    """Class that contains information about the different types of function nodes."""

    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.lists_populated = False

        # The indices between these 3 lists are synched.
        # They contain information about all function nodes
        # and corresponding node_info objects.
        self.indexed_node_info_list = []
        self.indexed_function_nodes = []
        self.function_nodes_indexed_names = []

        # These lists contain the function nodes that have
        # at least one graph input/output image respectively
        # Indexed in the setup of the graph_create function
        # (through call to shared.appendNodeInfo),
        # and used by the set_io functions (setInputImagesOnInputFunctionNode
        # and setOutputImagesOnOutputFunctionNode). These lists have synched indices
        # so an indexed name maps to a FirstInputIndex and FirstOutputIndex respectively
        # and their list indices is synched with the C-array indices defined
        # in the graph_create function
        self.input_function_nodes_indexed_names = []
        self.input_function_nodes_first_input_index = []
        self.output_function_nodes_indexed_names = []
        # Output images can be input to a function node so we need an extra list for this
        self.output_function_nodes_first_output_index = []
        self.output_function_nodes_first_input_index = []

        # Same indexing as for input/putput images above, but for debug nodes instead.
        # This may be confusing,
        # but the function node that takes output from the image node, has the image as an input index.
        # and vice versa.
        self.debug_input_function_nodes_indexed_names = []
        self.debug_input_function_nodes_first_output_index = []
        self.debug_output_function_nodes_indexed_names = []
        self.debug_output_function_nodes_first_input_index = []

        #List of 2-element lists containing a function node its corresponding parameter index for
        #the dynamic parameters (that can be changed between each graph execution)
        self.dynamic_nodes_info = []

        # Caching of the previous NodeInfo from get_node_info(), for performance reasons
        self.node_info = NodeInfo()
        self.current_node = minidom.Node()

    def populate_function_nodes_indexed_lists(self, graph, library, image_nodes):
        """Populates the lists related to function nodes and creates associated node_info objects"""
        for node in graph.getElementsByTagName('node'):  # visit every node <node />
            for node_appearance in node.getElementsByTagName('y:GenericNode'):  #TODO:: Change to if?
                if (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start1")\
                        or (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start2"):
                    self.indexed_node_info_list.append(self.create_node_info(graph, node))
                    self.indexed_function_nodes.append(node)
                    function_name = node.getElementsByTagName('y:NodeLabel')[0].firstChild.wholeText
                    self.function_nodes_indexed_names.append(function_name)
                    self.populate_io_function_node_indexed_lists(library.FIRST_INPUT_IMAGE_INDEX_DICT.get(function_name, -999) ,
                                                                 library.FIRST_OUTPUT_IMAGE_INDEX_DICT.get(function_name, -999) ,
                                                                 node, image_nodes) #Only happens if it is an I/O node
                    self.populate_debug_function_node_indexed_lists(library.FIRST_INPUT_IMAGE_INDEX_DICT.get(function_name, -999) ,
                                                                 library.FIRST_OUTPUT_IMAGE_INDEX_DICT.get(function_name, -999) ,
                                                                 node, image_nodes) #Only happens if it is an I/O node

        #Dynamic nodes info is dependent of that self.indexed_function_nodes
        #and self.function_nodes_indexed_names exists
        self.populate_dynamic_function_nodes_list(graph, library)
        self.lists_populated = True

    def populate_io_function_node_indexed_lists(self, first_input_index, first_output_index, current_node, image_nodes):
        """Appends information about function node id and I/O indexing structure to global I/O list

        Any node that is connected to at least one graph input or output image is added to this list
        It is used when defining the indexing for how to set new I/O images
        in the graph_set_io_function.py module.
        This list is not graph array index ordered,
        but e.g. the input_function_nodes_indexed_names, input_function_nodes_first_input_index indices are coupled
        """
        node_info = self.get_node_info(current_node)
        if any(e in node_info.input_image_node_ids for e in image_nodes.input_nodes_indexed_names):
            self.input_function_nodes_indexed_names.append(current_node.attributes["id"].value)
            self.input_function_nodes_first_input_index.append(first_input_index)

        # Handles when an output image is input to a function node ("in the middle of the graph"),
        # E.g. if first_output_index is 'None' then this function node has an output image as input but not as output
        if any(e in node_info.output_image_node_ids + node_info.input_image_node_ids
               for e in image_nodes.output_nodes_indexed_names):

            self.output_function_nodes_indexed_names.append(current_node.attributes["id"].value)
            if any(e in node_info.output_image_node_ids for e in image_nodes.output_nodes_indexed_names):
                self.output_function_nodes_first_output_index.append(first_output_index)
            else:
                self.output_function_nodes_first_output_index.append(None)

            if any(e in node_info.input_image_node_ids for e in image_nodes.output_nodes_indexed_names):
                self.output_function_nodes_first_input_index.append(first_input_index)
            else:
                self.output_function_nodes_first_input_index.append(None)

    def populate_debug_function_node_indexed_lists(self, first_input_index, first_output_index, current_node, image_nodes):
        """Appends information about function node id and I/O indexing structure to global debug function node list

        Any node that is connected to at least one graph debug image is added to this list
        It is used when defining the indexing for how to set new I/O images
        in the graph_set_debug_function.py module.
        This list is not graph array index ordered,
        but e.g. the debug_input_function_nodes_indexed_names, debug_input_function_nodes_first_output_index indices are coupled
        """
        node_info = self.get_node_info(current_node)
        #if debug image node is input to fkn node
        if any(e in node_info.input_image_node_ids for e in image_nodes.debug_nodes_indexed_names):
            #Add fkn node to debug function nodes list
            self.debug_output_function_nodes_indexed_names.append(current_node.attributes["id"].value)
            #This may be confusing, but the function node that takes output from the image node, has the image as an input index.
            self.debug_output_function_nodes_first_input_index.append(first_input_index)

        #if debug image node is output to fkn node
        if any(e in node_info.output_image_node_ids for e in image_nodes.debug_nodes_indexed_names):
            #Add fkn node to debug function nodes list
            self.debug_input_function_nodes_indexed_names.append(current_node.attributes["id"].value)
            #This may be confusing, but the function node that gives input to the image node, has the image as an output index.
            self.debug_input_function_nodes_first_output_index.append(first_output_index)

    # =========================================
    # Function node information related methods
    # =========================================
    def get_function_node_name(self, node):
        """Returns the function node name of the node given by 'node'."""
        try:
            return self.function_nodes_indexed_names[self.indexed_function_nodes.index(node)]
        except IndexError:
            print "ERROR: The class function_nodes has function node lists that are out of sync!"
            raise

    def get_input_function_node_index(self, current_node):
        """Gets the list index in input_function_nodes_indexed_names for current_node."""
        try:
            return self.input_function_nodes_indexed_names.index(current_node.attributes["id"].value)
        except:
            print "ERROR: function node is not in input function nodes list"
            raise

    def get_output_function_node_index(self, current_node):
        """Gets the list index in output_function_nodes_indexed_names for current_node."""
        try:
            return self.output_function_nodes_indexed_names.index(
                                        current_node.attributes["id"].value)
        except:
            print "ERROR: function node is not in output function nodes list"
            raise

    def get_debug_input_function_node_index(self, current_node):
        """Gets the list index in debug_input_function_nodes_indexed_names for current_node."""
        try:
            return self.debug_input_function_nodes_indexed_names.index(
                                        current_node.attributes["id"].value)
        except:
            print "ERROR: function node is not in debug input function nodes list"
            raise

    def get_debug_output_function_node_index(self, current_node):
        """Gets the list index in debug_output_function_nodes_indexed_names for current_node."""
        try:
            return self.debug_output_function_nodes_indexed_names.index(
                                        current_node.attributes["id"].value)
        except:
            print "ERROR: function node is not in debug output function nodes list"
            raise

    def create_node_info(self, graph, current_node):
        """Generates information about edges linked to current_node and the nearest neighbor nodes."""
        #If current_node has changed, clear node_info and generate new data
        if self.current_node != current_node:
            self.current_node = current_node
            self.node_info = NodeInfo()

            # Check all edges in the graph, to see if they are connected to the
            # current node
            for edge in graph.getElementsByTagName('edge'):

                # Also avoid closed loops (a bug causes these to appear in the XML
                # sometimes)
                if edge.attributes["source"].value != edge.attributes["target"].value:

                    if edge.attributes["target"].value == current_node.attributes["id"].value:

                        # ID for the data node of an edge that ends in the current
                        # function node is added to the indexed list
                        self.node_info.input_image_node_ids.append(
                            edge.attributes["source"].value)

                        # Check if there is a label on any of the input edges (used for
                        # ordering the input arguments)
                        if edge.getElementsByTagName('y:EdgeLabel'):
                            self.node_info.input_edge_labels.append(
                                edge.getElementsByTagName('y:EdgeLabel')[0].firstChild.wholeText)
                        else:
                            self.node_info.input_edge_labels.append("NO_LABEL")

                    if edge.attributes["source"].value == current_node.attributes["id"].value:

                        # ID for the data node of an edge that starts at the current
                        # function node is added to the indexed list
                        self.node_info.output_image_node_ids.append(
                            edge.attributes["target"].value)

                        # Check if there is a label on any of the output edges (used
                        # for ordering the output arguments)
                        if edge.getElementsByTagName('y:EdgeLabel'):
                            self.node_info.output_edge_labels.append(
                                edge.getElementsByTagName('y:EdgeLabel')[0].firstChild.wholeText)
                        else:
                            self.node_info.output_edge_labels.append("NO_LABEL")

        return self.node_info

    def get_node_info(self, current_node):
        """Returns the node_info object for current_node

        Assumes self.populate_function_nodes_indexed_lists() has been called prior to
        using this function
        """
        if current_node in self.indexed_function_nodes:
            return self.indexed_node_info_list[self.indexed_function_nodes.index(current_node)]
        else:
            print "ERROR: function node has no associated node_info object"
            return NodeInfo() #Return empty info object

    def verify_labels(self, node_info):
        success = True
        if len(node_info.input_edge_labels) == 2:
           if not ('in1' in node_info.input_edge_labels and 'in2' in node_info.input_edge_labels):
               success = False
        if len(node_info.output_edge_labels) == 2:
           if not ('out1' in node_info.output_edge_labels and 'out2' in node_info.output_edge_labels):
               success = False

        return success


    def get_index_lists_for_io_function_nodes(self, io_string, image_nodes):
        """Prepares a list of index lists used to set input or output images on I/O function nodes.

        Handles both function nodes connected to "ordinary" input/output images,
        and function nodes connected to debug image nodes, depending on the value of "io_string".

        Meant to be consistent with the function vxSetParameterByIndex
        which requires
        1: An input or output image as first parameter
        2: the parameter index for the image in question, attached to the function node, so that it can be replaced.
        3: the new image to be set on the function node.

        The return value is an IndexLists class object with index lists for all input or output nodes
        (depending on the value of io_string)
        assuming the function nodes are arranged in an array consistent with the internal indexing of the
        input (or output) function nodes in the graph parser,
        and similar indexing for the image array to be used as new images when I/O graph images are swapped.

        If an error with the labeling of function node inputs and/or outputs is detected, an empty IndexLists object is returned.
        """
        if(io_string == 'input' or io_string == 'output' or io_string == 'debug_input' or io_string == 'debug_output'):
            index_lists = IndexLists()
            input_labels = ['in1', 'in2']
            output_labels = ['out1', 'out2']
            for current_node in self.indexed_function_nodes:
                node_info = self.get_node_info(current_node)
                if not self.verify_labels(node_info):
                    logging.warning('WARNING: node_info label lists out of synch.')
                    return IndexLists()

                if (io_string == 'input'):
                    if len(node_info.input_edge_labels) == 1:
                        if node_info.input_image_node_ids[0] in image_nodes.input_nodes_indexed_names:
                            function_node_index = self.get_input_function_node_index(current_node)
                            first_input_index = self.input_function_nodes_first_input_index[function_node_index]
                            image_index = image_nodes.input_nodes_indexed_names.index(node_info.input_image_node_ids[0])
                            index_lists.append_to_index_lists(function_node_index, first_input_index, image_index)
                    elif len(node_info.input_edge_labels) == 2:
                        for label_index, label in enumerate(input_labels):
                            image_id = node_info.input_image_node_ids[node_info.input_edge_labels.index(label)]
                            if image_id in image_nodes.input_nodes_indexed_names:
                                function_node_index = self.get_input_function_node_index(current_node)
                                first_input_index = self.input_function_nodes_first_input_index[function_node_index]
                                image_index = image_nodes.input_nodes_indexed_names.index(image_id)
                                index_lists.append_to_index_lists(function_node_index, first_input_index + label_index, image_index)

                    if len(node_info.output_edge_labels) == 1:
                        if node_info.output_image_node_ids[0] in image_nodes.input_nodes_indexed_names:
                            raise ValueError('Graph input image can not be output image to a function node.')
                elif(io_string == 'output'):
                    if len(node_info.input_edge_labels) == 1:
                        if node_info.input_image_node_ids[0] in image_nodes.output_nodes_indexed_names:
                            function_node_index = self.get_output_function_node_index(current_node)
                            first_input_index = self.output_function_nodes_first_input_index[function_node_index]
                            image_index = image_nodes.output_nodes_indexed_names.index(node_info.input_image_node_ids[0])
                            index_lists.append_to_index_lists(function_node_index, first_input_index, image_index)

                    elif len(node_info.input_edge_labels) == 2:
                        for label_index, label in enumerate(input_labels):
                            image_id_out = node_info.input_image_node_ids[node_info.input_edge_labels.index(label)]
                            if image_id_out in image_nodes.output_nodes_indexed_names:
                                function_node_index = self.get_output_function_node_index(current_node)
                                first_input_index = self.output_function_nodes_first_input_index[function_node_index]
                                image_index = image_nodes.output_nodes_indexed_names.index(image_id_out)
                                index_lists.append_to_index_lists(function_node_index, first_input_index + label_index, image_index)

                    if len(node_info.output_edge_labels) == 1:
                        if node_info.output_image_node_ids[0] in image_nodes.output_nodes_indexed_names:
                            function_node_index = self.get_output_function_node_index(current_node)
                            first_output_index = self.output_function_nodes_first_output_index[function_node_index]
                            image_index = image_nodes.output_nodes_indexed_names.index(node_info.output_image_node_ids[0])
                            index_lists.append_to_index_lists(function_node_index, first_output_index, image_index)

                    elif len(node_info.output_edge_labels) == 2:
                        for label_index, label in enumerate(output_labels):
                            image_id_out = node_info.output_image_node_ids[node_info.output_edge_labels.index(label)]
                            if image_id_out in image_nodes.output_nodes_indexed_names:
                                function_node_index = self.get_output_function_node_index(current_node)
                                first_output_index = self.output_function_nodes_first_output_index[function_node_index]
                                image_index = image_nodes.output_nodes_indexed_names.index(image_id_out)
                                index_lists.append_to_index_lists(function_node_index, first_output_index + label_index, image_index)

                #This may be confusing, but the function node that takes output from the image node, has the image as an input index.
                elif io_string == 'debug_input':
                    if len(node_info.output_image_node_ids) == 1:
                        if node_info.output_image_node_ids[0] in image_nodes.debug_nodes_indexed_names:
                            function_node_index = self.get_debug_input_function_node_index(current_node)
                            first_output_index = self.debug_input_function_nodes_first_output_index[function_node_index]
                            image_index = image_nodes.debug_nodes_indexed_names.index(node_info.output_image_node_ids[0])
                            index_lists.append_to_index_lists(function_node_index, first_output_index, image_index)

                    elif len(node_info.output_image_node_ids) == 2:
                        for label_index, label in enumerate(output_labels):
                            image_id_out = node_info.output_image_node_ids[node_info.output_edge_labels.index(label)]
                            if image_id_out in image_nodes.debug_nodes_indexed_names:
                                function_node_index = self.get_debug_input_function_node_index(current_node)
                                first_output_index = self.debug_input_function_nodes_first_output_index[function_node_index]
                                image_index = image_nodes.debug_nodes_indexed_names.index(image_id_out)
                                index_lists.append_to_index_lists(function_node_index, first_output_index + label_index, image_index)

                elif io_string == 'debug_output':
                    if len(node_info.input_image_node_ids) == 1:
                        if node_info.input_image_node_ids[0] in image_nodes.debug_nodes_indexed_names:
                            function_node_index = self.get_debug_output_function_node_index(current_node)
                            first_input_index = self.debug_output_function_nodes_first_input_index[function_node_index]
                            image_index = image_nodes.debug_nodes_indexed_names.index(node_info.input_image_node_ids[0])
                            index_lists.append_to_index_lists(function_node_index, first_input_index, image_index)

                    elif len(node_info.input_image_node_ids) == 2:
                        for label_index, label in enumerate(input_labels):
                            image_id_in = node_info.input_image_node_ids[node_info.input_edge_labels.index(label)]
                            if image_id_in in image_nodes.debug_nodes_indexed_names:
                                function_node_index = self.get_debug_output_function_node_index(current_node)
                                first_input_index = self.debug_output_function_nodes_first_input_index[function_node_index]
                                image_index = image_nodes.debug_nodes_indexed_names.index(image_id_in)
                                index_lists.append_to_index_lists(function_node_index, first_input_index + label_index, image_index)

            return index_lists

        else:
            raise NameError('Input parameter io_string not a defined io_string.')

    def populate_dynamic_function_nodes_list(self, graph, library):
        """Creates and returns a list with nodes that have dynamic parameter and the corresponding parameter index on the node.

        List needs to be ordered with increasing indices as they are indicated in the graph definition,
        so that the developer can use the same indexing when he sets new parameter values on the graph
        """
        #Count how many dynamic parameters there are in the graph.
        #Also count multiple occurences in a single node.
        nbr_dynamic_nodes = 0;
        for node in graph.getElementsByTagName('node'):
            parameter_list = self.deep_parse_parameter("dynamic_type", node)
            nbr_dynamic_nodes += len(parameter_list)
        dynamic_nodes_debug_info = []

        #then search by index order for increasing values of the param index and put in list
        for idx in range(0, nbr_dynamic_nodes): #By index order
            for node in graph.getElementsByTagName('node'): #Check every node
                for node_appearance in node.getElementsByTagName('y:GenericNode'):  #Check only function nodes #TODO:: Change to if?
                    if (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start1")\
                            or (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start2"):
                        parameter_list = self.deep_parse_parameter("dynamic_type", node)
                        for parameter in parameter_list:
                            index_list = (parameter.split("[",1))
                            if(len(index_list) == 2):
                                dynamic_param_name = index_list[0]
                                dynamic_param_index = index_list[1].strip()

                                if int(dynamic_param_index) == idx:
                                    function_node_name = self.get_function_node_name(node)
                                    #Parse dynamic parameter name and corresponding index (as def. by the standard)
                                    parameter_names = library.PARAMETER_NAMES_DICT.get(function_node_name, [])
                                    parameter_name_index = parameter_names.index(dynamic_param_name)
                                    dynamic_param_index = library.PARAMETER_INDICES_DICT.get(function_node_name, [])[parameter_name_index]

                                    #Append a list with the node and the parameter index
                                    #for the parameter to be dynamic (changeable from outside)
                                    #Appending is done according to index order in the graph,
                                    #i.e. the index in [dynamic_type vx_typename[index]]
                                    self.dynamic_nodes_info.append([node, int(dynamic_param_index)])
                                    dynamic_nodes_debug_info.append([function_node_name, "id = " + node.attributes["id"].value, dynamic_param_name, int(dynamic_param_index)])

        #print "DYNAMIC_NODES_DEBUG_LIST = " + str(dynamic_nodes_debug_info)
        #print "DYNAMIC_NODES_LIST = " + str(self.dynamic_nodes_info)
        return self.dynamic_nodes_info

    def deep_parse_parameter(self, parameter, node):
        """Returns the values of all occurrences of a function node parameter

        Searches for a parameter that matches the given type in parameter.
        The values of all occurences found will be returned in a list.

        If no parameter of correct type is found the function returns an empty string.
        """
        parameter_values = []

        # TODO: Should use parse_common.get_node_datatext as helper function
        data_node = node.getElementsByTagName('data')[0] #Only first occurence used
        if data_node and data_node.attributes["key"].value == "d5":
            if data_node.firstChild:
                datatext = data_node.firstChild.wholeText
                parameter = "[" + parameter #Parameters should start with a [ character
                keep_parsing = True
                while keep_parsing:
                    if parameter in datatext:
                        datatext = datatext.split(parameter, 1)[1] #Keep string after the substring parameter
                        parameter_values.append((datatext.split("]", 1)[0]).strip()) #Split in 2 parts and store the 1:st part
                    else:
                        keep_parsing = False
        return parameter_values
