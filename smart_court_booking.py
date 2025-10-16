#!/usr/bin/env python3
"""
Smart court booking script that:
1. Logs in
2. Navigates to the target date
3. Extracts the schedule
4. Finds the best available singles court at the target time
5. Books it
"""

import os
import time
import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

load_dotenv()


def parse_time(time_str):
    """Parse a time string like '6:00 AM', '4:00 PM' to datetime object"""
    time_str = time_str.strip()
    time_str = time_str.replace('.', '').strip()
    time_str = re.sub(r'\s+', ' ', time_str)

    formats = ['%I:%M %p', '%I:%M%p']
    for fmt in formats:
        try:
            return datetime.strptime(time_str.upper(), fmt)
        except ValueError:
            continue
    return None


def parse_time_range(time_range_str):
    """Parse a time range like '4:00 p.m. - 5:00 p.m.' to (start_time, end_time)"""
    if ' - ' in time_range_str:
        parts = time_range_str.split(' - ')
        if len(parts) == 2:
            start = parse_time(parts[0])
            end = parse_time(parts[1])
            return (start, end)
    return (None, None)


def extract_schedule(driver):
    """Extract court schedule from current page"""
    print("\n🔍 Extracting court schedule...")

    # Get court names from header
    court_names = []
    try:
        header_rows = driver.find_elements(By.XPATH, "//tr[.//th]")
        for header_row in header_rows:
            ths = header_row.find_elements(By.TAG_NAME, "th")
            if len(ths) > 1:
                for i, th in enumerate(ths):
                    if i == 0:
                        continue
                    court_name = th.text.strip()
                    if court_name and "Court" in court_name:
                        court_names.append({
                            'column_index': i,
                            'name': court_name,
                            'is_singles': 'Singles' in court_name and 'Doubles' not in court_name
                        })
                break
    except:
        pass

    print(f"Found {len(court_names)} courts")

    # Find all bookings and buttons
    all_booking_divs = driver.find_elements(By.CLASS_NAME, "fn-portal-reservation-container")
    all_reserve_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Reserve')]")
    visible_reserve_buttons = [b for b in all_reserve_buttons if b.is_displayed()]

    print(f"Found {len(all_booking_divs)} bookings and {len(visible_reserve_buttons)} available slots")

    # Get header positions for position-based matching
    header_positions = {}
    try:
        header_rows = driver.find_elements(By.XPATH, "//tr[.//th]")
        for header_row in header_rows:
            ths = header_row.find_elements(By.TAG_NAME, "th")
            if len(ths) > 1:
                for court_info in court_names:
                    if court_info['column_index'] < len(ths):
                        th = ths[court_info['column_index']]
                        loc = th.location
                        size = th.size
                        header_positions[court_info['name']] = {
                            'x_start': loc['x'],
                            'x_end': loc['x'] + size['width'],
                        }
                break
    except:
        pass

    # Build schedule
    schedule = []
    for court_info in court_names:
        court_data = {
            'name': court_info['name'],
            'column_index': court_info['column_index'],
            'is_singles': court_info['is_singles'],
            'slots': []
        }

        court_pos = header_positions.get(court_info['name'])
        if not court_pos:
            continue

        # Find bookings for this court
        for booking_div in all_booking_divs:
            try:
                loc = booking_div.location
                x_center = loc['x'] + booking_div.size['width'] / 2
                if court_pos['x_start'] <= x_center <= court_pos['x_end']:
                    booking_text = booking_div.text.strip()
                    if booking_text:
                        lines = booking_text.split('\n')
                        court_data['slots'].append({
                            'status': 'booked',
                            'type': lines[0] if len(lines) > 0 else "",
                            'time': lines[1] if len(lines) > 1 else "",
                        })
            except:
                continue

        # Find available slots for this court
        for button in visible_reserve_buttons:
            try:
                loc = button.location
                x_center = loc['x'] + button.size['width'] / 2
                if court_pos['x_start'] <= x_center <= court_pos['x_end']:
                    button_text = button.text.strip()
                    time_str = button_text.replace('Reserve', '').strip()
                    court_data['slots'].append({
                        'status': 'available',
                        'time': time_str,
                        'button': button  # Keep reference to button for clicking
                    })
            except:
                continue

        schedule.append(court_data)

    return schedule


