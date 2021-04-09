from flask import Flask, request
import json
import os

app = Flask(__name__)

@app.route('/')
def display():
    return "Looks like it works!"

@app.route('/alpha')
def alpha():
    return "This is the alpha version"

@app.route('/beta')
def beta():
    return "This is the beta version"

@app.route('/input')
def input():
    if 'filename' in request.args:
        myfilename = request.args.get('filename')

        with open(myfilename, "r") as f:
            reference = json.load(f)

        return "reading file: " + os.getcwd()+ "\\" + myfilename + "\n" #+ str(reference)
        #return render_template(myfilename)
    else:
        return "No input file specified"


if __name__=='__main__':
    app.run(debug=True, port=3134)
