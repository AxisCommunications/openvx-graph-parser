"""Module with library method for accessing function node objects."""

from base_node import BaseNode
from half_scale_gaussian import HalfScaleGaussian
from subtract import Subtract
from threshold import Threshold
from sobel3x3 import Sobel3x3
from abs_diff import AbsDiff
from convert_depth import ConvertDepth
from dilate3x3 import Dilate3x3
from dilate2x2 import Dilate2x2
from erode3x3 import Erode3x3
from erode2x2 import Erode2x2
from add import Add
from multiply import Multiply
from scale_image import ScaleImage
from magnitude import Magnitude
from table_lookup import TableLookup
from or_node import Or
from and_node import And
from warp_affine import WarpAffine
from dubbel_io_test import DubbelIoTest

#Only create node classes once, when module is first loaded
DEFAULT_DUMMY_NODE = BaseNode() #Used if name of node is not in the dictionary

NODE_DICTIONARY = {'HalfScaleGaussian'  : HalfScaleGaussian(),
                   'Subtract'           : Subtract(),
                   'Threshold'          : Threshold(),
                   'Sobel3x3'           : Sobel3x3(),
                   'AbsDiff'            : AbsDiff(),
                   'ConvertDepth'       : ConvertDepth(),
                   'Dilate3x3'          : Dilate3x3(),
                   'Erode3x3'           : Erode3x3(),
                   'Add'                : Add(),
                   'Multiply'           : Multiply(),
                   'ScaleImage'         : ScaleImage(),
                   'Magnitude'          : Magnitude(),
                   'TableLookup'        : TableLookup(),
                   'Or'                 : Or(),
                   'And'                : And(),
                   'WarpAffine'         : WarpAffine(),
                   'DubbelIoTest'       : DubbelIoTest(), #This is a dummy node used only for testing the parser.
                   'Dilate2x2'          : Dilate2x2(),
                   'Erode2x2'           : Erode2x2()
                   }

#This dict gives the first parameter index for the first input image in the vxCreateXXXNode function call
#Note that the vx_graph parameter is not counted when accessing node parameters
#Therefore the first index starts on 0, for the first parameter AFTER vx_graph.
FIRST_INPUT_IMAGE_INDEX_DICT = {'HalfScaleGaussian' :    0,
                                'Subtract'          :    0,
                                'Threshold'         :    0,
                                'Sobel3x3'          :    0,
                                'AbsDiff'           :    0,
                                'ConvertDepth'      :    0,
                                'Dilate3x3'         :    0,
                                'Erode3x3'          :    0,
                                'Add'               :    0,
                                'Multiply'          :    0,
                                'ScaleImage'        :    0,
                                'Magnitude'         :    0,
                                'TableLookup'       :    0,
                                'Or'                :    0,
                                'And'               :    0,
                                'WarpAffine'        :    0,
                                'DubbelIoTest'      :    0,
                                'Dilate2x2'         :    1,
                                'Erode2x2'          :    1
                                }

#This dict gives the first parameter index for the first input image in the vxCreateXXXNode function call
#Note that the vx_graph parameter is not counted when accessing node parameters
#Therefore the first index starts on 0, for the first parameter AFTER vx_graph.
FIRST_OUTPUT_IMAGE_INDEX_DICT = {'HalfScaleGaussian':    1,
                                 'Subtract'         :    3,
                                 'Threshold'        :    2,
                                 'Sobel3x3'         :    1,
                                 'AbsDiff'          :    2,
                                 'ConvertDepth'     :    1,
                                 'Dilate3x3'        :    1,
                                 'Erode3x3'         :    1,
                                 'Add'              :    3,
                                 'Multiply'         :    5,
                                 'ScaleImage'       :    1,
                                 'Magnitude'        :    2,
                                 'TableLookup'      :    2,
                                 'Or'               :    2,
                                 'And'              :    2,
                                 'WarpAffine'       :    3,
                                 'DubbelIoTest'     :    2,
                                 'Dilate2x2'        :    3,
                                 'Erode2x2'         :    3
                                 }

