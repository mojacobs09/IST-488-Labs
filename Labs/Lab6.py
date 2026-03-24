response = client.chat.completions.create(
model="gpt-4o", messages=[ {"role": "user",
"content": "What is REST?"} ] )
print(response.choices[0].message.content)

response = client.responses.create(
model="gpt-4o", input="What is REST?" )
print(response.output_text)

response = client.responses.create(
model="gpt-4o",
instructions="You are a concise Python tutor.
Answer in 2 sentences max.",
input="Explain list comprehensions."
)
response = client.responses.create(
model="gpt-4o",
input=[
{"role": "developer",
"content": "You are a concise Python tutor.
Answer in 2 sentences max."},
{"role": "user",
"content": "Explain list comprehensions."}
]
)

# Turn 1 — start a conversation
response_1 = client.responses.create(
model="gpt-4o",
instructions="You are a helpful travel assistant.",
input="I'm planning a 3-day trip to Tokyo. What should I see?"
)
# Turn 2 — server loads full context
response_2 = client.responses.create(
model="gpt-4o",
instructions="You are a helpful travel assistant.",
input="What about food? I love ramen.",
previous_response_id=response_1.id
)
# Turn 3 — turn 1 + 2 + 3
response_3 = client.responses.create(
model="gpt-4o",
instructions="You are a helpful travel assistant.",
input="Can you put this into a day-by-day itinerary?",
previous_response_id=response_2.id
)

# Chat Completions streaming
stream = client.chat.completions.create(
model="gpt-4o",
messages=[{"role": "user",
"content": "Tell me a joke"}],
stream=True
)
for chunk in stream:
delta = chunk.choices[0].delta
if delta.content:
print(delta.content, end="")

# Responses API streaming
stream = client.responses.create(
model="gpt-4o",
input="Tell me a joke",
stream=True
)
for event in stream:
if event.type == "response.output_text.delta":
print(event.delta, end="")

# Model decides calls function
response = client.responses.create(
model="gpt-4o",
input="What's the weather in Paris?",
tools=tools
)
# Extract the function call
tool_call = response.output[0]
# Step 3: Execute and feed result back
weather_data = '{"temp": "18°C", "condition": "Partly cloudy"}'
response_2 = client.responses.create(
model="gpt-4o",
previous_response_id=response.id,
input=[{
"type": "function_call_output",
"call_id": tool_call.call_id,
"output": weather_data
}]
)
print(response_2.output_text)