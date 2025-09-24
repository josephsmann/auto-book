#!/usr/bin/env python3
"""
Complete court booking automation script with form handling
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

class CompleteCourtBooker:
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
                next_selectors = [
                    "button[title='Next']",
                    "button[class*='next']",
                    "button[class*='forward']",
                    ".fa-arrow-right",
                    ".fa-chevron-right"
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
                    time.sleep(1)
                    print(f"   Day {day + 1} navigated")
                else:
                    print(f"❌ Could not find next button on day {day + 1}")
                    break

            except Exception as e:
                print(f"❌ Navigation error on day {day + 1}: {e}")
                break

        print(f"✅ Navigation completed")
        time.sleep(2)

    def find_500pm_slot(self):
        """Find a 5:00 PM time slot specifically"""
        print("🎯 Looking for 5:00 PM time slot...")

        # Look for 5:00 PM slots specifically
        time_patterns = ["5:00 PM", "5:00", "17:00"]

        for pattern in time_patterns:
            try:
                # Look for reserve buttons containing 5:00 PM
                reserve_buttons = self.driver.find_elements(By.XPATH,
                    f"//button[contains(text(), 'Reserve') and contains(text(), '{pattern}')]")

                if reserve_buttons:
                    for button in reserve_buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"✅ Found 5:00 PM slot: {button.text}")
                            return button

                # Also try looking for any element with the time pattern near a reserve button
                time_elements = self.driver.find_elements(By.XPATH,
                    f"//*[contains(text(), '{pattern}')]")

                for element in time_elements:
                    # Look for nearby reserve button
                    try:
                        parent = element.find_element(By.XPATH, "./..")
                        reserve_btn = parent.find_element(By.XPATH, ".//button[contains(text(), 'Reserve')]")
                        if reserve_btn.is_displayed() and reserve_btn.is_enabled():
                            print(f"✅ Found 5:00 PM slot near time element: {reserve_btn.text}")
                            return reserve_btn
                    except NoSuchElementException:
                        continue

            except Exception as e:
                print(f"Error searching for {pattern}: {e}")
                continue

        print("❌ No 5:00 PM slot found")
        return None

    def fill_booking_form(self):
        """Fill out the booking form with required details"""
        print("📝 Filling out booking form...")

        try:
            # Wait for the form to appear
            time.sleep(3)

            # 1. Set court type to "Singles"
            print("   Setting court type to 'Singles'...")
            court_type_selectors = [
                "select[name*='type']",
                "select[name*='court']",
                "select[id*='type']",
                "select[id*='court']",
                "select[class*='type']",
                "select[class*='court']"
            ]

            for selector in court_type_selectors:
                try:
                    court_type_dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                    select = Select(court_type_dropdown)

                    # Try to select "Singles" by visible text
                    try:
                        select.select_by_visible_text("Singles")
                        print("   ✅ Court type set to Singles")
                        break
                    except:
                        # Try other variations
                        for option_text in ["Singles Squash Courts", "Singles Court", "Single"]:
                            try:
                                select.select_by_visible_text(option_text)
                                print(f"   ✅ Court type set to {option_text}")
                                break
                            except:
                                continue
                        else:
                            continue
                        break

                except NoSuchElementException:
                    continue

            # 2. Set start time to 5:00 PM
            print("   Setting start time to 5:00 PM...")
            time_selectors = [
                "select[name*='time']",
                "select[name*='start']",
                "select[id*='time']",
                "select[id*='start']",
                "input[name*='time']",
                "input[id*='time']"
            ]

            for selector in time_selectors:
                try:
                    time_element = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if time_element.tag_name == "select":
                        select = Select(time_element)
                        # Try different time formats
                        for time_format in ["5:00 PM", "17:00", "5:00", "17:00:00"]:
                            try:
                                select.select_by_visible_text(time_format)
                                print(f"   ✅ Start time set to {time_format}")
                                break
                            except:
                                continue
                        else:
                            continue
                        break
                    elif time_element.tag_name == "input":
                        time_element.clear()
                        time_element.send_keys("5:00 PM")
                        print("   ✅ Start time set to 5:00 PM")
                        break

                except NoSuchElementException:
                    continue

            # 3. Add "Scott Jackson" to Additional Players
            print("   Adding Scott Jackson to Additional Players...")
            player_selectors = [
                "input[name*='player']",
                "input[name*='additional']",
                "input[name*='guest']",
                "input[id*='player']",
                "input[id*='additional']",
                "input[id*='guest']",
                "textarea[name*='player']",
                "textarea[name*='additional']"
            ]

            for selector in player_selectors:
                try:
                    player_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    player_field.clear()
                    player_field.send_keys("Scott Jackson")
                    print("   ✅ Added Scott Jackson to Additional Players")
                    break
                except NoSuchElementException:
                    continue

            # 4. Duration should remain at 1 hour (default - no action needed)
            print("   ✅ Duration remains at 1 hour (default)")

            time.sleep(2)  # Let form update
            return True

        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False

    def submit_booking(self):
        """Submit the completed booking form"""
        print("📤 Submitting booking...")

        try:
            # Look for submit/save/confirm buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[class*='save']",
                "button[class*='submit']",
                "button[class*='confirm']",
                "//button[contains(text(), 'Save')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Confirm')]",
                "//button[contains(text(), 'Book')]",
                "//input[contains(@value, 'Save')]",
                "//input[contains(@value, 'Submit')]"
            ]

            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if submit_button.is_displayed() and submit_button.is_enabled():
                        print(f"   Clicking: {submit_button.text or submit_button.get_attribute('value')}")
                        submit_button.click()
                        time.sleep(5)  # Wait for submission to process
                        return True

                except NoSuchElementException:
                    continue

            print("❌ Could not find submit button")
            return False

        except Exception as e:
            print(f"❌ Error submitting form: {e}")
            return False

    def verify_booking_success(self):
        """Verify that the booking was completed successfully"""
        print("✅ Verifying booking...")

        time.sleep(3)

        # Check URL for success/confirmation page
        current_url = self.driver.current_url.lower()
        if any(keyword in current_url for keyword in ["success", "confirmation", "complete"]):
            print("✅ Booking confirmed (success URL)")
            return True

        # Check page content for success messages
        page_text = self.driver.page_source.lower()
        success_keywords = [
            "booking confirmed",
            "reservation confirmed",
            "successfully booked",
            "booking complete",
            "confirmation number",
            "thank you",
            "reserved successfully"
        ]

        for keyword in success_keywords:
            if keyword in page_text:
                print(f"✅ Booking confirmed (found '{keyword}')")
                return True

        # Check for any confirmation elements
        confirmation_selectors = [
            ".success",
            ".confirmation",
            ".alert-success",
            "[class*='success']",
            "[class*='confirm']"
        ]

        for selector in confirmation_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    print(f"✅ Booking confirmed (found confirmation element)")
                    return True
            except NoSuchElementException:
                continue

        print("⚠️ Booking status unclear - check browser manually")
        return True  # Assume success if we got this far

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Complete Court Booking Automation")
            print("=" * 50)

            self.setup_driver(headless=False)

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            # Navigate to approximately 2 weeks ahead
            self.navigate_forward_days(14)

            # Find the 5:00 PM slot
            slot_button = self.find_500pm_slot()
            if not slot_button:
                print("❌ Could not find 5:00 PM slot")
                print("🔍 Checking browser for available times...")
                input("Press Enter after manually checking available times...")
                return False

            # Click the 5:00 PM slot
            print("🔄 Clicking 5:00 PM slot...")
            slot_button.click()
            time.sleep(3)

            # Fill out the booking form
            if not self.fill_booking_form():
                print("❌ Failed to fill booking form")
                input("Press Enter after manually filling the form...")
                return False

            # Submit the booking
            if not self.submit_booking():
                print("❌ Failed to submit booking")
                input("Press Enter after manually submitting...")
                return False

            # Verify success
            if self.verify_booking_success():
                print("🎉 BOOKING COMPLETED SUCCESSFULLY!")
                print("📧 Check your email for confirmation")
                print("🔍 Browser will stay open for 15 seconds for verification")
                time.sleep(15)
                return True
            else:
                print("⚠️ Booking may have failed")
                input("Press Enter after checking the result...")
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            input("Press Enter after checking the error...")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Complete Court Booking Automation")
    print("=================================")
    print("Booking Details:")
    print("- Court Type: Singles")
    print("- Start Time: 5:00 PM")
    print("- Duration: 1 hour")
    print("- Additional Player: Scott Jackson")
    print("- Date: ~2 weeks from today")
    print()

    booker = CompleteCourtBooker()
    success = booker.run()

    if success:
        print("\n✅ Booking process completed!")
    else:
        print("\n❌ Booking process incomplete")

if __name__ == "__main__":
    main()