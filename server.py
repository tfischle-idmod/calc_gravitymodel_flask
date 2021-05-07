from flask import Flask, request, send_from_directory, abort
from werkzeug.utils import secure_filename
import json
import os
import uuid
import zipfile
import gravity
import pathlib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['PROCESSED_FOLDER'] = "processed"
app.config['RESULTS_FOLDER'] = "results"

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


@app.route('/uploader', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        random_uuid = uuid.uuid4()
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], str(random_uuid)))
        return str(random_uuid)


@app.route('/process', methods=['GET', 'POST'])
def process_files():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        path = pathlib.Path(app.config['UPLOAD_FOLDER'], input_json["uuid"])
        filename = pathlib.Path(path)

        if not pathlib.Path(filename).is_file():
            error_msg = "No input file found. '" + str(filename) + "' does not exist."
            return abort(400, error_msg)

        out_dir = pathlib.Path(app.config['PROCESSED_FOLDER'])
        results_path = gravity.from_json(filename, out_dir, request.args)

        # create unique zip file and add result from gravity module
        job_uuid = uuid.uuid4()
        path = pathlib.Path(app.config['RESULTS_FOLDER'], str(job_uuid) + ".zip")
        input_json['job_uuid'] = job_uuid

        with zipfile.ZipFile(path, "w") as z:
            zipfile.ZipFile.write(z, results_path)
            zipfile.ZipFile.write(z, filename)
            zipfile.ZipFile.writestr(z, "parameters.json", data=str(input_json))

        return str(job_uuid)

    elif request.method == 'GET':
        input_json = request.get_json(force=True)
        zip_file = str(input_json['job_uuid']) + ".zip"
        try:
            return send_from_directory(app.config["RESULTS_FOLDER"], filename=zip_file, as_attachment=True)
        except FileNotFoundError:
            error_msg = "Requested file not found. " + zip_file + " does not exist."
            abort(400, error_msg)

def run():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=3135)


if __name__ == '__main__':
    run()


