# -*- coding: utf-8 -*-

import os

from fury import window, actor
from matplotlib.cm import get_cmap
import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def screenshot_mosaic_wrapper(filename, output_prefix="", directory=".", skip=1,
                              pad=20, nb_columns=15, axis=True, cmap=None,
                              return_path=True):
    """
    Compute mosaic wrapper from an image

    Parameters
    ----------
    filename : string
        Image filename.
    output_prefix : string
        Image_prefix.
    directory : string
        Directory to save the mosaic.
    skip : int
        Number of images to skip between 2 images in the mosaic.
    pad : int
        Padding value between each images.
    nb_columns : int
        Number of columns.
    axis : bool
        Display axis.
    cmap : string
        Colormap name in matplotlib format.
    return_path : bool
        Return path of the mosaic


    Returns
    -------
    name : string
        Path of the mosaic
    imgs_comb : array 2D
        mosaic in array 2D
    """
    data = nib.load(filename).get_data()
    data = np.nan_to_num(data)

    imgs_comb = screenshot_mosaic(data, skip, pad, nb_columns, axis, cmap)

    if return_path:
        image_name = os.path.basename(str(filename)).split(".")[0]
        if isinstance(imgs_comb, list):
            name = os.path.join(directory, output_prefix + image_name + '.gif')
            imgs_comb[0].save(name, save_all=True, append_images=imgs_comb[1:],
                              duration=100, loop=0)
        else:
            name = os.path.join(directory, output_prefix + image_name + '.png')
            imgs_comb.save(name)
        return name
    else:
        return imgs_comb


def screenshot_mosaic_blend(image, mask, output_prefix="", directory=".",
                            blend_val=0.5, skip=1, pad=20, nb_columns=15,
                            cmap=None):
    """
    Compute a blend mosaic from an image and a mask

    Parameters
    ----------
    image : string
        Image filename.
    mask : string
        Mask filename.
    output_prefix : string
        Image_prefix.
    directory : string
        Directory to save the mosaic.
    blend_val : float
        Blending value.
    skip : int
        Number of images to skip between 2 images in the mosaic.
    pad : int
        Padding value between each images.
    nb_columns : int
        Number of columns.
    cmap : string
        Colormap name in matplotlib format.


    Returns
    -------
    name : string
        Path of the mosaic
    """
    mosaic_image = screenshot_mosaic_wrapper(image, skip=skip, pad=pad,
                                             nb_columns=nb_columns,
                                             axis=False,
                                             cmap=cmap,
                                             return_path=False)
    mask_mosaic = screenshot_mosaic_wrapper(mask, skip=skip, pad=pad,
                                            nb_columns=nb_columns,
                                            axis=False, return_path=False)

    data = np.array(mask_mosaic)
    data[(data == (255, 255, 255)).all(axis=-1)] = (255, 0, 0)
    mask_mosaic = Image.fromarray(data, mode="RGB")

    image_name = os.path.basename(str(image)).split(".")[0]
    if isinstance(mosaic_image, list):
        blend = []
        for _, mosaic in enumerate(mosaic_image):
            blend.append(Image.blend(mosaic, mask_mosaic,
                                     alpha=blend_val))
        name = os.path.join(directory, output_prefix + image_name + '.gif')
        blend[0].save(name, save_all=True, append_images=blend[1:],
                      duration=100, loop=0)
    else:
        blend = Image.blend(mosaic_image, mask_mosaic, alpha=blend_val)
        name = os.path.join(directory, output_prefix + image_name + '.png')
        blend.save(name)
    return name


