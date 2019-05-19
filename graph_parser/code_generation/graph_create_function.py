"""Module for generating the create graph function for the graph definition C-sourcefile

"""
from node_parse_info import function_node_library
from graphml_parser import graphml_parser
import graph_create_function_strip

def function_beginning(graphparser):
    """ Writes the very beginning of the create function, i.e. prototype and vxCreateGraph"""
    parsed_string = """\
bool
%s_create(graphmanager_t *graph_manager, graphmanager_nodes_t *nodes, io_param_t *io_param, void *userdata)
{
    if (!graph_manager || !nodes || !io_param ||
        io_param->nbr_inputs != %s || io_param->nbr_outputs != %s) {
        ERR(\"Invalid params.\");
        return false;
    }

    vx_graph graph_skeleton = graphmanager_get_graph(graph_manager);

""" % (graphparser.graphname, graphparser.image_nodes.nbr_input_images, graphparser.image_nodes.nbr_output_images)
    return parsed_string

def handle_userdata(graphparser):
    """ Handles the userdata argument, either create option struct or typecast to avoid compiler warning """
    if not graphparser.userdata.has_userdata:
        parsed_string = """\
    (void) userdata; /* To avoid compiler warning */\n\n"""
    else:
        parsed_string = """\
    %s_userdata_t *opts = (%s_userdata_t*)userdata;\n\n""" % (graphparser.graphname, graphparser.graphname)

    return parsed_string

def input_imagearray_definition(graphparser):
    """Writes the input image array definition."""

    parsed_string = """\
    struct { int width; int height; vx_df_image format; } in_virt[] =
    {"""
    for index, image_id in enumerate(graphparser.image_nodes.input_nodes_indexed_names):
        width, height, image_format, parsed_image_format = get_image_formats(graphparser, image_id)
        parsed_string += """
        { %s, %s, VX_DF_IMAGE_%s },""" % (width, height, image_format)
    parsed_string += "\n    };\n"

    parsed_string += """\
    vx_image input_images[io_param->nbr_inputs];
    int i;
    for (i = 0; i < io_param->nbr_inputs; i++) {
        graphmanager_image_t *input = &io_param->input_images[i];
        switch (input->type) {
            case GRAPHMANAGER_IMG_TYPE_VX:
                if (!input->image) { /* Create a virtual image */
                    input->image = vxCreateVirtualImage(graph_skeleton, in_virt[i].width, in_virt[i].height, in_virt[i].format);
                }
                input_images[i] = input->image;
                break;

            default:
                ERR("Unsupported image type %d.", input->type);
                return false;
        }
    }

"""
    return parsed_string

def output_imagearray_definition(graphparser):
    """Writes the output image array definition."""

    parsed_string = """\
    struct { int width; int height; vx_df_image format; } out_virt[] =
    {"""
    for index, image_id in enumerate(graphparser.image_nodes.output_nodes_indexed_names):
        width, height, image_format, parsed_image_format = get_image_formats(graphparser, image_id)
        parsed_string += """
        { %s, %s, VX_DF_IMAGE_%s },""" % (width, height, image_format)
    parsed_string += "\n    };\n"

    parsed_string += """\
    vx_image output_images[io_param->nbr_outputs];
    for (i = 0; i < io_param->nbr_outputs; i++) {
        graphmanager_image_t *output = &io_param->output_images[i];
        switch (output->type) {
            case GRAPHMANAGER_IMG_TYPE_VX:
                if (!output->image) { /* Create a virtual image */
                    output->image = vxCreateVirtualImage(graph_skeleton, out_virt[i].width, out_virt[i].height, out_virt[i].format);
                }
                output_images[i] = output->image;
                break;

            default:
                ERR("Unsupported image type %d.", output->type);
                return false;
        }
    }

"""
    return parsed_string

def get_image_formats(graphparser, image_id):
    """Gets some image formats

    Returns 'width', 'height', the generated image format 'image_format'
    and the corresponding parsed image enum 'parsed_image_format'

    Note that if the parsed image enum is not specified in the graph definition,
    the default attribute value is returned.
    """
    image_format = graphparser.get_image_format(image_id)

    (value_from_opts, width) = graphparser.get_value_for_attribute(image_id, 'width')
    if value_from_opts:
        # TODO: Do we need to handle more general case when userdata reference isn't at beginning of line?
        width = "opts->" + width

    (value_from_opts, height) = graphparser.get_value_for_attribute(image_id, 'height')
    if value_from_opts:
        height = "opts->" + height

    (value_from_opts, parsed_image_format) = graphparser.get_value_for_attribute(image_id, 'vx_df_image_e')
    if value_from_opts:
        raise(TypeError, "Attribute {} is of string type and can not be used as userdata input".format(parsed_image_format))

    return width, height, image_format, parsed_image_format

