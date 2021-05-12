import os
from flask import Flask, request, render_template
from pytz import utc
import requests
import random
import imghdr
import sys
from apscheduler.schedulers.background import BackgroundScheduler

import ocr_result

os.makedirs("tmp", exist_ok=True)

app = Flask(__name__)

UPLOAD_FOLDER = './tmp/'
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
    if request.method == "POST":
        if request.files['src_file'].filename == '':
            return {"status": "error", "message": "ファイルを指定してください"}
        img_file = request.files['src_file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(int(random.random() * 10000000000)))
        img_file.save(file_path)
    else:
        if request.args.get('src') is None:
            return {"status": "error", "message": "srcを指定してください"}
        src_url = request.args.get('src')
        try:
            file_data = requests.get(src_url)
        except requests.exceptions.RequestException:
            return {"status": "error", "message": "有効なURLではありません"}
        file_path = 'tmp/' + str(int(random.random() * 10000000000))
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
        return {"status": "error", "message": "スコアを取得出来ませんでした"}
    fixed_data = checker.correct(result)
    if fixed_data is None:
        return {"status": "error", "message": "正しい読み取りが出来ませんでした"}
    os.remove(file_path)
    res = fixed_data.to_dict()
    res["status"] = "ok"
    return res


if __name__ == "__main__":
    app.run(debug=True)
