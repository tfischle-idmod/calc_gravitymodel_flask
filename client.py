#make a POST request
import requests

parameters = {"param1": "parameter1", "param2": "123"}
dictToSend = {'file': open("demographics_test.json", "r")}

res = requests.post('http://localhost:3134/uploader', files=dictToSend)
print("response from server:", res.text)
print(res.elapsed)

parameters["uuid"] = res.text
res = requests.post('http://localhost:3134/params', json=parameters)
print("response from server:", res.text)
print(res.elapsed)

parameters["job_uuid"] = res.text
res = requests.get('http://localhost:3134/params', json=parameters)
print("response from server:", res.text)
print(res.elapsed)
print(res.headers)
print(res.headers['Content-Disposition'])
print(res.content)

with open('readme.zip', 'wb') as f:
    f.write(res.content)
