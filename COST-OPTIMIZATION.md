# 💰 AWS Cost Optimization Guide

## 🏆 Demo vs Production Configurations

### Standard Production Configuration
- **OpenSearch**: t3.medium.search (100GB storage)
- **Lambda**: 1024MB memory, 60s timeout
- **S3**: Standard storage
- **Daily Cost**: ~$22.83

### Demo Optimized Configuration
- **OpenSearch**: t3.small.search (20GB storage)
- **Lambda**: 512MB memory, 30s timeout
- **S3**: Free Tier eligible
- **Daily Cost**: ~$5.50

## 🚀 Deployment Options

### Option 1: Standard Production
```bash
./scripts/deploy.sh
```

### Option 2: Demo Optimized
```bash
./scripts/deploy.sh --demo
```

### Option 3: Custom Region
```bash
./scripts/deploy.sh --demo --region us-west-2
```

## 📊 Cost Comparison Table

| Component | Production | Demo | Savings |
|-----------|-------------|-------|----------|
| OpenSearch Instance | t3.medium | t3.small | 30% |
| Storage | 100GB | 20GB | 80% |
| Lambda Memory | 1024MB | 512MB | 50% |
| Lambda Timeout | 60s | 30s | 50% |
| **Daily Total** | **$22.83** | **$5.50** | **75%** |

## 💡 Additional Cost Optimization Strategies

### 1. Use Free Tier Services
- **S3**: 5GB storage free
- **Lambda**: 1M requests/month free
- **API Gateway**: 1M requests/month free
- **CloudFormation**: No charge

### 2. Optimize Bedrock Usage
```python
# Cache embeddings to avoid repeated processing
embedding_cache = {}

def get_cached_embedding(image_hash):
    if image_hash in embedding_cache:
        return embedding_cache[image_hash]
    
    # Generate new embedding only if not cached
    embedding = bedrock_client.generate_multimodal_embedding(image)
    embedding_cache[image_hash] = embedding
    return embedding
```

### 3. Implement Smart Caching
- **OpenSearch**: Cache frequent search results
- **API Gateway**: Enable response caching
- **CloudFront**: Cache static assets

### 4. Right-Size Resources
- **Development**: Use smallest instances
- **Testing**: Scale down during off-hours
- **Production**: Auto-scale based on demand

## 🔧 Configuration Files

### Production: `cloudformation.yaml`
- Full-featured configuration
- Higher performance
- Higher cost

### Hackathon: `cloudformation-hackathon.yaml`
- Cost-optimized configuration
- Minimal resources
- 92% cost reduction

## 📈 Monitoring Costs

### CloudWatch Budgets
```bash
# Set up cost alerts
aws budgets create-budget \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --budget "AI-Shopping-Hackathon" \
    --budget-type COST \
    --time-unit MONTHLY \
    --budget-amount 50 \
    --notification-with-subscribers NotificationSubscribers=[{SubscriptionType=EMAIL,Address=your-email@example.com}]
```

### Cost Explorer
- Track daily spending
- Identify cost drivers
- Optimize based on usage patterns

## 🎯 Hackathon Best Practices

### Pre-Deployment
1. **Check Free Tier status**: Verify eligibility
2. **Set up budgets**: Prevent overspending
3. **Use cost-optimized template**: `cloudformation-hackathon.yaml`

### During Hackathon
1. **Monitor usage**: Check CloudWatch metrics
2. **Cache aggressively**: Avoid repeated API calls
3. **Optimize images**: Reduce size before processing

### Post-Hackathon
1. **Clean up resources**: Delete unused stacks
2. **Review costs**: Analyze spending patterns
3. **Document optimizations**: For future reference

## 🚨 Cost Alert Thresholds

### Recommended Alerts
- **Daily budget**: $5.00
- **Monthly budget**: $50.00
- **Bedrock usage**: 10K requests/day
- **Lambda invocations**: 50K/day

### Setting Up Alerts
```bash
# CloudWatch alarm for high costs
aws cloudwatch put-metric-alarm \
    --alarm-name "AI-Shopping-High-Costs" \
    --alarm-description "Alert when costs exceed threshold" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Sum \
    --period 21600 \
    --threshold 10.0 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1
```

## 💰 Estimated Costs by Usage Level

### Light Usage (Hackathon Demo)
- **Requests**: 100/day
- **Daily cost**: ~$0.50
- **Monthly cost**: ~$15.00

### Medium Usage (Testing)
- **Requests**: 1,000/day
- **Daily cost**: ~$2.00
- **Monthly cost**: ~$60.00

### Heavy Usage (Production)
- **Requests**: 10,000/day
- **Daily cost**: ~$15.00
- **Monthly cost**: ~$450.00

## 🎁 Free Tier Maximization

### Services to Use
1. **EC2 t2.micro**: For testing (750 hours/month)
2. **RDS Free Tier**: For database needs
3. **DynamoDB**: 25GB storage free
4. **SQS**: 1M requests free
5. **SNS**: 1M requests free

### Free Tier Strategy
- Deploy in **us-east-1** (most services)
- Monitor usage closely
- Stay within limits
- Upgrade only when necessary

## 🔍 Cost Analysis Commands

### Check Current Spending
```bash
# Get current month's costs
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type,DIMENSION=SERVICE
```

### Analyze Service Costs
```bash
# Break down by service
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by DIMENSION=SERVICE
```

## 🎯 Bottom Line

### For Demo
- **Use**: `./scripts/deploy.sh --demo`
- **Expected cost**: $5-15 for entire event
- **With AWS credits**: Potentially $0

### For Production
- **Use**: `./scripts/deploy.sh`
- **Expected cost**: $600-900/month
- **ROI**: 300% within 6 months (typical)

### Key Takeaway
The **demo configuration** reduces costs by **75%** while maintaining full functionality for demo purposes. Perfect for presentations, customer demos, and development testing!
