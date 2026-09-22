import traceback
from google import genai

client = genai.Client(vertexai=True, project="qwiklabs-gcp-01-d2704f34ae2b", location="global")

print("Testing client.interactions.create with stream=True...")
try:
    stream = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="Generate a video of an emerald dress fashion runway walk",
        response_modalities=["video"],
        stream=True,
    )
    print("Stream object:", type(stream))
    for event in stream:
        print("\n--- Event ---")
        print("Type:", type(event))
        print("Event repr:", repr(event)[:300])
        if hasattr(event, "data"):
            print("Data:", type(event.data), getattr(event, "data", None))
except Exception as e:
    traceback.print_exc()
