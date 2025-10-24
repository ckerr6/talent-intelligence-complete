# PhantomBuster MCP Setup Instructions

## 1. Install Dependencies

```bash
cd enrichment_scripts
pip install -r requirements-phantombuster.txt
```

## 2. Configure Environment Variables

Add these to your `.env` file in the project root:

```bash
# PhantomBuster MCP Configuration
PHANTOMBUSTER_API_KEY=your_api_key_here
PHANTOMBUSTER_MCP_URL=https://mcp.pipedream.net/v2
```

## 3. Get Your PhantomBuster API Key

1. Visit https://phantombuster.com/
2. Go to Settings > API
3. Copy your API key
4. Paste it into the `.env` file

## 4. Run Test Enrichment

```bash
python phantombuster_linkedin_enrichment.py --test --batch-size 15
```

## 5. Monitor Progress

```bash
python monitor_enrichment_progress.py
```

Or use SQL queries:
```bash
psql postgresql://localhost/talent -f ../sql/queries/enrichment_monitor.sql
```