#PARAMETER_NAMES_DICT and PARAMETER_INDICES_DICT are synced dictionaries,
#so the position of the parameter name in the first dictionary gives
#the index to use in the list in the second dictionary.
#I.e. the vx_scalar parameter for ConvertDepth gets the second
#index in the list for ConvertDepth in PARAMETER_INDICES_DICT, that is, index = 3.
PARAMETER_NAMES_DICT =          {'HalfScaleGaussian':    ["vx_int32"],
                                 'Subtract'         :    ["vx_convert_policy_e"],
                                 'Threshold'        :    ["vx_threshold"],
                                 'Sobel3x3'         :    [],
                                 'AbsDiff'          :    [],
                                 'ConvertDepth'     :    ["vx_convert_policy_e", "vx_scalar"],
                                 'Dilate3x3'        :    [],
                                 'Erode3x3'         :    [],
                                 'Add'              :    ["vx_convert_policy_e"],
                                 'Multiply'         :    ["vx_scalar", "vx_convert_policy_e", "vx_round_policy_e"],
                                 'ScaleImage'       :    ["vx_interpolation_type_e"],
                                 'Magnitude'        :    [],
                                 'TableLookup'      :    ["vx_lut"],
                                 'Or'               :    [],
                                 'And'              :    [],
                                 'WarpAffine'       :    ["vx_matrix", "vx_interpolation_type"],
                                 'DubbelIoTest'     :    [],
                                 'Dilate2x2'        :    [],
                                 'Erode2x2'         :    [],
                                 }

#Note that the vx_graph parameter is not counted when accessing node parameters
#Therefore the first index starts on 0, for the first parameter AFTER vx_graph.
PARAMETER_INDICES_DICT =        {'HalfScaleGaussian':    [2],
                                 'Subtract'         :    [2],
                                 'Threshold'        :    [1],
                                 'Sobel3x3'         :    [],
                                 'AbsDiff'          :    [],
                                 'ConvertDepth'     :    [2,3],
                                 'Dilate3x3'        :    [],
                                 'Erode3x3'         :    [],
                                 'Add'              :    [2],
                                 'Multiply'         :    [2,3,4],
                                 'ScaleImage'       :    [2],
                                 'Magnitude'        :    [],
                                 'TableLookup'      :    [1],
                                 'Or'               :    [],
                                 'And'              :    [],
                                 'WarpAffine'       :    [1,2],
                                 'DubbelIoTest'     :    [],
                                 'Dilate2x2'        :    [],
                                 'Erode2x2'         :    [],
                                 }

#Input is always known when the parser checks for validity
#VALID_INPUT_IMAGE_FORMATS and VALID_OUTPUT_IMAGE_FORMATS are index-synced dictionaries,
VALID_INPUT_IMAGE_FORMATS =    {'HalfScaleGaussian' :[['U8'],['U8']],
                                'Subtract'          :[['U8','U8'],['U8','U8'],['S16','S16'],['U8','U8'],['S16','S16'],['U8','S16'],['S16','U8'],['U8','S16'],['S16','U8']],
                                'Threshold'         :[['U8'],['U8']],
                                'Sobel3x3'          :[['U8'],['U8']],
                                'AbsDiff'           :[['U8','U8'],['U8','U8']],
                                'ConvertDepth'      :[['U8'],['S16'],['U8'],['S16']],
                                'Dilate3x3'         :[['U8'],['U8']],
                                'Erode3x3'          :[['U8'],['U8']],
                                'Add'               :[['U8','U8'],['U8','U8'],['S16','S16'],['U8','U8'],['S16','S16'],['U8','S16'],['S16','U8'],['U8','S16'],['S16','U8']],
                                'Multiply'          :[['U8','U8'],['U8','U8'],['S16','S16'],['U8','U8'],['S16','S16'],['U8','S16'],['S16','U8'],['U8','S16'],['S16','U8']],
                                'ScaleImage'        :[['U8'],['U8']],
                                'Magnitude'         :[['S16','S16'],['S16','S16']],
                                'TableLookup'       :[['U8'],['U8']],
                                'Or'                :[['U8','U8'],['U8','U8']],
                                'And'               :[['U8','U8'],['U8','U8']],
                                'WarpAffine'        :[['U8'],['U8']],
                                'DubbelIoTest'      :[['U8','U8'],['U8','U8']],
                                'Dilate2x2'         :[['U8'],['U8']],
                                'Erode2x2'          :[['U8'],['U8']]
                                }

