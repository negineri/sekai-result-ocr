from PIL import Image
import pyocr
import sys
from typing import Optional
import requests


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

    def to_dict(self):
        res = {'live': self.live,
               'title': self.title,
               'difficulty': self.difficulty,
               'perfect': self.perfect,
               'great': self.great,
               'good': self.good,
               'bad': self.bad,
               'miss': self.miss}
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

    def correct(self, score_result: ScoreResult) -> Optional[ScoreResult]:
        if score_result.title not in self.music_combos:
            return None
        nc = self.music_combos[score_result.title][score_result.difficulty.lower()]
        nr = score_result.perfect + score_result.great + score_result.good + score_result.bad + score_result.miss
        if nc != nr:
            return None
        return score_result

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


def loadfile(fp: str) -> Optional[ScoreResult]:
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    tool = tools[0]
    result = ScoreResult()
    im = Image.open(fp)
    if im.height / im.width > 0.5625:
        h = int(im.width * 0.5625)
        w = im.width
        im_crop = im.crop((0, int((im.height - h) / 2), w, int((im.height - h) / 2) + h))
        im_difficulty = im.crop((int(w * 0.091), int(h * 0.077), int(w * 0.175), int(h * 0.117))).\
            convert("L").point(lambda _: 0 if _ > 200 else 1, mode="1")
        im_title = im.crop((int(w * 0.081), 0, int(w * 0.5), int(h * 0.066))).\
            convert("L").point(lambda _: 0 if _ > 180 else 1, mode="1")
    else:
        w = int(im.height * 16 / 9)
        h = im.height
        im_crop = im.crop((int((im.width - w) / 2), 0, int((im.width - w) / 2) + w, h))
        im_difficulty = im_crop.crop((int(w * 0.091), int(h * 0.077), int(w * 0.175), int(h * 0.117))).convert("L").point(lambda _: 0 if _ > 200 else 1, mode="1")
        im_title = im_crop.crop((int(w * 0.081), 0, int(w * 0.5), int(h * 0.066))).convert("L").point(lambda _: 0 if _ > 180 else 1, mode="1")

    im_score = im_crop.crop((int(w * 0.041), int(h * 0.622), int(w * 0.526), int(h * 0.964)))

    im_miss = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.818), int(im_score.width * 0.978), int(im_score.height * 0.958))).\
        convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
    miss = tool.image_to_string(im_miss, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    result.live = "challenge"
    if not miss.isdecimal():
        im_score = im_crop.crop((int(w * 0.101), int(h * 0.512), int(w * 0.586), int(h * 0.854)))
        im_miss = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.818), int(im_score.width * 0.978), int(im_score.height * 0.958))).\
            convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
        miss = tool.image_to_string(im_miss, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
        result.live = "normal"
        if not miss.isdecimal():
            return None
    result.miss = int(miss)

    im_perfect = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.249), int(im_score.width * 0.978), int(im_score.height * 0.389))).\
        convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
    perfect = tool.image_to_string(im_perfect, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    if not perfect.isdecimal():
        return None
    result.perfect = int(perfect)

    im_great = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.389), int(im_score.width * 0.978), int(im_score.height * 0.532))).\
        convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
    great = tool.image_to_string(im_great, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    if not great.isdecimal():
        return None
    result.great = int(great)

    im_good = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.532), int(im_score.width * 0.978), int(im_score.height * 0.675))).\
        convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
    good = tool.image_to_string(im_good, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    if not good.isdecimal():
        return None
    result.good = int(good)

    im_bad = im_score.crop((int(im_score.width * 0.859), int(im_score.height * 0.675), int(im_score.width * 0.978), int(im_score.height * 0.818))).\
        convert('1', dither=Image.NONE).point(lambda _: 1 if _ == 0 else 0)
    bad = tool.image_to_string(im_bad, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    if not bad.isdecimal():
        return None
    result.bad = int(bad)

    title = tool.image_to_string(im_title, lang="jpn", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    result.title = title

    difficulty = tool.image_to_string(im_difficulty, lang="eng", builder=pyocr.builders.TextBuilder(tesseract_layout=7))
    if difficulty not in ["EASY", "NORMAL", "HARD", "EXPERT", "MASTER"]:
        return None
    result.difficulty = difficulty

    return result
