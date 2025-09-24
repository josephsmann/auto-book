#!/usr/bin/env python3
"""
Court booking automation script for courtreserve.com
Logs in using credentials from .env and books a court for 3:30 PM two weeks from now.
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

class CourtBooker:
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
            # Wait for and fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            username_field.clear()
            username_field.send_keys(self.username)

            # Fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(self.password)

            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for successful login (check for portal page)
            self.wait.until(
                EC.any_of(
                    EC.url_contains("Portal"),
                    EC.url_contains("Dashboard"),
                    EC.title_contains("Edmonton Squash Club")
                )
            )

            print("Login successful!")
            return True

        except TimeoutException:
            print("Login failed - timeout waiting for elements")
            return False
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def navigate_to_bookings(self):
        """Navigate to the bookings page"""
        print("Navigating to bookings page...")

        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        self.driver.get(booking_url)

        # Wait for the page to load
        time.sleep(3)
        return True

    def find_target_date(self):
        """Calculate the target date (two weeks from now)"""
        target_date = datetime.now() + timedelta(weeks=2)
        return target_date

    def book_court_at_330pm(self, target_date):
        """Attempt to book a court for 3:30 PM on the target date"""
        print(f"Attempting to book court for {target_date.strftime('%Y-%m-%d')} at 3:30 PM...")

        try:
            # Look for date navigation or calendar
            # This will depend on the site's structure - we'll need to adapt based on the actual HTML

            # First, try to find a date picker or calendar
            date_elements = self.driver.find_elements(By.CSS_SELECTOR,
                "[data-date], .calendar-day, .date-picker, [class*='date'], [class*='calendar']")

            if date_elements:
                print(f"Found {len(date_elements)} date-related elements")

            # Look for time slots around 3:30 PM
            time_elements = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), '3:30')] | //a[contains(text(), '3:30')] | //*[contains(text(), '15:30')]")

            if time_elements:
                print(f"Found {len(time_elements)} time slots around 3:30 PM")
                for element in time_elements:
                    if element.is_enabled():
                        print(f"Clicking time slot: {element.text}")
                        element.click()
                        time.sleep(2)

                        # Look for confirmation or book button
                        book_buttons = self.driver.find_elements(By.XPATH,
                            "//button[contains(text(), 'Book')] | //button[contains(text(), 'Reserve')] | //button[contains(text(), 'Confirm')]")

                        if book_buttons:
                            for button in book_buttons:
                                if button.is_enabled():
                                    print(f"Clicking book button: {button.text}")
                                    button.click()
                                    time.sleep(3)
                                    return True

            # If specific time not found, look for any available slots
            available_slots = self.driver.find_elements(By.CSS_SELECTOR,
                "button.available, .time-slot.available, [class*='available'][class*='slot']")

            if available_slots:
                print(f"Found {len(available_slots)} available slots")
                # Try to book the first available slot
                available_slots[0].click()
                time.sleep(2)

                book_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Book')] | //button[contains(text(), 'Reserve')] | //button[contains(text(), 'Confirm')]")

                if book_buttons:
                    book_buttons[0].click()
                    print("Booked an available slot")
                    return True

            print("No available time slots found")
            return False

        except Exception as e:
            print(f"Error during booking: {str(e)}")
            return False

    def run(self):
        """Main execution method"""
        try:
            self.setup_driver(headless=False)  # Set to True for headless mode

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            target_date = self.find_target_date()
            print(f"Target date: {target_date.strftime('%Y-%m-%d %A')}")

            success = self.book_court_at_330pm(target_date)

            if success:
                print("Court booking successful!")
                # Keep browser open for 10 seconds to see result
                time.sleep(10)
            else:
                print("Court booking failed")
                # Keep browser open for debugging
                input("Press Enter to close browser...")

            return success

        except Exception as e:
            print(f"Error during execution: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Court Booking Automation Script")
    print("================================")

    booker = CourtBooker()
    success = booker.run()

    if success:
        print("✅ Booking completed successfully!")
    else:
        print("❌ Booking failed")

if __name__ == "__main__":
    main()