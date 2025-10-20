# 📅 7-Day Talent Database Recovery Plan

## Overview
Jesse, here's your pragmatic, step-by-step plan to get your recruiting database production-ready in one week. Each day has 2-3 hours of focused work with clear deliverables.

---

## Day 1 (Saturday) - Security & Foundation ✅
**Time Required: 2-3 hours**
**Status: READY TO EXECUTE**

### Morning Tasks
1. **Run Day 1 setup script** (5 minutes)
   ```bash
   cd /Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE
   chmod +x day1_setup.sh
   ./day1_setup.sh
   ```

2. **Test secure queries** (15 minutes)
   ```bash
   python3 query_database_secure.py
   # Try each option to verify SQL injection protection
   ```

3. **Set up automated backups** (10 minutes)
   ```bash
   # Add to crontab for 2 AM daily backups
   crontab -e
   # Add line: 0 2 * * * cd /Users/charlie.kerr/Documents/CK\ Docs/FINAL_DATABASE && /usr/bin/python3 backup_database.py --auto
   ```

4. **Git commit** (5 minutes)
   ```bash
   git add .
   git commit -m "Day 1: Fixed SQL injection, added backup system"
   git push origin main
   ```

### Deliverables
- ✅ SQL injection vulnerabilities fixed
- ✅ Automated backup system running
- ✅ Single database implementation (FINAL_DATABASE)
- ✅ All changes in git

---

## Day 2 (Sunday) - Configuration & GitHub Setup
**Time Required: 2-3 hours**
**Focus: GitHub API integration foundation**

### Morning Tasks
1. **Create configuration system** (30 minutes)
   - Replace all hardcoded paths with config file
   - Add .env support for API keys
   - Create config.py module

2. **Set up GitHub API client** (1 hour)
   - Test GitHub token from .env
   - Implement rate limiting handler
   - Add retry logic with exponential backoff

3. **Test GitHub enrichment** (30 minutes)
   - Run on 10 sample profiles
   - Verify data quality
   - Check rate limit handling

### Commands to Run
```bash
# Install dependencies
pip install python-dotenv requests

# Test GitHub setup
python3 test_github_setup.py

# Run small test batch
python3 github_api_enrichment.py --test --limit=10
```

### Deliverables
- ✅ Configuration management system
- ✅ Working GitHub API client
- ✅ Successful test enrichment of 10 profiles

---

## Day 3 (Monday) - Logging & GitHub Enrichment
**Time Required: 2-3 hours**
**Focus: Production logging and full GitHub run**

### Morning Tasks (30 minutes)
1. **Add proper logging** (30 minutes)
   - Replace print statements with logging module
   - Add rotating file handlers
   - Implement log levels (DEBUG, INFO, WARNING, ERROR)

### Evening Tasks (Set and Forget - 3-4 hours unattended)
2. **Run full GitHub enrichment**
   ```bash
   # Start in background/screen session
   screen -S github_enrichment
   python3 build_github_enrichment.py
   # Detach with Ctrl+A, D
   # Will run for 3-4 hours unattended
   ```

### Deliverables
- ✅ Professional logging system
- ✅ GitHub enrichment running (15k+ profiles processing)
- ✅ Enrichment logs for monitoring

---

## Day 4 (Tuesday) - Company Data & LinkedIn Import
**Time Required: 2-3 hours**
**Focus: Complete company database and LinkedIn CSVs**

### Morning Tasks
1. **Import LinkedIn CSVs** (1 hour)
   - Find all LinkedIn export CSVs
   - Run import with deduplication
   - Generate quality report

2. **Build company database** (1 hour)
   - Import company CSVs
   - Match companies to people
   - Add funding round data

3. **Run comprehensive deduplication** (30 minutes)
   ```bash
   python3 deduplicate_people.py --aggressive
   ```

### Commands to Run
```bash
# Import LinkedIn data
python3 import_linkedin_csvs.py

# Build company database
python3 build_company_database.py

# Check results
python3 query_database_secure.py
```

### Deliverables
- ✅ All LinkedIn profiles imported
- ✅ Company database populated
- ✅ Clean, deduplicated dataset

---

## Day 5 (Wednesday) - Testing & PostgreSQL Prep
**Time Required: 2-3 hours**
**Focus: Add tests and prepare for PostgreSQL migration**

