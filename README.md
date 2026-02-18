# AI Visual Shopping - Multimodal Ecommerce powered by Amazon Nova

A production-ready multimodal ecommerce application that combines image understanding, text intent understanding, semantic vector search, and generative explanations using Amazon Nova foundation models.

## 🎯 Project Overview

AI Visual Shopping allows users to:
- Upload an image of a product (e.g., outfit screenshot)
- Add text preferences (e.g., "Show me similar in blue under $100")
- Get visually similar products from an ecommerce catalog
- Receive AI-generated explanations of why products match

## 🏗 Architecture

### AWS Services Used
- **Amazon S3**: Store product and user-uploaded images
- **AWS Lambda**: Backend logic for image processing and search
- **Amazon API Gateway**: RESTful API endpoints
- **Amazon OpenSearch**: Vector search index with k-NN
- **Amazon Bedrock**: Invoke Nova foundation models
- **IAM**: Secure access management
- **CloudFormation**: Infrastructure as Code

### Nova Model Usage
- **Nova Multimodal Embedding**: Generate 1024-dimensional embeddings for images
- **Nova 2 Lite**: Generate conversational explanations and filter products
- **NO Nova Act**: No agentic automation (as per requirements)

## 📁 Project Structure

```
ai-visual-shopping/
├── backend/
│   ├── cloudformation.yaml          # Infrastructure template
│   ├── sample_catalog.json          # 30+ sample products
│   └── lambdas/
│       ├── bedrock_client.py        # Nova model integration
│       ├── opensearch_client.py    # Vector search operations
│       ├── image_search.py          # Main search Lambda
│       ├── generate_explanation.py  # Explanation Lambda
│       ├── seed_data.py            # Data seeding Lambda
│       └── requirements.txt        # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── ImageUpload.tsx     # Image upload component
│   │   │   ├── ProductCard.tsx     # Product display component
│   │   │   └── ChatInterface.tsx   # AI chat interface
│   │   ├── services/
│   │   │   └── api.ts              # API client
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript types
│   │   ├── App.tsx                 # Main React app
│   │   ├── index.tsx               # React entry point
│   │   └── index.css               # Tailwind CSS
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── scripts/
│   ├── deploy.sh                    # Deployment automation
│   └── test_api.py                 # API testing script
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI installed and configured
- Node.js 16+ (for frontend)
- Python 3.11 (for backend)
- AWS account with appropriate permissions

### 1. Clone and Setup
```bash
git clone https://github.com/your-username/ai-visual-shopping.git
cd ai-visual-shopping
```

### 2. Configure Bedrock model access for Nova models
Ensure you have access to these Nova models in your AWS account:
- `amazon.nova-multimodal-embedding-v1:0`
- `amazon.nova-lite-v1:0`

Request access through the AWS Console > Amazon Bedrock > Model Access.

### 3. Deploy Infrastructure
```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy standard production
./scripts/deploy.sh

# Or deploy demo-optimized version
./scripts/deploy.sh --demo
```

This will:
- Deploy CloudFormation stack
- Create S3 buckets, OpenSearch domain, Lambda functions, API Gateway
- Package and deploy Lambda code
- Seed OpenSearch with sample product data

### 4. Clean Up Resources (When Needed)
```bash
# Make cleanup script executable
chmod +x scripts/cleanup.sh

# Clean up all resources (with confirmation)
./scripts/cleanup.sh

# Clean up demo environment
./scripts/cleanup.sh --demo

# Force delete without confirmation
./scripts/cleanup.sh --force
```

### 5. Configure Frontend
After deployment, the script creates `frontend/.env` with your API URL. Install dependencies:

```bash
cd frontend
npm install
npm start
```

### 6. Test the Application
```bash
# Test API endpoints
python scripts/test_api.py https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev
```

## 🔧 Configuration

### Environment Variables
The Lambda functions use these environment variables (auto-configured by CloudFormation):

- `OPENSEARCH_ENDPOINT`: OpenSearch domain endpoint
- `OPENSEARCH_INDEX`: Index name (default: products)
- `PRODUCT_IMAGES_BUCKET`: S3 bucket for product images
- `USER_UPLOADS_BUCKET`: S3 bucket for user uploads
- `REGION`: AWS region

### Frontend Configuration
Create `frontend/.env`:
```
REACT_APP_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev
REACT_APP_REGION=us-east-1
```

## 📊 API Endpoints

### POST /search
Search for visually similar products.

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "query": "Show me similar products",
  "preferences": "Show me similar in blue under $100",
  "max_price": 100,
  "min_price": 50,
  "size": 5
}
```

