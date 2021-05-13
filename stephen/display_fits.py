#!/usr/bin/env python3

#------------------------------------------------------------------------
__doc__="""\
display_fits.py - simple FITS image tools
Simple FITS image load and display. Only meant for quick visuals and checks.
"""
__intro__= """\
Simple FITS image load and display. Only meant for quick visuals and checks.
Also displays the marginal sums for the displayed part of the image.
Scaling is linear.
Allows for zscale and minmax auto range set as well as explicit limits.
Toggle for marginal sum plots.
Allow plotting subregions.
"""
__author__="S. Levine"
__date__="2021 Jan 31"

#------------------------------------------------------------------------
# import glob
# import time
# import datetime as dt

# Command line arg parsing
import argparse

import matplotlib.pyplot    as plt
import matplotlib.animation as animation

# Use FFMpeg for generation of movie files
import matplotlib as mpl
mpl.rcParams['animation.ffmpeg_path'] = r'/Users/sel/Software/Media/ffmpeg-4.3.1/ffmpeg'
# mpl.rcParams['animation.ffmpeg_path'] = r'/usr/local/bin/ffmpeg'
# can also use
# plt.rcParams['animation.ffmpeg_path'] = r'/usr/local/bin/ffmpeg'

import numpy as np

import reduc_utils as ru
import reduc_fits_utils as rf

#------------------------------------------------------------------------
def compute_scaling_limits (dat, lims, lrms=1, disp_lims=[], echo=False):
    """
    Compute display scaling min and max.
    dat == 2-D image to compute limits for
    lims == the type of scale range
    lrms == optional args to lims
    disp_lims == optional pre-specified limits. Overrides others
    """

    # Set display value limits for 2-D image
    # Default to min, max
    im_min = np.min(dat)
    im_max = np.max(dat)
    if (echo == True):
        print ('Nominal img min,max = {}, {}'.format(im_min, im_max))

    # and if desired reset scaling and limits
    if (disp_lims != []):
        if (echo == True):
            print ('Computing w/in limits {} {}'.format(disp_lims[0], 
                                                        disp_lims[1]))
        if (disp_lims[0] != disp_lims[1]):
            im_min = np.min(disp_lims)
            im_max = np.max(disp_lims)
        else:
            im_min = np.min(dat)
            im_max = np.max(dat)

    elif (lims == 'zscale'):
        # Set default image min,max = avg +/- 1 RMS
        im_average = np.average(dat)
        im_rms = np.std(dat)

        if (echo == True):
            print ('Computing zscale, Nrms = {}, RMS = {}'.format(lrms, 
                                                                  im_rms))

        im_min = im_average - lrms * im_rms
        im_max = im_average + lrms * im_rms

    elif (lims == 'minmax'):
        if (echo == True):
            print ('Computing minmax')
        im_min = np.min(dat)
        im_max = np.max(dat)

    if (echo == True):
        print ('Computed img min,max = {}, {}'.format(im_min, im_max))

    return im_min, im_max

def rgb_scaling (dat, lims, lrms, disp_lims):
    """\
    Compute RGB scaling limits and rescale the data array for display.
    """
    rminF, rmaxF = compute_scaling_limits (dat[:,:,0], lims='minmax',
                                           lrms=lrms, disp_lims=disp_lims)
    gminF, gmaxF = compute_scaling_limits (dat[:,:,1], lims='minmax',
                                           lrms=lrms, disp_lims=disp_lims)
    bminF, bmaxF = compute_scaling_limits (dat[:,:,2], lims='minmax',
                                           lrms=lrms, disp_lims=disp_lims)

    # Rescale data to same ranges for display if 3 color RGB
    dat[:,:,0] = (dat[:,:,0] - rminF) / (rmaxF - rminF)
    dat[:,:,1] = (dat[:,:,1] - gminF) / (gmaxF - gminF)
    dat[:,:,2] = (dat[:,:,2] - bminF) / (bmaxF - bminF)

    rmin, rmax = compute_scaling_limits (dat[:,:,0], lims=lims,
                                         lrms=lrms, disp_lims=disp_lims)
    gmin, gmax = compute_scaling_limits (dat[:,:,1], lims=lims,
                                         lrms=lrms, disp_lims=disp_lims)
    bmin, bmax = compute_scaling_limits (dat[:,:,2], lims=lims,
                                         lrms=lrms, disp_lims=disp_lims)

    print ('RGB min,max = {},{} {},{} {},{}'.format(rmin, rmax, 
                                                    gmin, gmax, 
                                                    bmin, bmax))

    # Rescale data for display if 3 color RGB
    dat[:,:,0] = (dat[:,:,0] - rmin) / (rmax - rmin)
    dat[:,:,1] = (dat[:,:,1] - gmin) / (gmax - gmin)
    dat[:,:,2] = (dat[:,:,2] - bmin) / (bmax - bmin)
    
    im_min = 0.
    im_max = 1.

    return dat, im_min, im_max

