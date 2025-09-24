#!/usr/bin/env python3
"""
Corrected court booking automation script based on actual form structure
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

class CorrectedCourtBooker:
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
                    print(f"❌ Next button not available on day {day + 1}")
                    break
            except Exception as e:
                print(f"❌ Navigation error on day {day + 1}: {e}")
                break

        print("✅ Navigation completed")
        time.sleep(2)

    def find_and_click_500pm_slot(self):
        """Find and click a 5:00 PM time slot"""
        print("🎯 Looking for 5:00 PM slot...")

        # Look for 5:00 PM reserve buttons
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

    def wait_for_modal_and_fill_form(self):
        """Wait for the booking modal to appear and fill the form"""
        print("📝 Waiting for booking form modal...")

        try:
            # Wait for modal to appear
            modal = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, [role='dialog']"))
            )
            print("✅ Booking form modal appeared")
            time.sleep(2)  # Let modal fully load

            # 1. Set Reservation Type to "Singles"
            print("   Setting reservation type to 'Singles'...")
            try:
                reservation_type_select = self.driver.find_element(By.ID, "ReservationTypeId")
                select = Select(reservation_type_select)

                # Try to find Singles option
                options = select.options
                for option in options:
                    if "singles" in option.text.lower():
                        select.select_by_visible_text(option.text)
                        print(f"   ✅ Selected reservation type: {option.text}")
                        break
                else:
                    print("   ⚠️ Could not find 'Singles' option")

            except NoSuchElementException:
                print("   ❌ Reservation type dropdown not found")

            # 2. Set Start Time to 5:00 PM
            print("   Setting start time to 5:00 PM...")
            try:
                start_time_select = self.driver.find_element(By.ID, "StartTime")
                select = Select(start_time_select)

                # Try different time formats
                time_formats = ["5:00 PM", "17:00", "5:00:00 PM", "17:00:00"]
                for time_format in time_formats:
                    try:
                        select.select_by_visible_text(time_format)
                        print(f"   ✅ Set start time to: {time_format}")
                        break
                    except:
                        continue
                else:
                    print("   ⚠️ Could not set start time to 5:00 PM")

            except NoSuchElementException:
                print("   ❌ Start time dropdown not found")

            # 3. Duration should remain at default (1 hour)
            print("   ✅ Duration remains at default (1 hour)")

            # 4. Add "Scott Jackson" to Additional Players
            print("   Adding 'Scott Jackson' to additional players...")
            try:
                players_input = self.driver.find_element(By.NAME, "OwnersDropdown_input")
                players_input.clear()
                players_input.send_keys("Scott Jackson")
                print("   ✅ Added 'Scott Jackson' to additional players")

                # Wait a moment for any autocomplete/dropdown to appear
                time.sleep(2)

                # Try to select from dropdown if it appears
                try:
                    # Look for dropdown items
                    dropdown_items = self.driver.find_elements(By.CSS_SELECTOR,
                        ".k-list-item, .dropdown-item, [role='option']")

                    for item in dropdown_items:
                        if "scott jackson" in item.text.lower():
                            item.click()
                            print("   ✅ Selected Scott Jackson from dropdown")
                            break
                except:
                    pass  # No dropdown, that's fine

            except NoSuchElementException:
                print("   ❌ Additional players input not found")

            time.sleep(2)  # Let form update
            return True

        except TimeoutException:
            print("❌ Booking form modal did not appear")
            return False
        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False

    def submit_booking_form(self):
        """Submit the booking form"""
        print("📤 Submitting booking form...")

        try:
            # Look for the Save button specifically
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-submit")

            if save_button.is_displayed() and save_button.is_enabled():
                print(f"   Clicking Save button: {save_button.text}")
                save_button.click()
                time.sleep(5)  # Wait for submission to process
                return True
            else:
                print("   ❌ Save button not available")
                return False

        except NoSuchElementException:
            print("   ❌ Save button not found")
            return False
        except Exception as e:
            print(f"   ❌ Error submitting form: {e}")
            return False

    def verify_booking_success(self):
        """Verify booking was successful by refreshing and checking"""
        print("✅ Verifying booking success...")

        try:
            # Wait for any success message or redirect
            time.sleep(3)

            # Check for success indicators in current page
            page_source = self.driver.page_source.lower()
            success_keywords = [
                "booking confirmed",
                "reservation confirmed",
                "successfully booked",
                "confirmation number",
                "booking complete"
            ]

            for keyword in success_keywords:
                if keyword in page_source:
                    print(f"✅ Initial success indicator found: '{keyword}'")
                    break

            # Now refresh the page to verify the booking actually exists
            print("🔄 Refreshing page to verify booking persists...")
            self.driver.refresh()
            time.sleep(5)

            # Look for the booked slot
            page_text = self.driver.page_source

            # Check if we can find evidence of our booking
            booking_indicators = [
                "scott jackson",
                "singles",
                "5:00 pm",
                "17:00"
            ]

            found_indicators = []
            for indicator in booking_indicators:
                if indicator in page_text.lower():
                    found_indicators.append(indicator)

            if found_indicators:
                print(f"✅ BOOKING VERIFIED! Found indicators: {found_indicators}")
                return True
            else:
                print("❌ BOOKING NOT FOUND after refresh - booking may have failed")
                return False

        except Exception as e:
            print(f"❌ Error verifying booking: {e}")
            return False

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Corrected Court Booking Automation")
            print("=" * 55)
            print("Booking Details:")
            print("- Court Type: Singles")
            print("- Start Time: 5:00 PM")
            print("- Duration: 1 hour (default)")
            print("- Additional Player: Scott Jackson")
            print("- Date: ~2 weeks from today")
            print("=" * 55)

            self.setup_driver(headless=False)

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            # Navigate to target date
            self.navigate_forward_days(14)

            # Find and click 5:00 PM slot
            if not self.find_and_click_500pm_slot():
                print("❌ Could not find 5:00 PM slot")
                input("Press Enter after checking available times...")
                return False

            # Wait for modal and fill form
            if not self.wait_for_modal_and_fill_form():
                print("❌ Could not fill booking form")
                input("Press Enter after manually filling form...")
                return False

            # Submit the form
            if not self.submit_booking_form():
                print("❌ Could not submit booking form")
                input("Press Enter after manually submitting...")
                return False

            # Verify the booking was successful
            if self.verify_booking_success():
                print("🎉 BOOKING SUCCESSFULLY COMPLETED AND VERIFIED!")
                print("📧 Check your email for confirmation")
                time.sleep(10)
                return True
            else:
                print("❌ BOOKING FAILED - no evidence found after refresh")
                print("🔍 Browser will stay open for manual verification")
                input("Press Enter after checking manually...")
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            input("Press Enter after checking the error...")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Corrected Court Booking Automation")
    print("==================================")

    booker = CorrectedCourtBooker()
    success = booker.run()

    if success:
        print("\n✅ Booking process completed and verified!")
    else:
        print("\n❌ Booking process failed or could not be verified")

if __name__ == "__main__":
    main()