#!/usr/bin/env python3
"""
Debug version of court booking script to inspect page elements
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

def debug_login():
    username = os.getenv('ESC_USERNAME')
    password = os.getenv('ESC_PASSWORD')

    if not username or not password:
        print("❌ ESC_USERNAME and ESC_PASSWORD must be set in .env file")
        return

    print(f"Using username: {username}")
    print("Setting up browser...")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Navigating to login page...")
        driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")

        # Wait for page to load and take a screenshot
        time.sleep(5)
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Look for various possible input field selectors
        possible_username_selectors = [
            "UserName",
            "username",
            "email",
            "Email",
            "[type='email']",
            "[type='text']",
            "[name='UserName']",
            "[name='username']",
            "[name='email']",
            "[id='UserName']",
            "[id='username']",
            "[id='email']"
        ]

        print("\nLooking for username field...")
        username_field = None
        for selector in possible_username_selectors:
            try:
                if selector.startswith("["):
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    element = driver.find_element(By.ID, selector)
                print(f"✅ Found username field with selector: {selector}")
                username_field = element
                break
            except NoSuchElementException:
                print(f"❌ No element found with selector: {selector}")

        if not username_field:
            print("\n📝 Available input elements on page:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for i, inp in enumerate(inputs):
                print(f"  {i+1}. Type: {inp.get_attribute('type')}, "
                      f"Name: {inp.get_attribute('name')}, "
                      f"ID: {inp.get_attribute('id')}, "
                      f"Class: {inp.get_attribute('class')}")

            print("\n📝 Page source (first 1000 chars):")
            print(driver.page_source[:1000])

            # Try to find any text input
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
            if text_inputs:
                username_field = text_inputs[0]
                print(f"Using first text/email input found")

        if username_field:
            print("Filling username...")
            username_field.clear()
            username_field.send_keys(username)

            # Look for password field
            possible_password_selectors = [
                "Password",
                "password",
                "[type='password']",
                "[name='Password']",
                "[name='password']",
                "[id='Password']",
                "[id='password']"
            ]

            print("Looking for password field...")
            password_field = None
            for selector in possible_password_selectors:
                try:
                    if selector.startswith("["):
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                    else:
                        element = driver.find_element(By.ID, selector)
                    print(f"✅ Found password field with selector: {selector}")
                    password_field = element
                    break
                except NoSuchElementException:
                    print(f"❌ No element found with selector: {selector}")

            if password_field:
                print("Filling password...")
                password_field.clear()
                password_field.send_keys(password)

                # Look for submit button
                possible_submit_selectors = [
                    "input[type='submit']",
                    "button[type='submit']",
                    "input[value='Log In']",
                    "input[value='Login']",
                    "button:contains('Log In')",
                    "button:contains('Login')",
                    "[class*='login']",
                    "[class*='submit']"
                ]

                print("Looking for submit button...")
                submit_button = None
                for selector in possible_submit_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"✅ Found submit button with selector: {selector}")
                        submit_button = element
                        break
                    except NoSuchElementException:
                        print(f"❌ No element found with selector: {selector}")

                if not submit_button:
                    print("\n📝 Available buttons on page:")
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
                    all_buttons = buttons + inputs

                    for i, btn in enumerate(all_buttons):
                        print(f"  {i+1}. Tag: {btn.tag_name}, "
                              f"Type: {btn.get_attribute('type')}, "
                              f"Value: {btn.get_attribute('value')}, "
                              f"Text: {btn.text}, "
                              f"Class: {btn.get_attribute('class')}")

                if submit_button:
                    print("Clicking submit button...")
                    submit_button.click()

                    # Wait and see what happens
                    time.sleep(5)
                    print(f"After login - URL: {driver.current_url}")
                    print(f"After login - Title: {driver.title}")

                    # Check for success indicators
                    success_indicators = [
                        "dashboard",
                        "user-menu",
                        "logout",
                        "profile"
                    ]

                    for indicator in success_indicators:
                        try:
                            element = driver.find_element(By.CLASS_NAME, indicator)
                            print(f"✅ Found success indicator: {indicator}")
                            print("🎉 Login appears successful!")
                            break
                        except NoSuchElementException:
                            continue
                    else:
                        print("❌ No success indicators found")

                        # Check for error messages
                        error_selectors = [
                            ".error",
                            ".alert",
                            ".message",
                            "[class*='error']",
                            "[class*='alert']"
                        ]

                        for selector in error_selectors:
                            try:
                                error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                for error in error_elements:
                                    if error.text.strip():
                                        print(f"❌ Error message: {error.text}")
                            except:
                                continue

        # Keep browser open for inspection
        input("\nPress Enter to close browser...")

    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to close browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_login()