### Tasks
1. **Add pytest test suite** (1.5 hours)
   - Test deduplication logic
   - Test import functions
   - Test data quality scoring
   - Test query functions

2. **PostgreSQL preparation** (30 minutes)
   - Install PostgreSQL locally
   - Create migration schema
   - Set up connection pooling

3. **Data quality audit** (30 minutes)
   - Run comprehensive quality checks
   - Identify data gaps
   - Generate improvement report

### Commands to Run
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ --cov=. --cov-report=term-missing

# Set up PostgreSQL
brew install postgresql
brew services start postgresql
createdb talent_intelligence
```

### Deliverables
- ✅ Test suite with 80%+ coverage
- ✅ PostgreSQL ready for migration
- ✅ Data quality report

---

## Day 6 (Thursday) - PostgreSQL Migration & API Start
**Time Required: 3-4 hours**
**Focus: Move to production database and start API**

### Morning Tasks
1. **Migrate to PostgreSQL** (2 hours)
   - Run migration script
   - Verify all data transferred
   - Update queries for PostgreSQL

2. **Start FastAPI development** (1.5 hours)
   - Create basic API structure
   - Add authentication skeleton
   - Implement first endpoints

### Commands to Run
```bash
# Run migration
python3 migrate_to_postgres.py

# Install FastAPI
pip install fastapi uvicorn sqlalchemy psycopg2-binary

# Start API server
uvicorn main:app --reload
```

### Deliverables
- ✅ Data in PostgreSQL
- ✅ Basic API running locally
- ✅ /candidates endpoint working

---

## Day 7 (Friday) - API Completion & Deployment Prep
**Time Required: 3-4 hours**
**Focus: Complete API and prepare for deployment**

### Tasks
1. **Complete core API endpoints** (2 hours)
   - Search endpoints
   - Export endpoints
   - Company endpoints
   - Statistics endpoint

2. **Add Streamlit UI** (1 hour)
   - Basic search interface
   - Results display
   - Export functionality

3. **Dockerize application** (30 minutes)
   - Create Dockerfile
   - Add docker-compose.yml
   - Test container locally

4. **Documentation** (30 minutes)
   - API documentation
   - Deployment guide
   - User guide

### Commands to Run
```bash
# Install Streamlit
pip install streamlit

# Run Streamlit UI
streamlit run app.py

# Build Docker image
docker build -t talent-db .
docker run -p 8000:8000 talent-db
```

### Deliverables
- ✅ Complete API with documentation
- ✅ Basic UI for non-technical users
- ✅ Docker container ready for deployment
- ✅ Documentation complete

---

## Week 1 Success Metrics

By end of week, you'll have:
- **50,000+ enriched candidates** (vs 15k currently)
- **60%+ with verified emails** (vs 40% currently)  
- **40%+ with GitHub profiles** (vs 5% currently)
- **Production PostgreSQL database** (vs local SQLite)
- **RESTful API** with authentication
- **Web UI** for easy access
- **Docker container** ready for deployment
- **Automated backups** running daily
- **Test coverage** at 80%+

---

## Critical Path Items

**Must complete in order:**
1. Day 1: Security fixes (blocking everything)
2. Day 2-3: GitHub enrichment (48-hour process)
3. Day 4: Data completion (needed before migration)
4. Day 6: PostgreSQL migration (needed for API)

**Can parallelize:**
- Testing (Day 5) can happen anytime after Day 1
- UI development can start anytime after API basics

---

## Daily Success Checklist

At the end of each day, commit to git:
```bash
git add .
git commit -m "Day N: [What you accomplished]"
git push origin main
```

---

## If You Get Stuck

1. **Check logs first** - The answer is often there
2. **Run the test suite** - It will catch most issues
3. **Restore from backup** if database gets corrupted
4. **Ask specific questions** with error messages

---

## Week 2 Preview (If Ahead of Schedule)

- Deploy to Railway/Render ($20/month)
- Add OAuth authentication 
- Implement email verification
- Add advanced search filters
- Build recruiter workflow features
- Add CRM integrations

---

Remember Jesse: **Doing it right > doing it fast**. But this plan gets you both.

Ready? Start with:
```bash
cd /Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE
./day1_setup.sh
```