def find_best_court(schedule, target_time_str):
    """
    Find the best singles court available at target time
    Returns: (court_data, duration_minutes, button_element)
    """
    target_time = parse_time(target_time_str)
    if not target_time:
        return None, 0, None

    print(f"\n🔍 Finding best singles court for {target_time_str}...")

    best_court = None
    best_duration = 0
    best_button = None

    # Only consider singles courts
    singles_courts = [c for c in schedule if c['is_singles']]
    print(f"Checking {len(singles_courts)} singles courts")

    for court in singles_courts:
        # Build timeline for this court
        timeline = []

        for slot in court['slots']:
            if slot['status'] == 'available':
                slot_time = parse_time(slot['time'])
                if slot_time:
                    start_time = slot_time
                    end_time = slot_time + timedelta(minutes=30)
                    timeline.append((start_time, end_time, True, slot.get('button')))
            elif slot['status'] == 'booked':
                start_time, end_time = parse_time_range(slot['time'])
                if start_time and end_time:
                    timeline.append((start_time, end_time, False, None))

        timeline.sort(key=lambda x: x[0])

        # Check if target time is available
        for start_time, end_time, available, button in timeline:
            if start_time <= target_time < end_time and available:
                # Calculate total duration
                duration = int((end_time - target_time).total_seconds() / 60)
                current_end = end_time

                # Look ahead for consecutive slots
                for next_start, next_end, next_available, _ in timeline:
                    if next_available and next_start == current_end:
                        duration += 30
                        current_end = next_end
                    elif next_start >= current_end:
                        break

                print(f"  {court['name'].split(chr(10))[0]}: {duration} minutes available")

                if duration > best_duration:
                    best_duration = duration
                    best_court = court
                    best_button = button

                break

    return best_court, best_duration, best_button


