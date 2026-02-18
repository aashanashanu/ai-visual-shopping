# AI Visual Shopping - AWS Architecture

## Architecture Diagram

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Lambda Functions   │
│   (React)       │◄──►│   (REST API)    │◄──►│   - Image Search     │
│   - Image Upload│    │   - /search      │    │   - Generate Explanation │
│   - Search UI   │    │   - /explain    │    │   - Seed Data        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Buckets    │    │   OpenSearch    │    │   AWS Bedrock   │
│   - Product     │    │   (Vector DB)   │    │   - Titan Embed │
│     Images      │    │   - Product     │    │   - Claude LLM  │
│   - Static      │    │     Vectors     │    │   - Multimodal  │
│     Assets      │    │   - Metadata    │    │     Search      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## End-to-End Flow

### 1. Data Seeding Process

```text
sample_catalog.json → Seed Data Lambda → S3 (Images) → Bedrock (Embeddings) → OpenSearch (Index)
```

1. **Load Catalog**: Seed Data Lambda reads `sample_catalog.json`
2. **Generate Images**: Creates placeholder images via placeholder.com
3. **Upload to S3**: Stores images in product images bucket
4. **Create Embeddings**: Uses Bedrock Titan for multimodal embeddings
5. **Index Data**: Stores vectors + metadata in OpenSearch

### 2. Image Search Flow

```text
Frontend → API Gateway → Image Search Lambda → Bedrock → OpenSearch → Results
```

1. **User Upload**: Frontend uploads image via API Gateway
2. **Generate Embedding**: Lambda sends image to Bedrock for embedding
3. **Vector Search**: Query OpenSearch with embedding vector
4. **Return Results**: Similar products returned to frontend

### 3. Explanation Generation Flow

```text
Frontend → API Gateway → Generate Explanation Lambda → Bedrock Claude → Response
```

1. **Request Explanation**: User asks why products match
2. **LLM Analysis**: Claude analyzes image similarity and product attributes
3. **Natural Language**: Returns human-readable explanation

## AWS Services Used

- **API Gateway**: RESTful API endpoints
- **Lambda Functions**: Serverless compute
- **S3**: Image storage and static assets
- **OpenSearch**: Vector database for similarity search
- **Bedrock**: AI/ML services (embeddings, LLM)
- **CloudFormation**: Infrastructure as Code
- **IAM**: Security and permissions

## Data Flow Summary

1. **Setup**: CloudFormation creates all resources
2. **Seeding**: Sample data loaded with embeddings
3. **Runtime**: Users search images → get similar products → get explanations
