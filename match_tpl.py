import cv2
import numpy as np
import os.path


class TPLMatchException(Exception):
    ...


def pil2cv(image):
    ''' PIL型 -> OpenCV型 '''
    new_image = np.array(image, dtype=np.uint8)
    if new_image.ndim == 2:  # モノクロ
        pass
    elif new_image.shape[2] == 3:  # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
    elif new_image.shape[2] == 4:  # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)
    return new_image


def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
                                        key=lambda b: b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return (cnts, boundingBoxes)


class TPLMatcher:
    def __init__(self, tpls_path: str) -> None:
        self.tpls = [0] * 10
        for j in range(10):
            i_tmpl = cv2.imread(os.path.join(tpls_path, f"{j}.png"))
            self.tpls[j] = cv2.cvtColor(i_tmpl, cv2.COLOR_BGR2GRAY)
        self.bg = np.zeros((100, 100, 3), np.uint8)
        self.bg[:, :] = (255, 255, 255)
        self.bg = cv2.cvtColor(self.bg, cv2.COLOR_BGR2GRAY)

    def match(self, im_wb) -> str:
        im_bw = cv2.bitwise_not(im_wb)
        # im_bw = im_gray

        # 輪郭の検出
        cnts, _ = cv2.findContours(im_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        contours, _ = sort_contours(cnts)

        num = ""
        for i in range(len(contours)):
            base = self.bg.copy()
            x, y, w, h = cv2.boundingRect(contours[i])
            crop = im_wb[y:y + h, x:x + w]
            nw = int(w * 80 / h)
            try:
                t = cv2.resize(crop, (nw, 80))
            except Exception:
                raise TPLMatchException("Failed to tplmatch")
            x_offset = int((100 - nw) / 2)
            y_offset = 10
            try:
                base[y_offset:y_offset + t.shape[0], x_offset:x_offset + t.shape[1]] = t
            except Exception:
                raise TPLMatchException("Failed to tplmatch")

            maxVal_All = 0.4
            num_dsp = -1
            for j in range(10):
                result = cv2.matchTemplate(base, self.tpls[j], cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val > maxVal_All:
                    num_dsp = j
                    maxVal_All = max_val
            num += str(num_dsp)
        return num
