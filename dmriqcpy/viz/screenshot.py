# -*- coding: utf-8 -*-

import os

from fury import window, actor
from matplotlib.cm import get_cmap
import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from dmriqcpy.viz.utils import renderer_to_arr


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


def screenshot_mosaic_blend(image, image_blend, output_prefix="", directory=".",
                            blend_val=0.5, skip=1, pad=20, nb_columns=15,
                            cmap=None, is_mask=False):
    """
    Compute a blend mosaic from an image and a mask

    Parameters
    ----------
    image : string
        Image filename.
    image_blend : string
        Image blend filename.
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
    is_mask : bool
        Image blend is a mask.


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
    image_mosaic = screenshot_mosaic_wrapper(image_blend, skip=skip, pad=pad,
                                             nb_columns=nb_columns,
                                             axis=False, return_path=False)

    if is_mask:
        data = np.array(image_mosaic)
        data[(data == (255, 255, 255)).all(axis=-1)] = (255, 0, 0)
        image_mosaic = Image.fromarray(data, mode="RGB")

    image_name = os.path.basename(str(image)).split(".")[0]
    if isinstance(mosaic_image, list):
        blend = []
        for _, mosaic in enumerate(mosaic_image):
            blend.append(Image.blend(mosaic, image_mosaic,
                                     alpha=blend_val))
        name = os.path.join(directory, output_prefix + image_name + '.gif')
        blend[0].save(name, save_all=True, append_images=blend[1:],
                      duration=100, loop=0)
    else:
        blend = Image.blend(mosaic_image, image_mosaic, alpha=blend_val)
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

    is_rgb = False
    if is_4d:
        time = data.shape[3]
        if time == 3:
            is_rgb = True
        shape += (time, )
        padding += ((0, 0), )

    if not is_rgb:
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

        fnt = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 40)
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

    if is_4d and mosaic.shape[2] != 3:
        gif = []
        for i in range(mosaic.shape[2]):
            img_t = np.uint8(np.clip(mosaic[:, :, i], 0, 255))
            imgs_comb = Image.fromarray(img_t)

            draw = ImageDraw.Draw(imgs_comb)
            fnt = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 40)
            draw.text([0, 0], str(i), fill=255, font=fnt)

            gif.append(imgs_comb.convert("RGB"))
        return gif
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

        img = renderer_to_arr(renderer, (1080, 1080))
        if len(concat) == 0:
            concat = img
        else:
            concat = np.hstack((concat, img))

    imgs_comb = Image.fromarray(concat)
    imgs_comb.save(name)

    return name


def screenshot_tracking(tracking, t1, directory="."):
    """
    Compute 3 view screenshot with streamlines on T1.

    Parameters
    ----------
    tracking : string
        tractogram filename.
    t1 : string
        t1 filename.
    directory : string
        Directory to save the mosaic.

    Returns
    -------
    name : string
        Path of the mosaic
    """
    tractogram = nib.streamlines.load(tracking, True).tractogram
    t1 = nib.load(t1)
    t1_data = t1.get_data()

    slice_name = ['sagittal', 'coronal', 'axial']
    img_center = [(int(t1_data.shape[0] / 2) + 5, None, None),
                  (None, int(t1_data.shape[1] / 2), None),
                  (None, None, int(t1_data.shape[2] / 2))]
    center = [(330, 90, 60), (70, 330, 60), (70, 90, 400)]
    viewup = [(0, 0, -1), (0, 0, -1), (0, -1, 0)]
    size = (1920, 1080)

    image = np.array([])
    for i, _axis in enumerate(slice_name):
        streamlines = []
        it = 0
        slice_idx = img_center[i][i]

        for streamline in tractogram:
            if it > 10000:
                break
            stream = streamline.streamline
            if slice_idx in np.array(stream, dtype=int)[:, i]:
                it += 1
                idx = np.where(np.array(stream, dtype=int)[:, i] ==\
                                        slice_idx)[0][0]
                lower = idx - 2
                if lower < 0:
                    lower = 0
                upper = idx + 2
                if upper > len(stream) - 1:
                    upper = len(stream) - 1
                streamlines.append(stream[lower:upper])

        ren = window.Renderer()

        streamline_actor = actor.line(streamlines, linewidth=0.2)
        ren.add(streamline_actor)

        min_val = np.min(t1_data[t1_data > 0])
        max_val = np.percentile(t1_data[t1_data > 0], 99)
        t1_color = np.float32(t1_data - min_val) \
                   / np.float32(max_val - min_val) * 255.0
        slice_actor = actor.slicer(t1_color, opacity=0.8, value_range=(0, 255),
                                   interpolation='nearest')
        ren.add(slice_actor)
        slice_actor.display(img_center[i][0], img_center[i][1],
                            img_center[i][2])

        camera = ren.GetActiveCamera()
        camera.SetViewUp(viewup[i])
        center_cam = streamline_actor.GetCenter()
        camera.SetPosition(center[i])
        camera.SetFocalPoint((center_cam))

        img2 = renderer_to_arr(ren, size)
        if image.size == 0:
            image = img2
        else:
            image = np.hstack((image, img2))

    imgs_comb = Image.fromarray(image)
    imgs_comb = imgs_comb.resize((3*1920, 1080))
    image_name = os.path.basename(str(tracking)).split(".")[0]
    name = os.path.join(directory, image_name + '.png')
    imgs_comb.save(name)

    return name
