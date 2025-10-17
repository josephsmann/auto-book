# Fly.io Deployment Guide for Court Booking Automation

This guide will help you deploy the court booking script to Fly.io as a scheduled machine.

## Prerequisites

1. **Install Fly.io CLI**
   ```bash
   # macOS
   brew install flyctl

   # Or download from: https://fly.io/docs/hands-on/install-flyctl/
   ```

2. **Sign up/Login to Fly.io**
   ```bash
   flyctl auth signup  # If you're new
   # OR
   flyctl auth login   # If you already have an account
   ```

## Initial Setup

### 1. Launch the App

From the project directory, run:

```bash
flyctl launch
```

This will:
- Detect the Dockerfile
- Ask you to choose an app name (or use `auto-book-courts`)
- Ask you to select a region (choose `den` for Denver/Mountain Time)
- Create a `fly.toml` configuration file (already provided)

**Important:** When asked:
- "Would you like to set up a Postgresql database?" → **No**
- "Would you like to deploy now?" → **No** (we need to set secrets first)

### 2. Set Secrets

Set your environment variables as secrets:

```bash
flyctl secrets set ESC_USERNAME="your_username"
flyctl secrets set ESC_PASSWORD="your_password"
flyctl secrets set ESC_ADDITIONAL_PLAYER="Scott Jackson"
```

### 3. Deploy the App

```bash
flyctl deploy
```

This builds the Docker image and deploys it to Fly.io.

## Scheduling the Booking

Fly.io Machines don't have built-in cron scheduling, so we'll use GitHub Actions to trigger the Fly.io machine on schedule.

### Option A: GitHub Actions Scheduler (Recommended)

Update `.github/workflows/court-booking.yml` to call the Fly.io machine instead of running locally:

```yaml
name: Trigger Court Booking on Fly.io

on:
  schedule:
    # During MDT (March-November): Monday/Thursday at 11 PM UTC = 5 PM MDT
    - cron: '0 23 * 3-10 1,4'  # March through October
    - cron: '0 23 1-7 11 1,4'  # November 1-7 (before DST ends)
    # During MST (November-March): Tuesday/Friday at 12 AM UTC = 5 PM MST (previous day)
    - cron: '0 0 8-30 11 2,5'  # November 8-30 (after DST ends)
    - cron: '0 0 * 12 2,5'     # December
    - cron: '0 0 * 1-2 2,5'    # January through February
    - cron: '0 0 1-9 3 2,5'    # March 1-9 (before DST starts)

  workflow_dispatch:

jobs:
  trigger-booking:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Fly.io Machine
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
        run: |
          curl -X POST \
            -H "Authorization: Bearer $FLY_API_TOKEN" \
            -H "Content-Type: application/json" \
            "https://api.machines.dev/v1/apps/auto-book-courts/machines" \
            -d '{
              "config": {
                "image": "registry.fly.io/auto-book-courts:latest",
                "auto_destroy": true
              }
            }'
```

### Option B: External Cron Service

Use a service like:
- **Cron-job.org** - Free cron service
- **EasyCron** - Scheduled HTTP requests
- **Render Cron Jobs** - Another deployment platform with cron

### Option C: Fly.io + Supercronic (Self-contained)

Modify the Dockerfile to run a cron service inside the container.

## Manual Testing

To manually run the booking:

```bash
flyctl machine run . --command "python smart_court_booking.py 14 '5:00 PM' 45"
```

Or deploy and check logs:

```bash
flyctl deploy
flyctl logs
```

## Monitoring

### View Logs
```bash
flyctl logs
```

### Check Machine Status
```bash
flyctl machine list
```

### SSH into Machine (for debugging)
```bash
flyctl ssh console
```

## Cost Estimation

Fly.io pricing (as of 2024):
- **Machines**: ~$0.0000008/second when running (~$0.003/hour)
- **For this use case**: Script runs ~1 minute twice per week = ~$0.20/month
- **Free tier**: Includes $5/month credit, so this should be **FREE**

## Troubleshooting

### If Cloudflare Still Blocks

1. **Add delays**: Modify the script to add random delays
2. **Use Fly.io's shared IPv6**: Less likely to be blocked
3. **Try different regions**: Some regions have cleaner IPs

### If Machine Won't Start

Check logs:
```bash
flyctl logs
```

Common issues:
- Chrome installation failed → Check Dockerfile
- Secrets not set → Run `flyctl secrets list`
- Out of memory → Increase machine size in fly.toml

## Cleanup

If you want to delete everything:

```bash
flyctl apps destroy auto-book-courts
```

## Next Steps

1. Complete initial setup (steps 1-3 above)
2. Set up scheduling (Option A recommended)
3. Test with manual run
4. Monitor logs for first scheduled run
