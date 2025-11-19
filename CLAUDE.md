# AdoptAI API - Claude Instructions

## Project Overview

REST API for the Adopt AI Grand Palais conference (Nov 25-26, 2025, Paris).
Provides AI-accessible endpoints for 240+ sessions and 200+ speakers.

## Architecture

- **Infrastructure**: AWS CDK (TypeScript) in `/cdk`
- **Runtime**: Lambda Python 3.14 with SnapStart
- **Storage**: S3 bucket for JSON data
- **Delivery**: CloudFront + Lambda Function URL
- **Domain**: adoptai.codecrafter.fr

## Project Structure

```
AdoptAI/
├── data/                    # Conference data
│   ├── sessions.json        # 243 sessions
│   └── speakers.json        # 499 speakers
├── cdk/                     # CDK infrastructure
│   ├── bin/cdk.ts          # Entry point
│   ├── lib/
│   │   ├── adoptai-stack.ts # Main stack
│   │   └── lambda/
│   │       └── handler.py   # API handler
│   ├── package.json
│   └── yarn.lock
├── llms.txt                 # API documentation for LLMs
└── readme.txt               # Project README
```

## Development Commands

```bash
# CDK commands (from /cdk directory)
yarn install          # Install dependencies
yarn cdk synth        # Synthesize CloudFormation
yarn cdk deploy       # Deploy stack
yarn cdk diff         # Compare with deployed

# Deploy with custom domain
yarn cdk deploy --context certificateArn=arn:aws:acm:us-east-1:xxx:certificate/xxx
```

## API Endpoints

- `GET /` or `/llms.txt` - API documentation
- `GET /sessions` - List sessions (filters: date, stage, time, search)
- `GET /speakers` - List speakers (filter: search)
- `GET /health` - Health check

## Key Files

- `cdk/lib/adoptai-stack.ts` - Main CDK stack definition
- `cdk/lib/lambda/handler.py` - Lambda handler with routing and filtering logic
- `data/sessions.json` - Session data with speakers embedded
- `llms.txt` - LLM-friendly API documentation

## Notes

- Uses CDK Nag for security best practices validation
- SnapStart enabled for reduced cold start latency
- CORS enabled for all origins
- Data is static (scraped Nov 19, 2025)

## Deployment Prerequisites

1. AWS CLI configured
2. ACM certificate in us-east-1 for custom domain
3. Route 53 or DNS access for domain validation
