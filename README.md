# AI Visual Shopping - Multimodal Ecommerce with Amazon Nova

An AI-powered visual shopping application that allows users to upload product images and receive personalized recommendations using Amazon's Nova multimodal models and S3-backed vector storage.

## 🎯 Features

- **🖼️ Visual Search**: Upload product images to find visually similar items
- **🤖 AI-Powered**: Uses Amazon Nova models for embeddings and text generation
- **💰 Cost-Optimized**: S3 vector storage instead of expensive OpenSearch clusters
- **🔍 Smart Filtering**: Filter results by price, color, category, and style
- **📝 AI Explanations**: Get personalized explanations for product recommendations
- **🚀 Serverless**: Built with AWS Lambda and API Gateway for scalability

## 🏗️ Architecture

```
User Upload Image → Lambda → Nova Embeddings → S3 Vector Store → k-NN Search → Similar Products → AI Explanation
```

### Key Components

- **Frontend**: React application for image upload and results display
- **Backend**: AWS Lambda functions for processing
- **AI Models**: Amazon Nova multimodal embeddings and text generation
- **Vector Storage**: S3-backed vector storage (cost-optimized)
- **API**: Amazon API Gateway for REST endpoints
- **Storage**: S3 buckets for images and vector data

## 💡 Cost Optimization

This project uses **S3-backed vector storage** instead of traditional OpenSearch clusters:

| Component | Traditional | This Project | Monthly Savings |
|-----------|------------|--------------|----------------|
| Vector Database | OpenSearch ($540/month) | S3 Storage ($2/month) | **$538** |
| Total Cost | ~$542/month | ~$15/month | **97% reduction** |

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with access to:
   - AWS Lambda
   - Amazon Bedrock
   - Amazon S3
   - Amazon API Gateway

2. **Request Nova Model Access** in AWS Bedrock Console:
   - `amazon.nova-2-multimodal-embeddings-v1:0`
   - `amazon.nova-2-lite-v1:0`

3. **Install AWS CLI** and configure credentials

### Deployment

#### Deployment (Cost-Optimized)
```bash
./scripts/deploy.sh
```

#### Production Deployment
```bash
./scripts/deploy.sh
```


## 📁 Project Structure

```
ai-visual-shopping/
├── backend/
│   ├── cloudformation.yaml          # Infrastructure template
│   └── lambdas/                      # Lambda functions
│       ├── seed_data.py             # Data seeding
│       ├── image_search.py          # Visual search
│       ├── generate_explanation.py  # AI explanations
│       ├── bedrock_client.py        # Nova model client
│       └── s3_vector_store.py       # S3 vector storage
├── frontend/                         # React application
├── scripts/                         # Deployment and utility scripts
│   ├── deploy.sh                    # Main deployment script
│   ├── cleanup.sh                   # Resource cleanup
│   └── test_api.py                  # API testing
└── README.md                        # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|-----------|-------------|---------|
| `PRODUCT_IMAGES_BUCKET` | S3 bucket for product images | `ai-shopping-catalog` |
| `USER_UPLOADS_BUCKET` | S3 bucket for user uploads | `ai-shopping-uploads` |
| `REGION` | AWS region | `us-east-1` |

### Nova Models

- **Embeddings**: `amazon.nova-2-multimodal-embeddings-v1:0`
- **Text Generation**: `amazon.nova-2-lite-v1:0`

## API Endpoints

Below are the primary REST endpoints exposed by the API Gateway. Responses are JSON.

### POST /search
Search for visually similar products. The request should include a base64 image and optional query/preferences/filters.

Example curl request:
```bash
curl -X POST https://{api_base}/search \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "query": "similar summer dress",
    "preferences": "blue, casual, under $100",
    "max_price": 100,
    "min_price": 10,
    "size": 5
  }'
```

Request body (JSON):
```json
{
  "image": "data:image/jpeg;base64,...",
  "query": "optional text query",
  "preferences": "natural language preferences",
  "max_price": 100,
  "min_price": 10,
  "color": "blue",
  "category": "dresses",
  "size": 5
}
```

Response (successful):
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
      "image_url": "https://.../images/dress_002.jpg",
      "score": 0.95,
      "explanation": "Matches your uploaded style because the silhouette, color and fabric..."
    }
  ],
  "total_results": 5
}
```

Notes:
- Each returned product may include an `explanation` field with a short AI-generated rationale for that product.
- The top-level `explanation` field is no longer used; explanations are per-product.

### POST /explain
Generate or refresh AI explanations for a list of products (server-side; useful for batch workflows).

Request body:
```json
{
  "query": "optional contextual query",
  "products": [ { "product_id": "...", "title": "...", "image_url": "..." } ],
  "preferences": "I prefer blue items under $100"
}
```

Response:
```json
{
  "products": [
    { "product_id": "dress_002", "explanation": "..." },
    { "product_id": "shoe_004", "explanation": "..." }
  ]
}
```

## 🧠 How It Works

### 1. Image Upload & Processing
- User uploads product image via React frontend
- Image is converted to base64 and sent to API Gateway
- Lambda function receives the image and generates embedding using Nova Multimodal Embedding

### 2. Vector Search
- Generated embedding is used to query S3 vector store
- S3 vector store performs in-memory k-NN search for similar products
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
- In-memory k-NN search with cosine similarity for fast matching
- 1024-dimensional embeddings for high-quality visual matching
- Configurable search parameters (size, similarity threshold)

### Lambda Scaling
- Automatic scaling based on request volume
- 1024MB memory, 60-second timeout for image processing
- Cold start optimization with package size optimization

### Cost Optimization
- Pay-per-use Lambda pricing
- S3 Intelligent-Tiering for image storage
- S3 vector storage eliminates expensive database costs

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

# Rebuild environment
./scripts/rebuild.sh

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


## 📝 Monitoring & Logging

### CloudWatch Metrics
- Lambda invocation count and duration
- API Gateway request/response metrics
- S3 vector storage performance

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

**S3 Vector Storage Issues**
- Check S3 bucket permissions and CORS configuration
- Verify vector data is properly seeded in S3
- Check Lambda function logs for S3 access errors

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

# Test S3 vector storage
aws s3 ls s3://ai-shopping-catalog-dev/vectors/
```

## 📞 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check AWS documentation for service-specific issues
- Review CloudWatch logs for detailed error information
