#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
#include <VX/vx.h>

// Include the correct generated header and name of graph
#include "diffdemo2_strip.h"
#define GRAPHNAME "diffdemo2"

/* Fwd declarations of local functions */
static vx_image
create_vx_image_from_handle(vx_context context, vx_uint8 *ptr, vx_uint32 width, vx_uint32 height);

static void
file_write_pgm(const char *filename, vx_image img);

static vx_uint8*
file_read_pgm(FILE *stream, int *width, int *height);

static vx_uint8*
file_read_pgm_impl(FILE *stream, int width, int height, int maxval, bool binary);

int main(int argc, char *argv[]) {
     int i;
    FILE *fid;
    int width, height;

    // Correct number of inputs and outputs
    int num_inputs = 2;
    int num_outputs = 2;

    vx_uint8 *input_ptrs[num_inputs];
    vx_image input_images[num_inputs];

    vx_image output_images[num_outputs];

    printf("standalone test of graph %s \n", GRAPHNAME);
    vx_context context = vxCreateContext();
    vx_graph graph_skeleton = vxCreateGraph(context);

    /* Quick sanity check of input arguments */
    if (argc != num_inputs + 3 && argc != num_inputs + num_outputs + 3) {
        printf("ERROR: Requires %d input arguments as paths to input files + 2 arguments "
                "for width and height! (got %d)\n\n", num_inputs, argc);
        printf("Usage: %s in_0.pgm ... in_n.pgm width height [out_0.pgm ... out_m.pgm]\n\n"
               "where n == %d is the number of edge images to use in pgm-format.\n"
               "Width and height are the reference dimensions used when creating the graph.\n"
               "The last m == %d arguments are optional custom filenames for the output files.\n",
               argv[0], num_inputs, num_outputs);
        return EXIT_FAILURE;
    }

    /* Parse arguments and read input images */
    for (i = 0; i < num_inputs; i++) {
        printf("reading input image #%d from file: %s \n", i, argv[i + 1]);
        fid = fopen(argv[i + 1], "r");
        input_ptrs[i] = file_read_pgm(fid, &width, &height);
        assert(input_ptrs[i]);
        input_images[i] = create_vx_image_from_handle(context, input_ptrs[i], width, height);
        assert(input_images[i]);
        fclose(fid);
    }

    /* Define reference dimensions from last two command line arguments */
    int ref_width = atoi(argv[num_inputs + 1]);
    int ref_height = atoi(argv[num_inputs + 2]);
    printf("userdata reference dimensions: w=%d h=%d \n", ref_width, ref_height);

    // Update potential userdata type name and set the necessary fields specified in the graphml file
    diffdemo2_userdata_t userdata = {.ref_width = ref_width, .ref_height = ref_height};

    // Create the correct number of output images and set image dimensions corresponding to graphml file
    output_images[0] =  vxCreateImage(context, userdata.ref_width, userdata.ref_height, VX_DF_IMAGE_U8);
    output_images[1] =  vxCreateImage(context, userdata.ref_width, userdata.ref_height, VX_DF_IMAGE_U8);

    /* Call the generated create function to actually create the nodes and populate the graph skeleton */
    // Update the name of the generated create function
    bool create_status = diffdemo2_create(context, graph_skeleton, input_images, output_images, &userdata);
    printf("graph creation status %s \n", create_status ? "OK" : "NOT OK");

    /* Here you can manually modify the graph before verifying and running it,
     * e.g. this is a good place to set any dynamic parameters on the graph by
     * calling vxSetGraphParameterByIndex */

    /* All nodes should be appended to graph so verify and process it */
    vx_status status = vxVerifyGraph(graph_skeleton);
    printf("vxVerifyGraph vx_status: %d \n", status);
    if (status != VX_SUCCESS) {
        return EXIT_FAILURE;
    } else {
        status = vxProcessGraph(graph_skeleton);
        printf("vxProcessGraph vx_status: %d \n", status);
    }

    /* Write the output images to file */
    char filename[200];
    for (i = 0; i < num_outputs; i++) {
        if (argc == num_inputs + num_outputs + 3) {
            sprintf(filename, "%s", argv[num_inputs + 3 + i]);
        } else {
            sprintf(filename, "%s-output_%d.pgm", argv[0], i);
        }
        printf("writing output image #%d to file: %s \n", i, filename);
        file_write_pgm(filename, output_images[i]);
    }

    /* Release everything OpenVX */
    vxReleaseContext(&context);

    /* Free pixel buffers */
    for (i = 0; i < num_inputs; i++) {
        free(input_ptrs[i]);
    }

    return EXIT_SUCCESS;
}


/* General helper functions */

/* Create vx_image from simple unaligned pixel buffer starting at ptr */
static vx_image
create_vx_image_from_handle(vx_context context, vx_uint8 *ptr, vx_uint32 width, vx_uint32 height)
{
    void *input_ptrs[1];
    input_ptrs[0] = (void*) ptr;

    vx_imagepatch_addressing_t input_addrs[1];
    input_addrs[0].dim_x = width;
    input_addrs[0].dim_y = height;
    input_addrs[0].stride_x = 1;
    input_addrs[0].stride_y = width;
    input_addrs[0].scale_x = VX_SCALE_UNITY;
    input_addrs[0].scale_y = VX_SCALE_UNITY;
    input_addrs[0].step_x = 1;
    input_addrs[0].step_y = 1;

    return vxCreateImageFromHandle(context, VX_DF_IMAGE_U8, input_addrs, input_ptrs, VX_MEMORY_TYPE_HOST);
}

