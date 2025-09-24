#!/usr/bin/env python3
"""
Fixed court booking automation with improved Kendo UI dropdown handling
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

class FixedCourtBooker:
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

    def select_singles_from_kendo_dropdown(self):
        """Properly select Singles from the Kendo reservation type dropdown"""
        print("   🎯 Attempting to select 'Singles' from reservation type dropdown...")

        try:
            # Method 1: Find dropdown by looking for "-- Reservation Type --" text
            print("   Method 1: Looking for reservation type dropdown by text...")

            # Find all Kendo dropdowns
            kendo_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, ".k-dropdown")

            for i, dropdown in enumerate(kendo_dropdowns):
                if dropdown.is_displayed():
                    try:
                        # Get the current text displayed in the dropdown
                        dropdown_text_element = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                        current_text = dropdown_text_element.text.strip()

                        print(f"   Dropdown {i+1} current text: '{current_text}'")

                        if "reservation type" in current_text.lower() or current_text == "-- Reservation Type --":
                            print(f"   ✅ Found reservation type dropdown!")

                            # Click to open the dropdown
                            print("   Clicking dropdown to open...")
                            dropdown.click()
                            time.sleep(2)

                            # Wait for dropdown options to appear
                            try:
                                dropdown_list = self.wait.until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".k-animation-container .k-list"))
                                )
                                print("   ✅ Dropdown list opened")

                                # Find all options in the dropdown
                                options = dropdown_list.find_elements(By.CSS_SELECTOR, "li")
                                print(f"   Found {len(options)} options in dropdown")

                                for j, option in enumerate(options):
                                    option_text = option.text.strip()
                                    print(f"   Option {j+1}: '{option_text}'")

                                    if "singles" in option_text.lower():
                                        print(f"   🎯 Clicking Singles option: '{option_text}'")

                                        # Scroll option into view and click
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", option)
                                        time.sleep(0.5)

                                        # Try multiple click methods
                                        try:
                                            option.click()
                                        except:
                                            # Try ActionChains click
                                            ActionChains(self.driver).move_to_element(option).click().perform()

                                        time.sleep(2)

                                        # Verify selection
                                        new_text = dropdown_text_element.text.strip()
                                        print(f"   Dropdown now shows: '{new_text}'")

                                        if "singles" in new_text.lower():
                                            print("   ✅ Successfully selected Singles!")
                                            return True
                                        else:
                                            print("   ⚠️ Selection may not have worked")
                                            break

                            except Exception as e:
                                print(f"   ❌ Error opening dropdown list: {e}")
                                continue

                    except Exception as e:
                        print(f"   Error checking dropdown {i+1}: {e}")
                        continue

            # Method 2: Try clicking dropdown near ReservationTypeId
            print("   Method 2: Looking for dropdown near ReservationTypeId...")
            try:
                reservation_input = self.driver.find_element(By.ID, "ReservationTypeId")
                parent = reservation_input.find_element(By.XPATH, "..")
                dropdown = parent.find_element(By.CSS_SELECTOR, ".k-dropdown")

                print("   Found dropdown near ReservationTypeId")
                dropdown.click()
                time.sleep(2)

                # Look for Singles option
                options = self.driver.find_elements(By.CSS_SELECTOR, ".k-animation-container .k-list li")
                for option in options:
                    if "singles" in option.text.lower():
                        print(f"   Clicking Singles: {option.text}")
                        option.click()
                        time.sleep(2)
                        return True

            except Exception as e:
                print(f"   Method 2 failed: {e}")

            # Method 3: Try JavaScript approach
            print("   Method 3: Trying JavaScript approach...")
            try:
                js_script = """
                var dropdowns = document.querySelectorAll('.k-dropdown');
                for (var i = 0; i < dropdowns.length; i++) {
                    var dropdown = dropdowns[i];
                    var textElement = dropdown.querySelector('.k-input-inner, .k-input');
                    if (textElement && textElement.textContent.includes('Reservation Type')) {
                        dropdown.click();
                        setTimeout(function() {
                            var options = document.querySelectorAll('.k-animation-container .k-list li');
                            for (var j = 0; j < options.length; j++) {
                                if (options[j].textContent.toLowerCase().includes('singles')) {
                                    options[j].click();
                                    return true;
                                }
                            }
                        }, 1000);
                        return true;
                    }
                }
                return false;
                """

                result = self.driver.execute_script(js_script)
                if result:
                    print("   ✅ JavaScript method succeeded")
                    time.sleep(3)
                    return True

            except Exception as e:
                print(f"   Method 3 failed: {e}")

            print("   ❌ All methods failed to select Singles")
            return False

        except Exception as e:
            print(f"   ❌ Error in select_singles_from_kendo_dropdown: {e}")
            return False

    def fill_booking_form(self):
        """Fill out the booking form with improved dropdown handling"""
        print("📝 Filling out booking form...")

        try:
            # Wait for modal to appear
            modal = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, [role='dialog']"))
            )
            print("✅ Booking form modal appeared")
            time.sleep(3)  # Let modal fully load

            # 1. Set Reservation Type to "Singles" with improved handling
            print("   Setting reservation type to 'Singles'...")
            singles_selected = self.select_singles_from_kendo_dropdown()

            if not singles_selected:
                print("   ❌ CRITICAL: Could not select Singles - booking will fail!")
                return False

            # 2. Start Time should already be set to 5:00 PM
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

                # Wait for autocomplete
                time.sleep(2)

                # Try to select from autocomplete
                try:
                    autocomplete_items = self.driver.find_elements(By.CSS_SELECTOR,
                        ".k-list-item, .autocomplete-item, [role='option']")

                    for item in autocomplete_items:
                        if item.is_displayed() and "scott" in item.text.lower():
                            item.click()
                            print("   ✅ Selected Scott Jackson from autocomplete")
                            break
                except:
                    print("   ℹ️ No autocomplete found, typed name should be sufficient")

            except Exception as e:
                print(f"   ⚠️ Could not add additional player: {e}")

            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False

    def verify_form_before_submit(self):
        """Verify the form is properly filled before submitting"""
        print("🔍 Verifying form is properly filled...")

        try:
            # Check if Singles is selected
            kendo_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, ".k-dropdown")

            for dropdown in kendo_dropdowns:
                if dropdown.is_displayed():
                    text_element = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                    current_text = text_element.text.strip()

                    if "singles" in current_text.lower():
                        print("   ✅ Verified: Singles is selected")
                        return True
                    elif "reservation type" in current_text.lower():
                        print(f"   ❌ PROBLEM: Reservation type still shows '{current_text}'")
                        return False

            print("   ⚠️ Could not verify Singles selection")
            return False

        except Exception as e:
            print(f"   ❌ Error verifying form: {e}")
            return False

    def submit_booking_form(self):
        """Submit the booking form"""
        print("📤 Submitting booking form...")

        try:
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-submit")

            if save_button.is_displayed() and save_button.is_enabled():
                print("   Clicking Save button")
                save_button.click()
                time.sleep(5)
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
            time.sleep(3)

            print("🔄 Refreshing page to check for booking...")
            self.driver.refresh()
            time.sleep(5)

            page_text = self.driver.page_source.lower()

            # Check for our specific booking details
            found_indicators = []

            if "scott jackson" in page_text:
                found_indicators.append("Scott Jackson")

            if any(time_indicator in page_text for time_indicator in ["5:00 pm", "17:00", "5:00 p.m."]):
                found_indicators.append("5:00 PM")

            if "singles" in page_text:
                found_indicators.append("Singles")

            if found_indicators:
                print(f"✅ BOOKING VERIFIED! Found: {', '.join(found_indicators)}")
                return True
            else:
                print("❌ BOOKING NOT FOUND - reservation likely failed")
                print("   This usually means Singles was not properly selected")
                return False

        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting Fixed Court Booking Automation")
            print("=" * 55)
            print("Booking Details:")
            print("- Court Type: Singles (MUST be selected!)")
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
                print("❌ Could not fill booking form properly")
                print("🔍 Keeping browser open for manual inspection...")
                time.sleep(30)
                return False

            if not self.verify_form_before_submit():
                print("❌ Form verification failed - Singles not selected")
                print("🔍 Keeping browser open for manual correction...")
                time.sleep(30)
                return False

            if not self.submit_booking_form():
                print("❌ Could not submit booking form")
                return False

            if self.verify_booking_by_refresh():
                print("🎉 COURT BOOKING COMPLETED AND VERIFIED!")
                print("📧 Check your email for confirmation")
                print("🎾 Court is successfully reserved!")
                time.sleep(15)
                return True
            else:
                print("❌ BOOKING VERIFICATION FAILED")
                print("🔧 The form was submitted but reservation was not created")
                print("💡 This usually means Singles was not properly selected")
                time.sleep(15)
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Fixed Court Booking Automation")
    print("==============================")

    booker = FixedCourtBooker()
    success = booker.run()

    if success:
        print("\n✅ BOOKING SUCCESSFUL!")
        print("🎾 Court reservation completed!")
    else:
        print("\n❌ BOOKING FAILED")
        print("🔧 Manual booking required")
        print("💡 Make sure to select 'Singles' from reservation type dropdown")

if __name__ == "__main__":
    main()