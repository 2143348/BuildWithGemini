import traceback
from google import genai

client = genai.Client(vertexai=True, project="qwiklabs-gcp-01-d2704f34ae2b", location="global")

def test_config(name, **kwargs):
    print(f"\n--- Testing {name} ---")
    try:
        stream = client.interactions.create(
            model="gemini-omni-flash-preview",
            stream=True,
            **kwargs
        )
        for event in stream:
            print("Event type:", type(event).__name__)
            if hasattr(event, "error") and event.error:
                print(" -> Error:", event.error)
            elif hasattr(event, "delta") and event.delta:
                print(" -> Delta:", getattr(event.delta, "content", event.delta))
            elif hasattr(event, "interaction"):
                print(" -> Interaction status:", getattr(event.interaction, "status", None))
    except Exception as e:
        print(" -> Exception:", type(e), e)

test_config("input string only", input="A high fashion runway walk showcasing an autumn coat")
test_config("input list of dicts", input=[{"role": "user", "content": "A high fashion runway walk"}])
test_config("generation_config", input="A high fashion runway walk", generation_config={"response_modalities": ["video"]})
