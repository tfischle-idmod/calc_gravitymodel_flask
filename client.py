#make a POST request
# POST a CSV to "/csv" get back a file-id
# POST a JSON blob with parameters and file-id to "/job" get back a job-id
# GET "/<job-id>" get back .zip with migration file(s)

import requests


def run():
    server = 'http://localhost:3135'

    parameters = {"param1": "parameter1", "param2": "123"}
    #dictToSend = {'file': open("demographics_test.json", "r")}
    dictToSend = {'file': open("demographics.json", "r")}

    # post a json file (e.g. demographics.json), return unique id
    res = requests.post(server + '/uploader', files=dictToSend)
    print("response from server:", res.text)
    print(res.elapsed)

    # post a json blob that contains the unique file id
    parameters["uuid"] = res.text
    res = requests.post(server + '/process', json=parameters)
    print("response from server:", res.text)
    print(res.elapsed)

    parameters["job_uuid"] = res.text
    res = requests.get(server + '/process', json=parameters)
    #print("response from server:", res.text)
    print(res.elapsed)
    #print(res.headers)
    #print(res.headers['Content-Disposition'])
    #print(res.content)

    save_as = 'output.zip'
    with open(save_as, 'wb') as f:
        f.write(res.content)


if __name__ == '__main__':
    run()