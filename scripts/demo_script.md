## 3-Minute Demo Script — AI Visual Shopping

Duration: 3:00 (approx.)

Goal: Quickly demonstrate uploading an image, running an image-search, and showing AI explanations and system behavior.

0:00 — 0:20 — Intro (Vocal)
- Vocal: "I'll show AI Visual Shopping: image-based product search with AI explanations and a cost-optimized S3-backed vector store."
- Action: Stand with the browser and terminal visible.

0:20 — 1:00 — Open the app and explain UI (Vocal + Action)
- Action: Open the deployed frontend URL (or local frontend). Walk through the UI flow live:
  - Show the Upload panel (how to drag & drop or click to select).
  - Show the Search Preferences panel (query, preferences, advanced filters).
  - Show the Search button and the disabled state when no image is uploaded.
- Vocal: "This is the user flow: upload an image, optionally enter preferences, then click Search. Results appear below with per-product AI explanations. Backend limits results to 5 and explanation tokens are configurable via the `EXPLANATION_MAX_TOKENS` env var."

1:00 — 1:20 — Architecture snapshot (Vocal + Action)
- Vocal: "Quick overview: the React frontend calls an API Gateway, which invokes Lambda functions for image search and explanation. Embeddings and product data live in S3; AI models run via Bedrock (Nova models)."
- Action: Briefly show [docs/ARCHITECTURE.md] on-screen and point to the frontend → API Gateway → Lambdas → S3 → Bedrock flow.

1:10 — 1:40 — Upload image & run search (Action + Short Vocal)
- Action: Click 'Upload Image', select `products/dress_001.png` (or drag & drop). Click 'Search'.
- Vocal while waiting: "The frontend sends the image as a base64 payload to /search; the Image Search Lambda builds a multimodal embedding via Nova and runs a k-NN search in our S3-backed vector store."

1:40 — 2:10 — Results & explanation (Vocal + Action)
- Action: Point to the returned product cards on the right and the AI explanation panel.
- Vocal: "Here are the top matches (capped to 5). The AI-generated explanation explains why each product is a fit. The explanation is rendered as markdown-like HTML in the UI."

2:10 — 2:30 — Quick runtime verification (Terminal commands)
- Action: Switch to terminal and run two quick checks (copy/paste):

```bash
# Confirm deployed EXPLANATION_MAX_TOKENS
aws lambda get-function-configuration \
  --function-name ai-shopping-generate-explanation-demo \
  --query 'Environment.Variables.EXPLANATION_MAX_TOKENS' --output text --region us-east-1

# Re-run a test search (uses local sample image encoded)
IMG_B64=$(base64 products/dress_001.png | tr -d '\n')
curl -s -X POST 'https://<API_GATEWAY>/demo/search' \
  -H 'Content-Type: application/json' \
  -d "{\"image\":\"data:image/png;base64,$IMG_B64\",\"query\":\"red dress\",\"size\":3}"
```

- Vocal while running: "This confirms the explanation token limit and replicates the same request the frontend makes." (Show the output JSON briefly.)

2:30 — 2:50 — Notes on limits & behavior (Vocal)
- Vocal: "A few important points: the backend enforces a max of 5 results; images must be valid base64 and under the configured size limit; large Lambda packages are uploaded via S3 staging in the deploy script. Explanations can be long — the UI renders them directly, and the deployed function currently uses 6000 tokens by default."

2:50 — 3:00 — Close & CTA (Vocal)
- Vocal: "That's the demo — image search, ranked results, and an AI explanation. Next steps: try different images, tweak `EXPLANATION_MAX_TOKENS`, or plug in your own product catalog. Happy to walk through any part in detail now."

Notes for the presenter:
- Keep the terminal commands ready to paste to avoid typing delays.
- If the frontend is slow, explain what is happening (embedding + vector search + explanation generation) rather than waiting on the screen.
- Replace `<API_GATEWAY>` in commands with the actual API Gateway host from your deployment summary if needed.
