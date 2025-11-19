# 🤖 Adopt AI Grand Palais 2025 - API

> An AI-friendly REST API for the Adopt AI Grand Palais conference schedule

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)](https://aws.amazon.com/lambda/)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Why?

The official [Adopt AI Grand Palais](https://adoptai.artefact.com) website uses infinite-scroll JavaScript rendering that's impossible for AI assistants to parse. 

This API provides **clean, structured, filterable endpoints** so AI assistants like Claude and ChatGPT can actually help attendees navigate the conference.

**The irony**: An AI summit without AI-readable data. This fixes that.

## 🚀 Quick Start

### For AI Assistants

Just tell Claude/ChatGPT:
```
"Fetch https://adoptai.codecrafter.fr and help me find sessions 
about AI in banking on November 25"
```

The API is designed to be self-documenting. AI assistants can read the `/llm.txt` endpoint for full instructions.

### For Developers
```bash
# Get all sessions
curl https://adoptai.codecrafter.fr/sessions

# Filter by date and stage
curl "https://adoptai.codecrafter.fr/sessions?date=2025-11-25&stage=CEO%20Stage"

# Search sessions
curl "https://adoptai.codecrafter.fr/sessions?search=banking"

# Get speakers
curl https://adoptai.codecrafter.fr/speakers
```

## 📚 API Documentation

### Endpoints

| Endpoint | Description | Filters |
|----------|-------------|---------|
| `GET /sessions` | All conference sessions | `date`, `stage`, `time`, `search` |
| `GET /speakers` | All speakers | `search` |
| `GET /` | API documentation | - |
| `GET /health` | Health check | - |

### Query Parameters

#### `/sessions`

- **`date`**: `2025-11-25` or `2025-11-26`
- **`stage`**: `CEO Stage`, `Mainstage South`, `Mainstage North`, `Mainstage East`, `Masterclass South`, `Masterclass North`, `Startup Stage`
- **`time`**: `morning` (before 12:00) or `afternoon` (12:00+)
- **`search`**: Full-text search in titles, descriptions, speaker names

#### `/speakers`

- **`search`**: Search by name, company, or role

### Examples
```bash
# Nobel Prize keynote
curl "https://adoptai.codecrafter.fr/sessions?search=Aghion"

# All morning sessions on Nov 25
curl "https://adoptai.codecrafter.fr/sessions?date=2025-11-25&time=morning"

# Finance-related sessions
curl "https://adoptai.codecrafter.fr/sessions?search=finance"

# Speakers from Anthropic
curl "https://adoptai.codecrafter.fr/speakers?search=Anthropic"
```

## 🏗️ Architecture
```
┌─────────────┐
│   Client    │
│ (AI/Human)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  CloudFront     │
│  + Custom       │
│  Domain         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Lambda         │
│  Function URL   │
│  (Python 3.14)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  S3 Bucket      │
│  sessions.json  │
│  speakers.json  │
└─────────────────┘
```

**Tech Stack:**
- **AWS Lambda** (Python 3.14) - Serverless compute
- **S3** - Data storage
- **Lambda Function URL** - Direct HTTPS endpoint (no API Gateway)
- **CloudFront** - CDN + custom domain

## 📊 Data

- **240+ sessions** across 8 stages
- **200+ speakers** from leading AI companies
- **2 days**: November 25-26, 2025
- **Venue**: Grand Palais, Paris

### Notable Speakers

- **Philippe Aghion** - 2025 Nobel Prize in Economics
- **Guillaume Princen** - Anthropic Head of EMEA
- **Dr. Najwa Aaraj** - Technology Innovation Institute CEO
- And many more...

## 💰 Cost

Essentially **free** with AWS Free Tier:
- Lambda: 1M requests/month free
- S3: Negligible storage + GET costs
- CloudFront: 1TB transfer/month free

Estimated cost beyond free tier: **~$0.10/month** for typical usage.

## 🚀 Deployment

### Prerequisites

- AWS account
- AWS CLI configured
- Python 3.14
- Domain configured (codecrafter.fr)

### Deploy
```bash
# Clone the repo
git clone https://github.com/ThomasHoussin/adoptai-api.git
cd adoptai-api

# Run deployment script
./deploy.sh

# Configure custom domain (CloudFront)
# See DEPLOYMENT.md for details
```

## 🤝 Contributing

Found incorrect data? Session changed? Open an issue or PR!
```bash
# Update sessions data
vi data/sessions.json

# Redeploy
./deploy.sh
```

## 📝 License

MIT License - feel free to use this for other conferences!

## 👨‍💻 Author

**Thomas Houssin**
- GitHub: [@ThomasHoussin](https://github.com/ThomasHoussin)
- Website: [codecrafter.fr](https://codecrafter.fr)

Built in 3 hours because AI events should be AI-accessible.

## 🙏 Acknowledgments

- Data scraped from [Adopt AI Grand Palais](https://adoptai.artefact.com)
- Inspired by the llms.txt convention
- Built with the best serverless tools AWS offers

---

**"Adopt AI... but make it actually adoptable by AI"** 🤖