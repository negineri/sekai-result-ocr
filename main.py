import os
from flask import Flask, request, render_template
import requests
import random
import json
import imghdr

import ocr_result

os.makedirs("tmp", exist_ok=True)

app = Flask(__name__)


@app.route('/')
def hello():
    if request.args.get('src') is None:
        return render_template("home/index.html")
    src_url = request.args.get('src')
    try:
        file_data = requests.get(src_url)
    except requests.exceptions.RequestException as err:
        print(err)
        return '{message: "有効なURLではありません"}'
    file_path = 'tmp/' + str(int(random.random() * 10000000000))
    with open(file_path, mode='wb') as f:
        f.write(file_data.content)
    ext = imghdr.what(file_path)
    if ext is None:
        return '{message: "非対応の画像形式です"}'
    os.rename(file_path, file_path + "." + ext)
    file_path = file_path + "." + ext
    result = ocr_result.loadfile(file_path)
    if result is None:
        return '{message: "スコアを取得出来ませんでした"}'
    os.remove(file_path)
    return json.dumps(result.to_dict())


if __name__ == "__main__":
    app.run(debug=True)
