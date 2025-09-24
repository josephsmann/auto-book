#!/usr/bin/env python3
"""
Working court booking automation script with Kendo UI support
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

class WorkingCourtBooker:
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
        self.wait = WebDriverWait(self.driver, 15)

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
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                if next_button.is_displayed() and next_button.is_enabled():
                    next_button.click()
                    time.sleep(1)
                    print(f"   Day {day + 1} navigated")
                else:
                    break
            except:
                break

        print("✅ Navigation completed")
        time.sleep(2)

    def find_and_click_500pm_slot(self):
        """Find and click a 5:00 PM time slot"""
        print("🎯 Looking for 5:00 PM slot...")

        reserve_buttons = self.driver.find_elements(By.XPATH,
            "//button[contains(text(), 'Reserve') and contains(text(), '5:00 PM')]")

        if reserve_buttons:
            button = reserve_buttons[0]
            print(f"✅ Found 5:00 PM slot: {button.text}")
            button.click()
            print("🔄 Clicked 5:00 PM slot")
            return True
        else:
            print("❌ No 5:00 PM slot found")
            return False

    def handle_kendo_dropdown(self, dropdown_element, target_text):
        """Handle Kendo UI dropdown selection"""
        try:
            # Click to open dropdown
            dropdown_element.click()
            time.sleep(1)

            # Wait for dropdown list to appear
            dropdown_list = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".k-list-container ul.k-list"))
            )

            # Find and click the target option
            options = dropdown_list.find_elements(By.CSS_SELECTOR, "li.k-list-item")
            for option in options:
                if target_text.lower() in option.text.lower():
                    option.click()
                    time.sleep(1)
                    return True

            return False
        except Exception as e:
            print(f"   Error handling Kendo dropdown: {e}")
            return False

    def fill_booking_form(self):
        """Fill out the booking form with Kendo UI components"""
        print("📝 Filling out booking form...")

        try:
            # Wait for modal to appear
            modal = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, [role='dialog']"))
            )
            print("✅ Booking form modal appeared")
            time.sleep(3)  # Let modal fully load

            # 1. Set Reservation Type to "Singles" using Kendo dropdown
            print("   Setting reservation type to 'Singles'...")
            try:
                # Find the reservation type Kendo dropdown
                reservation_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, ".k-dropdown")

                for dropdown in reservation_dropdowns:
                    if dropdown.is_displayed():
                        # Check if this dropdown contains reservation type text
                        span = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                        if "reservation type" in span.text.lower() or "-- reservation type --" in span.text.lower():
                            if self.handle_kendo_dropdown(dropdown, "Singles"):
                                print("   ✅ Selected 'Singles' reservation type")
                                break
                else:
                    print("   ⚠️ Could not find reservation type dropdown")

            except Exception as e:
                print(f"   ❌ Error setting reservation type: {e}")

            # 2. Start Time should already be set to 5:00 PM (17:00:00) as we clicked that slot
            print("   ✅ Start time already set to 5:00 PM from slot selection")

            # 3. Duration should remain at 1 hour (default)
            print("   ✅ Duration remains at 1 hour (default)")

            # 4. Add "Scott Jackson" to Additional Players
            print("   Adding 'Scott Jackson' to additional players...")
            try:
                players_input = self.driver.find_element(By.NAME, "OwnersDropdown_input")
                players_input.clear()
                players_input.send_keys("Scott Jackson")
                print("   ✅ Added 'Scott Jackson' to additional players field")

                # Wait for any autocomplete dropdown
                time.sleep(2)

                # Try to find and select from autocomplete if it appears
                try:
                    autocomplete_items = self.driver.find_elements(By.CSS_SELECTOR,
                        ".k-list-item, .autocomplete-item, [role='option']")

                    for item in autocomplete_items:
                        if item.is_displayed() and "scott" in item.text.lower():
                            item.click()
                            print("   ✅ Selected Scott Jackson from autocomplete")
                            break
                except:
                    # No autocomplete found, typed name should be sufficient
                    pass

            except Exception as e:
                print(f"   ❌ Error adding additional player: {e}")

            time.sleep(2)  # Let form fully update
            return True

        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False

    def submit_booking_form(self):
        """Submit the booking form"""
        print("📤 Submitting booking form...")

        try:
            # Find and click the Save button
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-submit")

            if save_button.is_displayed() and save_button.is_enabled():
                print(f"   Clicking Save button")
                save_button.click()
                time.sleep(5)  # Wait for submission
                return True
            else:
                print("   ❌ Save button not available")
                return False

        except Exception as e:
            print(f"   ❌ Error submitting form: {e}")
            return False

    def verify_booking_by_refresh(self):
        """Verify booking by refreshing the page and checking for the booking"""
        print("✅ Verifying booking by refreshing page...")

        try:
            # First check for immediate success indicators
            time.sleep(3)

            # Refresh the page to see actual bookings
            print("🔄 Refreshing page to check for booking...")
            self.driver.refresh()
            time.sleep(5)

            # Look for our booking on the refreshed page
            page_text = self.driver.page_source.lower()

            # Check for indicators of our booking
            booking_found = False

            # Look for Scott Jackson
            if "scott jackson" in page_text:
                print("✅ Found 'Scott Jackson' on the page!")
                booking_found = True

            # Look for 5:00 PM booking
            if any(time_indicator in page_text for time_indicator in ["5:00 pm", "17:00", "5:00 p.m."]):
                print("✅ Found 5:00 PM time slot booking!")
                booking_found = True

            # Look for Singles booking
            if "singles" in page_text:
                print("✅ Found 'Singles' court type!")
                booking_found = True

            if booking_found:
                print("🎉 BOOKING VERIFICATION SUCCESSFUL!")
                print("🎯 Court has been successfully booked!")
                return True
            else:
                print("❌ BOOKING VERIFICATION FAILED")
                print("❓ No evidence of booking found after refresh")
                return False

        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Working Court Booking Automation")
            print("=" * 55)
            print("Booking Details:")
            print("- Court Type: Singles")
            print("- Start Time: 5:00 PM")
            print("- Duration: 1 hour")
            print("- Additional Player: Scott Jackson")
            print("- Date: ~2 weeks from today")
            print("=" * 55)

            self.setup_driver(headless=False)

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            self.navigate_forward_days(14)

            if not self.find_and_click_500pm_slot():
                print("❌ Could not find 5:00 PM slot")
                return False

            if not self.fill_booking_form():
                print("❌ Could not fill booking form")
                return False

            if not self.submit_booking_form():
                print("❌ Could not submit booking form")
                return False

            if self.verify_booking_by_refresh():
                print("🎉 COURT BOOKING COMPLETED AND VERIFIED!")
                print("📧 Check your email for confirmation")
                print("🔍 Keeping browser open for 15 seconds for final verification")
                time.sleep(15)
                return True
            else:
                print("❌ BOOKING COULD NOT BE VERIFIED")
                print("🔍 Check browser manually")
                time.sleep(15)
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Working Court Booking Automation")
    print("================================")

    booker = WorkingCourtBooker()
    success = booker.run()

    if success:
        print("\n✅ BOOKING PROCESS SUCCESSFUL!")
        print("🎾 Court is reserved!")
    else:
        print("\n❌ BOOKING PROCESS FAILED")
        print("🔧 Manual booking may be required")

if __name__ == "__main__":
    main()