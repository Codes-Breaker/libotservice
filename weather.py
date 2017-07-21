from pprint import pprint
import requests

def weather(location):
	weblink = 'http://api.openweathermap.org/data/2.5/weather?q=' + location + '&APPID=abd665195099dc466a4a29b842749dc5'
	r = requests.get(weblink)
	result = r.json()
	if result.get("cod") == "404":
		print("not found")
		return None
	else:
		print("found")
		return "Weather now in " +result.get("name")+ " is " + str(int(result.get("main").get("temp"))-273.15) +" degree."


