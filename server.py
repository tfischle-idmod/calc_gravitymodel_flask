from flask import Flask, request
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)


@app.route('/')
def display():
    return "Looks like it works!"


# 127.0.0.1:3134/test
@app.route('/test')
def reply_test():
    return "Some reply"


# 127.0.0.1:3134/input?filename=demographics.json
@app.route('/input')
def input_filename():
    if 'filename' in request.args:
        myfilename = request.args.get('filename')

        with open(myfilename, "r") as f:
            reference = json.load(f)

        return "reading file: " + os.getcwd() + "\\" + myfilename + "\n" #+ str(reference)
    else:
        return "No input file specified"


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return 'file uploaded successfully'


@app.route('/params', methods=['GET', 'POST'])
def upload_params():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        return 'received json: ' + str(input_json)


if __name__ == '__main__':
    app.run(debug=True, port=3134)