#Output can be unknown, i.e. VIRT when the parser checks for validity, but should result in some definite format
#note that two similar output format lists must have different input format lists otherwise the mapping between
#input and output is not uniquely defined (i.e. this spec. is then wrong).
VALID_OUTPUT_IMAGE_FORMATS =   {'HalfScaleGaussian' :[['U8'],['VIRT->U8']],
                                'Subtract'          :[['U8'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16']],
                                'Threshold'         :[['U8'],['VIRT->U8']], # Boolean U8 values are either 0 or 255
                                'Sobel3x3'          :[['S16','S16'],['VIRT->S16','VIRT->S16']],
                                'AbsDiff'           :[['U8'],['VIRT->U8']],
                                'ConvertDepth'      :[['S16'],['U8'],['VIRT->S16'],['VIRT->U8']],
                                'Dilate3x3'         :[['U8'],['VIRT->U8']],
                                'Erode3x3'          :[['U8'],['VIRT->U8']],
                                'Add'               :[['U8'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16']],
                                'Multiply'          :[['U8'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16'],['S16'],['S16'],['VIRT->S16'],['VIRT->S16']],
                                'ScaleImage'        :[['U8'],['VIRT->U8']],
                                'Magnitude'         :[['S16'],['VIRT->S16']],
                                'TableLookup'       :[['U8'],['VIRT->U8']],
                                'Or'                :[['U8'],['VIRT->U8']],
                                'And'               :[['U8'],['VIRT->U8']],
                                'WarpAffine'        :[['U8'],['VIRT->U8']],
                                'DubbelIoTest'      :[['U8','U8'],['VIRT->U8','VIRT->U8']],
                                'Dilate2x2'         :[['U8'],['VIRT->U8']],
                                'Erode2x2'          :[['U8'],['VIRT->U8']]
                                }

def get_node(nodename):
    """Create the relevant function node based on the input string

    Returns dummy node if node is not in the node dictionary.
    """
    return NODE_DICTIONARY.get(nodename, DEFAULT_DUMMY_NODE)

from graphml_parser import graphml_parser
class Library:
    """Class that contains information about the parameters of the supported nodes."""

    def __init__(self, vx_version=graphml_parser.VX_VERSION_DEFAULT):
        self.FIRST_INPUT_IMAGE_INDEX_DICT = FIRST_INPUT_IMAGE_INDEX_DICT
        self.FIRST_OUTPUT_IMAGE_INDEX_DICT = FIRST_OUTPUT_IMAGE_INDEX_DICT
        self.PARAMETER_NAMES_DICT = PARAMETER_NAMES_DICT
        self.PARAMETER_INDICES_DICT = PARAMETER_INDICES_DICT
        self.VALID_INPUT_IMAGE_FORMATS = VALID_INPUT_IMAGE_FORMATS
        self.VALID_OUTPUT_IMAGE_FORMATS = VALID_OUTPUT_IMAGE_FORMATS

        # Certain overrides has to be done if not default OpenVX version
        if vx_version is graphml_parser.VX_VERSION_1_0_1:
            # Our own 2x2 morphology nodes has simpler structure and I/O parameters
            # have different indices
            self.FIRST_INPUT_IMAGE_INDEX_DICT['Dilate2x2'] = 0
            self.FIRST_OUPUT_IMAGE_INDEX_DICT['Dilate2x2'] = 1
            self.FIRST_INPUT_IMAGE_INDEX_DICT['Erode2x2'] = 0
            self.FIRST_OUPUT_IMAGE_INDEX_DICT['Erode2x2'] = 1
