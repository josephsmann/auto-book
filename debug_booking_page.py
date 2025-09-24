#!/usr/bin/env python3
"""
Debug script to explore the booking page structure
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

def debug_booking_page():
    username = os.getenv('ESC_USERNAME')
    password = os.getenv('ESC_PASSWORD')

    if not username or not password:
        print("❌ ESC_USERNAME and ESC_PASSWORD must be set in .env file")
        return

    print("Setting up browser...")
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Login first
        print("Logging in...")
        driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")

        username_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        username_field.send_keys(username)

        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(password)

        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        wait.until(EC.url_contains("Portal"))
        print("Login successful!")

        # Navigate to booking page
        print("Navigating to booking page...")
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        driver.get(booking_url)
        time.sleep(5)

        print(f"Booking page URL: {driver.current_url}")
        print(f"Booking page title: {driver.title}")

        # Calculate target date (two weeks from now)
        target_date = datetime.now() + timedelta(weeks=2)
        print(f"Target date: {target_date.strftime('%Y-%m-%d %A')}")

        # Look for date elements
        print("\n📅 Looking for date-related elements...")
        date_selectors = [
            "[data-date]",
            ".calendar-day",
            ".date-picker",
            ".date-cell",
            "[class*='date']",
            "[class*='calendar']",
            "[class*='day']"
        ]

        for selector in date_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        print(f"   {i+1}. Text: '{elem.text}', Data-date: '{elem.get_attribute('data-date')}'")
            except Exception as e:
                continue

        # Look for time-related elements
        print("\n🕐 Looking for time-related elements...")
        time_selectors = [
            "[data-time]",
            ".time-slot",
            ".booking-slot",
            "[class*='time']",
            "[class*='slot']",
            "button[class*='book']",
            "button[class*='available']"
        ]

        for selector in time_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:5]):  # Show first 5
                        text = elem.text.strip()
                        if text:
                            print(f"   {i+1}. Text: '{text}', Enabled: {elem.is_enabled()}")
            except Exception as e:
                continue

        # Look for any buttons containing 3:30 or 15:30
        print("\n🎯 Looking specifically for 3:30 PM slots...")
        time_patterns = ["3:30", "15:30", "1530"]
        for pattern in time_patterns:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
            if elements:
                print(f"✅ Found {len(elements)} elements containing '{pattern}':")
                for i, elem in enumerate(elements):
                    print(f"   {i+1}. Tag: {elem.tag_name}, Text: '{elem.text}', Clickable: {elem.is_enabled()}")

        # Look for navigation buttons (next week, etc.)
        print("\n🔄 Looking for navigation elements...")
        nav_selectors = [
            "button[class*='next']",
            "button[class*='prev']",
            "button[class*='forward']",
            "button[class*='back']",
            "[class*='arrow']",
            "[class*='navigate']"
        ]

        for selector in nav_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} navigation elements with selector: {selector}")
                    for i, elem in enumerate(elements[:3]):
                        print(f"   {i+1}. Text: '{elem.text}', Title: '{elem.get_attribute('title')}'")
            except Exception as e:
                continue

        # Check page source for any obvious booking-related patterns
        print("\n📄 Analyzing page structure...")
        page_source = driver.page_source.lower()

        booking_keywords = ["book", "reserve", "available", "schedule", "court", "time slot"]
        for keyword in booking_keywords:
            count = page_source.count(keyword)
            if count > 0:
                print(f"'{keyword}' appears {count} times in page")

        print("\n🔍 Page is ready for inspection. Check the browser window.")
        print("Look for:")
        print("1. Calendar or date picker")
        print("2. Time slots around 3:30 PM")
        print("3. Navigation buttons to move to future dates")
        print("4. Available court booking slots")

        # Keep browser open for manual inspection
        input("\nPress Enter to close browser after inspection...")

    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to close browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_booking_page()