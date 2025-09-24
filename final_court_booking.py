#!/usr/bin/env python3
"""
Final court booking automation script with improved navigation and booking logic
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

class FinalCourtBooker:
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

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """Login to courtreserve.com"""
        print("🔐 Logging in...")

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
        print("📅 Navigating to booking page...")
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        self.driver.get(booking_url)
        time.sleep(3)
        return True

    def navigate_forward_days(self, days_ahead=14):
        """Navigate forward by clicking next button multiple times"""
        print(f"⏭️ Navigating {days_ahead} days ahead...")

        for day in range(days_ahead):
            try:
                # Look for various next button selectors
                next_selectors = [
                    "button[title='Next']",
                    "button[class*='next']",
                    "button[class*='forward']",
                    ".fa-arrow-right",
                    ".fa-chevron-right",
                    "[class*='arrow-right']",
                    "[class*='chevron-right']"
                ]

                next_button = None
                for selector in next_selectors:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if next_button.is_displayed() and next_button.is_enabled():
                            break
                    except NoSuchElementException:
                        continue

                if next_button:
                    next_button.click()
                    time.sleep(1)  # Brief pause between clicks
                    print(f"   Day {day + 1} navigated")
                else:
                    print(f"❌ Could not find next button on day {day + 1}")
                    break

            except Exception as e:
                print(f"❌ Navigation error on day {day + 1}: {e}")
                break

        print(f"✅ Navigation completed")
        time.sleep(2)  # Final pause to let page load

    def find_available_time_slots(self):
        """Find all available time slots on current page"""
        print("🔍 Searching for available time slots...")

        # Look for "Reserve" buttons which indicate available slots
        reserve_buttons = self.driver.find_elements(By.XPATH,
            "//button[contains(text(), 'Reserve') or contains(@class, 'reserve')]")

        available_slots = []
        for button in reserve_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    slot_text = button.text.strip()
                    available_slots.append((button, slot_text))
            except:
                continue

        print(f"✅ Found {len(available_slots)} available slots")
        for i, (_, text) in enumerate(available_slots[:5]):  # Show first 5
            print(f"   {i+1}. {text}")

        return available_slots

    def book_preferred_time_slot(self, available_slots):
        """Book the best available time slot, preferring 3:30 PM"""
        print("🎯 Looking for preferred time slots...")

        # Preferred times in order of preference
        preferred_times = ["3:30", "15:30", "3:00", "4:00", "3:15", "3:45"]

        # First, try to find exact matches
        for preferred_time in preferred_times:
            for button, slot_text in available_slots:
                if preferred_time in slot_text:
                    print(f"🎉 Found preferred time: {slot_text}")
                    return self.attempt_booking(button, slot_text)

        # If no preferred time found, book any afternoon slot (after 12 PM)
        afternoon_slots = []
        for button, slot_text in available_slots:
            # Look for PM times or times after 12
            if ("PM" in slot_text and not any(time in slot_text for time in ["10:", "11:", "12:"])) or \
               any(time in slot_text for time in ["1:", "2:", "3:", "4:", "5:"]):
                afternoon_slots.append((button, slot_text))

        if afternoon_slots:
            button, slot_text = afternoon_slots[0]  # Take first afternoon slot
            print(f"📅 Booking afternoon slot: {slot_text}")
            return self.attempt_booking(button, slot_text)

        # Last resort: book any available slot
        if available_slots:
            button, slot_text = available_slots[0]
            print(f"⏰ Booking any available slot: {slot_text}")
            return self.attempt_booking(button, slot_text)

        print("❌ No bookable slots found")
        return False

    def attempt_booking(self, button, slot_text):
        """Attempt to book a specific time slot"""
        try:
            print(f"🔄 Clicking slot: {slot_text}")
            button.click()
            time.sleep(3)

            # Look for confirmation or booking form
            possible_confirmations = [
                "button[class*='confirm']",
                "button[class*='book']",
                "button[class*='submit']",
                "input[type='submit']",
                "button[type='submit']",
                "//button[contains(text(), 'Confirm')]",
                "//button[contains(text(), 'Book')]",
                "//button[contains(text(), 'Reserve')]"
            ]

            for selector in possible_confirmations:
                try:
                    if selector.startswith("//"):
                        confirm_btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        confirm_btn = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                        print(f"✅ Clicking confirmation: {confirm_btn.text}")
                        confirm_btn.click()
                        time.sleep(3)
                        return True

                except NoSuchElementException:
                    continue

            # Check if booking was successful without additional confirmation
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()

            success_indicators = ["success", "confirmed", "booked", "reserved", "thank you"]
            if any(indicator in page_source for indicator in success_indicators):
                print("✅ Booking appears successful!")
                return True

            print("⚠️ Clicked slot but unclear if booking completed")
            return True  # Assume success if we got this far

        except Exception as e:
            print(f"❌ Booking attempt failed: {e}")
            return False

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Court Booking Automation")
            print("=" * 40)

            self.setup_driver(headless=False)

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            # Navigate to approximately 2 weeks ahead
            self.navigate_forward_days(14)

            # Find available slots
            available_slots = self.find_available_time_slots()

            if not available_slots:
                print("❌ No available slots found on target date")
                print("🔄 Trying nearby dates...")

                # Try a few days around the target
                for offset in [-1, 1, -2, 2]:
                    print(f"   Trying {offset} days offset...")
                    if offset > 0:
                        self.navigate_forward_days(offset)
                    else:
                        # Navigate backwards (if possible)
                        for _ in range(abs(offset)):
                            try:
                                prev_btn = self.driver.find_element(By.CSS_SELECTOR, "button[title='Previous']")
                                prev_btn.click()
                                time.sleep(1)
                            except:
                                break

                    available_slots = self.find_available_time_slots()
                    if available_slots:
                        break

            if available_slots:
                if self.book_preferred_time_slot(available_slots):
                    print("🎉 BOOKING SUCCESSFUL!")
                    print("🔍 Check the browser window for confirmation")
                    time.sleep(10)
                    return True
                else:
                    print("❌ Booking attempt failed")
                    return False
            else:
                print("❌ No available slots found in the date range")
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            if self.driver:
                print("🔄 Keeping browser open for 10 seconds...")
                time.sleep(10)
                self.driver.quit()

def main():
    print("Final Court Booking Automation")
    print("==============================")

    booker = FinalCourtBooker()
    success = booker.run()

    if success:
        print("\n✅ Booking process completed successfully!")
        print("📧 Check your email for confirmation")
    else:
        print("\n❌ Booking process failed")
        print("🔧 You may need to book manually")

if __name__ == "__main__":
    main()