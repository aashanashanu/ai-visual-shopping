## Inspiration

AI Visual Shopping was inspired by the gap between image-first browsing and search-driven e-commerce. We wanted to let users find products from photos or screenshots and receive concise, contextual explanations — combining visual search with AI reasoning so shoppers can act on images they already have.

## What it does

- Accepts an image from the user and extracts visual features.
- Performs nearest-neighbor search in a vector store to find visually similar catalog items.
- Uses an LLM-backed explanation service to generate human-readable reasons why results match (style, color, pattern, fit).
- Serves a React frontend with image upload, chat-like explanations, and product cards; backend Lambdas handle vector indexing, image search, and LLM calls.

## How we built it

- Frontend: React + TypeScript (see `src/` and `src/components/`) for image upload, product display, and explanation UI.
- Backend: AWS Lambda functions in `backend/lambdas/` for image processing, vector indexing (`s3_vector_store.py`), and Bedrock/LLM integration (`bedrock_client.py`).
- Data: A sample product catalog (`sample_catalog.json`) seeded into the vector store via `backend/lambdas/seed_data.py` and `products/` utilities.
- Infrastructure: CloudFormation templates (`backend/cloudformation.yaml`) and helper scripts in `scripts/` for deployment and operational flows.

## Challenges we ran into

- Aligning visual embeddings with product metadata — ensuring image features map meaningfully to catalog attributes (color, pattern, silhouette) required iterative seeding and tuning.
- Latency control — composing image feature extraction, vector search, and LLM explanation while keeping response times reasonable.
- Cost and safety tradeoffs — LLM calls add quality but increase cost; deciding when to synthesize explanations versus returning raw matches required careful UX decisions.

## Accomplishments that we're proud of

- End-to-end flow from image upload to actionable product matches with clear, concise AI explanations.
- Modular backend Lambdas that separate concerns (embedding, search, and LLM logic) and are easy to extend.
- Clean, componentized frontend with reusable pieces: `ImageUpload`, `ProductCard`, `ChatInterface`, and `AIExplanation`.

## What we learned

- Vector search quality is highly dependent on catalog coverage and embedding consistency — small changes to preprocessing or seed data materially affect result relevance.
- Hybrid UX (visual matches + short LLM explanations) helps users trust recommendations more than raw similarity lists.
- Operationalizing LLMs in production needs throttling, caching, and cost-awareness; a lightweight fallback for high-latency or high-cost paths is crucial.

## What's next for AI Visual Shopping

- Expand catalog coverage and continuous re-indexing pipelines so new products are searchable immediately.
- Add personalization signals (user preferences, purchase history) to re-rank vector results.
- Provide on-device preprocessing and client-side batching to reduce backend load and latency.
- Improve explanation fidelity with structured extraction (e.g., extract attributes like color/pattern and surface them alongside LLM text).
