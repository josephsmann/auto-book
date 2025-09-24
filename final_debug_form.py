#!/usr/bin/env python3
"""
Final debug to get exact form element details
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

def final_debug_form():
    username = os.getenv('ESC_USERNAME')
    password = os.getenv('ESC_PASSWORD')

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        # Login
        driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")
        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        username_field.send_keys(username)
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(password)
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        wait.until(EC.url_contains("Portal"))

        # Navigate to booking page
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        driver.get(booking_url)
        time.sleep(3)

        # Navigate forward 14 days
        for day in range(14):
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                next_button.click()
                time.sleep(1)
            except:
                break

        # Find and click 5:00 PM slot
        reserve_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Reserve') and contains(text(), '5:00 PM')]")
        if reserve_buttons:
            reserve_buttons[0].click()
            time.sleep(5)

            print("🔍 DETAILED FORM ELEMENT ANALYSIS")
            print("=" * 50)

            # Check specific form elements
            target_ids = ["ReservationTypeId", "StartTime", "Duration"]
            target_names = ["OwnersDropdown_input"]

            for element_id in target_ids:
                try:
                    element = driver.find_element(By.ID, element_id)
                    print(f"\n📋 Element ID '{element_id}':")
                    print(f"   Tag: {element.tag_name}")
                    print(f"   Type: {element.get_attribute('type')}")
                    print(f"   Class: {element.get_attribute('class')}")
                    print(f"   Value: {element.get_attribute('value')}")
                    print(f"   Displayed: {element.is_displayed()}")

                    if element.tag_name == "select":
                        options = element.find_elements(By.TAG_NAME, "option")
                        print(f"   Options ({len(options)}):")
                        for opt in options:
                            print(f"     - '{opt.text}' (value: '{opt.get_attribute('value')}')")
                    elif element.tag_name == "input":
                        print(f"   Input type: {element.get_attribute('type')}")

                except Exception as e:
                    print(f"\n❌ Element ID '{element_id}' not found: {e}")

            for element_name in target_names:
                try:
                    element = driver.find_element(By.NAME, element_name)
                    print(f"\n📋 Element NAME '{element_name}':")
                    print(f"   Tag: {element.tag_name}")
                    print(f"   Type: {element.get_attribute('type')}")
                    print(f"   Class: {element.get_attribute('class')}")
                    print(f"   Placeholder: {element.get_attribute('placeholder')}")
                    print(f"   Value: {element.get_attribute('value')}")
                    print(f"   Displayed: {element.is_displayed()}")

                except Exception as e:
                    print(f"\n❌ Element NAME '{element_name}' not found: {e}")

            # Look for any dropdowns that might be custom components
            print(f"\n🔍 Looking for custom dropdown components...")

            # Check for Kendo UI dropdowns (common in this type of app)
            kendo_dropdowns = driver.find_elements(By.CSS_SELECTOR, ".k-dropdown, .k-combobox, .k-dropdownlist")
            print(f"Found {len(kendo_dropdowns)} Kendo dropdowns")

            for i, dropdown in enumerate(kendo_dropdowns):
                if dropdown.is_displayed():
                    print(f"\n📋 Kendo Dropdown {i+1}:")
                    print(f"   Class: {dropdown.get_attribute('class')}")
                    print(f"   ID: {dropdown.get_attribute('id')}")

                    # Look for associated span or input
                    try:
                        span = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                        print(f"   Current value: '{span.text}'")
                    except:
                        pass

            # Check the page HTML around the reservation type
            print(f"\n📄 HTML around ReservationTypeId:")
            try:
                element = driver.find_element(By.ID, "ReservationTypeId")
                parent = element.find_element(By.XPATH, "..")
                print(f"Parent HTML: {parent.get_attribute('outerHTML')[:500]}...")
            except:
                print("Could not find ReservationTypeId")

            print(f"\n🚀 Manual check - browser staying open for inspection...")
            input("Press Enter after manual inspection...")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    final_debug_form()