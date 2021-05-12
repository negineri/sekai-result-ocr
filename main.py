import os
from flask import Flask, request, render_template
import requests
import random
import json
import imghdr

import ocr_result

os.makedirs("tmp", exist_ok=True)

app = Flask(__name__)

UPLOAD_FOLDER = './tmp/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def hello():
    return render_template("home/index.html")


@app.route('/ocr', methods=["GET", "POST"])
def ocr():
    file_path = ""
    if request.method == "POST":
        if request.files['src_file'].filename == '':
            return '{status: "error", message: "ファイルを指定してください"}'
        img_file = request.files['src_file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(int(random.random() * 10000000000)))
        img_file.save(file_path)
    else:
        if request.args.get('src') is None:
            return '{status: "error", message: "srcを指定してください"}'
        src_url = request.args.get('src')
        try:
            file_data = requests.get(src_url)
        except requests.exceptions.RequestException:
            return '{status: "error", message: "有効なURLではありません"}'
        file_path = 'tmp/' + str(int(random.random() * 10000000000))
        with open(file_path, mode='wb') as f:
            f.write(file_data.content)
    ext = imghdr.what(file_path)
    if ext is None:
        os.remove(file_path)
        return '{status: "error", message: "非対応の画像形式です"}'
    os.rename(file_path, file_path + "." + ext)
    file_path = file_path + "." + ext
    result = ocr_result.loadfile(file_path)
    if result is None:
        return '{status: "error", message: "スコアを取得出来ませんでした"}'
    os.remove(file_path)
    res = result.to_dict()
    res["status"] = "ok"
    return json.dumps(res, ensure_ascii=False)


if __name__ == "__main__":
    app.run(debug=True)
