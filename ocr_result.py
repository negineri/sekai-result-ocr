from PIL import Image, ImageChops
import pyocr
import sys
from typing import Optional
import requests
import unicodedata
import difflib
import copy
import match_tpl

NOTES_THRESHOLD = 190


class OCRException(Exception):
    ...


class ScoreResult:
    def __init__(self):
        self.live = ""
        self.title = ""
        self.difficulty = ""
        self.perfect = 0
        self.great = 0
        self.good = 0
        self.bad = 0
        self.miss = 0
        self.x_series = ""

    def to_dict(self):
        res = {'live': self.live,
               'title': self.title,
               'difficulty': self.difficulty,
               'perfect': self.perfect,
               'great': self.great,
               'good': self.good,
               'bad': self.bad,
               'miss': self.miss,
               'x_series': self.x_series}
        return res


class ScoreResultChecker:
    def __init__(self) -> None:
        self.music_combos = {}
        self.musics_url = "https://sekai-world.github.io/sekai-master-db-diff/musics.json"
        self.music_difficulties_url = "https://sekai-world.github.io/sekai-master-db-diff/musicDifficulties.json"
        try:
            self.update()
        except OCRException as err:
            raise err

    def __correct_title(self, title):
        title = unicodedata.normalize('NFKC', title)
        match_ratio = 0
        correct_title = ""
        for t in self.music_combos:
            s = difflib.SequenceMatcher(None, t, title).ratio()
            if s > match_ratio:
                match_ratio = s
                correct_title = t
        return correct_title

    def correct(self, score_result: ScoreResult) -> Optional[ScoreResult]:
        res = copy.deepcopy(score_result)
        if score_result.title not in self.music_combos:
            res.title = self.__correct_title(score_result.title)
        nc = self.music_combos[res.title][res.difficulty.lower()]
        nr = res.perfect + res.great + res.good + res.bad + res.miss
        if nc != nr:
            return None
        return res

    def update(self) -> None:
        try:
            musics_data = requests.get(self.musics_url)
        except requests.exceptions.RequestException:
            raise OCRException("Failed to download musics.json")
        musics = musics_data.json()
        try:
            music_difficulties_data = requests.get(self.music_difficulties_url)
        except requests.exceptions.RequestException:
            raise OCRException("Failed to download musicDifficulties.json")
        music_difficulties = music_difficulties_data.json()
        for d in music_difficulties:
            music_title = ""
            for m in musics:
                if d["musicId"] == m["id"]:
                    music_title = m["title"]
                    break
            if music_title not in self.music_combos:
                self.music_combos[music_title] = {}
            self.music_combos[music_title][d["musicDifficulty"]] = d["noteCount"]


