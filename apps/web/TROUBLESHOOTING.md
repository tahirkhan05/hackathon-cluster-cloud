# Frontend Troubleshooting Guide

## Issue: Styles Not Loading (Fixed!)

### What Was Wrong
The Tailwind configuration had incorrect glob patterns that prevented it from detecting your component files.

### What Was Fixed
✅ **tailwind.config.js** - Added `**/` to content paths for recursive scanning
✅ **.next cache** - Cleared build cache

---

## How to Restart After Fix

### 1. Stop Current Server
Find the terminal running `npm run dev` and press `Ctrl + C`

### 2. Start Fresh
```bash
cd apps/web
npm run dev
```

### 3. Clear Browser Cache
Choose one method:
- **Hard Refresh**: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- **DevTools**: F12 → Right-click refresh → "Empty Cache and Hard Reload"
- **Manual**: Browser settings → Clear browsing data → Cached images and files

### 4. Verify
Navigate to http://localhost:3000 and you should see:
- ✅ Gradient background (purple to blue)
- ✅ Styled navigation header
- ✅ Colored buttons
- ✅ Proper typography and spacing

---

## Still Having Issues?

### Check 1: Is the Dev Server Running?
```bash
# Should show "ready - started server on 0.0.0.0:3000"
# Check your terminal
```

### Check 2: Check Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for errors (should be none)

### Check 3: Verify CSS is Loading
1. Open DevTools (F12)
2. Go to Network tab
3. Refresh page
4. Look for `globals.css` - should return 200 OK

### Check 4: Verify Tailwind is Working
1. Open DevTools (F12)
2. Go to Elements/Inspector tab
3. Click on any element
4. Check Styles panel - should see Tailwind classes

### Check 5: Port Conflict
If port 3000 is already in use:
```bash
# Windows: Find and kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F

# Or use a different port
npm run dev -- -p 3001
```

---

## Full Clean Restart (Nuclear Option)

If nothing else works:

```bash
# Stop the server (Ctrl+C)

# Remove all generated files
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules

# Reinstall dependencies
npm install

# Start fresh
npm run dev
```

---

## What Should You See?

### Landing Page (/)
- Gradient background (blue/purple)
- ClusterCloud logo with lightning bolt
- "Go to Dashboard" button
- Large heading: "Build Your Cloud. Not Your Infrastructure."
- Two action buttons: "Get Started" and "View Demo"
- Stats grid: "10x", "100%", "24/7"
- Feature cards with icons

### Dashboard (/dashboard)
- Navigation sidebar
- System stats cards
- Recent activity feed
- WebSocket connection indicator

### Jobs Page (/jobs)
- List of jobs with status badges
- Progress bars
- Action buttons
- Real-time updates

---

## Technical Details

### Tailwind Content Paths
```javascript
// ✅ Correct (recursive scanning)
content: [
  './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
  './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  './src/app/**/*.{js,ts,jsx,tsx,mdx}',
]

// ❌ Wrong (only scans top level)
content: [
  './src/pages*.{js,ts,jsx,tsx,mdx}',
  './src/components*.{js,ts,jsx,tsx,mdx}',
  './src/app*.{js,ts,jsx,tsx,mdx}',
]
```

### CSS Loading Order
1. `globals.css` imported in `layout.tsx`
2. Tailwind directives processed by PostCSS
3. Utility classes generated based on content paths
4. CSS injected into page

### Common Causes of CSS Not Loading
- ❌ Incorrect Tailwind content paths (FIXED)
- ❌ Cached .next directory (CLEARED)
- ❌ Browser cache holding old CSS
- ❌ PostCSS not configured
- ❌ globals.css not imported

---

## Contact Points

If styles still aren't loading after following this guide:
1. Check the terminal output for errors
2. Check browser console for errors
3. Verify `tailwind.config.js` has `**/` in content paths
4. Ensure `globals.css` exists and imports Tailwind
5. Try a different browser

The fix has been applied, so a simple restart should resolve everything! 🎨
