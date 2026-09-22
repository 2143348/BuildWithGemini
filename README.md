# Divi's Verve & Vogue — AI Fashion Concierge Agent

![Divi's Verve & Vogue Demo](./demo.gif)

Divi's Verve & Vogue is an AI fashion concierge agent built on Google Cloud's Agent Development Kit (ADK) and Gemini models. It manages luxury fashion inventory, searches historical fashion trend guides via RAG, creates studio-grade fashion imagery and videos, and serves interactive A2UI interfaces to users.

---

## 🛠 Features & Architecture

### 1. Memory Bank
- **Context Persistence**: Uses ADK `PreloadMemoryTool` and `generate_memories_callback` to remember client style preferences and past interactions across conversations.

### 2. Firestore Catalog & Content Calendar Management
- **Catalog Lookup**: `get_firestore_catalog` retrieves fashion inventory from GCP Firestore (`products` collection).
- **Inventory Updates**: `add_product_to_firestore` and `update_firestore_stock` update stock levels in real time.
- **Content Calendar**: `save_content_calendar_post` schedules marketing posts directly to Firestore (`content_calendar` collection).

### 3. Fashion RAG (Retrieval-Augmented Generation)
- **Trend Knowledge Base**: `search_fashion_trends` searches historical fashion literature and trend guides for styling recommendations.

### 4. Studio Image & Omni Video Generation
- **Image Generation**: `generate_fashion_item_image` invokes `gemini-3.1-flash-lite-image` in the `global` region, saves artifacts locally, and uploads PNG assets directly to Google Cloud Storage.
- **Video Generation**: `generate_fashion_item_video` uses `gemini-omni-flash-preview` streaming Interactions API to produce fashion item videos uploaded directly to Google Cloud Storage.
- **Public Cloud Storage**: Media assets are stored in the public GCS bucket (`divis-verve-vogue-media-829511890781`).

### 5. Fashion Styling Helpers
- **Color Palette Generator**: `get_fashion_color_palette` provides hex codes, complementary shades, and styling advice.
- **Social Caption & Hashtags**: `generate_caption_and_hashtags` writes tailored social copy and tags.

### 6. A2UI Rendered Interface
- **Structured Surfaces**: Automatically transforms structured outputs into interactive A2UI Cards, Images, Text blocks, and Status Badges.

---

## 📁 Repository Structure

```
.
├── app/                      # Agent definition & tools
│   ├── agent.py              # Root agent configuration, tools & callbacks
│   └── tools.py              # Firestore, RAG, palette, and caption tools
├── frontend/                 # Web interface & proxy
│   ├── main.py               # FastAPI proxy server for agent communication
│   └── static/
│       └── index.html        # Glassmorphic luxury chat UI
├── demo.gif                  # Inline demo preview
├── agents-cli-manifest.yaml  # Agent manifest configuration
└── deployment_metadata.json  # Deployment resource tracking
```

---

## 💻 Local Setup & Execution

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud` CLI) authenticated to your GCP Project
- Vertex AI Reasoning Engine deployed agent resource name

### Step 1: Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

Set `AGENT_ENGINE_RESOURCE_NAME` to your Vertex AI Reasoning Engine resource path, and `AGENT_DIRECTORY` to your agent folder:

```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
```

### Step 3: Launch the Frontend Server

```bash
python main.py
```

The server will start on port `8080`. Open your browser to the configured local host port to interact with the concierge.

---

## ☁️ Cloud Run Deployment

To deploy the frontend proxy to Cloud Run and grant it access to your deployed reasoning engine:

```bash
gcloud run deploy divis-verve-and-vogue-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="$AGENT_ENGINE_RESOURCE_NAME",AGENT_DIRECTORY="$AGENT_DIRECTORY"
```

Grant the Cloud Run service account access to Vertex AI:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:<SERVICE_ACCOUNT_EMAIL>" \
  --role="roles/aiplatform.user"
```
