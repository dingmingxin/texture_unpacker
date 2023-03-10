#/usr/local/bin/python
import os,sys
import errno
from xml.etree import ElementTree
from PIL import Image

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def tree_to_dict(tree):
    d = {}
    for index, item in enumerate(tree):
        if item.tag == 'key':
            if tree[index + 1].tag == 'string':
                d[item.text] = tree[index + 1].text
            elif tree[index + 1].tag == 'true':
                d[item.text] = True
            elif tree[index + 1].tag == 'false':
                d[item.text] = False
            elif tree[index + 1].tag == 'integer':
                d[item.text] = int(tree[index + 1].text);
            elif tree[index + 1].tag == 'real':
                d[item.text] = float(tree[index + 1].text);
            elif tree[index + 1].tag == 'dict':
                d[item.text] = tree_to_dict(tree[index + 1])
    return d

def do_unpack_format_0(plist_dict):
    info = {}
    for k,v in plist_dict['frames'].items():
        x = int(v["x"])
        y = int(v["y"])
        width = int(v["width"])
        height = int(v["height"])
        box = (x,y,x+width,y+height)

        data = {}
        data["box"] = box
        data["size"] = (width, height)
        info[k] = data

    return info

def do_unpack_format_2(plist_dict):
    to_list = lambda x: x.replace('{','').replace('}','').split(',')
    info = {}
    for k,v in plist_dict['frames'].items():
        box = to_list(v["frame"])
        x = int(box[0])
        y = int(box[1])
        rotated = v["rotated"]
        width = int(box[3] if rotated else box[2])
        height = int(box[2] if rotated else box[3])
        #width = int(box[2])
        #height = int(box[3])

        sourceSize = to_list(v["sourceSize"])
        box = (x,
               y,
               x+width,
               y+height)
        sourceSize = (int(sourceSize[0]), int(sourceSize[1]))
        result_box = (
                int((sourceSize[0] - width)/2),
                int((sourceSize[1] - height)/2),
                int((sourceSize[0] + width)/2),
                int((sourceSize[1] + height)/2),
                )
        data = {
                "box": box,
                "size": sourceSize,
                "result_box" : result_box,
                "rotated" : v["rotated"]
                }
        info[k] = data
    return info

def do_unpack_format_3(plist_dict):
    to_list = lambda x: x.replace('{','').replace('}','').split(',')
    info = {}
    for k,v in plist_dict['frames'].items():
        box = to_list(v["textureRect"])
        x = int(box[0])
        y = int(box[1])
        rotated = v["textureRotated"]
        width = int(box[3] if rotated else box[2])
        height = int(box[2] if rotated else box[3])

        sourceSize = to_list(v["spriteSourceSize"])
        box = (x,
               y,
               x+width,
               y+height)
        sourceSize = (int(sourceSize[0]), int(sourceSize[1]))
        result_box = (
                int((sourceSize[0] - width)/2),
                int((sourceSize[1] - height)/2),
                int((sourceSize[0] + width)/2),
                int((sourceSize[1] + height)/2),
                )
        data = {
                "box": box,
                "size": sourceSize,
                "result_box" : result_box,
                "rotated" : v["textureRotated"]
                }
        info[k] = data
    return info

def save_image_file(result_image, file_path, image_name):
    if not os.path.isdir(file_path):
        os.mkdir(file_path)
    outfile = os.path.join(file_path, image_name)
    outdir = os.path.dirname(outfile)
    mkdir_p(outdir)
    result_image.save(outfile)

def do_crop_images(big_image, file_path, images_info_dict):
    for k, v in images_info_dict.items():
        rect_on_big = big_image.crop(v["box"])
        image_size = v["size"]
        result_image = Image.new('RGBA', image_size, (0,0,0,0))
        if "result_box" in v:
            result_box = v["result_box"]
        else:
            result_box = (0,0, image_size[0], image_size[1])
        result_image.paste(rect_on_big, result_box, mask=0)
        if "rotated" in v and v["rotated"] == True:
            result_image = result_image.rotate(90)
        save_image_file(result_image, file_path, k)

def gen_png_from_plist(plist_filename, png_filename):
    file_path = plist_filename.replace('.plist', '')
    big_image = Image.open(png_filename)
    root = ElementTree.fromstring(open(plist_filename, 'r').read())
    plist_dict = tree_to_dict(root[0])
    
    plist_format = plist_dict["metadata"]["format"]

    images_info_dict = {}
    if ( plist_format == 0):
        images_info_dict = do_unpack_format_0(plist_dict)
    elif (plist_format == 1):
        images_info_dict = do_unpack_format_2(plist_dict)
    elif (plist_format == 2):
        images_info_dict = do_unpack_format_2(plist_dict)
    elif (plist_format == 3):
        images_info_dict = do_unpack_format_3(plist_dict)
    else:
        print("plist format not supported")

    if(len(images_info_dict) > 0):
        do_crop_images(big_image, file_path, images_info_dict)


if __name__ == '__main__':
    filename = sys.argv[1]
    plist_filename = filename + '.plist'
    image_filename = filename + '.webp'
    image_filename_png = filename + '.png'
    if os.path.exists(plist_filename):
        if os.path.exists(image_filename):
            gen_png_from_plist(plist_filename, image_filename)
        if os.path.exists(image_filename_png):
            gen_png_from_plist(plist_filename, image_filename_png)
    else:
        print("make sure you have boith plist and image files in the same directory")
