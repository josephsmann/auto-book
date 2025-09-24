# Court Booking Automation

Automated court booking system for Edmonton Squash Club using Selenium WebDriver.

## 🎯 Features

- **Automated Login**: Uses credentials from environment variables
- **Smart Navigation**: Navigates to target date (default: 2 weeks ahead)
- **Time Slot Booking**: Specifically books 5:00 PM slots
- **Form Automation**: Handles complex Kendo UI dropdowns
- **Verification**: Confirms bookings by page refresh
- **GitHub Actions**: Can run on schedule or manually

## 📋 Booking Details

- **Court Type**: Singles
- **Start Time**: 5:00 PM
- **Duration**: 1 hour
- **Additional Player**: Scott Jackson
- **Date**: Configurable (default: 14 days ahead)

## 🚀 Local Usage

### Prerequisites

```bash
# Install Python dependencies
pip install selenium python-dotenv webdriver-manager
```

### Environment Setup

Create a `.env` file:

```bash
ESC_USERNAME=your_email@example.com
ESC_PASSWORD=your_password
```

### Run Locally

```bash
# Run the working booking script
python fixed_court_booking.py

# Or run the GitHub Actions compatible version
python github_actions_court_booking.py
```

## ⚙️ GitHub Actions Setup

### 1. Repository Secrets

Add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add repository secrets:
   - `ESC_USERNAME`: Your court booking username
   - `ESC_PASSWORD`: Your court booking password

### 2. Workflow Configuration

The workflow is already configured in `.github/workflows/court-booking.yml`

**Schedule**: Runs daily at 6 AM UTC (customize the cron expression)

**Manual Trigger**: Can be run manually with custom days ahead

### 3. Running on GitHub Actions

#### Manual Run:
1. Go to **Actions** tab in your repository
2. Select "Court Booking Automation"
3. Click "Run workflow"
4. Optionally specify days ahead (default: 14)

#### Scheduled Run:
- Automatically runs daily at 6 AM UTC
- Modify the cron expression in the workflow file to change timing

## 📁 File Structure

```
courts/
├── .github/workflows/
│   └── court-booking.yml           # GitHub Actions workflow
├── fixed_court_booking.py          # Local booking script (most reliable)
├── github_actions_court_booking.py # GitHub Actions optimized script
├── debug_booking_form.py           # Debug form elements
├── .env                            # Environment variables (local)
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## 🔧 Troubleshooting

### Common Issues

1. **"Singles not selected"**: The most common failure point
   - The script has multiple fallback methods to handle Kendo UI dropdowns
   - JavaScript method is most reliable

2. **"No 5:00 PM slot found"**:
   - All slots may be booked
   - Try different times or dates

3. **Login failures**:
   - Check username/password in secrets
   - Website may have changed login elements

### Debug Mode

The GitHub Actions version takes screenshots at each step for debugging:
- `login_page.png`
- `booking_form.png`
- `verification.png`
- etc.

These are uploaded as artifacts when the workflow fails.

## 📅 Scheduling Options

### GitHub Actions Cron Examples

```yaml
# Daily at 6 AM UTC
- cron: '0 6 * * *'

# Monday, Wednesday, Friday at 8 AM UTC
- cron: '0 8 * * 1,3,5'

# Every hour from 6 AM to 10 AM UTC
- cron: '0 6-10 * * *'
```

### Local Scheduling

Use your system's cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Linux/Mac cron example (daily at 6 AM)
0 6 * * * cd /path/to/courts && python fixed_court_booking.py
```

## 🔒 Security Notes

- Never commit `.env` files with real credentials
- Use GitHub repository secrets for Actions
- The script uses headless mode in GitHub Actions
- Screenshots may contain sensitive information

## 🎾 Success Indicators

When successful, you should see:
- ✅ Login successful
- ✅ Found 5:00 PM slot
- ✅ Singles selected
- ✅ Scott Jackson added
- ✅ BOOKING VERIFIED with all indicators found

The system will also send you an email confirmation from the court booking system.

## 📞 Support

If the automation fails:
1. Check the GitHub Actions logs/artifacts
2. Verify your credentials in repository secrets
3. Check if the website structure has changed
4. Fall back to manual booking if needed