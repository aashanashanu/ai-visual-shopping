# AI Visual Shopping - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  React Frontend (TypeScript)                                    │   │
│  │  • Image Upload & Preview                                       │   │
│  │  • Search Interface                                             │   │
│  │  • Results Display                                              │   │
│  │  • AI Explanations                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                         ↓ HTTP/REST API                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS API GATEWAY                               │
│              (CORS-enabled, Rate limiting, API routing)                 │
│                                                                         │
│    POST /search ────────┐                                               │
│    POST /explain ───────┴───→ Lambda Integrations                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         LAMBDA LAYER (Serverless)                       │
│                                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────┐ │
│  │   Image Search          │  │  Generate Explanation  │  │ Seed Data│ │
│  │   (Python 3.11)         │  │  (Python 3.11)         │  │ (Python)│ │
│  │                         │  │                         │  │          │ │
│  │ • Multimodal embeddings │  │ • AI explanations     │  │• Initial│ │
│  │ • k-NN vector search     │  │ • Product reasoning   │  │  data    │ │
│  │ • Filter by color/price │  │ • Preference analysis   │  │  loading │ │
│  │ • CORS headers          │  │                         │  │          │ │
│  └───────────┬─────────────┘  └───────────┬─────────────┘  └──────────┘ │
└──────────────┼───────────────────────────┼─────────────────────────────┘
               │                           │
               ↓                           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI/ML SERVICES                                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │           Amazon Bedrock                                         │   │
│  │                                                                  │   │
│  │  ┌────────────────────────────┐  ┌─────────────────────────────┐ │   │
│  │  │ Amazon Nova Multimodal     │  │ Amazon Nova Lite v2         │ │   │
│  │  │ Embeddings                 │  │                             │ │   │
│  │  │                            │  │ • Explanations              │ │   │
│  │  │ • 1024-dim embeddings      │  │ • Product matching logic    │ │   │
│  │  │ • Image similarity         │  │ • Preference filtering      │ │   │
│  │  │ • Visual search            │  │ • Natural language         │ │   │
│  │  └────────────────────────────┘  └─────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER (S3)                             │
│                                                                         │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌─────────────────┐ │
│  │ Product Images       │ │ User Uploads         │ │ Vector Store    │ │
│  │ Bucket               │ │ Bucket               │ │ (S3-backed)     │ │
│  │                      │ │                      │ │                 │ │
│  │ • Product photos     │ │ • User images        │ │ • embeddings.json│ │
│  │ • S3 URLs            │ │ • Temporary storage  │ │ • products.json │ │
│  │ • Public access      │ │ • Lifecycle policy   │ │ • k-NN index    │ │
│  └──────────────────────┘ └──────────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Image Search Flow

```
User Uploads Image
        │
        ↓
┌───────────────┐
│ Frontend      │
│ converts to   │
│ base64        │
└───────────────┘
        │
        ↓
┌───────────────┐
│ API Gateway   │
│ POST /search  │
└───────────────┘
        │
        ↓
┌───────────────┐
│ Image Search  │
│ Lambda        │
└───────────────┘
        │
        ├──────────────────────────────────────┐
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│ Bedrock       │                    │ Vector Store  │
│ (Embeddings)  │                    │ (S3)          │
│               │                    │               │
│ • Generate    │                    │ • Load index  │
│   1024-dim    │                    │ • k-NN search │
│   embedding   │                    │ • Return top  │
└───────────────┘                    │   matches     │
        │                            └───────────────┘
        │                                    │
        ↓                                    ↓
        └────────────────┬───────────────────┘
                         ↓
                  ┌───────────────┐
                  │ Filter by:    │
                  │ • color       │
                  │ • category    │
                  │ • price range │
                  └───────────────┘
                         │
                         ↓
                  ┌───────────────┐
                  │ Return JSON:  │
                  │ • products    │
                  │ • explanation │
                  │ • query       │
                  └───────────────┘
```

### 2. Data Seeding Flow

```
┌───────────────┐
│ Seed Data     │
│ Lambda        │
└───────────────┘
        │
        ├──────────────────────────────────────┐
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│ sample_catalog│                    │ Product       │
│ .json         │                    │ Images        │
│               │                    │ (products/)   │
│ • 32 products │                    │ • 32 images   │
│ • metadata    │                    │ • PNG format  │
└───────────────┘                    └───────────────┘
        │                                      │
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│ Upload to S3  │                    │ Bedrock       │
│ (Product      │                    │ (Embeddings)  │
│  Images       │                    │               │
│  Bucket)      │                    │ • Generate    │
│               │                    │   embeddings  │
│ • images/     │                    │   for each    │
│   *.png       │                    │   product     │
└───────────────┘                    └───────────────┘
        │                                      │
        └────────────────┬───────────────────────┘
                         ↓
                  ┌───────────────┐
                  │ Save to S3    │
                  │ Vector Store:   │
                  │               │
                  │ • embeddings  │
                  │   .json       │
                  │ • products    │
                  │   .json       │
                  └───────────────┘
```

## Key Design Decisions

### 1. S3-Backed Vector Store (vs OpenSearch)
**Rationale:** Cost optimization
- **Savings:** ~97% cost reduction (~$540/month → ~$15/month)
- **Trade-off:** Slightly slower search (acceptable for demo)
- **Implementation:** JSON files stored in S3 with in-memory cache

### 2. Multimodal Embeddings
**Technology:** Amazon Nova Multimodal Embeddings
- **Dimension:** 1024
- **Purpose:** Image-to-image similarity search
- **Fallback:** Text embeddings if image unavailable

### 3. Filtering Strategy
**Two-Layer Approach:**
1. **Hard Filters** (color, category, price) - Applied first
2. **AI Filters** (preferences) - Only applied when no hard filters

**Benefit:** Ensures explicit user constraints are always respected

### 4. CORS Configuration
**Layers:**
1. API Gateway OPTIONS methods
2. Lambda response headers
3. S3 bucket CORS rules

## Security Considerations

- ✅ Bedrock IAM permissions required
- ✅ API Gateway rate limiting
- ✅ S3 bucket lifecycle policies
- ✅ Input validation (image size, format)
- ✅ CORS restrictions
- ✅ No PII storage

## Cost Optimization Features

| Component | Optimized Config | Production | Savings |
|-----------|------------------|------------|---------|
| Lambda Memory | 512MB | 1024MB | 50% |
| Vector Storage | S3 | OpenSearch | 95% |
| Nova Model | Lite | Pro | ~30% |
| Frontend | S3 Static | CDN | Variable |
