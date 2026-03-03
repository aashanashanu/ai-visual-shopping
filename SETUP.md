# AI Visual Shopping - Clean Project Setup

This is a clean, production-ready version of the AI Visual Shopping project. All temporary files, test outputs, and build artifacts have been removed.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js 16+ and npm
- Python 3.8+
- AWS account with access to:
  - Lambda
  - API Gateway
  - S3
  - Bedrock (Nova models)

### 1. Deploy Infrastructure
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy the full stack
./scripts/deploy.sh
```

### 2. Access the Application
- **Frontend URL**: Available after deployment (shown in deploy output)
- **API Gateway URL**: Available after deployment (shown in deploy output)

### 3. Test the Application
```bash
# Test with sample image
curl -X POST "YOUR_API_GATEWAY_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image",
    "query": "Summer dress for beach vacation",
    "preferences": "Prefer cotton material, casual style, under $100",
    "size": 5
  }'
```

## Project Structure

```
ai-visual-shopping/
├── backend/                 # AWS Lambda functions
│   ├── lambdas/
│   │   ├── image_search.py      # Main search API
│   │   ├── generate_explanation.py # AI explanations
│   │   ├── seed_data.py         # Data seeding
│   │   ├── bedrock_client.py    # AWS Bedrock integration
│   │   └── s3_vector_store.py   # Vector store implementation
│   └── cloudformation-demo.yaml # Infrastructure template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProductCard.tsx
│   │   │   ├── AIExplanation.tsx
│   │   │   └── ImageUpload.tsx
│   │   └── App.tsx
│   └── package.json
├── products/              # Product images
├── sample_catalog.json   # Product catalog
├── scripts/              # Deployment scripts
│   ├── deploy.sh
│   ├── cleanup.sh
│   └── rebuild.sh
└── docs/                 # Documentation
    ├── ARCHITECTURE.md
    └── API.md
```

## Key Features

- **Visual Search**: Upload images to find similar products
- **AI-Powered Filtering**: Natural language preferences with Nova models
- **Smart Explanations**: AI explains why products match
- **Modern UI**: Clean, responsive React interface
- **Scalable Architecture**: Serverless AWS infrastructure

## Configuration

### Environment Variables
The deployment script automatically configures:
- `PRODUCT_IMAGES_BUCKET`: S3 bucket for product images
- `USER_UPLOADS_BUCKET`: S3 bucket for user uploads
- `REGION`: AWS region (us-east-1)

### AWS Bedrock Models
- **Nova 2 Lite**: Text generation and explanations
- **Nova Multimodal**: Image embeddings

## Cleanup

To remove all AWS resources:
```bash
./scripts/cleanup.sh
```

## Development

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Backend Testing
```bash
# Test Lambda functions locally (requires AWS SAM)
cd backend/lambdas
python -m pytest
```

## Support

- **Documentation**: See `docs/` folder
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API.md`

---

**Note**: This clean version contains only production-ready code. All temporary files, test outputs, and build artifacts have been excluded via `.gitignore`.