def display_2d_margs_img (hdr, indat, title=None, outfile=None, cm='inv',
                          disp_lims=[], lims='zscale', lrms=1.0,
                          marg_plot=True, naxlims=[], isrgb=False,
                          yratio=1.0, anim=0, zstep=1):
    """\
    Display a single 2-D FITS image plus marginals, or
    planes of a 3-D cube, or a single RGB (3plane, 3color) image.

    Display options:
    - cm == color map - inv == inverted gray scale
                        non == normal gray scale
    - disp_lims == [min, max] if not equal, they set the min and max scale range
    - lims == type of auto limits
              zscale, lrms == +/- lrms * rms about the average value
              minmax == min to max data value
    - marg_plot == true/false - plot or don't plot marginal sums
    - naxlims == [xmin, xmax, ymin, ymax] - plot subregion. If [], full image
    - isrgb == true if the image is a 3 plane RGB image
    - yratio == 1.0 mean y = x scaling.  Else y scale = yratio * x scale
                to allow for expansion in one or the other axis
                equivalent to setting the aspect ratio
    - anim == delay in millisec between animation frames. animate only if != 0.
               anim < 0 means repeat loop, else only once.
    - zstep == stride in Z dimension when displaying a 3D cube. default = 1
    """

    # Set up plot box fractions
    big_dim    = 0.8
    small_dim  = 0.1
    spacing    = 0.005
    left       = 0.045
    bottom     = 0.045
    marg_size  = small_dim

    # Shorthand for grayscale color tables
    cm_inv     = 'Greys'
    cm_non_inv = 'gray'
    # or gist_yarg, gist_gray

    # Color maps setup
    if (cm=='inv'):
        cm_arg = cm_inv
    elif (cm=='non'):
        cm_arg = cm_non_inv
    else:
        cm_arg = cm

    # print (naxlims)

    # Extract a subset of an image cube (either 2 or 3-D)
    # update rgb status
    cdat, rgb_flag, img_ndim, img_shape = \
        rf.extract_subimage (indat, naxlims, isrgb)

    # Set number of frames to display in sequence based on 
    # input dimensions and rgb flag
    if (img_ndim == 2):
        nfr = 1
    elif ((img_ndim == 3) and (rgb_flag == False)):
        nfr = img_shape[0]
    elif ((img_ndim == 3) and (rgb_flag == True)):
        nfr = 1

    # if doing an animation, set up the fig and ax for accumulating
    if (anim != 0):
        an_frames = []

    for inum in range(0, nfr, zstep):
        if (img_ndim == 2):
            dat = cdat
        elif ((img_ndim == 3) and (rgb_flag == True)):
            dat = cdat
        elif ((img_ndim == 3) and (rgb_flag == False)):
            dat = cdat[inum]

        # Compute x and y marginal sums
        #  xmarg = column sums, plotted along x axis
        #  ymarg = row sums, plotted along y axis
        xmarg, ymarg, xlen, ylen, xidx, yidx = rf.compute_xy_marginals (dat)

        # Compute display limits for RGB image and rescale to 0-1 range
        # for each color plane
        if (rgb_flag == True):
            # Compute display limits for RGB and rescale 3-d data array
            dat, im_min, im_max = rgb_scaling (dat, lims, lrms, disp_lims)

        else:
            # Compute display pixel value limits - Monochrome
            im_min, im_max = compute_scaling_limits (dat, lims=lims, 
                                                     lrms=lrms, 
                                                     disp_lims=disp_lims)

        # Compute boundaries and definitions for the axes
        yscale = ylen * yratio

        if (xlen >= yscale):
            xyratio  = yscale / xlen
            width  = big_dim
            height = big_dim * xyratio

        else:
            xyratio = xlen / yscale
            width  = big_dim * xyratio
            height = big_dim

        print ('{} = {:.3f} {:.3f} {:.3f} {:.3f} {:>.3f} {:>.3f} {:>.3f}'.\
                   format('l,b,w,h,xy,im_min,im_max',
                          left, bottom, width, height, xyratio,
                          im_min, im_max))
        rect_img   = [left, bottom, width, height]
        rect_xmarg = [left, bottom + height + spacing, width, marg_size]
        rect_ymarg = [left + width + spacing, bottom, marg_size, height]

        # Display --------------------

        if (anim != 0):
            #  Setup and load for animation

            # add time marker by overwriting pixels on the image
            mrkrpix_x = int(inum / (img_shape[0]-1) * (xlen - 1))
            mrkrpix_y = 0
            mr_dy = int(np.min([10, np.max([ylen/20, 1])]))
            dat[mrkrpix_y:mrkrpix_y+mr_dy, mrkrpix_x] = im_max

            if (inum == 0):
                an_fg = plt.figure(figsize=(6.5, 6.5))
                an_ax_img = an_fg.add_axes (rect=rect_img)
                an_ax_img.tick_params(direction='in', labelsize='x-small')
                an_ax_img.imshow (dat, origin='lower', 
                                  vmin=im_min, vmax=im_max, 
                                  cmap=cm_arg, aspect=yratio)
                an_ttl = an_ax_img.text (0.05, 1.05, title,
                                         transform=an_ax_img.transAxes,
                                         verticalalignment='top')

            an_fr1 = an_ax_img.imshow (dat, origin='lower', 
                                       vmin=im_min, vmax=im_max, 
                                       cmap=cm_arg, aspect=yratio,
                                       animated=True)
            # an_ttl.set_text(inum)
            # an_ttl.figure.canvas.draw()

            an_frames.append([an_fr1])

        else:
            # Regular frame display

            # Open Figure and subplot boxes
            fg = plt.figure(figsize=(6.5, 6.5))
            ax_img = fg.add_axes (rect=rect_img)
            ax_img.tick_params(direction='in', labelsize='x-small')
            #                   labelbottom=False, labelleft=False)

            if (marg_plot == True):
                ax_xma = fg.add_axes (rect=rect_xmarg, sharex=ax_img)
                ax_yma = fg.add_axes (rect=rect_ymarg, sharey=ax_img)

                ax_xma.tick_params(direction='in', labelsize='x-small',
                                   labelbottom=False)
                ax_yma.tick_params(direction='in', labelsize='x-small',
                                   labelleft=False)
            
                ax_img.imshow (dat, origin='lower', vmin=im_min, vmax=im_max,
                               cmap=cm_arg, aspect=yratio)
                # norm=clrs.Normalize().autoscale(lgs))

            # Add plot title, with possible frame counter
            if (title != None):
                if (title == 'sliced'):
                    ttl_str = (str(hdr['OR3DFILE']))
                elif (title == 'object'):
                    ttl_str =(str(hdr['OBJECT']))
                else:
                    ttl_str = (title)

                if (nfr > 1):
                    ttl_str += ' ({} of {})'.format(inum + 1, nfr)

            if (marg_plot == True):
                # ax_img.plot (xidx, xmarg)
                ax_xma.plot (xidx, xmarg, linewidth=1)
                ax_yma.plot (ymarg, yidx, linewidth=1)

                if (title != None):
                    ax_xma.set_title (ttl_str)
                    
            else:
                if (title != None):
                    ax_img.set_title (ttl_str)


            # Setup out or display for image
            if ((outfile == None) or (outfile.lower() == 'screen')):
                plt.show()
            elif (outfile.lower() == 'skip'):
                pass
            elif (outfile != None):
                plt.savefig (outfile, orientation='portrait')
            else:
                plt.show()

    if (anim != 0):
        # If requested, write out animation file

        if (anim < 0):
            rpt = True
        else:
            rpt = False

        ani = animation.ArtistAnimation (an_fg, an_frames, interval=abs(anim),
                                    blit=True, repeat=rpt)

        # Setup out or display for image
        if ((outfile == None) or (outfile.lower() == 'screen')):
            plt.show()

        elif (outfile.lower() == 'skip'):
            pass

        elif (outfile != None):
            an_writer = animation.FFMpegWriter(fps=10)
