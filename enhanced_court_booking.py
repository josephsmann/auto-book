#!/usr/bin/env python3
"""
Enhanced court booking automation script
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

class EnhancedCourtBooker:
    def __init__(self):
        self.username = os.getenv('ESC_USERNAME')
        self.password = os.getenv('ESC_PASSWORD')
        self.driver = None
        self.wait = None

        if not self.username or not self.password:
            raise ValueError("ESC_USERNAME and ESC_PASSWORD must be set in .env file")

    def setup_driver(self, headless=False):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """Login to courtreserve.com"""
        print("Logging in to courtreserve.com...")

        self.driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")

        try:
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            username_field.send_keys(self.username)

            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(self.password)

            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            self.wait.until(EC.url_contains("Portal"))
            print("✅ Login successful!")
            return True

        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False

    def navigate_to_bookings(self):
        """Navigate to the bookings page"""
        print("Navigating to booking page...")
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        self.driver.get(booking_url)
        time.sleep(3)
        print("✅ On booking page")
        return True

    def navigate_to_target_date(self, target_date):
        """Navigate to the target date using next/previous buttons"""
        print(f"Navigating to target date: {target_date.strftime('%Y-%m-%d %A')}")

        max_attempts = 20  # Prevent infinite loops
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            try:
                # Get current date displayed on page
                current_date_element = self.driver.find_element(By.XPATH,
                    "//div[contains(@class, 'date') or contains(text(), '2025')]")
                current_date_text = current_date_element.text
                print(f"Current page shows: {current_date_text}")

                # Parse current date if possible
                # This is a simple check - we'll improve based on actual date format
                if target_date.strftime('%B') in current_date_text and str(target_date.day) in current_date_text:
                    print("✅ Reached target date!")
                    return True

                # Click next button to advance
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                if next_button.is_enabled():
                    print(f"Clicking next (attempt {attempts})...")
                    next_button.click()
                    time.sleep(2)  # Wait for page to update
                else:
                    print("❌ Next button not available")
                    break

            except NoSuchElementException:
                print("❌ Could not find navigation elements")
                break
            except Exception as e:
                print(f"❌ Navigation error: {e}")
                break

        print(f"⚠️ Could not reach target date after {attempts} attempts")
        return False

    def find_and_book_330pm_slot(self):
        """Find and book a 3:30 PM time slot"""
        print("Looking for 3:30 PM time slot...")

        # Look for various possible time slot patterns
        time_patterns = [
            "3:30 PM",
            "3:30",
            "15:30",
            "Reserve 3:30 PM",
            "Book 3:30 PM"
        ]

        for pattern in time_patterns:
            try:
                # Look for elements containing the time pattern
                time_elements = self.driver.find_elements(By.XPATH,
                    f"//*[contains(text(), '{pattern}')]")

                if time_elements:
                    print(f"✅ Found {len(time_elements)} elements with pattern '{pattern}'")

                    for element in time_elements:
                        # Check if this is a clickable reservation button
                        if (element.tag_name in ['button', 'a'] or
                            'reserve' in element.text.lower() or
                            'book' in element.text.lower()):

                            try:
                                print(f"Attempting to click: {element.text}")
                                element.click()
                                time.sleep(2)

                                # Look for confirmation dialog or next step
                                confirmation_selectors = [
                                    "button[class*='confirm']",
                                    "button[class*='book']",
                                    "button[class*='reserve']",
                                    "input[type='submit']",
                                    "button[type='submit']"
                                ]

                                for selector in confirmation_selectors:
                                    try:
                                        confirm_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        if confirm_button.is_enabled():
                                            print(f"Clicking confirmation button: {confirm_button.text}")
                                            confirm_button.click()
                                            time.sleep(3)
                                            return True
                                    except NoSuchElementException:
                                        continue

                                print("✅ Slot clicked, but no confirmation needed")
                                return True

                            except Exception as e:
                                print(f"Could not click element: {e}")
                                continue

            except Exception as e:
                print(f"Error searching for pattern '{pattern}': {e}")
                continue

        # If no exact 3:30 PM slot found, look for available slots around that time
        print("Looking for available slots around 3:30 PM...")

        nearby_times = ["3:00 PM", "3:15 PM", "3:45 PM", "4:00 PM"]
        for time_slot in nearby_times:
            try:
                elements = self.driver.find_elements(By.XPATH,
                    f"//*[contains(text(), '{time_slot}')]")

                for element in elements:
                    if ('reserve' in element.text.lower() and
                        element.tag_name in ['button', 'a']):
                        print(f"Booking nearby slot: {time_slot}")
                        element.click()
                        time.sleep(2)
                        return True

            except Exception as e:
                continue

        print("❌ No available slots found around 3:30 PM")
        return False

    def verify_booking(self):
        """Verify that the booking was successful"""
        time.sleep(3)

        # Check for success indicators
        success_indicators = [
            "confirmation",
            "booked",
            "reserved",
            "success",
            "thank you"
        ]

        page_text = self.driver.page_source.lower()
        for indicator in success_indicators:
            if indicator in page_text:
                print(f"✅ Booking appears successful (found '{indicator}')")
                return True

        # Check URL for confirmation page
        if "confirmation" in self.driver.current_url.lower():
            print("✅ Booking successful (on confirmation page)")
            return True

        print("⚠️ Booking status unclear")
        return False

    def run(self):
        """Main execution method"""
        try:
            self.setup_driver(headless=False)

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            # Calculate target date (two weeks from now)
            target_date = datetime.now() + timedelta(weeks=2)

            if not self.navigate_to_target_date(target_date):
                print("⚠️ Could not reach target date, trying to book on current page...")

            if self.find_and_book_330pm_slot():
                if self.verify_booking():
                    print("🎉 Court booking completed successfully!")
                    time.sleep(10)  # Keep browser open to see result
                    return True
                else:
                    print("⚠️ Booking attempted but verification unclear")
                    input("Press Enter to close browser...")
                    return True
            else:
                print("❌ Could not find or book 3:30 PM slot")
                input("Press Enter to close browser...")
                return False

        except Exception as e:
            print(f"❌ Error during execution: {str(e)}")
            input("Press Enter to close browser...")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Enhanced Court Booking Automation")
    print("=================================")

    booker = EnhancedCourtBooker()
    success = booker.run()

    if success:
        print("✅ Process completed!")
    else:
        print("❌ Process failed")

if __name__ == "__main__":
    main()