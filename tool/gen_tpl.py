from PIL import Image


def __resize_image(img, magnification):
    ImgWidth = img.width * magnification
    ImgHeight = img.height * magnification
    img_resize = img.resize((int(ImgWidth), int(ImgHeight)), Image.LANCZOS)
    return img_resize


im = Image.open("/workspace/data/src/combo.png")
im = __resize_image(im, 1080 / im.height + 1)
bg = Image.new("L", im.size)
im_mono = im.convert("L").point(lambda _: 255 if _ > 220 else 0)
im_mono.save("data/tpls/combo.png", "PNG")
