# Quick Start: Deploy Court Booking to Fly.io

This is a streamlined guide to get your court booking automation running on Fly.io in under 10 minutes.

## Step 1: Install Fly.io CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Or using Homebrew
brew install flyctl
```

## Step 2: Sign Up / Login

```bash
flyctl auth signup
# OR if you have an account:
flyctl auth login
```

## Step 3: Deploy from Project Directory

```bash
cd /path/to/auto-book

# Launch the app (follow the prompts)
flyctl launch --name auto-book-courts --region den

# When prompted:
# - Choose region: den (Denver - closest to Mountain Time)
# - Setup Postgres? NO
# - Deploy now? NO (we need secrets first)
```

## Step 4: Set Your Secrets

```bash
flyctl secrets set \
  ESC_USERNAME="your_username" \
  ESC_PASSWORD="your_password" \
  ESC_ADDITIONAL_PLAYER="Scott Jackson"
```

## Step 5: Deploy

```bash
flyctl deploy
```

This will:
- Build the Docker image with Chrome
- Upload to Fly.io
- Create a machine ready to run

## Step 6: Test Manually

```bash
# Trigger a test booking
flyctl machine run . --command "python smart_court_booking.py 14 '5:00 PM' 45"

# Watch the logs
flyctl logs
```

## Step 7: Set Up GitHub Actions Scheduler

1. Get your Fly.io API token:
   ```bash
   flyctl auth token
   ```

2. Add it to GitHub Secrets:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `FLY_API_TOKEN`
   - Value: (paste the token from step 1)

3. The workflow `.github/workflows/trigger-flyio-booking.yml` is already configured!
   - It will trigger the Fly.io machine every Monday/Thursday at 5:00 PM MT
   - Handles MDT/MST timezone changes automatically

## Step 8: Verify

Wait for the next scheduled run, or manually trigger:
- Go to GitHub Actions tab
- Select "Trigger Fly.io Court Booking"
- Click "Run workflow"

Check results:
```bash
flyctl logs
```

## Done! 🎉

Your court booking automation will now run automatically:
- **Monday & Thursday at 5:00 PM Mountain Time**
- **Books courts 2 weeks (14 days) in advance**
- **Intelligently picks best available singles court**
- **Auto-selects Singles or Solo Practice based on time**

## Cost

- Should be **FREE** on Fly.io's free tier ($5/month credit)
- Machines only run for ~1 minute, twice per week
- Estimated cost: ~$0.20/month (covered by free tier)

## Troubleshooting

**Logs not showing?**
```bash
flyctl logs --app auto-book-courts
```

**Want to check machine status?**
```bash
flyctl machine list
```

**Need to update secrets?**
```bash
flyctl secrets set ESC_PASSWORD="new_password"
```

**Want to destroy and start over?**
```bash
flyctl apps destroy auto-book-courts
```
