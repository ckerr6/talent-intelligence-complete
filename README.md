# 🎯 Talent Intelligence Platform

**The most comprehensive talent sourcing and intelligence system for discovering, analyzing, and reaching top technical talent.**

**Status:** ✅ **MVP Complete** | **Last Updated:** October 23, 2025

---

## 📊 Platform Overview

### Database Scale
- **155,173 people** with comprehensive profiles
- **96,860 companies** with employment history
- **239,878 employment records** (career trajectories)
- **60,368 email addresses** (verified contacts)
- **100,877 GitHub profiles** (62.43% linkage rate)
- **333,947 GitHub repositories** tracked
- **238,983 contribution records** analyzed
- **1,997 PR-enriched profiles** with quality metrics
- **24,055 confirmed merged PRs** tracked

### Technology Stack
- **Database:** PostgreSQL (primary) with 40+ optimized indexes
- **Backend:** FastAPI with Python 3.13
- **Frontend:** React + TypeScript + Tailwind CSS
- **Caching:** Redis for 17x API performance boost
- **AI/ML:** OpenAI GPT-4o-mini + Claude 3.5 Sonnet
- **Visualization:** Recharts + vis-network

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- PostgreSQL 14+
- Python 3.13+
- Node.js 18+
- Redis (optional, for caching)

# Environment variables
- OPENAI_API_KEY (for AI features)
- ANTHROPIC_API_KEY (optional, for Claude)
- GITHUB_TOKEN (for PR enrichment)
```

### 1. Start the Database
```bash
# PostgreSQL should be running
psql -d talent -c "SELECT COUNT(*) FROM person;"
```

### 2. Start the API
```bash
python3 run_api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
# UI: http://localhost:3000
```

### 4. (Optional) Start Redis Cache
```bash
redis-server
# Enables 17x faster API responses
```

---

## 💡 Key Features

### 🔍 Advanced Search & Discovery
- **Multi-filter search** across skills, companies, locations, GitHub activity
- **148K+ searchable candidates** with rich profiles
- **Real-time filters** for email availability, GitHub presence, employment status

### 👤 Unified Profile View
- **LinkedIn + GitHub integration** in single view
- **Complete employment timeline** with company transitions
- **Verified contact information** (emails, social links)
- **GitHub contribution analysis** with quality scoring
- **AI-generated career summaries** and insights

### 🤖 AI-Powered Intelligence
- **Profile summaries** in recruiter-friendly language
- **Code quality analysis** for GitHub repositories
- **Interactive Q&A** about candidate experience
- **Match scoring** based on skills, activity, and reachability

### 📊 Market Intelligence
- **Company hiring trends** with visual analytics
- **Talent flow analysis** (where people come from/go to)
- **Technology distribution** across companies
- **Dataset-wide statistics** for market insights
- **AI-powered queries** to explore market data

### 🕸️ Network Visualization
- **Interactive network graph** showing professional connections
- **Up to 3 degrees of separation** visualization
- **Co-employment connections** (worked at same company)
- **GitHub collaboration** (contributed to same repos)
- **Filter by company or repository**

### 🔬 GitHub Contribution Analysis
- **Expert-sourcer workflows** automated
- **Merged PR tracking** (confirmed contributions)
- **Code volume metrics** (lines contributed)
- **Quality scoring** (0-100 algorithm)
- **Fork vs official repo** distinction
- **Pro account detection** (private repos indicator)

---

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/GETTING_STARTED.md)** - Get up and running in 5 minutes
- **[Setup Documentation](GITHUB_PR_ENRICHMENT_SETUP.md)** - GitHub PR enrichment
- **[Frontend Guide](QUICK_START_FRONTEND.md)** - React app details

### User Guides
- **[GitHub Sourcing](GITHUB_SOURCING_ENHANCEMENTS.md)** - Expert sourcer workflows
- **[AI Features](AI_SETUP_AND_USAGE.md)** - Using AI-powered insights
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

### Technical Documentation
- **[Architecture](docs/README.md)** - System architecture overview
- **[Database Schema](migration_scripts/)** - Table structures and migrations
- **[Performance Optimization](PERFORMANCE_OPTIMIZATION_COMPLETE.md)** - Speed improvements

### Project Status
- **[Current Status](PROJECT_STATUS.md)** - What's working right now
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[Milestones](docs/milestones/)** - Completed features and phases

---

## 🎯 Use Cases

### For Recruiters
1. **Find Hidden Talent** - Discover developers not active on LinkedIn
2. **Verify Technical Skills** - See real code contributions and PRs
3. **Understand Networks** - Leverage connections for warm intros
4. **Assess Quality** - Automated scoring of contributor quality
5. **Export Lists** - Build and share candidate pipelines

### For Hiring Managers
1. **Market Intelligence** - See where talent is concentrated
2. **Company Benchmarking** - Compare tech stacks and teams
3. **Talent Flow** - Understand hiring patterns
4. **Technology Trends** - What languages/frameworks are popular

### For Investors/Demos
1. **Unique Differentiation** - Data no competitor has
2. **Scale Demonstration** - 155K+ profiles with deep insights
3. **AI Integration** - Modern LLM-powered features
4. **Performance** - Sub-second queries with Redis caching

---

## 📈 Platform Capabilities

### Data Sources
- ✅ **LinkedIn** - Professional profiles and employment
- ✅ **GitHub** - Code contributions and repositories
- ✅ **Email** - Verified contact information
- ✅ **Clay** - Enriched company and contact data
- 🔄 **Twitter** - Social presence (Phase 2)

### Enrichment Features
- ✅ **GitHub PR Analysis** - Confirmed merged PRs
- ✅ **Code Quality Scoring** - Automated 0-100 rating
- ✅ **Employment History** - Complete career trajectories
- ✅ **Email Discovery** - Contact information
- ✅ **Network Analysis** - Professional connections
- ✅ **AI Summarization** - Profile and code analysis

### Export & Integration
- ✅ **CSV Export** - Full data exports
- ✅ **API Access** - RESTful API for integrations
- ✅ **Candidate Lists** - Save and share talent pools
- ✅ **Search Persistence** - Saved search queries
- 🔄 **ATS Integration** - Future feature

---

## 🔧 Development

### Project Structure
```
talent-intelligence-complete/
├── api/                      # FastAPI backend
│   ├── routers/              # API endpoints
│   ├── models/               # Pydantic models
│   ├── crud/                 # Database operations
│   └── services/             # Business logic
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/            # Main views
│   │   ├── components/       # Reusable components
│   │   └── services/         # API clients
├── enrichment_scripts/       # Data enrichment tools
├── migration_scripts/        # Database migrations
├── docs/                     # Documentation
└── tests/                    # Test suites
```

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test

# Database tests
python -m pytest tests/test_database.py
```