/* Save vx_image to pgm image file.*/
static void
file_write_pgm(const char *filename, vx_image img)
{
    if (img == NULL) {
        printf("\n%s is %p!\n", filename, img);
        abort();
    }
    vx_status status;
    vx_uint32 width, height;
    status = vxQueryImage(img, VX_IMAGE_WIDTH, &width, sizeof(vx_uint32));
    status = vxQueryImage(img, VX_IMAGE_HEIGHT, &height, sizeof(vx_uint32));
    if (status != VX_SUCCESS) {
        printf("Could not query image for width/height, img: %s, vx_status: %d!", filename, status);
        abort();
    }

    vx_rectangle_t rect = {.start_x = 0, .start_y = 0, .end_x = width, .end_y = height};
    vx_imagepatch_addressing_t addr;
    void *base_ptr = NULL;
    vx_uint32 plane = 0; /* Only support single plane images */

    vx_map_id map_id;
    status = vxMapImagePatch(img, &rect, plane, &map_id, &addr, &base_ptr, VX_READ_ONLY, VX_MEMORY_TYPE_HOST, 0);

    if (status != VX_SUCCESS) {
        printf("Could not access image patch, img: %s vx_status: %d!", filename, status);
        abort();
    }

    FILE *stream = fopen(filename, "w");
    /* Write the header */
    fprintf(stream, "P5\n%d %d 255\n", width, height);

    /* Write pixel data */
    unsigned x, y;
    for (y = 0; y < height; y++) {
        vx_uint32 j = (addr.stride_y*y*addr.scale_y) / VX_SCALE_UNITY;
        for (x = 0; x < width; x++) {
            vx_uint8 *tmp = (vx_uint8*)base_ptr;
            vx_uint32 i = j + (addr.stride_x*x*addr.scale_x) / VX_SCALE_UNITY;
            vx_uint8 val = tmp[i];
            if(!fwrite(&val, 1, 1, stream) && ferror(stream)){
                printf("Error writing to file!\n");
                abort();
            }
        }
    }
    fclose(stream);
    status = vxUnmapImagePatch(img, map_id);
}

/**
 *  Create a vx_uint8 pixel buffer from a pgm image file stream.
 */
static vx_uint8*
file_read_pgm(FILE *stream, int *width, int *height)
{
    vx_uint8    *image = NULL;
    int         magic1 = 0;
    int         magic2 = 0;
    int         maxval = 0;
    bool        skip   = true;

    /* Check arguments */
    if (!stream) {
        goto Fail_arg;
    }

    /* Read the magic number */
    magic1 = fgetc(stream);
    magic2 = fgetc(stream);

    /* Read comments */
    do {
        int ch = fgetc(stream);
        switch (ch) {
            case '#':
            {
                int tmp;
                do {
                    tmp = fgetc(stream);
                } while (tmp != '\n' && tmp != EOF);
            }
            break;

            case EOF:
                goto Fail_parse;

            case ' ':
            case '\n':
            case '\t':
                /* No action */
                break;

            default:
                ungetc(ch, stream);
                skip = false;
        }
    } while (skip);

    /* Read width and height */
    if (fscanf(stream, " %d %d", width, height) == EOF) {
        goto Fail_parse;
    }

    /* Check parameters */
    if (magic1 != 'P' ||
        (magic2 != '2'  && magic2 != '5') ||
        *width <= 0    || *height <= 0)
    {
        goto Fail_parse;
    }

    /* Get the maximum value */
    if (fscanf(stream, "%d", &maxval) == EOF) {
        goto Fail_parse;
    }

    /* Read single white space character */
    if (fgetc(stream) == EOF) {
        goto Fail_parse;
    }

    /* Read the image data */
    image = file_read_pgm_impl(stream, *width, *height,
                               maxval, magic2 == '5');

    return image;

Fail_arg:
    printf("Invalid argument\n");
    return NULL;

Fail_parse:
    printf("Parse error\n");
    abort();
    return NULL;
}

static vx_uint8*
file_read_pgm_impl(FILE *stream, int width, int height, int maxval, bool binary)
{
    /* Catch uint16 cases */
    if (maxval > 0xff) {
        goto Fail_type;
    }

    /* Create a new image buffer */
    vx_uint8  *pix = malloc(width*height*sizeof(vx_uint8));
    if (!pix) {
        goto Fail_mem;
    }

    /* Read pixel data */
    if (binary) { /* image file is binary format*/
        int y;
        int size = 1;

        /* Read binary pixel data */
        for (y = 0; y < height; y++) {
            int i = y*width;

            /* Read buffer */
            if (fread(&pix[i], size, width, stream) != (size_t)width) {
                goto Fail_io;
            }
        }
    }
    else {
        /* image file is character format */
        const char *fmt = "%hhu";
        int         y;

        /* Read character pixel data */
        for (y = 0; y < height; y++) {
            int i = y*width;
            int x;

            for (x = 0; x < width; x++, i++) {
                if (fscanf(stream, fmt, &pix[i]) == EOF) {
                    goto Fail_io;
                }
            }
        }
    }

    return pix;

Fail_io:
    printf("error reading monochrome image file.\n");
    free(pix);
    return NULL;

Fail_mem:
    printf("failed to create new image.\n");
    return NULL;

Fail_type:
    printf("type not supported.\n");
    return NULL;
}
