import traceback
from google import genai

client = genai.Client(vertexai=True, project="qwiklabs-gcp-01-d2704f34ae2b", location="global")

print("Extracting video bytes from gemini-omni-flash-preview stream...")
try:
    stream = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="A high fashion runway walk of an emerald silk blazer",
        stream=True,
    )
    
    video_bytes = None
    mime_type = "video/mp4"
    
    for event in stream:
        evt_type = getattr(event, "event_type", type(event))
        print("Received event:", evt_type)
        print("Event attrs:", dir(event))
        if hasattr(event, "delta") and event.delta:
            print(" -> delta:", type(event.delta), dir(event.delta))
            print(" -> delta repr:", repr(event.delta)[:300])
            delta = event.delta
            if hasattr(delta, "bytes") and delta.bytes:
                print(f" -> Found delta.bytes! Len: {len(delta.bytes)}")
            if hasattr(delta, "parts"):
                print(f" -> Found delta.parts! {delta.parts}")

except Exception as e:
    traceback.print_exc()
