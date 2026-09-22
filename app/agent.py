# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from app.a2ui_utils import a2ui_callback


# Hardcode the GCP Project ID string to avoid project number issues on Agent Platform
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-d2704f34ae2b"
PUBLIC_GCS_BUCKET_NAME = "divis-verve-vogue-media-829511890781"
REASONING_ENGINE_RESOURCE_NAME = "projects/829511890781/locations/us-east1/reasoningEngines/4911503048112603136"





async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: Send the session events to Memory Bank for extraction after each turn."""
    await callback_context.add_session_to_memory()
    return None


def get_firestore_catalog(category: str = "all") -> str:
    """Reads the product catalog from Firestore database.

    Args:
        category: Category filter such as 'blazers', 'dresses', 'activewear', or 'all'.

    Returns:
        Formatted summary of matched products with fabric compositions, prices, and stock status.
    """
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    catalog_ref = db.collection("catalog")

    docs = catalog_ref.stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        if category.lower() != "all" and data.get("category", "").lower() != category.lower():
            continue
        items.append(data)

    if not items:
        return f"No products found in Firestore catalog for category '{category}'."

    results = []
    for item in items:
        fabrics = ", ".join(item.get("fabrics", []))
        colors = ", ".join(item.get("colors", []))
        stock = "In Stock" if item.get("in_stock", True) else "Out of Stock"
        results.append(
            f"[{item.get('product_id')}] {item.get('name')} (${item.get('price')} - {stock}) | Fabrics: {fabrics} | Colors: {colors} | Vibe: {item.get('vibe')}"
        )
    return "\n".join(results)


def add_product_to_firestore(
    product_id: str,
    name: str,
    category: str,
    fabrics: list[str],
    colors: list[str],
    price: float,
    vibe: str = "chic",
    description: str = "",
) -> str:
    """Adds or updates a product in the Firestore catalog backend.

    Args:
        product_id: Unique product identifier (e.g. 'dress-002').
        name: Name of the garment.
        category: Product category (e.g., 'dresses', 'blazers', 'activewear').
        fabrics: List of fabrics and material compositions (e.g. ['100% Organic Cotton']).
        colors: List of available colors.
        price: Price in USD.
        vibe: Aesthetic vibe (e.g. 'chic', 'evening', 'bold').
        description: Brief product description.

    Returns:
        Confirmation message upon writing to Firestore.
    """
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    doc_ref = db.collection("catalog").document(product_id)
    product_data = {
        "product_id": product_id,
        "name": name,
        "category": category.lower(),
        "fabrics": fabrics,
        "colors": colors,
        "price": float(price),
        "vibe": vibe,
        "in_stock": True,
        "description": description,
    }
    doc_ref.set(product_data)
    return f"Successfully added product '{name}' ({product_id}) to Firestore catalog."


def update_firestore_stock(product_id: str, in_stock: bool) -> str:
    """Updates the stock availability status of a product in Firestore.

    Args:
        product_id: The unique product identifier.
        in_stock: True if in stock, False if out of stock.

    Returns:
        Confirmation message after updating Firestore.
    """
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    doc_ref = db.collection("catalog").document(product_id)
    doc = doc_ref.get()
    if not doc.exists:
        return f"Product with ID '{product_id}' not found in Firestore catalog."
    doc_ref.update({"in_stock": in_stock})
    status_str = "In Stock" if in_stock else "Out of Stock"
    return f"Updated product '{product_id}' stock status to {status_str} in Firestore."


def save_content_calendar_post(
    post_date: str,
    outfit_name: str,
    caption: str,
    hashtags: list[str],
    status: str = "scheduled",
) -> str:
    """Saves a planned Instagram post into the Firestore content_calendar collection.

    Args:
        post_date: Scheduled date or time string (e.g. '2026-10-01' or '2026-10-01 10:00 AM').
        outfit_name: Name of the featured outfit or collection.
        caption: The Instagram caption text.
        hashtags: List of hashtags.
        status: Post status (e.g. 'draft', 'scheduled', 'published').

    Returns:
        Confirmation message with generated document ID.
    """
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    doc_ref = db.collection("content_calendar").document()
    post_data = {
        "post_id": doc_ref.id,
        "post_date": post_date,
        "outfit_name": outfit_name,
        "caption": caption,
        "hashtags": hashtags,
        "status": status,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    doc_ref.set(post_data)
    return f"Successfully saved post for '{outfit_name}' on {post_date} to content_calendar (ID: {doc_ref.id})."


def get_fashion_color_palette(
    hex_code: str = "2C3E50",
    mode: str = "analogic",
    count: int = 4,
) -> str:
    """Fetches real complementary fashion color palettes and color names from The Color API.

    Args:
        hex_code: 6-character hex code representing a base garment or collection color (e.g. '2C3E50' or 'A32A29').
        mode: Palette mode such as 'analogic', 'monochrome', 'complement', or 'triad'.
        count: Number of palette colors to generate (default 4).

    Returns:
        A formatted list of color names and hex codes for outfit styling and Instagram visual design.
    """
    clean_hex = hex_code.strip("#")
    url = f"https://www.thecolorapi.com/scheme?hex={clean_hex}&mode={mode}&count={count}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            colors = [
                f"{c['name']['value']} ({c['hex']['value']})"
                for c in data.get("colors", [])
            ]
            return f"Color Palette for #{clean_hex} ({mode} mode): " + ", ".join(colors)
    except Exception as e:
        return f"Unable to fetch color palette: {str(e)}"


def search_fashion_trends(season: str = "current") -> str:
    """Looks up current fashion trends and hashtag recommendations for Divi's Verve & Vogue.

    Args:
        season: The season to check trends for (e.g. 'autumn', 'spring', 'current').

    Returns:
        A summary of trending aesthetics, textures, and top hashtags.
    """
    return (
        "Trending Aesthetics: Quiet Luxury, Soft Tailoring, Elevated Basics, Rich Jewel Tones.\n"
        "Top Hashtags: #DivisVerveAndVogue #OOTDGuide #CapsuleWardrobe #QuietLuxury #StyleInspo #ChicWear"
    )


def generate_caption_and_hashtags(outfit_name: str, vibe: str = "chic") -> str:
    """Formats an Instagram caption and curated hashtag set for an outfit or collection.

    Args:
        outfit_name: The name of the featured garment or collection.
        vibe: The mood or theme (e.g. 'chic', 'bold', 'effortless', 'evening').

    Returns:
        A complete Instagram caption draft ready to post.
    """
    return (
        f"Bringing the ultimate {vibe} energy to your rotation with the {outfit_name}. ✨\n\n"
        f"Engineered for confidence, movement, and timeless elegance. Which way are you styling this piece?\n\n"
        f"🛍️ Tap link in bio to shop Divi's Verve & Vogue.\n\n"
        f"#DivisVerveAndVogue #{outfit_name.replace(' ', '')} #StyleInspo #VogueVibes"
    )


def generate_fashion_item_image(
    prompt: str, tool_context: ToolContext = None
) -> str:
    """Generates an image for a fashion item, outfit, or editorial concept using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an artifact in the Playground panel and uploads the bytes to public Cloud Storage.

    Args:
        prompt: Detailed description of the fashion item or outfit to generate (e.g. 'Emerald silk blazer on runway').
        tool_context: ToolContext instance for saving artifacts in Agent Engine / Playground.

    Returns:
        Public Cloud Storage HTTPS URL of the uploaded image.
    """
    from google import genai

    genai_client = genai.Client(
        vertexai=True, project=FIRESTORE_PROJECT_ID, location="global"
    )
    full_prompt = f"High-fashion editorial photo for Divi's Verve and Vogue: {prompt}. Professional studio lighting, 8k luxury aesthetic."

    res = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image", contents=full_prompt
    )

    if not res.candidates or not res.candidates[0].content.parts:
        return "Error: Image generation returned empty response."

    part = res.candidates[0].content.parts[0]
    if not hasattr(part, "inline_data") or not part.inline_data:
        return "Error: Response did not contain inline image data."

    image_bytes = part.inline_data.data
    mime_type = getattr(part.inline_data, "mime_type", "image/jpeg")
    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"fashion_item_{uuid.uuid4().hex[:8]}.{ext}"

    # (1) Save artifact with tool_context if available (so it displays in Playground Artifacts panel)
    if tool_context:
        try:
            artifact_part = types.Part.from_bytes(
                data=image_bytes, mime_type=mime_type
            )
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Could not save artifact in tool context: {e}")

    # (2) Upload image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(PUBLIC_GCS_BUCKET_NAME)
    object_path = f"generated_images/{filename}"
    blob = bucket.blob(object_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{PUBLIC_GCS_BUCKET_NAME}/{object_path}"
    return (
        f"Image generated and uploaded successfully! Public URL: {public_url}"
    )


def generate_fashion_item_video(
    prompt: str, tool_context: ToolContext = None
) -> str:
    """Generates a short video for a fashion item or editorial showcase using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an artifact in the Playground panel and uploads the video bytes to public Cloud Storage.

    Args:
        prompt: Detailed description of the fashion item, garment, or editorial showcase to generate a video for (e.g. 'Emerald silk blazer runway walk').
        tool_context: ToolContext instance for saving artifacts in Agent Engine / Playground.

    Returns:
        Public Cloud Storage HTTPS URL of the uploaded video.
    """
    from google import genai

    genai_client = genai.Client(
        vertexai=True, project=FIRESTORE_PROJECT_ID, location="global"
    )
    full_prompt = f"High-fashion video for Divi's Verve and Vogue: {prompt}. Cinematic studio lighting, 4k luxury editorial motion."

    stream = genai_client.interactions.create(
        model="gemini-omni-flash-preview",
        input=full_prompt,
        stream=True,
    )

    video_bytes = None
    mime_type = "video/mp4"

    for event in stream:
        if hasattr(event, "delta") and event.delta:
            delta = event.delta
            if hasattr(delta, "type") and delta.type == "video":
                if hasattr(delta, "bytes") and delta.bytes:
                    video_bytes = delta.bytes
                    mime_type = getattr(delta, "mime_type", "video/mp4")
                    break
                elif hasattr(delta, "data") and delta.data:
                    video_bytes = delta.data
                    mime_type = getattr(delta, "mime_type", "video/mp4")
                    break
        elif hasattr(event, "bytes") and event.bytes:
            video_bytes = event.bytes
            break

    if not video_bytes:
        return "Error: Video generation with gemini-omni-flash-preview returned empty video bytes."

    ext = "mp4"
    if "webm" in mime_type:
        ext = "webm"
    filename = f"fashion_video_{uuid.uuid4().hex[:8]}.{ext}"

    # (1) Save video as artifact using tool_context.save_artifact if available
    if tool_context:
        try:
            artifact_part = types.Part.from_bytes(
                data=video_bytes, mime_type=mime_type
            )
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Could not save video artifact in tool context: {e}")

    # (2) Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(PUBLIC_GCS_BUCKET_NAME)
    object_path = f"generated_videos/{filename}"
    blob = bucket.blob(object_path)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{PUBLIC_GCS_BUCKET_NAME}/{object_path}"
    return f"Video generated and uploaded successfully! Public URL: {public_url}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_system_prompt = schema_manager.generate_system_prompt(
    role_description=(
        "You are the AI fashion & lifestyle content concierge for Divi's Verve & Vogue. "
        "You help plan Instagram content, write captions, generate product images, generate short fashion videos, recommend outfit pairings, and organize content calendars."
    ),
    workflow_description="Analyze the user request, query necessary fashion catalog or trend tools, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

agent_instruction = (
    a2ui_system_prompt
    + "\n\n"
    + "DATABASE BACKEND & EXTERNAL APIS:\n"
    + "1. You have direct access to our live Firestore backend via tools: `get_firestore_catalog`, `add_product_to_firestore`, `update_firestore_stock`, and `save_content_calendar_post`.\n"
    + "2. You can query live color aesthetics and fashion palettes via `get_fashion_color_palette` from The Color API to suggest complementary outfit colors and Instagram grid aesthetics.\n"
    + "3. You can generate studio-quality fashion imagery using `generate_fashion_item_image` powered by gemini-3.1-flash-lite-image in the global region.\n"
    + "4. You can generate short fashion videos using `generate_fashion_item_video` powered by Google's Omni model (gemini-omni-flash-preview) in the global region.\n\n"
    + "CRITICAL MEMORY & ALLERGY INSTRUCTION:\n"
    + "1. You strictly remember and track all stated user allergies (such as wool, synthetic dyes, latex, nickel, fragrance, or food/environmental allergies) and material sensitivities across sessions.\n"
    + "2. Before recommending any garment, outfit pairing, or styling advice, check the memories retrieved by your memory tool for any allergy restrictions.\n"
    + "3. Never recommend or showcase products containing fabrics or materials that conflict with the user's recorded allergies."
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=REASONING_ENGINE_RESOURCE_NAME
    ),
    instruction=agent_instruction,
    tools=[
        PreloadMemoryTool(),
        get_firestore_catalog,
        add_product_to_firestore,
        update_firestore_stock,
        save_content_calendar_post,
        get_fashion_color_palette,
        search_fashion_trends,
        generate_caption_and_hashtags,
        generate_fashion_item_image,
        generate_fashion_item_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)


app = App(
    root_agent=root_agent,
    name="app",
)

