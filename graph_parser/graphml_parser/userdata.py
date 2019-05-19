"""Userdata class"""

import parse_common

class Userdata:
    """ Class for handling the special userdata node for adding custom attributes to graph creation.
    NOTE: The userdata attributes are assumed to be specified on separate lines in the userdata node's data field.
    Example of userdata node data field:
    [unsigned ref_width]
    [int ref_height]'
    """

    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.has_userdata = False
        self.attributes_populated = False
        # A dictionary containing userdata attributes with names as keys and types as values
        self.attributes = {}

    def populate_userdata(self, graph, validation_output_graph):
        """ Populates the userdata attributes dictionary """
        graph_has_errors = False

        userdata_node = None
        datatext = ""
        for node in graph.getElementsByTagName('node'):
            for nodeAppearance in node.getElementsByTagName('y:GenericNode'):
                if nodeAppearance.attributes["configuration"].value == "com.yworks.flowchart.userMessage":
                    if self.has_userdata:
                        print "ERROR: Found multiple userdata nodes, only one is allowed"
                        graph_has_errors = True
                        parse_common.set_text_on_node(validation_output_graph, node,
                                                      "Userdata\nis not\nunique", 'Red', True)
                    else:
                        self.has_userdata = True
                        userdata_node = node
                        datatext = parse_common.get_node_datatext(node)

        if self.debug_mode:
            print "userdata node contains data:\n", datatext, "\n"

        for attribute in datatext.splitlines():
            try:
                data_type, attribute_name = attribute.lstrip('[').rstrip(']').split()
            except ValueError:
                print "ERROR: userdata node data is not formatted correctly at: {}".format(attribute)
                graph_has_errors = True
                parse_common.set_text_on_node(validation_output_graph, userdata_node,
                                              "Userdata\nnot\nformatted\ncorrectly", 'Red', True)
            else:
                if attribute_name in self.attributes:
                    print "ERROR: userdata cannot contain several entries with same name"
                    graph_has_errors = True
                    parse_common.set_text_on_node(validation_output_graph, userdata_node,
                                                  "Userdata\nhas\nnon-unique\nentries", 'Red', True)
                else:  # Add attribute to userdata
                    # TODO: Should add check that attribute_name is valid C-variable name
                    self.attributes[attribute_name] = data_type

        self.attributes_populated = True
        return graph_has_errors