def screenshot_mosaic(data, skip, pad, nb_columns, axis, cmap):
    """
    Compute a mosaic from an image

    Parameters
    ----------
    data : array 3D or 4D
        Data for the mosaic.
    skip : int
        Number of images to skip between 2 images in the mosaic.
    pad : int
        Padding value between each images.
    nb_columns : int
        Number of columns.
    axis : bool
        Display axis.
    cmap : string
        Colormap name in matplotlib format.

    Returns
    -------
    gif : array 3D
        GIF in array 3D
    imgs_comb : array 2D
        mosaic in array 2D
    """
    range_row = range(0, data.shape[2], skip)
    nb_rows = int(np.ceil(len(range_row) / nb_columns))
    is_4d = True if len(data.shape) == 4 else False

    unique = np.unique(data)
    min_val = np.min(data[data > 0])
    max_val = np.percentile(data[data > 0], 99)
    shape = ((data[:, :, 0].shape[1] + pad) * nb_rows + pad * nb_rows,
             (data[:, :, 0].shape[0] + pad) * nb_columns + nb_columns * pad)
    padding = ((int(pad / 2), int(pad / 2)), (int(pad / 2), int(pad / 2)))

    if is_4d:
        time = data.shape[3]
        shape += (time, )
        padding += ((0, 0), )

    if len(unique) > 20:
        data = np.float32(data - min_val) \
            / np.float32(max_val - min_val) * 255.0
    elif len(unique) > 2:
        data = np.interp(data, xp=[data.min(), data.max()], fp=[0, 255])
    else:
        data *= 255

    mosaic = np.zeros(shape)
    for i, idx in enumerate(range_row):
        corner = i % nb_columns
        row = int(i / nb_columns)
        curr_img = np.rot90(data[:, :, idx])

        curr_img = np.pad(curr_img, padding, 'constant')
        curr_shape = curr_img.shape
        mosaic[curr_shape[0] * row + row * pad:
               row * curr_shape[0] + curr_shape[0] + row * pad,
               curr_shape[1] * corner + corner * pad:
               corner * curr_shape[1] + curr_shape[1] + corner * pad] = curr_img

    if axis and not is_4d:
        mosaic = np.pad(mosaic, ((50, 50), (50, 50)), 'constant')
        img = Image.fromarray(mosaic)
        draw = ImageDraw.Draw(img)

        fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 40)
        draw.text([mosaic.shape[1] / 2, 0], "A", fill=255, font=fnt)
        draw.text([mosaic.shape[1] / 2, mosaic.shape[0] - 40], "P", fill=255,
                  font=fnt)
        draw.text([0, mosaic.shape[0] / 2], "L", fill=255, font=fnt)
        draw.text([mosaic.shape[1] - 40, mosaic.shape[0] / 2], "R", fill=255,
                  font=fnt)
        mosaic = np.array(img)

    if cmap is not None:
        colormap = get_cmap(cmap)
        mosaic = colormap(mosaic/255.0) * 255

    if is_4d and mosaic.shape[2] > 3:
        gif = []
        for i in range(mosaic.shape[2]):
            img_t = np.uint8(np.clip(mosaic[:, :, i], 0, 255))
            imgs_comb = Image.fromarray(img_t)
            gif.append(imgs_comb.convert("RGB"))
        return gif
    else:
        img = np.uint8(np.clip(mosaic, 0, 255))
        imgs_comb = Image.fromarray(img)
        imgs_comb = imgs_comb.convert("RGB")
        return imgs_comb


def screenshot_fa_peaks(fa, peaks, directory='.'):
    """
    Compute 3 view screenshot with peaks on FA.

    Parameters
    ----------
    fa : string
        FA filename.
    peaks : string
        Peak filename.
    directory : string
        Directory to save the mosaic.

    Returns
    -------
    name : string
        Path of the mosaic
    """
    slice_name = ['sagittal', 'coronal', 'axial']
    data = nib.load(fa).get_data()
    evecs_data = nib.load(peaks).get_data()

    evecs = np.zeros(data.shape + (1, 3))
    evecs[:, :, :, 0, :] = evecs_data[...]

    middle = [data.shape[0] // 2 + 4, data.shape[1] // 2,
              data.shape[2] // 2]

    slice_display = [(middle[0], None, None), (None, middle[1], None),
                     (None, None, middle[2])]

    concat = []
    for j, slice_name in enumerate(slice_name):
        image_name = os.path.basename(str(peaks)).split(".")[0]
        name = os.path.join(directory, image_name + '.png')
        slice_actor = actor.slicer(data, interpolation='nearest', opacity=0.3)
        peak_actor = actor.peak_slicer(evecs, colors=None)

        peak_actor.GetProperty().SetLineWidth(2.5)

        slice_actor.display(slice_display[j][0], slice_display[j][1],
                            slice_display[j][2])
        peak_actor.display(slice_display[j][0], slice_display[j][1],
                           slice_display[j][2])

        renderer = window.ren()

        renderer.add(slice_actor)
        renderer.add(peak_actor)

        center = slice_actor.GetCenter()
        pos = None
        viewup = None
        if slice_name == "sagittal":
            pos = (center[0] - 350, center[1], center[2])
            viewup = (0, 0, -1)
        elif slice_name == "coronal":
            pos = (center[0], center[1] + 350, center[2])
            viewup = (0, 0, -1)
        elif slice_name == "axial":
            pos = (center[0], center[1], center[2] + 350)
            viewup = (0, -1, 1)

        camera = renderer.GetActiveCamera()
        camera.SetViewUp(viewup)

        camera.SetPosition(pos)
        camera.SetFocalPoint(center)

        img = window.snapshot(renderer, size=(1080, 1080), offscreen=True)
        if len(concat) == 0:
            concat = img
        else:
            concat = np.hstack((concat, img))

    imgs_comb = Image.fromarray(concat)
    imgs_comb.save(name)

    return name
