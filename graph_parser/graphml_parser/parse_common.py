"""Common node-related functions

"""

def set_text_on_node(graph, current_node, errorstring, highlight_color, resize):
    """Sets an error string on the current_node in graph.

    Also changes the color to red to highlight it.

    The parameter current_node should come from the graph that was parsed from file,
    but errors are written on the corresponding node on a validation/error graph,
    which was cloned from the original graph during initialization of the GraphParser.
    """
    for node in graph.getElementsByTagName('node'):
        if node.attributes["id"].value == current_node.attributes["id"].value:
            node.getElementsByTagName(
                'y:NodeLabel')[0].firstChild.replaceWholeText(errorstring)

            if highlight_color == 'Red':
                node.getElementsByTagName(
                    'y:Fill')[0].attributes["color"].value = "#FF9090"
                node.getElementsByTagName(
                    'y:Fill')[0].attributes["color2"].value = "#CC0000"
            elif highlight_color == 'Green':
                node.getElementsByTagName(
                    'y:Fill')[0].attributes["color"].value = "#90FF90"
                node.getElementsByTagName(
                    'y:Fill')[0].attributes["color2"].value = "#008800"
            if resize == True:
                old_width = node.getElementsByTagName(
                    'y:Geometry')[0].attributes["width"].value
                new_width = len(errorstring * 5) + 80
                node.getElementsByTagName(
                    'y:Geometry')[0].attributes["width"].value = str(new_width)
                old_x = node.getElementsByTagName(
                    'y:Geometry')[0].attributes["x"].value
                node.getElementsByTagName('y:Geometry')[0].attributes["x"].value = str(
                    float(old_x) - (new_width - float(old_width)) / 2)

def get_node_datatext(node):
    """Returns a string with data node text if it exists on the node, otherwise returns an empty string"""
    datatext = ""
    if node.attributes["id"].value:
        for data_node in node.getElementsByTagName('data'):
            if data_node.attributes["key"].value == "d5":
                if data_node.firstChild:
                    datatext = data_node.firstChild.wholeText

    return datatext

def parse_parameter(parameter, node):
    """Creates a C-code function node parameter

    Searches for a parameter that matches the given type in parameter.
    The first occurence found will be used. If the function node creation function has multiple
    parameters of the given type, deep_parse_parameter must be called.

    If no parameter of correct type is found the function returns an empty string.
    """
    parameter_value = ""

    data_nodes = node.getElementsByTagName('data')
    for data_node in data_nodes:
        if data_node and data_node.attributes["key"].value == "d5":
            if data_node.firstChild:
                datatext = data_node.firstChild.wholeText
                parameter = "[" + parameter #Parameters should start with a [ character
                if parameter in datatext:
                    datatext_after_parameter = datatext.split(parameter, 1)[1]
                    parameter_value = (datatext_after_parameter.split("]", 1)[0]).strip()

    return parameter_value
