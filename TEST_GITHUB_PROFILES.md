# Test GitHub Profile Displays - Verification Guide

**After fixing GitHub profile display issues**

---

## Quick Test Instructions

1. **Restart Frontend** (if running):
```bash
cd frontend
# Stop current process (Ctrl+C)
npm run dev
```

2. **Test These Profiles**:

### Profile 1: 0age (25 contributions)
**URL**: http://localhost:3000/profile/679c5f97-d1f8-46a9-bc1b-e8959d4288c2

**Should See:**
- ✅ GitHub profile section with username "@0age"
- ✅ 25 repositories listed under "Repository Contributions"
- ✅ Working links (format: `https://github.com/owner/repo`)
- ✅ Sort buttons: Quality, Commits, Stars
- ✅ "Quality" selected by default (blue background)
- ✅ If PR data exists: green checkmarks for merged PRs
- ✅ If enriched: Career Highlights box with stats

### Profile 2: Adrian Kant (1 contribution)  
**URL**: http://localhost:3000/profile/0612729b-3cf6-304a-7fb3-cf15918809b8

**Should See:**
- ✅ GitHub profile section with username "@adjkant"
- ✅ 1 repository listed
- ✅ Working link to the repository
- ✅ All available stats displayed

---

## What Each Element Should Look Like

### 1. GitHub Profile Section (Top)
```
┌──────────────────────────────────────────────────────┐
│  [Avatar]                                            │
│                                                      │
│  John Doe                                            │
│  @johndoe  [PRO badge if applicable]                │
│  "Building the decentralized future"                 │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │   1.2k   │ │   245    │ │    52    │            │
│  │ Followers│ │ Following│ │  Repos   │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│                                                      │
│  Career Highlights (if enriched data exists)        │
│  ┌─────────────────────────────────────────┐        │
│  │    245         ⭐ 3.2k      127k        │        │
│  │ Merged PRs  Stars Earned  Lines of Code│        │
│  │                                         │        │
│  │ Updated Oct 20, 2025                   │        │
│  └─────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

### 2. Repository Contributions Section

**Header:**
```
Repository Contributions
25 repositories • 1.2k total commits • 15.3k ⭐ across repos

Sort by: [Quality] [Commits] [Stars]
         ^^^^^^^^ (default, blue)
```

**Each Contribution Row:**
```
#1  Uniswap/v3-core  ● Solidity
    A concentrated liquidity AMM for Ethereum

    🔨 127 commits  ✓ 15 merged PRs  ⭐ 3.2k  +12.3k lines  
    Quality: 87/100  Since Jan 15, 2024
```

**Key Visual Elements:**
- `#1, #2, #3` - Rank numbers (gold, silver, bronze for top 3)
- `Uniswap/v3-core` - Blue clickable link (full repo name)
- `● Solidity` - Language badge with colored dot
- `✓ 15 merged PRs` - GREEN text with checkmark (if data exists)
- `+12.3k lines` - EMERALD GREEN (if data exists)
- `Quality: 87/100` - PURPLE text (if data exists)
- `Since Jan 15, 2024` - Gray with clock icon

---

## Sorting Behavior

### Quality Sort (Default)
- Prioritizes: merged_pr_count × 100 + quality_score
- Shows: High-impact contributions first
- Example order:
  1. 15 merged PRs, quality 87 → Score: 1587
  2. 8 merged PRs, quality 92 → Score: 892
  3. 50 commits, 0 PRs → Score: 0

### Commits Sort
- Prioritizes: contribution_count
- Shows: Most active contributions first

### Stars Sort
- Prioritizes: repository stars
- Shows: Most popular repos first

---

## Data States to Test

### State 1: Full Enrichment (Best Case)
**Has:**
- ✅ merged_pr_count
- ✅ lines_added
- ✅ contribution_quality_score
- ✅ total_merged_prs (profile)
- ✅ total_stars_earned
- ✅ total_lines_contributed

**Should Display:**
- Green PR badges on each repo
- Purple quality scores
- Career Highlights box
- Lines of code stats

### State 2: Partial Data (Common)
**Has:**
- ✅ contribution_count
- ✅ stars
- ✅ language
- ❌ No PR enrichment

**Should Display:**
- Commit counts and stars
- Language badges
- NO PR badges (expected)
- NO Career Highlights box (expected)

### State 3: Minimal Data (Basic)
**Has:**
- ✅ contribution_count
- ✅ repo_full_name
- ❌ No stars, language, or enrichment

**Should Display:**
- Repo name (clickable)
- Commit count
- Nothing else (expected)

---

## Known Issues That Should Be Fixed

### ✅ FIXED: Broken Links
**Before**: `https://github.com/v3-core` (404 error)  
**After**: `https://github.com/Uniswap/v3-core` (works!)

### ✅ FIXED: Missing PR Data
**Before**: Only showed commits and stars  
**After**: Shows merged PRs, lines added, quality score

### ✅ FIXED: Wrong Sort Order
**Before**: Always sorted by commits  
**After**: Defaults to quality (merged PRs first)

### ✅ FIXED: No Career Stats
**Before**: Only showed followers/repos  
**After**: Shows career highlights if enriched

---

## Troubleshooting

### Issue: "No GitHub profile found"
**Check:**
1. Is `github_profile.person_id` set for this person?
2. Run in psql:
   ```sql
   SELECT gp.github_username, gp.person_id
   FROM github_profile gp
   WHERE gp.person_id = 'your-person-id';
   ```

### Issue: Links still broken
**Check:**
1. Does contribution have `repo_full_name`?
2. Run in psql:
   ```sql
   SELECT gr.repo_name, gr.full_name
   FROM github_contribution gc
   JOIN github_repository gr ON gc.repo_id = gr.repo_id
   WHERE gc.github_profile_id = 'github-profile-id'
   LIMIT 5;
   ```

### Issue: No PR data showing
**Expected** - Most profiles haven't been enriched yet. Run:
```bash
python3 scripts/github/batch_pr_enrichment_orchestrator.py
```

### Issue: TypeScript errors
**If you see compilation errors**, check:
- Did frontend restart pickup the changes?
- Are there any remaining `profile.github` (should be `profile.github_profile`)?

---

## Success Criteria

**All Checks Must Pass:**

✅ GitHub profile section displays  
✅ Username link works (opens GitHub profile)  
✅ Contribution list shows (25 for 0age)  
✅ All repo links work (open correct GitHub repos)  
✅ Sort buttons present (Quality, Commits, Stars)  
✅ Quality selected by default  
✅ PR data displays IF it exists  
✅ Career highlights IF profile enriched  
✅ No TypeScript errors  
✅ No broken images  
✅ No console errors  

---

## Next Steps After Verification

Once profiles display correctly:

1. ✅ GitHub display is production-ready
2. 🔄 Can run batch PR enrichment (Tier 1, Priority 4)
3. 🔄 Can build collaboration network API endpoints
4. 🔄 Can add network visualization UI

**Charlie, please test the profiles and confirm everything works! 🚀**

