# Quick Start Guide - Frontend Testing

## Prerequisites

- Python 3.9+
- PostgreSQL database with talent intelligence data
- Web browser (Chrome, Firefox, or Safari recommended)

## Step 1: Start the API

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Start the FastAPI server
python run_api.py
```

The API should start on `http://localhost:8000`

**Verify API is running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "talent",
  "timestamp": "2025-10-22T...",
  "pool_health": {...}
}
```

## Step 2: Test Backend Endpoints

### Test Person Full Profile
```bash
# Replace {person_id} with an actual UUID from your database
curl http://localhost:8000/api/people/{person_id}/full
```

Expected: Complete profile with employment, emails, and GitHub data

### Test Analytics Endpoints
```bash
# Top repositories
curl "http://localhost:8000/api/analytics/top-repositories?limit=10"

# Top contributors  
curl "http://localhost:8000/api/analytics/top-contributors?limit=10"

# Technology distribution
curl "http://localhost:8000/api/analytics/technology-distribution"

# Developer activity summary
curl "http://localhost:8000/api/analytics/developer-activity-summary"

# Companies list
curl "http://localhost:8000/api/analytics/companies?limit=20"
```

## Step 3: Open the Dashboard

### Method 1: Double-click HTML files
1. Navigate to `dashboard/` folder in Finder
2. Double-click `index.html` to open in your default browser

### Method 2: Command line
```bash
cd dashboard
open index.html  # macOS
# or
xdg-open index.html  # Linux
```

### Method 3: Python HTTP Server (if CORS issues)
```bash
cd dashboard
python3 -m http.server 8080
```
Then open `http://localhost:8080` in your browser

## Step 4: Test Each Page

### A. People Database Page

1. Click "People" in navigation
2. **Test Search:**
   - Enter a company name (e.g., "Uniswap", "Google")
   - Click "Search" or press Enter
   - Verify table loads with results
3. **Test Filters:**
   - Try location filter (e.g., "San Francisco")
   - Try headline filter (e.g., "engineer")
   - Try "Has Email: Yes"
   - Combine multiple filters
4. **Test Pagination:**
   - Click "Next" to load more results
   - Verify server-side pagination works
5. **Test Profile Links:**
   - Click on a person's name
   - Should open profile page in new tab

**Expected Results:**
- ✅ Filters work and update results
- ✅ Pagination loads new pages
- ✅ "Showing X to Y of Z people" displays correctly
- ✅ Notification appears when filters applied

### B. Person Profile Page

1. Click on any person from People page OR navigate directly:
   ```
   file:///path/to/dashboard/profile.html?id={person_id}
   ```

2. **Verify Sections Display:**
   - ✅ Profile header with name and headline
   - ✅ Contact Information section with emails
   - ✅ Employment History with timeline
   - ✅ GitHub Profile stats (if available)
   - ✅ GitHub Contributions list (if available)

3. **Check Details:**
   - Primary email highlighted
   - Current job has green border + "Current" badge
   - Job durations calculated correctly
   - GitHub links work

4. **Test Error Handling:**
   - Try invalid person_id: `profile.html?id=invalid-uuid`
   - Should show error with "Try Again" button

**Expected Results:**
- ✅ All sections render without errors
- ✅ Skeleton loading appears briefly then content loads
- ✅ Employment history sorted (current first)
- ✅ Links to LinkedIn/GitHub work

### C. Analytics Dashboard Page

1. Click "Analytics" in navigation

2. **Verify Initial Load:**
   - Wait for loading message
   - Should show 3 metric cards + 3 charts
   - Company filter dropdown populated

3. **Test Charts:**
   - ✅ Top Repositories chart displays
   - ✅ Top Contributors chart displays
   - ✅ Technology Distribution donut chart displays
   - ✅ Metrics show numbers (not "-")

4. **Test Filters:**
   - Select a company from dropdown
   - Click "Apply Filters"
   - Watch charts reload with filtered data
   - Click "Reset" to go back to all companies

5. **Test Interactivity:**
   - Hover over chart bars (tooltip should appear)
   - Hover over donut segments (details shown)

