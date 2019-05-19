"""Module for generating the set_io function for the graph definition C-sourcefile

"""

def parse(graphparser):
    """Writes the graph set io function C-code in strip mode"""

    graphname = graphparser.graphname
    graphname_strip = graphname + "_strip"
    num_input_imgs = len(graphparser.image_nodes.input_nodes_indexed_names)
    num_output_imgs = len(graphparser.image_nodes.output_nodes_indexed_names)
    parsed_string = """\

bool
%s_io_set_imgs(vx_image input_images[%s], vx_image output_images[%s], %s_io_nodes_t *io_nodes)
{
    bool success = false;
    int num_errors = 0;
    vx_node *input_nodes = io_nodes->input_nodes;
    vx_node *output_nodes = io_nodes->output_nodes;
    vx_status status;

""" % (graphname_strip, num_input_imgs, num_output_imgs, graphname_strip)

    #Fetch index structures for the vxSetParameterByIndex function calls to set new I/O images
    #and generate the C function calls.
    set_io_images_string = ""
    index_lists = graphparser.function_nodes.get_index_lists_for_io_function_nodes('input', graphparser.image_nodes)
    input_nodes_array_index_list = index_lists.function_nodes_index_list
    input_nodes_image_index_list = index_lists.function_param_index_list
    input_images_array_index_list = index_lists.images_nodes_index_list
    for idx, val in enumerate(input_nodes_array_index_list):
        node_idx_str = str(input_nodes_array_index_list[idx])
        param_idx_str = str(input_nodes_image_index_list[idx])
        img_idx_str = str(input_images_array_index_list[idx])
        set_io_images_string += "    status = vxSetParameterByIndex(input_nodes[" + node_idx_str + "], "
        set_io_images_string += param_idx_str + ", (vx_reference) input_images[" + img_idx_str + "]);\n"
        set_io_images_string += "    if (status != VX_SUCCESS) {"
        set_io_images_string += " fprintf(stderr, \"Failed to set input image #" + img_idx_str + \
                                " on input node #" + node_idx_str + "\\n\");"
        set_io_images_string += " num_errors++;"
        set_io_images_string += " }\n\n"

    index_lists = graphparser.function_nodes.get_index_lists_for_io_function_nodes('output', graphparser.image_nodes)
    output_nodes_array_index_list = index_lists.function_nodes_index_list #index in graph output nodes array (which function node)
    output_nodes_image_index_list = index_lists.function_param_index_list # param index in function node (where to set the image)
    output_images_array_index_list = index_lists.images_nodes_index_list #index in output images array (which image to set)
    for idx, val in enumerate(output_nodes_array_index_list):
        node_idx_str = str(output_nodes_array_index_list[idx])
        param_idx_str = str(output_nodes_image_index_list[idx])
        img_idx_str = str(output_images_array_index_list[idx])
        set_io_images_string += "    status = vxSetParameterByIndex(output_nodes[" + node_idx_str + "], "
        set_io_images_string += param_idx_str + ", (vx_reference) output_images[" + img_idx_str + "]);"
        set_io_images_string += " if (status != VX_SUCCESS) {"
        set_io_images_string += " fprintf(stderr, \"Failed to set output image #" + img_idx_str + \
                                " on output node #" + node_idx_str + "\\n\");"
        set_io_images_string += " num_errors++;"
        set_io_images_string += " }\n\n"

    parsed_string += set_io_images_string

    parsed_string += """\
    success = (num_errors == 0);
    return success;\n}
"""

    return parsed_string
