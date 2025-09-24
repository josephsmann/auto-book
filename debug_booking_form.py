#!/usr/bin/env python3
"""
Debug script to inspect the actual booking form elements
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

def debug_booking_form():
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
    wait = WebDriverWait(driver, 15)

    try:
        # Login
        print("🔐 Logging in...")
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
        print("✅ Login successful!")

        # Navigate to booking page
        print("📅 Navigating to booking page...")
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        driver.get(booking_url)
        time.sleep(3)

        # Navigate forward 14 days
        print("⏭️ Navigating 14 days ahead...")
        for day in range(14):
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                if next_button.is_displayed() and next_button.is_enabled():
                    next_button.click()
                    time.sleep(1)
            except:
                break

        print("✅ Navigation completed")
        time.sleep(2)

        # Find and click 5:00 PM slot
        print("🎯 Looking for 5:00 PM slot...")
        reserve_buttons = driver.find_elements(By.XPATH,
            "//button[contains(text(), 'Reserve') and contains(text(), '5:00 PM')]")

        if reserve_buttons:
            print(f"✅ Found 5:00 PM slot: {reserve_buttons[0].text}")
            reserve_buttons[0].click()
            print("🔄 Clicked 5:00 PM slot")
            time.sleep(5)  # Wait for form to appear

            # Now debug the form that appears
            print("\n" + "="*50)
            print("🔍 DEBUGGING BOOKING FORM")
            print("="*50)

            # Check if we're in a modal/popup
            modals = driver.find_elements(By.CSS_SELECTOR, ".modal, [role='dialog'], .popup, .overlay")
            if modals:
                print(f"✅ Found {len(modals)} modal/popup elements")
                for i, modal in enumerate(modals):
                    if modal.is_displayed():
                        print(f"   Modal {i+1} is visible")

            # Look for all form elements
            print("\n📝 ALL FORM ELEMENTS:")

            # All inputs
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"\n🔤 Found {len(inputs)} input elements:")
            for i, inp in enumerate(inputs):
                if inp.is_displayed():
                    print(f"   {i+1}. Type: {inp.get_attribute('type')}, "
                          f"Name: {inp.get_attribute('name')}, "
                          f"ID: {inp.get_attribute('id')}, "
                          f"Placeholder: {inp.get_attribute('placeholder')}, "
                          f"Value: {inp.get_attribute('value')}")

            # All selects
            selects = driver.find_elements(By.TAG_NAME, "select")
            print(f"\n📋 Found {len(selects)} select elements:")
            for i, sel in enumerate(selects):
                if sel.is_displayed():
                    print(f"   {i+1}. Name: {sel.get_attribute('name')}, "
                          f"ID: {sel.get_attribute('id')}")

                    # Show options
                    options = sel.find_elements(By.TAG_NAME, "option")
                    print(f"      Options ({len(options)}):")
                    for j, opt in enumerate(options[:10]):  # Show first 10 options
                        print(f"        - {opt.text} (value: {opt.get_attribute('value')})")

            # All textareas
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            print(f"\n📄 Found {len(textareas)} textarea elements:")
            for i, ta in enumerate(textareas):
                if ta.is_displayed():
                    print(f"   {i+1}. Name: {ta.get_attribute('name')}, "
                          f"ID: {ta.get_attribute('id')}, "
                          f"Placeholder: {ta.get_attribute('placeholder')}")

            # All buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n🔘 Found {len(buttons)} button elements:")
            for i, btn in enumerate(buttons):
                if btn.is_displayed():
                    print(f"   {i+1}. Text: '{btn.text}', "
                          f"Type: {btn.get_attribute('type')}, "
                          f"Class: {btn.get_attribute('class')}")

            # Look for labels to understand form structure
            labels = driver.find_elements(By.TAG_NAME, "label")
            print(f"\n🏷️ Found {len(labels)} label elements:")
            for i, label in enumerate(labels):
                if label.is_displayed() and label.text.strip():
                    print(f"   {i+1}. Text: '{label.text}', "
                          f"For: {label.get_attribute('for')}")

            # Check page source for form-related keywords
            print(f"\n📄 Form-related content analysis:")
            page_source = driver.page_source.lower()
            keywords = ["singles", "doubles", "scott jackson", "additional player", "start time", "duration"]
            for keyword in keywords:
                count = page_source.count(keyword)
                print(f"   '{keyword}': {count} occurrences")

            print(f"\n🔍 Current URL: {driver.current_url}")
            print(f"📋 Page title: {driver.title}")

            print("\n" + "="*50)
            print("🚀 MANUAL INSPECTION TIME")
            print("="*50)
            print("The browser is now open with the booking form visible.")
            print("Please manually inspect the form and note:")
            print("1. How to select 'Singles' court type")
            print("2. How to set start time to 5:00 PM")
            print("3. Where to enter 'Scott Jackson' as additional player")
            print("4. How to submit the form")
            print("\nBrowser will stay open for manual inspection...")

            input("\nPress Enter after inspecting the form...")

        else:
            print("❌ No 5:00 PM slot found")

    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to close browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_booking_form()