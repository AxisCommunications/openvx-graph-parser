"""Image Format Checker Class
"""

import re #Module for regexp expressions
import parse_common

class ImageNodeFormatChecker:
    """Class that..."""
    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        #Processed image node lists for id and format
        #Will be populated after check_graph_image_formats has been called
        #Indexing is synched between the lists.
        self.PIN_ID = []
        self.PIN_FORMAT = []
        self.validation_output_graph = [None, None]

    # ========================================
    # Graph image format check related methods
    # ========================================
    def check_graph_image_formats(self, graph, image_nodes, function_nodes, library):
        """Parses the graph and checks that all function nodes' input and output image formats are consistent

        parse graph xml for all function nodes with id not on processed fkn nodes (PFN) list
        The code assumes the check that all input images have specified formats, has been done already
        The code also assumes that the number of input/output legs for the node is consistent with the node requirements
        (and thus the function node library)
        TODO: Add simple check that node_info contains input/output image node lists of correct length
        OBS when matching, need to match per In1/In2 and Out1/Out2 for multiple legs
        What about other formats than images, algo. should handle this as well...

        Return a tuple (has_errors, validation_output_graph)
        """
        self.validation_output_graph = graph.cloneNode(True)
        has_errors = False

        #Create processed image node [id,format] list and initialize Processed Function Nodes list (PFN)
        [PIN_ID, PIN_FORMAT, PFN] = self.create_processed_nodes_lists(graph, image_nodes)
        if self.debug_mode:
            print "Input node list: " + str(PIN_ID)

        unprocessed_function_node_found = True
        while unprocessed_function_node_found == True:
            unprocessed_function_node_found = False
            for node in graph.getElementsByTagName('node'):
                if self.node_is_unprocessed_function_node(node, PFN) and self.node_input_image_formats_fully_specified(function_nodes, node, PIN_ID):
                    if self.debug_mode:
                        print "\nPARSING NEW NODE*******************************************************************"
                    unprocessed_function_node_found = True
                    node_info = function_nodes.get_node_info(node)
                    PFN.append(node.attributes["id"].value)
                    input_image_specified_format_list = self.create_image_format_list_from_image_id_list(graph, image_nodes, node_info, PIN_ID, PIN_FORMAT)
                    output_image_specified_format_list = self.create_output_image_specified_format_list(graph, image_nodes, node_info)
                    valid_input_formats = library.VALID_INPUT_IMAGE_FORMATS.get(function_nodes.get_function_node_name(node), [[]])
                    valid_output_formats = library.VALID_OUTPUT_IMAGE_FORMATS.get(function_nodes.get_function_node_name(node), [[]])
                    [compatible_input_formats, compatible_output_formats, dim_check_ok] = self.create_compatible_io_lists(node, valid_input_formats, valid_output_formats, input_image_specified_format_list)

                    if not dim_check_ok:
                        has_errors = True
                        return has_errors, self.validation_output_graph

                    #Do this fkn call from inside the set fkn on the line below.
                    [explicit_format_list, virt_format_list] = self.separate_virt_from_explicit_formats(compatible_output_formats)
                    success = self.set_unique_output_image_format_list(graph, node_info, output_image_specified_format_list, virt_format_list, explicit_format_list, PIN_ID, PIN_FORMAT)

                    if success:
                        # Save the unique format lists for use when we generate the code
                        # with explicit image formats.
                        self.PIN_ID = PIN_ID
                        self.PIN_FORMAT = PIN_FORMAT
                    else:
                        # Stop and return if incompatible function node image formats found.
                        has_errors = True
                        return has_errors, self.validation_output_graph

                    if self.debug_mode:
                        print "NODE FULLY SPECIFIED. id = " + node.attributes["id"].value
                        print "node_info.input_image_node_ids = " + str(node_info.input_image_node_ids)
                        print "valid_input_formats" + str(valid_input_formats)
                        print "valid_output_formats" + str(valid_output_formats)

                        print "INPUT IMAGE SPECIFIED (by graph or previous parsing) FORMAT LIST = " + str(input_image_specified_format_list)
                        print "OUTPUT IMAGE SPECIFIED (by graph or previous parsing) FORMAT LIST = " + str(output_image_specified_format_list)
                        print "COMPATIBLE INPUT IMAGE FORMAT LIST = " + str(compatible_input_formats)
                        print "COMPATIBLE OUTPUT IMAGE FORMAT LIST = " + str(compatible_output_formats)
                        print "virt format list is: " + str(virt_format_list)
                        print "explicit format list is: " + str(explicit_format_list)

                        print "PIN_ID = " + str(PIN_ID)
                        print "PIN_FORMAT = " + str(PIN_FORMAT)

        return has_errors, self.validation_output_graph

    def create_processed_nodes_lists(self, graph, image_nodes):
        """Creates the initial Processed Image Nodes (PIN) lists

        PIN_ID contains the id numbers of the already processed image nodes.
        PIN_FORMAT contains the corresponding image format of the already processed
        image nodes contained in PIN_ID (with the same indexing)
        """
        PIN_ID = []
        PIN_FORMAT = []
        for item in image_nodes.input_nodes_indexed_names:
            node = self.get_node_with_id(graph, item)
            datatext = parse_common.get_node_datatext(node)
            image_format = self.get_image_format_from_datatext(datatext)
            parse_common.set_text_on_node(self.validation_output_graph, node, image_format, 'Green', False)
            PIN_ID.append(item)
            PIN_FORMAT.append(image_format)
            PFN = []


        for item in image_nodes.uniform_input_image_indexed_names:
            node = self.get_node_with_id(graph, item)
            datatext = parse_common.get_node_datatext(node)
            image_format = self.get_image_format_from_datatext(datatext)
            parse_common.set_text_on_node(self.validation_output_graph, node, image_format, 'Green', False)
            PIN_ID.append(item)
            PIN_FORMAT.append(image_format)
            PFN = []

        return [PIN_ID, PIN_FORMAT, PFN]

    def get_node_with_id(self, graph, node_id):
        """Returns the node with the id number specified in 'node_id'."""
        # TODO: Should probably move to parse_common
        nodes = []
        for node in graph.getElementsByTagName('node'):
            if node.attributes["id"].value == node_id:
                nodes.append(node)
        if len(nodes) != 1:
            raise NameError('Node id either missing or not unique.')
        else:
            return nodes[0]

    def get_image_format_from_datatext(self, datatext):
        """Extracts the substring containing an image format from the string 'datatext'

        Asssumes the image format is correctly formatted in the string,
        e.g. [vx_df_image_e VX_DF_IMAGE_U8] for an U8 image
        """
        image_format = "VIRT"
        temp = re.search('VX_DF_IMAGE_(.+?)\]', datatext)  #Obs. Needed to ecape the [ ]'s
        if temp:
            image_format = temp.group(1)
        return image_format

    def node_is_unprocessed_function_node(self, node, PFN):
        """Checks if a function node is currently unprocessed by the image format parser

        All processed function nodes are stored in the Processed Function Nodes (PFN) list.
        """
        unprocessed_function_node_found = False
        if node.attributes["id"].value not in PFN:
            node_appearance_list = node.getElementsByTagName('y:GenericNode')
            if len(node_appearance_list) > 0:
                node_appearance = node_appearance_list[0]
                if (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start1")\
                        or (node_appearance.attributes["configuration"].value == "com.yworks.flowchart.start2"):
                    unprocessed_function_node_found = True

        return unprocessed_function_node_found

    def node_input_image_formats_fully_specified(self, function_nodes, node, PIN_ID):
        """Checks if all input image formats for a function node are fully specified

        Returns True if the function node specified by 'node'
        has uniquely defined image formats, stored in the PIN_ID vector.
        """
        node_info = function_nodes.get_node_info(node)
        missing_input_format_spec = False
        for node_id in node_info.input_image_node_ids:
            #print "INPUT: " + node_id
            if node_id not in PIN_ID:
                missing_input_format_spec = True
                if self.debug_mode:
                    print "MISSING INPUT FOR NODE " + node.attributes["id"].value + " IS IMAGE NODE: " + node_id
        return not missing_input_format_spec

    def create_image_format_list_from_image_id_list(self, graph, image_nodes, node_info, PIN_ID, PIN_FORMAT):
        """Create list of in image formats as they are specified in the graph

        (Or as specified by the output from the
        previous function node if they are specified as Virt)
        If they are not specified in the graph,
        get_image_format_from_image_node_id should return the format as VIRT by default.
        """
        input_image_format_list = []
        for node_id in node_info.input_image_node_ids:
            input_image_format = self.get_image_format_from_image_node_id(graph, image_nodes, node_id)
            if self.debug_mode:
                print "INPUT IMAGE FORMAT = " + input_image_format
            if input_image_format == 'VIRT' and node_id in PIN_ID:
                input_image_format = PIN_FORMAT[PIN_ID.index(node_id)]
                if self.debug_mode:
                    print "MODIFIED INPUT IMAGE FORMAT = " + input_image_format
            input_image_format_list.append(input_image_format)

        return input_image_format_list

    def get_image_format_from_image_node_id(self, graph, image_nodes, node_id):
        """Returns the image format of the node specified by 'node_id'."""
        node = self.get_node_with_id(graph, node_id)
        datatext = parse_common.get_node_datatext(node)
        return self.get_image_format_from_datatext(datatext)

    def create_output_image_specified_format_list(self, graph, image_nodes, node_info):
        """Create list of output image formats as they are specified in the graph

        Uses VIRT for every image node that does not specify a format in the graph.
        """
        output_image_specified_format_list = []
        for node_id in node_info.output_image_node_ids:
            output_image_specified_format_list.append(self.get_image_format_from_image_node_id(graph, image_nodes, node_id))

        return output_image_specified_format_list

    def create_compatible_io_lists(self, node, valid_input_formats, valid_output_formats, input_image_format_list):
        """Creates the compatible io lists from the input_image_format_list

        It takes the list named valid_input_formats and picks out the compatible format list entries,
        meaning all the format entries that are identical to the input_image_format_list that
        contains the specified input image formats, either from the graph, or from parsing the previous nodes in the graph.
        The valid input formats are put in the list named compatible_input_formats.

        Then it selects the corresponding output format list entries from the list named valid_output_formats,
        and puts them in the list named compatible_output_formats. The indexing between the ntwo output lists is synched.

        There should only be one unique candidate if the graph is correct,
        or no candidate if the graph is inconsistent with respect to image formatting.

        TODO: Need to check order in1/in2? So far no nodes are like that. maybe need to order node info somehow?
        This will get more complicated if there are other node inputs than images.
        """
        dim_check_ok = True
        compatible_input_formats = []
        compatible_output_formats = []
        for idx, item in enumerate(valid_input_formats):
            if self.equal_ignore_order(input_image_format_list, item):
                compatible_input_formats.append(input_image_format_list)
                compatible_output_formats.append(valid_output_formats[idx])

        #Length checks for io image formats. output must have at least two entries, one explicit and one virtual.
        if len(compatible_input_formats) < 1:
            parse_common.set_text_on_node(self.validation_output_graph, node, "Input image format not valid.", 'Red', True)
            dim_check_ok = False
        elif len(compatible_output_formats) < 2:
            parse_common.set_text_on_node(self.validation_output_graph, node, "No compatible output image format found.", 'Red', True)
            dim_check_ok = False

        return [compatible_input_formats, compatible_output_formats, dim_check_ok]

    def equal_ignore_order(self, a, b):
        """Returns true if two lists contains the same elements, regardless of order."""
        unmatched = list(b)
        for element in a:
            try:
                unmatched.remove(element)
            except ValueError:
                return False
        return not unmatched

    def separate_virt_from_explicit_formats(self, compatible_output_formats):
        """Splits the entries of the list compatible_output_formats list into two separate lists

        virt_format_list contains all format lists with virtual entries
        (which map to some specified explicit format).
        explicit_format_list contains all format lists with explicit entries.
        """
        virt_format_list = []
        explicit_format_list = []
        for output_image_format in compatible_output_formats:
            if output_image_format[0][0] == 'V':
                virt_format_list.append(output_image_format)
            else:
                explicit_format_list.append(output_image_format)

        return [explicit_format_list, virt_format_list]

    def set_unique_output_image_format_list(self, graph, node_info, output_image_specified_format_list, virt_format_list, explicit_format_list, PIN_ID, PIN_FORMAT):
        """Sets the final unique output image format for each output image node of the node that generated 'node_info'

        The id's of the output images and their corresponding formats are stored
        in the Processed Imaged Nodes ID list (PIN_ID) and
        in the Processed Imaged Nodes format list (PIN_FORMAT) respectively.
        """
        success = True
        for idx, specified_image_format in enumerate(output_image_specified_format_list):
            image_node = self.get_node_with_id(graph, node_info.output_image_node_ids[idx])
            output_image_format = self.get_valid_output_format(idx, virt_format_list, explicit_format_list, specified_image_format)
            if output_image_format == "":
                parse_common.set_text_on_node(self.validation_output_graph, image_node, "Output image\nformat\n" + specified_image_format + "\nerror.", 'Red', False)
                success = False
            else:
                parse_common.set_text_on_node(self.validation_output_graph, image_node, output_image_format, 'Green', False)

            #Add format and image node id to processed lists.(indexing is the same as for the node_info still)
            if node_info.output_image_node_ids[idx] not in PIN_ID:
                PIN_ID.append(node_info.output_image_node_ids[idx])
                PIN_FORMAT.append(output_image_format)
            else:
                raise NameError('Duplicate ids in PIN_ID list.')

        return success

    def get_valid_output_format(self, idx, virt_format_list, explicit_format_list, specified_image_format):
        """Returns the definite output format for a given image node, based on the specified_image_format.

        Same indexing (idx) as for node info, so we can get the image id and write to that node.
        """
        output_image_format = ""
        if self.debug_mode:
            print "\nwanted output image format is: " + str(specified_image_format)
        if specified_image_format == "VIRT":
            virt_image_format = virt_format_list[0][idx] #Should be reduced to a unique list now (so we can index by 0)
            if self.debug_mode:
                print "output virt resulting image format is: " + virt_image_format
            output_image_format = virt_image_format.strip('VIRT->')
            if self.debug_mode:
                print "output image format is: " + output_image_format
        else:
            for image_format in explicit_format_list:
                if specified_image_format == image_format[idx]:
                    output_image_format = specified_image_format #Should be unique value in the list
            if self.debug_mode:
                print "(explicit) output image format is: " + str(output_image_format)

        return output_image_format
