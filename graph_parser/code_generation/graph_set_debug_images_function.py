"""Module for generating the set_debug_images function for the graph definition C-sourcefile

"""

def create_set_debug_images_function(graphparser):
    """Writes the graph set debug images function C-code

    First writes the boilerplate code for the image arrays, adressing structures etc.
    Then calls the GraphParser to write the set io function C-code

    OBS: This function is used for debugging purposes during algorithm development only.
    No image format checking is done. The user must keep trackl of this manually
    """

    # TODO:: VX_DF_IMAGE_U8 should be parsed in the 2 calls to vxCreateImageFromHandle
    parsed_string = """\

bool
%s_set_debug_images(graphmanager_t *graph_manager, debug_param_t *debug_param)
{
    if (debug_param->nbr_images != %s) {
        INFO(\"INVALID NUMBER OF IO IMAGES!!!\");
        return false;
    }

    bool success = false;

    vx_image debug_images[debug_param->nbr_images];
    int i;
    for (i = 0; i < debug_param->nbr_images; i++) {
        debug_images[i] = graphmanager_create_vxu8_from_avu8(graph_manager, debug_param->debug_images[i]);
    }

    node_rc_t **debug_input_nodes = graphmanager_get_debug_input_nodes(graph_manager);
    node_rc_t **debug_output_nodes = graphmanager_get_debug_output_nodes(graph_manager);

""" % (graphparser.graphname, str(len(graphparser.image_nodes.debug_nodes_indexed_names)))

    #Fetch index structures for the vxSetParameterByIndex function calls to set new I/O images
    #and generate the C function calls.
    set_debug_images_string = ""

    index_lists = graphparser.function_nodes.get_index_lists_for_io_function_nodes('debug_input', graphparser.image_nodes)
    debug_input_nodes_array_index_list = index_lists.function_nodes_index_list #The index of the function node to set an image on (function nodes listed in an array)
    debug_input_nodes_image_index_list = index_lists.function_param_index_list #The index of where to set the new image on a function node
    debug_input_images_array_index_list = index_lists.images_nodes_index_list #The index of the debug image to set on the function node (images listed in an array)
    for idx, val in enumerate(debug_input_nodes_array_index_list):
        set_debug_images_string += "    vxSetParameterByIndex(debug_input_nodes[" + str(
                                debug_input_nodes_array_index_list[idx]) + "]->vxnode, "
        set_debug_images_string += str( debug_input_nodes_image_index_list[idx]) + ", (vx_reference) debug_images[" + str(
                                debug_input_images_array_index_list[idx]) + "]);\n"

    index_lists = graphparser.function_nodes.get_index_lists_for_io_function_nodes('debug_output', graphparser.image_nodes)
    debug_output_nodes_array_index_list = index_lists.function_nodes_index_list
    debug_output_nodes_image_index_list = index_lists.function_param_index_list
    debug_output_images_array_index_list = index_lists.images_nodes_index_list
    for idx, val in enumerate(debug_output_nodes_array_index_list):
        set_debug_images_string += "    vxSetParameterByIndex(debug_output_nodes[" + str(
                                debug_output_nodes_array_index_list[idx]) + "]->vxnode, "
        set_debug_images_string += str( debug_output_nodes_image_index_list[idx]) + ", (vx_reference) debug_images[" + str(
                                debug_output_images_array_index_list[idx]) + "]);\n"

    parsed_string += set_debug_images_string

    parsed_string += """\

    for (i = 0; i < debug_param->nbr_images; i++) {
        vxReleaseImage(&debug_images[i]);
    }

    return success;\n}
"""

    return parsed_string

def parse(graphparser):
    parsed_string = ""
    if len(graphparser.image_nodes.debug_nodes_indexed_names) > 0 and not graphparser.strip_mode:
        parsed_string += create_set_debug_images_function(graphparser)

    return parsed_string
