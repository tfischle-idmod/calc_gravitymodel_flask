from flask import Flask, request, send_from_directory, abort
from werkzeug.utils import secure_filename
import json
import os
import uuid
import zipfile


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['PROCESSED_FOLDER'] = "processed"


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
        random_uuid = uuid.uuid4()
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], str(random_uuid)))
        return str(random_uuid)


@app.route('/params', methods=['GET', 'POST'])
def upload_params():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        path = os.path.join(app.config['UPLOAD_FOLDER'], input_json["uuid"])

        with open(path, "r") as f:
            reference = json.load(f)

        # Do processing and save file
        param2 = input_json["param2"]
        reference["Returned"] = True
        reference[param2] = "Test"

        job_uuid = uuid.uuid4()
        path = os.path.join(app.config['PROCESSED_FOLDER'], str(job_uuid) + ".zip")

        with zipfile.ZipFile(path, "w") as z:
            zipfile.ZipFile.writestr(z, "result.json", str(reference))

        return str(job_uuid)

    elif request.method == 'GET':
        input_json = request.get_json(force=True)
        zip_file = str(input_json['job_uuid']) + ".zip"
        try:
            return send_from_directory(app.config["PROCESSED_FOLDER"], filename=zip_file, as_attachment=True)
        except FileNotFoundError:
            abort(404)



if __name__ == '__main__':
    app.run(debug=True, port=3134)

