"""Class for writing C-code to create a vxThresholdNode object.

Done by parsing the graph parameters of the xml description of the node.

parsed_string contains the C code to be written to file
"""
from base_node import BaseNode
from graphml_parser import graphml_parser


class Threshold(BaseNode):
    """Class for parsing node with the given class name."""

    def __init__(self):
        """Initialization of Class object"""
        BaseNode.__init__(self)
        self.thresh_count = 0
        self.thresh_val_count = 0

    def parse(self, graphparser, current_node, assignment_string, dry_run = False):
        """Parsing of xml and C code for creation of the function node."""
        self.reset_parameters(graphparser, current_node, dry_run)
        parsed_string = ""

        #===============
        # ERROR CHECKING
        #===============
        self.require_nbr_input_edges(graphparser, current_node, 1)
        self.require_nbr_output_edges(graphparser, current_node, 1)
        #Add error checking for the used parameters

        #=================
        # PARSE PARAMETERS
        #=================
        #TODO: Only binary threshold currently supported.
        if not self.node_has_errors:
            if self.thresh_val_count == 0 and not dry_run:
                self.thresh_val_count += 1
                if graphparser.vx_version == graphml_parser.VX_VERSION_1_2:
                    parsed_string += "    vx_pixel_value_t thresh_value;\n"
                else:
                    parsed_string += "    " + self.parse_single_parameter(graphparser, "vx_size", current_node)
                    parsed_string += " thresh_value;\n"

            #Create the threshold object
            if self.thresh_count == 0 and not dry_run:
                self.thresh_count += 1
                parsed_string += "    vx_threshold thresh;\n"

            if graphparser.vx_version == graphml_parser.VX_VERSION_1_2:
                input_format = graphparser.image_format_checker.get_image_format_from_image_node_id(graphparser.graph,
                                                                                                    graphparser.image_nodes,
                                                                                                    self.node_info.input_image_node_ids[0])
                output_format = graphparser.image_format_checker.get_image_format_from_image_node_id(graphparser.graph,
                                                                                                     graphparser.image_nodes,
                                                                                                     self.node_info.output_image_node_ids[0])

                parsed_string += "    thresh_value.{} = ".format(input_format)
                parsed_string += self.parse_single_parameter(graphparser, "vx_pixel_value_t", current_node)
                parsed_string += ";\n"

                parsed_string += "    thresh = vxCreateThresholdForImage(graphmanager_get_context(graph_manager)"
                parsed_string += self.parse_parameter(graphparser, "vx_threshold_type_e", current_node)
                parsed_string += ", VX_DF_IMAGE_" + input_format
                parsed_string += ", VX_DF_IMAGE_" + output_format
                parsed_string += ");\n"

                #Set the threshold pointer value on the threshold object
                parsed_string += "    vxCopyThresholdValue(thresh, &thresh_value, VX_WRITE_ONLY, VX_MEMORY_TYPE_HOST);\n"

            else:
                parsed_string += "    thresh_value = " #vx_int32 = typedef of int32_t. Maybe find better name than vx_size?
                parsed_string += self.parse_single_parameter(graphparser, self.parse_single_parameter(graphparser, "vx_size", current_node), current_node)
                parsed_string += ";\n"

                parsed_string += "    thresh = vxCreateThreshold(graphmanager_get_context(graph_manager)"
                parsed_string += self.parse_parameter(graphparser, "vx_threshold_type_e", current_node) #e.g. VX_THRESHOLD_TYPE_BINARY (VX_THRESHOLD_TYPE_RANGE also supported but not yet implemented)
                parsed_string += self.parse_parameter(graphparser, "vx_type_e", current_node) #Only VX_TYPE_UINT8 supported in vx1.0
                parsed_string += ");\n"

                #Set the threshold pointer value on the threshold object
                parsed_string += "    vxSetThresholdAttribute(thresh"
                parsed_string += self.parse_parameter(graphparser, "vx_threshold_attribute_e", current_node) #e.g. VX_THRESHOLD_ATTRIBUTE_THRESHOLD_VALUE (which other are supported?)
                parsed_string += ", &thresh_value"
                parsed_string += ", sizeof(" + self.parse_single_parameter(graphparser, "vx_size", current_node) + ")"
                parsed_string += ");\n"

            #Create the threshold node with the attached threshold object
            parsed_string += "    " + assignment_string + "vxThresholdNode(graph_skeleton"
            parsed_string += self.parse_input_parameters(graphparser, current_node)
            parsed_string += ", thresh"
            parsed_string += self.parse_output_parameters(graphparser, current_node)
            parsed_string += ");\n"
            parsed_string += "    vxReleaseThreshold(&thresh);\n"
            parsed_string += self.append_to_io_arrays(graphparser, current_node)

        return parsed_string