def uniform_imagearray_definition(graphparser):
    """Writes the uniform image array definition."""
    parsed_string = ""

    if len(graphparser.get_indexed_names('uniform_input_image_nodes')) > 0:
        uniform_image_var_names = {"VX_DF_IMAGE_U8" : "uint8",
                                   "VX_DF_IMAGE_S16" : "int16"}
        uniform_value_assign_strings = {"VX_DF_IMAGE_U8" : "U8",
                                        "VX_DF_IMAGE_S16" : "S16"}
        for key in uniform_image_var_names:
            if key in graphparser.image_nodes.uniform_input_image_indexed_formats:
                uniform_value_type = "vx_pixel_value_t"
                if graphparser.vx_version == graphml_parser.VX_VERSION_1_0_1:
                    uniform_value_type = "vx_{}".format(uniform_image_var_names[key])
                parsed_string += "    {} uniform_value_{};\n".format(uniform_value_type, uniform_image_var_names[key])

        parsed_string += "    vx_image uniform_input_images[{}];\n".format(len(graphparser.get_indexed_names('uniform_input_image_nodes')))

        for index, uniform_image_id in enumerate(graphparser.get_indexed_names('uniform_input_image_nodes')):
            width, height, image_format, parsed_image_format = get_image_formats(graphparser, uniform_image_id)
            uniform_value_assign_string = ""
            if graphparser.vx_version != graphml_parser.VX_VERSION_1_0_1:
                uniform_value_assign_string = ".{}".format(uniform_value_assign_strings[parsed_image_format])
            parsed_string += "    uniform_value_{}{} = {};\n".format(uniform_image_var_names[parsed_image_format], uniform_value_assign_string, str(graphparser.get_uniform_image_value_for_id(uniform_image_id)))
            parsed_string += "    uniform_input_images[{}] = vxCreateUniformImage(graphmanager_get_context(graph_manager), {}, {}, VX_DF_IMAGE_{}, &uniform_value_{});\n".\
                                                    format(index, width, height, image_format, uniform_image_var_names[parsed_image_format])

        parsed_string += "\n"

    return parsed_string

# TODO: rename virtual_nodes_indexed_names to internal_nodes_indexed_names

def internal_imagearray_definition(graphparser):
    """Writes the internal virtual image array definition."""
    parsed_string = ""

    # TODO:Remove explicit refs to image_nodes in this file. (go via graphmanager)
    num_imgs = len(graphparser.image_nodes.virtual_nodes_indexed_names)
    if num_imgs > 0:
        parsed_string += "    vx_image internal_images[{}];\n".format(num_imgs)

        for index, image_id in enumerate(graphparser.image_nodes.virtual_nodes_indexed_names):
            width, height, image_format, parsed_image_format = get_image_formats(graphparser, image_id)

            (value_from_opts, nodetype) = graphparser.get_value_for_attribute(image_id, 'nodetype')
            if value_from_opts:
                raise(TypeError, "Attribute {} is of string type and can not be used as userdata input".format(nodetype))

            parsed_string += "    internal_images[{}] = ".format(index)
            if nodetype == "uniform_input_image":
                parsed_string += "uniform_input_images[{}];\n".format(graphparser.image_nodes.get_uniform_image_index(image_id))
            else:
                parsed_string += "vxCreateVirtualImage(graph_skeleton, {}, {}, VX_DF_IMAGE_{});\n".\
                    format(width, height, image_format)

        parsed_string += "\n"

    return parsed_string

