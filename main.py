import os
from flask import Flask, request, render_template
from pytz import utc
import requests
import imghdr
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import shutil
import os.path
import json
import uuid

import ocr_result

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'tmp')
CORRECT_FOLDER = os.environ.get('CORRECT_FOLDER', 'data/correct')
WRONG_FOLDER = os.environ.get('WRONG_FOLDER', 'data/wrong')
for p in [UPLOAD_FOLDER, os.path.join(CORRECT_FOLDER, "img"), os.path.join(CORRECT_FOLDER, "json"), os.path.join(WRONG_FOLDER, "img")]:
    os.makedirs(p, exist_ok=True)
if os.environ.get('SAVE_CORRECT', 'false').lower() == 'true':
    SAVE_CORRECT = True
else:
    SAVE_CORRECT = False

if os.environ.get('SAVE_WRONG', 'false').lower() == 'true':
    SAVE_WRONG = True
else:
    SAVE_WRONG = False


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

try:
    checker = ocr_result.ScoreResultChecker()
except ocr_result.OCRException as err:
    print(err)
    sys.exit(1)

apsd = BackgroundScheduler(timezone=utc)


@apsd.scheduled_job('interval', days=1)
def update_musicdata():
    try:
        checker.update()
    except ocr_result.OCRException as err:
        print(err)


apsd.start()


@app.route('/')
def hello():
    return render_template("home/index.html")


@app.route('/ocr', methods=["GET", "POST"])
def ocr():
    file_path = ""
    file_name = str(uuid.uuid4())
    if request.method == "POST":
        if request.files['src_file'].filename == '':
            return {"status": "error", "message": "ファイルを指定してください"}
        img_file = request.files['src_file']
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        img_file.save(file_path)
    else:
        if request.args.get('src') is None:
            return {"status": "error", "message": "srcを指定してください"}
        src_url = request.args.get('src')
        try:
            file_data = requests.get(src_url)
        except requests.exceptions.RequestException:
            return {"status": "error", "message": "有効なURLではありません"}
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        with open(file_path, mode='wb') as f:
            f.write(file_data.content)
    ext = imghdr.what(file_path)
    if ext is None:
        os.remove(file_path)
        return {"status": "error", "message": "非対応の画像形式です"}
    os.rename(file_path, file_path + "." + ext)
    file_path = file_path + "." + ext
    result = ocr_result.loadfile(file_path)
    if result is None:
        if SAVE_WRONG:
            shutil.move(file_path, os.path.join(WRONG_FOLDER, "img"))
        else:
            os.remove(file_path)
        return {"status": "error", "message": "スコアを取得出来ませんでした"}
    fixed_data = checker.correct(result)
    if fixed_data is None:
        if SAVE_WRONG:
            shutil.move(file_path, os.path.join(WRONG_FOLDER, "img"))
        else:
            os.remove(file_path)
        return {"status": "error", "message": "正しい読み取りが出来ませんでした"}
    if SAVE_CORRECT:
        shutil.move(file_path, os.path.join(CORRECT_FOLDER, "img"))
        with open(os.path.join(CORRECT_FOLDER, "json", file_name + ".json"), 'w') as f:
            json.dump(fixed_data.to_dict(), f, ensure_ascii=False)
    else:
        os.remove(file_path)
    res = fixed_data.to_dict()
    res["status"] = "ok"
    return res


if __name__ == "__main__":
    app.run(debug=True)
