import requests 
# location in form City, State, Country
# e.g. Syracuse New yORK
# default units is in Dahrenhiet 


def get_current_weather(location, api_key, units='imperial'):
  url = (' ')


response = requests.get(url)
if response.status_code == 401:
  raise Exception('Authentication failed: Invalid API key (401 Unauthorized)')
if response.status_code == 404:
  error_message = response.json().get('message')
  raise Exception(f'404 error: {error_message}')
data = response.json()
temp = data['main']['temp']
feels_like = data['main']['feels_like']
temp_min = data['main']['temp_min']
temp_max = data['main']['temp_max']
humidity = data['main']['humidity']
return {'location': location,
  'temperature': round(temp, 2),
  'feels_like': round(feels_like, 2),
  'temp_min': round(temp_min, 2),
  'temp_max': round(temp_max, 2),
  'humidity': round(humidity, 2)
}
