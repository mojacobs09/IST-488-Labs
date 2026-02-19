import requests 
import streamlit as st 
import json
from openai import OpenAI


# location in form City, State, Country
# e.g. Syracuse New yORK
# default units is in Dahrenhiet 

#function to get the weather of everything

def get_current_weather(location, units='imperial'):
    api_key = st.secrets["OPENWEATHERMAP_API_KEY"]
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={units}'

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

    return {
      'location': location,
      'temperature': round(temp, 2),
      'feels_like': round(feels_like, 2),
      'temp_min': round(temp_min, 2),
      'temp_max': round(temp_max, 2),
      'humidity': round(humidity, 2)
      }

weather_api_key = st.secrets['WEATHER_API_KEY']

#the test of Syracuse 
syracuse_weather = get_current_weather('Syracuse, NY, US', weather_api_key)
print(syracuse_weather)


# the test of Lima, Peru
lima_weather = get_current_weather('Lima, Peru', weather_api_key)
print(lima_weather)

#CREEATING THE MAIN APP

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city to get weather for, e.g. Syracuse, NY, US. Default to 'Syracuse, NY, US' if no location is provided."
                    }
                },
                "required": ["location"]
            }
        }
    }
]


def get_weather_advice(city):
    # If no city provided, default to Syracuse
    if not city:
        city = "Syracuse, NY, US"

    # First API call - let OpenAI decide if it needs weather
    messages = [
        {"role": "system", "content": "You are a helpful weather assistant. When given a city, get the weather and provide clothing suggestions and outdoor activity recommendations based on the current weather conditions."},
        {"role": "user", "content": f"What is the weather like in {city}? Give me clothing suggestions and outdoor activity recommendations."}
    ]

    response = client.chat.completions.create(
        model="gpt-5-2025-08-07",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Check if OpenAI wants to call the weather tool
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        location = args.get("location", "Syracuse, NY, US")

        # Call the weather function
        weather_data = get_current_weather(location)

        # Second API call - provide weather data and get suggestions
        messages.append(response_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(weather_data)
        })

        second_response = client.chat.completions.create(
            model="gpt-5-2025-08-07",
            messages=messages,
        )

        return second_response.choices[0].message.content, weather_data

    return response_message.content, None


# Streamlit UI
st.title("🌤️ Weather Assistant")
st.write("Enter a city and get clothing suggestions and outdoor activity recommendations!")

city = st.text_input("Enter a city:", placeholder="e.g. Syracuse, NY, US")

if st.button("Get Weather Advice"):
    if city:
        with st.spinner("Fetching weather and generating advice..."):
            try:
                advice, weather_data = get_weather_advice(city)

                if weather_data:
                    st.subheader(f"Current Weather in {weather_data['location']}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Temperature", f"{weather_data['temperature']}°F")
                    col2.metric("Feels Like", f"{weather_data['feels_like']}°F")
                    col3.metric("Humidity", f"{weather_data['humidity']}%")
                    st.write(f"**Conditions:** {weather_data['description'].capitalize()}")

                st.subheader("💡 Advice")
                st.write(advice)

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        with st.spinner("No city entered, using Syracuse, NY as default..."):
            try:
                advice, weather_data = get_weather_advice("Syracuse, NY, US")

                if weather_data:
                    st.subheader(f"Current Weather in {weather_data['location']}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Temperature", f"{weather_data['temperature']}°F")
                    col2.metric("Feels Like", f"{weather_data['feels_like']}°F")
                    col3.metric("Humidity", f"{weather_data['humidity']}%")
                    st.write(f"**Conditions:** {weather_data['description'].capitalize()}")

                st.subheader("💡 Advice")
                st.write(advice)

            except Exception as e:
                st.error(f"Error: {e}")