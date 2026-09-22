import traceback
from google import genai

client = genai.Client(vertexai=True, project="qwiklabs-gcp-01-d2704f34ae2b", location="global")

print("--- Test 1: input='string' only ---")
try:
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="Generate a video of an emerald dress",
    )
    print("Test 1 res:", res)
except Exception as e:
    print("Test 1 error:", type(e), e)

print("--- Test 2: input with response_modalities=['text', 'video'] ---")
try:
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="Generate a video of an emerald dress",
        response_modalities=["text", "video"],
    )
    print("Test 2 res:", res)
except Exception as e:
    print("Test 2 error:", type(e), e)

print("--- Test 3: input with stream=True ---")
try:
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="Generate a video of an emerald dress",
        response_modalities=["video"],
        stream=True,
    )
    print("Test 3 res:", res)
    for chunk in res:
        print("Chunk:", chunk)
except Exception as e:
    print("Test 3 error:", type(e), e)
