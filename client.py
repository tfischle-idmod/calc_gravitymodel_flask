#make a POST request
import requests

parameters = {"p1": "parameter1", "p2": "123"}
dictToSend = {'file': open("demographics.json", "r")}

res = requests.post('http://localhost:3134/uploader', files=dictToSend)
print("response from server:", res.text)
print(res.elapsed)

res = requests.post('http://localhost:3134/params', json=parameters)
print("response from server:", res.text)
print(res.elapsed)
