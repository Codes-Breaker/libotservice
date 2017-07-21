import requests
import json

def hello(name):
	payload = {
		"key1" : name
	}
	url = 'aws api gateway'
	r = requests.post(url, data=json.dumps(payload))
	return r.content

