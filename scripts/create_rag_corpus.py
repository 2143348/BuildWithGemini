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

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-01-d2704f34ae2b"
LOCATION = "us-central1"  # Serverless mode is us-central1 only
GCS_PATH = "gs://divis-verve-vogue-media-829511890781/rag/pg49513.txt"

print(f"Initializing Vertex AI (project={PROJECT_ID}, location={LOCATION})...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 1. Switch region's RAG managed DB to serverless mode
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
print("Updating RAG engine config to serverless mode...")
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    )
)

# 2. Create the serverless RAG corpus
print("Creating serverless RAG corpus...")
corpus = rag.create_corpus(
    display_name="culpeper-herbal-corpus",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print(f"CREATED_CORPUS_NAME: {corpus.name}")

# 3. Import + chunk + embed documents
print(f"Importing document {GCS_PATH} into corpus...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
)
print(f"Import completed! Imported files count: {resp.imported_rag_files_count}")