def create_function_nodes(graphparser, dry_run = False):
    """Writes function node creation code and connects edges."""
    parsed_string = ""

    if not dry_run:
        #Writes memory allocation code for the correct number of input and output function nodes
        #to go into the node lists.
        parsed_string += "    nodes->nbr_input_images  = " + str(graphparser.image_nodes.nbr_input_images) + ";\n"
        parsed_string += "    nodes->nbr_output_images = " + str(graphparser.image_nodes.nbr_output_images) + ";\n"
        parsed_string += "    nodes->input_images  = (vx_image *) malloc(sizeof(vx_image) * nodes->nbr_input_images);\n"
        parsed_string += "    nodes->output_images = (vx_image *) malloc(sizeof(vx_image) * nodes->nbr_output_images);"
        parsed_string += """
    for (i = 0; i < nodes->nbr_input_images; i++) {
        nodes->input_images[i] = input_images[i];
    }
    for (i = 0; i < nodes->nbr_output_images; i++) {
        nodes->output_images[i] = output_images[i];
    }

"""
        parsed_string += "    nodes->nbr_debug_input_nodes  = " + str(len(graphparser.get_indexed_names('debug_input_function_nodes'))) + ";\n"
        parsed_string += "    nodes->nbr_debug_output_nodes = " + str(len(graphparser.get_indexed_names('debug_output_function_nodes')))+ ";\n"
        parsed_string += "    nodes->debug_input_nodes  = (node_rc_t**) malloc(sizeof(node_rc_t*) * nodes->nbr_debug_input_nodes);\n"
        parsed_string += "    nodes->debug_output_nodes = (node_rc_t**) malloc(sizeof(node_rc_t*) * nodes->nbr_debug_output_nodes);\n\n"

        parsed_string += "    vx_node function_node;\n"
        if graphparser.use_any_refcounted_assignment_string():
            parsed_string += "    node_rc_t *function_node_rc;\n"

        if len(graphparser.get_dynamic_function_nodes_info()) > 0:
            parsed_string += "    node_rc_t *dynamic_nodes[" + str(len(graphparser.get_dynamic_function_nodes_info())) + "];\n"

    for idx, node in enumerate(graphparser.get_indexed_names('function_nodes')):
        function_name = graphparser.function_nodes.get_function_node_name(node)
        if graphparser.verbose and not dry_run:
            print "Parsing vx" + function_name + "Node"
        parsed_string += function_node_library.get_node(function_name).parse(graphparser, node, "function_node = ", dry_run)
        parsed_string += function_node_library.get_node(function_name).parse_border_mode(graphparser, node, "function_node", dry_run)
        if graphparser.using_refcounted_assignment_string(node):
            parsed_string += "    node_rc_release(&function_node_rc);\n"
        else:
            parsed_string += "    vxReleaseNode(&function_node);\n"
        if idx < len(graphparser.get_indexed_names('function_nodes'))-1:
            parsed_string += "\n"

    if not dry_run:
        if len(graphparser.get_dynamic_function_nodes_info()) > 0:
            parsed_string += "\n"
        for idx, itemlist in enumerate(graphparser.get_dynamic_function_nodes_info()):
            parsed_string += "    graphmanager_add_parameter_to_graph(graph_manager, vxGetParameterByIndex(dynamic_nodes[" + str(idx) + "]->vxnode, " + str(itemlist[1]) + "));\n"
        for idx, itemlist in enumerate(graphparser.get_dynamic_function_nodes_info()):
            parsed_string += "    node_rc_release(&dynamic_nodes[" + str(idx) + "]);\n"

        parsed_string += "\n    return graph_skeleton != NULL ? true : false;\n"
        parsed_string += "}\n"

    return parsed_string

def parse(graphparser, dry_run = False):
    """Writes the graph create function C-code by calling several helper functions."""

    # Special function if strip_mode
    if not dry_run and graphparser.strip_mode:
        return graph_create_function_strip.parse(graphparser)

    parsed_string = ""

    if not dry_run:
        parsed_string += function_beginning(graphparser)
        parsed_string += handle_userdata(graphparser)
        parsed_string += input_imagearray_definition(graphparser)
        parsed_string += output_imagearray_definition(graphparser)
        parsed_string += uniform_imagearray_definition(graphparser)
        parsed_string += internal_imagearray_definition(graphparser)

    parsed_string += create_function_nodes(graphparser, dry_run)

    if graphparser.verbose and not dry_run:
        print "Input image node IDs:\n" + str(graphparser.get_indexed_names('input_image_nodes')) + "\n"
        print "Output image node IDs:\n" + str(graphparser.get_indexed_names('output_image_nodes')) + "\n"
        print "Virtual (internal) image node IDs:\n" + str(graphparser.get_indexed_names('virtual_image_nodes')) + "\n"

    if graphparser.debug_mode and not dry_run:
        print "Image node attributes:"
        for img_attr in graphparser.image_nodes.image_attributes:
            print 'ID: ', img_attr.node_id, img_attr.attributes

    return parsed_string

