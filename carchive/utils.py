def live_link(url: str):
	import contextlib, requests, time
	response = False
	with contextlib.suppress(Exception):
		response_type = requests.get(url)
		response = response_type.status_code < 400
		time.sleep(2)
	return response

def str_to_base64(string, encoding:str='utf-8'):
	import base64
	try:
		return base64.b64encode(string.encode(encoding)).decode(encoding)
	except Exception as e:
		print(e)
		return None

def base64_to_str(b64, encoding:str='utf-8'):
	import base64
	return base64.b64decode(b64).decode(encoding)