#                                               metadata=dict(artist='Me'),
#                                               bitrate=1800)
# extra_args=['-vcodec', 'libx264']
            ani.save(outfile, writer=an_writer)

        else:
            plt.show()

    return

#------------------------------------------------------------------------
def parse_cmd_line (iargv):
    """
    Read and parse the command line
    """

    # --- Default inputs ---

    fits_input0 = './*.fits'

    # Prep the line for input
    argc = len(iargv)
    print ('argc = {} {}'.format(argc,iargv[0]))

    # Parse command line input
    # - using argparse

    cli = argparse.ArgumentParser(prog='display_fits.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    cli.add_argument ('fitsfiles', nargs='?', default=fits_input0,
                      help='Required Input Filename - Fits files. ' + 
                      'Default: ' + fits_input0)

    def_anim = 0
    cli.add_argument ('-a', '--anim', type=int, default=def_anim,
                      help='Only for image cubes.  Delay between ' +
                      'images in animation in millisec if not zero. ' +
                      'If less than zero, repeats the loop. ' +
                      'Default: ' + str(def_anim))

    def_xylims3 = []
    str_def_xylims3 = '[min:max, min:max, min:max]'
    cli.add_argument ('-B', '--Bounds', type=int, nargs=6, default=def_xylims3,
                      help='Image bounds (in pixels). ' + 
                      'Default: ' + str(str_def_xylims3))

    def_xylims = []
    str_def_xylims = '[min:max, min:max]'
    cli.add_argument ('-b', '--bounds', type=int, nargs=4, default=def_xylims,
                      help='Image bounds (in pixels). ' + 
                      'Default: ' + str(str_def_xylims))

    def_cmap = 'inv'
    cmap_options = ['inv', 'non', 'Greys', 'gray', 
                    'gist_gray', 'gist_yarg', 'viridis', 'magma']
    cli.add_argument ('-c', '--cmap', type=str, default=def_cmap,
                      choices=cmap_options,
                      help='Color Map Choices. ' + 
                      'Default: ' + def_cmap)

    def_lims = 'zscale'
    lims_options = ['zscale', 'minmax']
    cli.add_argument ('-l', '--lims', type=str, default=def_lims,
                      choices=lims_options,
                      help='Auto Scaling Limit Choices. ' + 
                      'Default: ' + def_lims)

    def_disp = []
    str_def_disp = '[min, max]'
    cli.add_argument ('-m', '--displims', type=float, nargs=2, 
                      default=def_disp,
                      help='Display range values ' + 
                      'Default: ' + str(str_def_disp))

    def_output = 'screen'
    cli.add_argument ('-o', '--output', type=str, default=def_output,
                      help='Output file name. Output file type is ' +
                      'determined from the file post-fix. ' + 
                      'Default: ' + def_output)

    def_rgb = 'n'
    rgb_options = ['+', 'y', 'Y', '-', 'n', 'N']
    cli.add_argument ('-R', '--rgb', type=str, default=def_rgb,
                      choices=rgb_options,
                      help='Input image is RGB file (y/n). ' + 
                      'Default: ' + def_rgb)

    def_rms = 1
    cli.add_argument ('-r', '--rms', type=float, default=def_rms,
                      help='Num of +/- RMS about average for zscale. ' + 
                      'Default: ' + str(def_rms))

    def_mplot = '+'
    mplot_options = ['+', 'y', 'Y', '-', 'n', 'N']
    cli.add_argument ('-s', '--sums', type=str, default=def_mplot,
                      choices=mplot_options,
                      help='Turn on(+) or off(-) marginal sum plots. ' + 
                      'Default: ' + def_mplot)
    
    def_title = 'filename'
    cli.add_argument ('-t', '--title', type=str, default=def_title,
                      help='Display title. ' + 
                      'Default: ' + str(def_title))

    def_yscl = 1.0
    cli.add_argument ('-y', '--yscale', type=float, default=def_yscl,
                      help='Y expansion factor. ' + 
                      'Default: ' + str(def_yscl))

    def_zstep = 1
    cli.add_argument ('-z', '--zstep', type=int, default=def_zstep,
                      help='For 3D image cubes, stride in z.  ' +
                      'Default: ' + str(def_zstep))

    args = cli.parse_args(args=iargv[1:])

    anim = args.anim
    print ('anim = {}'.format(anim))

    fits_input = args.fitsfiles
    print ('fits_input = {}'.format(fits_input))

    cmap = args.cmap
    print ('cmap = {}'.format(cmap))

    disp_lims = args.displims
    if (disp_lims != []):
        print ('display min,max = {} {}'.format(np.min(disp_lims), 
                                                np.max(disp_lims)))
    else:
        print ('display min,max = {} {}'.format('min', 'max'))

    lims = args.lims
    lrms = args.rms
    print ('limits, lrms = {} {}'.format(lims, lrms))

    mplot = args.sums
    print ('display marginal sums = {}'.format(mplot))
    if ((mplot == '-') or (mplot == 'n') or (mplot == 'N')):
        marg_plot = False
    else:
        marg_plot = True

    title = args.title
    print ('display title = {}'.format(title))

    outfile = args.output
    print ('output file = {}'.format(outfile))

    naxlims = args.bounds
    print ('x(min,max), y(min,max) bounds = {}'.format(naxlims))

    if (naxlims == []):
        naxlims = args.Bounds
        print ('x(min,max), y(min,max), z(min,max) bounds = {}'.\
                   format(naxlims))

    rgb = args.rgb
    print ('Image is rgb = {}'.format(rgb))
    if ((rgb == '+') or (rgb == 'y') or (rgb == 'Y')):
        isrgb = True
    else:
        isrgb = False

    yscale = args.yscale
    if (yscale <= 0.0):
        print ('Y expansion factor {} must be >= 0.0'.format(yscale))
        print ('Setting to 1.0')
        yscale = 1.0
    print ('Y expansion factor = {}'.format(yscale))

    zstep = args.zstep
    if (zstep < 1):
        print ('z stride {} must be >= 1.'.format(zstep))
        print ('Setting to 1')
        zstep = 1
    print ('z stride = {}'.format(zstep))
        
    return anim, fits_input, cmap, disp_lims, lims, lrms, \
        marg_plot, title, outfile, naxlims, isrgb, yscale, zstep