**Expected Results:**
- ✅ All charts render without errors
- ✅ Filtering updates all charts and metrics
- ✅ Tooltips show additional information
- ✅ Charts are responsive (try resizing window)

## Step 5: Test Accessibility

### Keyboard Navigation:
1. On People page, use Tab to navigate filters
2. Press Enter in any text input to trigger search
3. Tab through DataTable pagination
4. Verify all interactive elements accessible

### Screen Reader Test (if available):
1. Turn on VoiceOver (macOS) or NVDA (Windows)
2. Navigate through filters
3. Verify ARIA labels are read correctly
4. Check chart descriptions are announced

## Step 6: Test Responsive Design

1. Open browser DevTools (F12 or Cmd+Option+I)
2. Toggle device toolbar
3. Test on:
   - iPhone (375px width)
   - iPad (768px width)
   - Desktop (1920px width)

**Expected:**
- ✅ Charts stack vertically on mobile
- ✅ Filters wrap appropriately
- ✅ DataTable scrolls horizontally on small screens
- ✅ No horizontal overflow

## Common Issues & Solutions

### Issue: API Connection Error

**Symptom:** "Connection issue. Check your network..."

**Solutions:**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check API_BASE_URL in JS files is correct
3. Check CORS settings if using file:// protocol
4. Try Python HTTP server method (Step 3, Method 3)

### Issue: No Data in Charts

**Symptom:** Charts empty or show "-"

**Solutions:**
1. Check API endpoints return data:
   ```bash
   curl http://localhost:8000/api/analytics/top-repositories
   ```
2. Verify database has GitHub data
3. Check browser console for errors (F12)

### Issue: DataTables Not Loading

**Symptom:** "Processing..." never completes

**Solutions:**
1. Check API endpoint: `curl http://localhost:8000/api/people?offset=0&limit=50`
2. Verify jQuery and DataTables CDNs loaded (check Network tab)
3. Look for JavaScript errors in console

### Issue: Person Profile Shows Skeleton Forever

**Symptom:** Skeleton loading doesn't disappear

**Solutions:**
1. Check person_id is valid UUID
2. Test endpoint: `curl http://localhost:8000/api/people/{person_id}/full`
3. Check browser console for errors

## Performance Checks

### Check Page Load Times:
1. Open DevTools → Network tab
2. Reload page
3. Look at "DOMContentLoaded" time
4. **Target:** <3 seconds

### Check API Response Times:
```bash
# Should all complete in <2 seconds
time curl "http://localhost:8000/api/analytics/top-repositories"
time curl "http://localhost:8000/api/people?offset=0&limit=50"
```

### Check Bundle Size:
1. DevTools → Network tab
2. Filter by JS files
3. Check total transferred size
4. **Target:** <800KB

## Success Criteria

Before marking implementation as complete, verify:

- [ ] API starts without errors
- [ ] All 5 analytics endpoints return data
- [ ] People page loads and filters work
- [ ] Person profile shows complete data
- [ ] Analytics charts render correctly
- [ ] Filters update charts/tables
- [ ] Error messages are actionable
- [ ] Keyboard navigation works
- [ ] Mobile/tablet layouts work
- [ ] No console errors on any page

## Next Steps

1. **If all tests pass:**
   - Mark implementation complete ✅
   - Deploy to production environment
   - Monitor performance with real users

2. **If issues found:**
   - Check console for specific errors
   - Review API responses
   - Verify database has required data
   - Check CORS configuration

3. **For production deployment:**
   - Update API_BASE_URL in JS files to production URL
   - Minify JavaScript files
   - Enable caching headers
   - Set up monitoring/logging

## Support

For issues or questions:
1. Check `dashboard/README.md` for detailed documentation
2. Review `FRONTEND_IMPLEMENTATION_COMPLETE.md` for implementation details
3. Check browser console for error messages
4. Test API endpoints directly with curl

---

**Quick Test Commands:**

```bash
# Full test sequence
python run_api.py &
sleep 3
curl http://localhost:8000/health
curl "http://localhost:8000/api/analytics/top-repositories?limit=5"
open dashboard/index.html
```

Happy testing! 🚀