def book_court(driver, wait, button, duration_minutes, target_date_str, target_time_str):
    """
    Click the reserve button and fill out the booking form

    Args:
        driver: Selenium webdriver
        wait: WebDriverWait instance
        button: The Reserve button element to click
        duration_minutes: How many minutes to book
        target_date_str: Date string (e.g., 'tomorrow', 'today')
        target_time_str: Time string (e.g., '4:00 PM')
    """
    print(f"\n📝 Booking court for {duration_minutes} minutes...")

    # Determine reservation type based on day and time
    # Singles: Weekdays 4:30PM-9:00PM OR Weekends 10:30AM-3:00PM
    # Solo Practice: All other times

    # Calculate the actual booking date
    from datetime import datetime, timedelta
    if target_date_str.lower() == 'tomorrow':
        booking_date = datetime.now() + timedelta(days=1)
    elif target_date_str.lower() == 'today':
        booking_date = datetime.now()
    else:
        # Try to parse as date string
        try:
            booking_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        except:
            booking_date = datetime.now()  # Fallback to today

    # Get day of week (0=Monday, 6=Sunday)
    day_of_week = booking_date.weekday()
    is_weekend = day_of_week >= 5  # Saturday or Sunday

    # Parse booking time
    booking_time = parse_time(target_time_str)
    if not booking_time:
        print("⚠️  Could not parse booking time, defaulting to Solo Practice")
        reservation_type = "solo practice"
        needs_additional_player = False
    else:
        # Check time ranges
        booking_hour = booking_time.hour
        booking_minute = booking_time.minute
        time_in_minutes = booking_hour * 60 + booking_minute

        if is_weekend:
            # Weekend: Singles if 10:30 AM - 3:00 PM
            start_time = 10 * 60 + 30  # 10:30 AM in minutes
            end_time = 15 * 60  # 3:00 PM in minutes
            if start_time <= time_in_minutes < end_time:
                reservation_type = "singles"
                needs_additional_player = True
            else:
                reservation_type = "solo practice"
                needs_additional_player = False
        else:
            # Weekday: Singles if 4:30 PM - 9:00 PM
            start_time = 16 * 60 + 30  # 4:30 PM in minutes
            end_time = 21 * 60  # 9:00 PM in minutes
            if start_time <= time_in_minutes < end_time:
                reservation_type = "singles"
                needs_additional_player = True
            else:
                reservation_type = "solo practice"
                needs_additional_player = False

    day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
    print(f"   Booking for {day_name} at {target_time_str}")
    print(f"   Reservation type: {reservation_type.title()}")
    if needs_additional_player:
        print(f"   Additional player: Required")

    try:
        # Click the Reserve button
        print("Clicking Reserve button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(1)
        button.click()
        time.sleep(3)

        # Wait for the booking form modal
        print("Waiting for booking form...")
        # Look for the Duration dropdown as indicator the form loaded
        wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Duration')]")))
        time.sleep(2)

        # Fill out the form using JavaScript for Kendo UI dropdowns
        print("Filling out form...")
        driver.save_screenshot("booking_form.png")

        # Select reservation type from dropdown using JavaScript
        print(f"Selecting '{reservation_type.title()}' from Reservation Type...")
        js_script_reservation = f"""
        var success = false;
        var dropdowns = document.querySelectorAll('.k-dropdown');

        for (var i = 0; i < dropdowns.length; i++) {{
            var dropdown = dropdowns[i];
            var textElement = dropdown.querySelector('.k-input-inner, .k-input');

            if (textElement && textElement.textContent.includes('Reservation Type')) {{
                dropdown.click();
                setTimeout(function() {{
                    var options = document.querySelectorAll('.k-animation-container .k-list li');
                    for (var j = 0; j < options.length; j++) {{
                        if (options[j].textContent.toLowerCase().includes('{reservation_type}')) {{
                            options[j].click();
                            success = true;
                            break;
                        }}
                    }}
                }}, 1000);
                break;
            }}
        }}
        return success;
        """
        driver.execute_script(js_script_reservation)
        time.sleep(3)

        # Verify reservation type selection
        kendo_dropdowns = driver.find_elements(By.CSS_SELECTOR, ".k-dropdown")
        reservation_selected = False
        for dropdown in kendo_dropdowns:
            if dropdown.is_displayed():
                try:
                    text_element = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                    if reservation_type in text_element.text.lower():
                        print(f"✅ Successfully selected {reservation_type.title()}!")
                        reservation_selected = True
                        break
                except:
                    continue

        if not reservation_selected:
            print(f"❌ CRITICAL: Could not select {reservation_type.title()}")
            driver.save_screenshot("reservation_type_failed.png")
            return False

        # Select duration using JavaScript
        print(f"Setting duration...")
        if duration_minutes >= 60:
            target_duration = "hour"
        elif duration_minutes >= 45:
            target_duration = "45"
        else:
            target_duration = "30"

        js_script_duration = f"""
        var success = false;
        var dropdowns = document.querySelectorAll('.k-dropdown');

        for (var i = 0; i < dropdowns.length; i++) {{
            var dropdown = dropdowns[i];
            var textElement = dropdown.querySelector('.k-input-inner, .k-input');

            if (textElement && (textElement.textContent.includes('minute') || textElement.textContent.includes('hour'))) {{
                dropdown.click();
                setTimeout(function() {{
                    var options = document.querySelectorAll('.k-animation-container .k-list li');
                    for (var j = 0; j < options.length; j++) {{
                        if (options[j].textContent.toLowerCase().includes('{target_duration}')) {{
                            options[j].click();
                            success = true;
                            break;
                        }}
                    }}
                }}, 1000);
                break;
            }}
        }}
        return success;
        """
        driver.execute_script(js_script_duration)
        time.sleep(3)
        print(f"✅ Set duration to {target_duration}")

        # Add additional player (only required for Singles)
        if needs_additional_player:
            print("Adding additional player...")
            try:
                # Look for the additional player search box
                player_input = driver.find_element(By.NAME, "OwnersDropdown_input")
                player_input.clear()

                # Get additional player from environment or use default
                additional_player = os.getenv('ESC_ADDITIONAL_PLAYER', 'Scott Jackson')
                player_input.send_keys(additional_player)
                print(f"   Searching for: {additional_player}")
                time.sleep(3)

                # Try to select from autocomplete
                try:
                    autocomplete_items = driver.find_elements(By.CSS_SELECTOR, ".k-list-item, [role='option']")
                    first_name = additional_player.split()[0].lower()
                    for item in autocomplete_items:
                        if item.is_displayed() and first_name in item.text.lower():
                            item.click()
                            print(f"   ✅ Selected {item.text} from autocomplete")
                            break
                except:
                    print(f"   ⚠️ Autocomplete not found, continuing with typed name")
                    pass

                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Could not add additional player: {e}")
        else:
            print("No additional player needed (Solo Practice)")

        driver.save_screenshot("form_filled.png")

        # Submit the form
        print("Submitting booking form...")
        save_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-submit")

        if save_button.is_displayed() and save_button.is_enabled():
            save_button.click()
            time.sleep(5)

            # Check if modal closed
            modals = driver.find_elements(By.CSS_SELECTOR, ".modal, [role='dialog']")
            open_modals = [m for m in modals if m.is_displayed()]

            driver.save_screenshot("after_submit.png")

            if not open_modals:
                print("✅ Booking successful - modal closed!")
                return True
            else:
                print("⚠️ Modal still open - checking for errors...")
                for modal in open_modals:
                    modal_text = modal.text.lower()
                    if 'error' in modal_text or 'required' in modal_text:
                        print(f"❌ Error: {modal.text[:200]}")
                        return False
                print("⚠️ No error found, might be processing")
                return True
        else:
            print("❌ Save button not available")
            return False

    except Exception as e:
        print(f"❌ Error during booking: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("booking_error.png")
        return False


def smart_book_court(target_date_str, target_time_str, duration_minutes=45):
    """
    Main function to book a court

    Args:
        target_date_str: Date to book (e.g., 'tomorrow', 'today', or 'YYYY-MM-DD')
        target_time_str: Time to book (e.g., '4:00 PM')
        duration_minutes: Preferred duration (default 45)
    """
    username = os.getenv('ESC_USERNAME')
    password = os.getenv('ESC_PASSWORD')

    if not username or not password:
        print("ERROR: ESC_USERNAME and ESC_PASSWORD must be set")
        return False

    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")

    # Enable headless mode in GitHub Actions or if HEADLESS env var is set
    if os.getenv('GITHUB_ACTIONS') == 'true' or os.getenv('HEADLESS', '').lower() == 'true':
        print("Running in headless mode")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

    wait = WebDriverWait(driver, 20)

    try:
        # Login
        print("🔐 Logging in...")
        driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")
        time.sleep(2)

        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        username_field.send_keys(username)

        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(password)

        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        wait.until(EC.url_contains("Portal"))
        print("✅ Logged in\n")

        # Navigate to bookings
        print("📅 Navigating to bookings page...")
        driver.get("https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491")
        time.sleep(5)

        # Navigate to target date
        if target_date_str.lower() == 'tomorrow':
            print("📆 Navigating to tomorrow...")
            next_button = driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
            if next_button.is_displayed() and next_button.is_enabled():
                next_button.click()
                time.sleep(3)
                print("✅ Navigated to tomorrow")
        elif target_date_str.lower() == 'today':
            print("📆 Staying on today")
        elif target_date_str.isdigit():
            # Days ahead (e.g., '14' for two weeks)
            days_ahead = int(target_date_str)
            print(f"📆 Navigating {days_ahead} days ahead...")
            next_button = driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
            for i in range(days_ahead):
                if next_button.is_displayed() and next_button.is_enabled():
                    next_button.click()
                    time.sleep(0.5)
            time.sleep(2)
            print(f"✅ Navigated {days_ahead} days ahead")
        else:
            print(f"📆 Navigating to {target_date_str}...")
            # TODO: Add date picker navigation for specific dates
            print("⚠️  Specific date navigation not yet implemented, staying on current page")

        # Extract schedule
        schedule = extract_schedule(driver)

        # Find best court
        best_court, best_duration, best_button = find_best_court(schedule, target_time_str)

        if not best_court:
            print(f"\n❌ No singles courts available at {target_time_str}")
            driver.save_screenshot("no_availability.png")
            return False

        court_name = best_court['name'].split('\n')[0]
        print(f"\n✅ Best option: {court_name}")
        print(f"   Available for {best_duration} minutes")

        # Book the court
        success = book_court(driver, wait, best_button, min(duration_minutes, best_duration), target_date_str, target_time_str)

        if success:
            print(f"\n🎉 Successfully booked {court_name} at {target_time_str}!")
            return True
        else:
            print(f"\n❌ Failed to complete booking")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
        return False

    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == '__main__':
    import sys

    print("Smart Court Booking Script")
    print("=" * 80)

    # Example usage
    if len(sys.argv) >= 3:
        target_date = sys.argv[1]  # 'tomorrow', 'today', or date
        target_time = sys.argv[2]  # '4:00 PM'
        duration = int(sys.argv[3]) if len(sys.argv) >= 4 else 45
    else:
        # Default: book tomorrow at 4:00 PM
        target_date = 'tomorrow'
        target_time = '4:00 PM'
        duration = 45
        print(f"Usage: python {sys.argv[0]} <date> <time> [duration]")
        print(f"Example: python {sys.argv[0]} tomorrow '4:00 PM' 45")
        print(f"\nUsing defaults: {target_date} at {target_time} for {duration} minutes\n")

    success = smart_book_court(target_date, target_time, duration)
    sys.exit(0 if success else 1)