class ResultReader:
    def __init__(self, tpl_path: str) -> None:
        self.matcher = match_tpl.TPLMatcher(tpl_path)

    def __resize_image(self, img, magnification):
        ImgWidth = img.width * magnification
        ImgHeight = img.height * magnification
        img_resize = img.resize((int(ImgWidth), int(ImgHeight)), Image.LANCZOS)
        return img_resize

    def __correct_num(self, num: str) -> str:
        res = ""
        for c in num:
            if c in ['U', 'O']:
                res += '0'
            elif c in ['I', 'l']:
                res += '1'
            else:
                res += c
        return res

    def __crop_score(self, im: Image.Image, w, h, tool, result: ScoreResult, debug=False) -> Optional[Image.Image]:
        xs_buffer = h * 0.018   # iPhone X series homebar buffer

        for b in [0, xs_buffer]:
            im_score = im.crop((int(w * 0.041), int(h * 0.622 - b), int(w * 0.526), int(h * 0.964 - b)))
            im_perfect = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.259), int(im_score.width * 0.978), int(im_score.height * 0.379))).\
                convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
            perfect = tool.image_to_string(im_perfect, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
            if debug:
                print(perfect)
                im_perfect.save(f"data/dst/perfect_c_{b}.png", "PNG")
            if perfect.isdecimal():
                try:
                    perfect = self.matcher.match(match_tpl.pil2cv(im_perfect))
                except match_tpl.TPLMatchException as err:
                    print(err)
                    return None
                if debug:
                    print(f"perfect: {perfect}", end="")
                result.live = "challenge"
                result.perfect = int(perfect)
                if b == 0:
                    result.x_series = "no"
                else:
                    result.x_series = "yes"
                return im_score

            im_score = im.crop((int(w * 0.101), int(h * 0.512 - b), int(w * 0.586), int(h * 0.854 - b)))
            im_perfect = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.259), int(im_score.width * 0.978), int(im_score.height * 0.379))).\
                convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
            perfect = tool.image_to_string(im_perfect, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
            if debug:
                print(perfect)
                im_perfect.save(f"data/dst/perfect_n_{b}.png", "PNG")
            if perfect.isdecimal():
                try:
                    perfect = self.matcher.match(match_tpl.pil2cv(im_perfect))
                except match_tpl.TPLMatchException as err:
                    print(err)
                    return None
                if debug:
                    print(f"perfect: {perfect}", end="")
                result.live = "normal"
                result.perfect = int(perfect)
                if b == 0:
                    result.x_series = "no"
                else:
                    result.x_series = "yes"
                return im_score
        return None

    def loadfile(self, fp: str, debug=False) -> Optional[ScoreResult]:
        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            print("No OCR tool found")
            sys.exit(1)
        tool = tools[0]
        result = ScoreResult()
        im = Image.open(fp)
        im = self.__resize_image(im, 1080 / im.height + 1)
        bg = Image.new("L", im.size)
        im_mono = im.convert("L").point(lambda _: 255 if _ > 10 else 0)
        diff = ImageChops.difference(im_mono, bg)
        croprange = diff.convert("RGB").getbbox()
        if croprange is not None:
            im = im.crop(croprange)

        if im.height / im.width > 0.5625:
            h = int(im.width * 0.5625)
            w = im.width
            im_crop = im.crop((0, int((im.height - h) / 2), w, int((im.height - h) / 2) + h))
            im_difficulty = im.crop((int(w * 0.091), int(h * 0.077), int(w * 0.175), int(h * 0.117))).\
                convert("L").point(lambda _: 0 if _ > 200 else 255)
            im_title = im.crop((int(w * 0.081), int(h * 0.010), int(w * 0.5), int(h * 0.056))).\
                convert("L").point(lambda _: 0 if _ > 180 else 255)
        else:
            w = int(im.height * 16 / 9)
            h = im.height
            im_crop = im.crop((int((im.width - w) / 2), 0, int((im.width - w) / 2) + w, h))
            im_difficulty = im_crop.crop((int(w * 0.091), int(h * 0.077), int(w * 0.175), int(h * 0.117))).\
                convert("L").point(lambda _: 0 if _ > 200 else 255)
            im_title = im_crop.crop((int(w * 0.081), int(h * 0.010), int(w * 0.5), int(h * 0.056))).\
                convert("L").point(lambda _: 0 if _ > 180 else 255)

        im_score = self.__crop_score(im_crop, w, h, tool, result, debug)
        if im_score is None:
            print("im_score is none")
            return None

        if debug:
            im_title.save("data/dst/title.png", "PNG")
            im_difficulty.save("data/dst/difficulty.png", "PNG")
            im_crop.save("data/dst/crop.png", "PNG")
            im.save("data/dst/im.png", "PNG")
            im_mono.save("data/dst/im_mono.png", "PNG")
            # print(f"{croprange}")

        im_great = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.399), int(im_score.width * 0.978), int(im_score.height * 0.522))).\
            convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
        try:
            great = self.matcher.match(match_tpl.pil2cv(im_great))
        except match_tpl.TPLMatchException as err:
            print(err)
            return None
        if debug:
            print(f"/ great: {great} ", end="")
            im_great.save("data/dst/great.png", "PNG")
        result.great = int(great)

        im_good = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.542), int(im_score.width * 0.978), int(im_score.height * 0.665))).\
            convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
        try:
            good = self.matcher.match(match_tpl.pil2cv(im_good))
        except match_tpl.TPLMatchException as err:
            print(err)
            return None
        if debug:
            print(f"/ good: {good} ", end="")
            im_good.save("data/dst/good.png", "PNG")
        result.good = int(good)

        im_bad = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.685), int(im_score.width * 0.978), int(im_score.height * 0.808))).\
            convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
        try:
            bad = self.matcher.match(match_tpl.pil2cv(im_bad))
        except match_tpl.TPLMatchException as err:
            print(err)
            return None
        if debug:
            print(f"/ bad: {bad} ", end="")
            im_bad.save("data/dst/bad.png", "PNG")
        result.bad = int(bad)

        im_miss = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.828), int(im_score.width * 0.978), int(im_score.height * 0.948))).\
            convert("L").point(lambda _: 0 if _ > NOTES_THRESHOLD else 255)
        try:
            miss = self.matcher.match(match_tpl.pil2cv(im_miss))
        except match_tpl.TPLMatchException as err:
            print(err)
            return None
        if debug:
            print(f"/ miss: {miss} ", end="")
            im_miss.save("data/dst/miss.png", "PNG")
        result.miss = int(miss)

        title = tool.image_to_string(im_title, lang="jpn", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
        if debug:
            print(f"/ title: {title} ")
        result.title = title

        difficulty = tool.image_to_string(im_difficulty, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
        if debug:
            print(f"/ difficulty: {difficulty}")
        match_ratio = 0
        correct_difficulty = ""
        for d in ["EASY", "NORMAL", "HARD", "EXPERT", "MASTER"]:
            s = difflib.SequenceMatcher(None, d, difficulty).ratio()
            if s > match_ratio:
                match_ratio = s
                correct_difficulty = d
        result.difficulty = correct_difficulty

        return result