#------------------------------------------------------------------------
def display_fits_main (iargv):
    """
    Run simple fits image display.
    """

    # Read and parse the command line
    anim, fits_input, cmap, disp_lims, lims, lrms, \
        marg_plot, title, outfile, naxlims, isrgb, yscale, zstep \
        = parse_cmd_line (iargv)

    # Get list of files for display
    f_files = ru.expand_list_files2(ipfiles=fits_input)

    # Loop through files, open and display
    for pf in f_files:
        hdr, dat = rf.load_fits_file (pf)
        if (title == 'filename'):
            dtitle = pf
        else:
            dtitle = title

        # set up special meanings for outfile to write multiple
        # images to files based on the input file name
        if (outfile == 'filename'):
            ofile = pf + '.png'
        elif (outfile == 'filename.png'):
            ofile = pf + '.png'
        elif (outfile == 'filename.pdf'):
            ofile = pf + '.pdf'
        else:
            ofile = outfile

        display_2d_margs_img (hdr, dat, title=dtitle, outfile=ofile,
                              cm=cmap, 
                              disp_lims=disp_lims, lims=lims, lrms=lrms,
                              marg_plot=marg_plot,
                              naxlims=naxlims, isrgb=isrgb,
                              yratio=yscale,
                              anim=anim, zstep=zstep)

    return

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    display_fits_main (argv)
    
    exit()

#------------------------------------------------------------------------
# Un-used code snippet(s)

def display_2d_fits_img (hdr, dat, title=None, outfile=None):
    """\
    Display a single 2-D FITS image.
    Not used at this point.
    Test code.
    """
    fg, ax = plt.subplots(1, 1, sharex='col', sharey='row',
                          squeeze=True)

    ax.tick_params(direction='in')
    fg.subplots_adjust (wspace=0.0, hspace=0.0)
    # ax.plot (x, y, 'b.', label=lbl)

    # Set default image min,max = avg +/- 1 RMS
    im_average = np.average(dat)
    im_rms = np.std(dat)
    im_min = im_average - im_rms
    im_max = im_average + im_rms

    ax.imshow (dat, origin='lower', vmin=im_min, vmax=im_max, 
                   cmap='Greys')
    # norm=clrs.Normalize().autoscale(lgs))

    if (title != None):
        ax.set_title (title)

    if (outfile == None):
        plt.show()
    elif (outfile.lower() == 'skip'):
        pass
    elif (outfile != None):
        plt.savefig (outfile, orientation='portrait')
    else:
        plt.show()

    return