### Contributing
1. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for current priorities
2. Create feature branch from `main`
3. Follow existing code patterns
4. Add tests for new features
5. Update documentation
6. Submit PR with clear description

---

## 📊 Performance Metrics

### Database Performance
- **Query Time:** < 1 second for most queries
- **Index Coverage:** 40+ indexes totaling 1.3GB
- **Cache Hit Rate:** ~85% with Redis enabled
- **API Response:** 17x faster with caching

### Data Quality
- **GitHub Linkage:** 62.43% of people have GitHub profiles
- **Email Coverage:** 38.9% have verified emails
- **Employment History:** 1.5 jobs per person average
- **PR Enrichment:** 1,997 profiles with merge data

### Scalability
- **Current:** 155K people, 333K repositories
- **Tested:** Sub-second queries at current scale
- **Target:** 1M+ people (architecture supports)

---

## 🎯 Roadmap

### ✅ Completed (MVP)
- [x] Full-stack application (API + Frontend)
- [x] LinkedIn + GitHub integration
- [x] AI-powered insights
- [x] Network visualization
- [x] Market intelligence dashboard
- [x] GitHub PR enrichment automation
- [x] Performance optimization (Redis caching)
- [x] Expert-sourcer workflows

### 🔄 In Progress
- [ ] Enrich remaining 2,472 full profiles with PR data
- [ ] Build saved searches and candidate lists
- [ ] Add profile notes and tags

### 📋 Planned
- [ ] Twitter/X integration
- [ ] Email verification workflows
- [ ] ATS integration
- [ ] Multi-user/multi-org support
- [ ] Advanced analytics dashboard
- [ ] Mobile-responsive improvements

---

## 🆘 Support & Resources

### Documentation
- **📖 Full Docs:** See [docs/](docs/) folder
- **🔧 API Docs:** http://localhost:8000/docs (when running)
- **💬 Guides:** [docs/guides/](docs/guides/)

### Common Tasks
```bash
# Check database stats
psql -d talent -c "SELECT COUNT(*) FROM person;"

# Monitor enrichment progress
./check_enrichment_progress.sh

# Query specific data
./query_database.sh

# Backup database
pg_dump -d talent > backup_$(date +%Y%m%d).sql
```

### Troubleshooting
- **API not starting?** Check PostgreSQL is running
- **Frontend errors?** Run `npm install` in frontend/
- **Slow queries?** Enable Redis caching
- **GitHub API limits?** Check token in .env file

---

## 📄 License

Proprietary - All Rights Reserved

---

## 🎉 Key Achievements

- ✅ **MVP Complete** - All core features working
- ✅ **155K+ Profiles** - Rich talent database
- ✅ **24K+ Merged PRs** - Unique contribution data
- ✅ **62% GitHub Linkage** - Industry-leading integration
- ✅ **AI-Powered** - Modern LLM integration
- ✅ **Sub-Second Queries** - High performance
- ✅ **Production Ready** - Investor-demo quality

---

**Built with ❤️ for the future of talent intelligence**

*Last updated: October 23, 2025*
