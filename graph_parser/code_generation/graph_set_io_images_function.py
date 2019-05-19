"""Module for generating the set_io function for the graph definition C-sourcefile

"""

import graph_set_io_images_function_strip_io

def parse(graphparser):
    """Writes the graph set io function C-code

    First writes the boilerplate code for the image arrays, adressing structures etc.
    Then calls the GraphParser to write the set io function C-code

    """

    # Do not create this function if strip_mode since there is no graphmanager
    if graphparser.strip_mode:
        # Unless we run strip_io mode
        if graphparser.strip_io:
            return graph_set_io_images_function_strip_io.parse(graphparser)
        else:
            return ""

    # TODO:: VX_DF_IMAGE_U8 should be parsed in the 2 calls to vxCreateImageFromHandle
    parsed_string = """\

bool
%s_update_io_images(graphmanager_t *graph_manager, io_param_t *io_param)
{
    if (io_param->nbr_inputs != %s || io_param->nbr_outputs != %s) {
        ERR(\"INVALID NUMBER OF IO IMAGES!!!\");
        return false;
    }

    vx_image *input_images = graphmanager_get_input_nodes(graph_manager);
    vx_image *output_images = graphmanager_get_output_nodes(graph_manager);

    int num_errors = 0;
    int i;
    for (i = 0; i < io_param->nbr_inputs; i++) {
        // TODO: Implement image setters here
    }
    for (i = 0; i < io_param->nbr_outputs; i++) {
        // TODO: Implement image setters here
    }

    bool success = (num_errors == 0);
    return success;
}
""" % (graphparser.graphname, str(graphparser.image_nodes.nbr_input_images),
       str(graphparser.image_nodes.nbr_output_images))

    return parsed_string