**Response:**
```json
{
  "products": [
    {
      "product_id": "dress_002",
      "title": "Blue Summer Sundress",
      "description": "Light and comfortable blue sundress...",
      "price": 45.99,
      "category": "dresses",
      "color": "blue",
      "style": "casual",
      "image_url": "s3://bucket/images/dress_002.jpg",
      "score": 0.95
    }
  ],
  "explanation": "This blue summer sundress matches your uploaded style because...",
  "total_results": 5
}
```

### POST /explain
Generate AI explanations for products.

**Request:**
```json
{
  "query": "Show me similar products",
  "products": [...],
  "preferences": "I prefer blue items under $100"
}
```

## 🧠 How It Works

### 1. Image Upload & Processing
- User uploads product image via React frontend
- Image is converted to base64 and sent to API Gateway
- Lambda function receives the image and generates embedding using Nova Multimodal Embedding

### 2. Vector Search
- Generated embedding is used to query OpenSearch k-NN index
- OpenSearch returns top 5 most similar products based on visual similarity
- Results are filtered by price, color, and category if specified

### 3. AI-Powered Filtering
- Nova 2 Lite analyzes user preferences ("blue under $100")
- Filters search results based on natural language understanding
- Ensures results match both visual similarity and user constraints

### 4. Generative Explanation
- Nova 2 Lite generates personalized explanation
- Explains why each product matches the user's uploaded image and preferences
- Provides conversational, helpful shopping assistance

## 📈 Performance & Scaling

### Vector Search Performance
- OpenSearch k-NN with HNSW algorithm for fast similarity search
- 1024-dimensional embeddings for high-quality visual matching
- Configurable search parameters (ef_search, k)

### Lambda Scaling
- Automatic scaling based on request volume
- 1024MB memory, 60-second timeout for image processing
- Cold start optimization with package size optimization

### Cost Optimization
- Pay-per-use Lambda pricing
- S3 Intelligent-Tiering for image storage
- OpenSearch reserved instances for production workloads

## 🔒 Security

### IAM Permissions
The solution uses least-privilege IAM roles:
- Lambda functions have access only to required resources
- Bedrock access limited to specific Nova models
- S3 bucket policies prevent unauthorized access

### Data Privacy
- Images are processed server-side, not stored in browser
- No PII collected or stored
- S3 encryption at rest and in transit

### 7. Complete Rebuild (Clean + Deploy)
```bash
# Make rebuild script executable
chmod +x scripts/rebuild.sh

# Complete rebuild with confirmation
./scripts/rebuild.sh

# Rebuild demo environment
./scripts/rebuild.sh --demo

# Skip confirmation (automated rebuild)
./scripts/rebuild.sh --skip-confirm
```

## 🧪 Testing

### Unit Tests
```bash
# Test individual components
cd backend/lambdas
python -m pytest tests/

# Test frontend
cd frontend
npm test
```

### Integration Tests
```bash
# Test API endpoints
python scripts/test_api.py <api-url>

# Load testing
 artillery run load-test-config.json
```

## 📝 Monitoring & Logging

### CloudWatch Metrics
- Lambda invocation count and duration
- API Gateway request/response metrics
- OpenSearch search performance

### Logging
- Structured JSON logging in Lambda functions
- Error tracking and alerting
- Performance monitoring

## 🚀 Deployment

### Production Deployment
1. Update environment variables in `scripts/deploy.sh`
2. Set `ENVIRONMENT=prod`
3. Run deployment script
4. Configure custom domain for API Gateway
5. Set up CloudFront for frontend hosting

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to AWS
        run: ./scripts/deploy.sh
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## 🎮 Demo Script

See `scripts/demo.md` for a complete demo walkthrough:
1. Upload red dress image
2. Search for "similar in blue under $80"
3. Review AI-generated explanations
4. Test various preference combinations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Bedrock Model Access Denied**
- Ensure Nova models are enabled in AWS Console > Bedrock > Model Access
- Check IAM permissions for Bedrock InvokeModel

**OpenSearch Connection Timeout**
- Wait for OpenSearch domain to be fully available (can take 15-20 minutes)
- Check VPC configuration if using VPC endpoints

**Lambda Memory Issues**
- Increase memory allocation for image processing functions
- Optimize image size before processing

**CORS Errors**
- Check API Gateway CORS configuration
- Ensure frontend URL is allowed in CORS headers

### Debug Commands
```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name ai-visual-shopping

# Check Lambda function logs
aws logs tail /aws/lambda/ai-shopping-image-search-dev --follow

# Test OpenSearch connectivity
curl -X GET "https://your-domain.us-east-1.es.amazonaws.com/_cluster/health"
```

## 📞 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check AWS documentation for service-specific issues
- Review CloudWatch logs for detailed error information
