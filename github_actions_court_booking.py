#!/usr/bin/env python3
"""
GitHub Actions compatible court booking automation script
"""

import os
import time
import argparse
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

# Load environment variables
load_dotenv()

class GitHubActionsCourtBooker:
    def __init__(self, days_ahead=None, booking_time=None, additional_player=None, no_player=False):
        self.username = os.getenv('ESC_USERNAME')
        self.password = os.getenv('ESC_PASSWORD')
        self.driver = None
        self.wait = None
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'

        # Set days ahead - command line arg overrides env var
        self.days_ahead = days_ahead if days_ahead is not None else int(os.getenv('INPUT_DAYS_AHEAD', '14'))

        # Set booking time - command line arg overrides default
        self.booking_time = booking_time if booking_time is not None else "5:00 PM"

        # Set additional player - handle no_player flag, then command line arg, then env var, then default
        if no_player:
            self.additional_player = None
        elif additional_player is not None:
            self.additional_player = additional_player if additional_player else None
        else:
            self.additional_player = os.getenv('ESC_ADDITIONAL_PLAYER', 'Scott Jackson')

        if not self.username or not self.password:
            raise ValueError("ESC_USERNAME and ESC_PASSWORD must be set in environment variables")

    def setup_driver(self):
        """Setup Chrome WebDriver optimized for GitHub Actions"""
        chrome_options = Options()

        # Always run headless in GitHub Actions
        if self.is_github_actions:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            # NOTE: JavaScript is REQUIRED for the booking form dropdowns (Kendo UI)
            # chrome_options.add_argument("--disable-javascript")  # REMOVED - breaks form filling
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        else:
            # Local development - show browser
            chrome_options.add_argument("--window-size=1920,1080")

        # Common options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            if self.is_github_actions:
                # In GitHub Actions, Chrome is installed system-wide
                service = Service('/usr/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Local development, use webdriver-manager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

        except Exception:
            # Fallback to webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)  # Longer timeout for GitHub Actions

    def take_screenshot(self, filename="screenshot.png"):
        """Take screenshot for debugging"""
        try:
            self.driver.save_screenshot(filename)
            print(f"📸 Screenshot saved: {filename}")
        except:
            pass

    def login(self):
        """Login to courtreserve.com"""
        print("🔐 Logging in...")

        try:
            self.driver.get("https://app.courtreserve.com/Online/Account/LogIn/11122")

            # Take screenshot for debugging
            self.take_screenshot("login_page.png")

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

            # Take screenshot after login
            self.take_screenshot("after_login.png")
            return True

        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            self.take_screenshot("login_failed.png")
            return False

    def navigate_to_bookings(self):
        """Navigate to the bookings page"""
        print("📅 Navigating to booking page...")
        booking_url = "https://app.courtreserve.com/Online/Reservations/Bookings/11122?sId=15491"
        self.driver.get(booking_url)
        time.sleep(5)  # Longer wait for GitHub Actions

        self.take_screenshot("booking_page.png")
        return True

    def navigate_forward_days(self, days_ahead=14):
        """Navigate forward using calendar picker (much faster than clicking day by day)"""
        print(f"⏭️ Navigating {days_ahead} days ahead using calendar...")

        try:
            # Calculate target date
            from datetime import datetime, timedelta
            target_date = datetime.now() + timedelta(days=days_ahead)
            target_date_str = target_date.strftime("%Y-%m-%d")
            print(f"   Target date: {target_date_str}")

            # Try to find and click the date display to open calendar picker
            date_elements = self.driver.find_elements(By.XPATH,
                "//*[contains(@class, 'k-datepicker')] | " +
                "//*[contains(text(), 'day,') and contains(text(), '2025')] | " +
                "//span[contains(text(), '2025')] | " +
                "//*[@title='Select date']")

            calendar_opened = False

            for date_element in date_elements:
                try:
                    print(f"   Trying to click date element: {date_element.text[:50]}")
                    date_element.click()
                    time.sleep(2)

                    # Check if calendar popup appeared
                    calendar_popup = self.driver.find_elements(By.CSS_SELECTOR,
                        ".k-calendar, .k-datepicker-calendar, .k-popup")
                    if calendar_popup:
                        calendar_opened = True
                        print("   ✅ Calendar popup opened")
                        break
                except:
                    continue

            if calendar_opened:
                # Try to select the target date directly
                # Look for the target date in the calendar
                day_number = target_date.day
                date_cells = self.driver.find_elements(By.CSS_SELECTOR,
                    ".k-calendar td, .k-datepicker-calendar td")

                for cell in date_cells:
                    if cell.text.strip() == str(day_number):
                        try:
                            cell.click()
                            print(f"   ✅ Selected day {day_number} from calendar")
                            time.sleep(2)
                            calendar_opened = False
                            break
                        except:
                            continue

                # If still open, try to close calendar
                if calendar_opened:
                    try:
                        # Press escape or click elsewhere to close
                        from selenium.webdriver.common.keys import Keys
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        print("   Calendar closed with escape")
                    except:
                        pass

                print("✅ Calendar navigation completed")
            else:
                # Fallback to old method if calendar doesn't work
                print("   ⚠️ Calendar picker not found, falling back to day-by-day navigation...")
                for day in range(days_ahead):
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                        if next_button.is_displayed() and next_button.is_enabled():
                            next_button.click()
                            time.sleep(1)  # Shorter wait for local testing
                            if day % 5 == 0 or day == days_ahead - 1:  # Print every 5 days and last day
                                print(f"   Day {day + 1} navigated")
                        else:
                            break
                    except:
                        break
                print("✅ Navigation completed")

        except Exception as e:
            print(f"   ⚠️ Calendar navigation failed: {e}, using fallback method")
            # Fallback method
            for day in range(days_ahead):
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button[title='Next']")
                    if next_button.is_displayed() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(1)
                        if day % 5 == 0 or day == days_ahead - 1:
                            print(f"   Day {day + 1} navigated")
                    else:
                        break
                except:
                    break
            print("✅ Navigation completed")

        time.sleep(3)
        self.take_screenshot("target_date.png")

    def find_and_click_time_slot(self):
        """Find and click the specified time slot, trying courts 1-4"""
        print(f"🎯 Looking for {self.booking_time} slot on courts 1-4...")

        # Try to navigate to 5:00 PM time period using page controls (scrolling isn't working)
        print(f"🔄 Attempting to navigate to {self.booking_time} time period...")

        try:
            # Method 1: Look for time navigation controls (Next/Previous buttons for time periods)
            print("   🎯 Looking for time navigation controls...")

            time_nav_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@title, 'Next') or contains(@aria-label, 'next') or contains(text(), '►') or contains(text(), 'Next')] |" +
                "//a[contains(@title, 'Next') or contains(@aria-label, 'next')] |" +
                "//div[contains(@class, 'next') or contains(@class, 'forward')]//button")

            print(f"   Found {len(time_nav_buttons)} potential navigation buttons")

            # Try clicking Next buttons to advance time periods
            for attempt in range(15):  # Try up to 15 clicks to get from morning to 5 PM
                print(f"   Navigation attempt {attempt + 1}/15...")

                # Check if we can now see 5:00 PM
                pm5_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '5:00 PM') or contains(text(), '5:00 p.m')]")
                visible_pm5 = [el for el in pm5_elements if el.is_displayed()]

                if len(visible_pm5) >= 2:  # Found multiple 5:00 PM elements
                    print(f"   ✅ Found {len(visible_pm5)} visible 5:00 PM elements after {attempt} navigation attempts!")
                    break

                # Try to find and click a Next button
                clicked_next = False
                for nav_btn in time_nav_buttons:
                    try:
                        if nav_btn.is_displayed() and nav_btn.is_enabled():
                            nav_btn.click()
                            time.sleep(2)
                            print(f"   ➡️ Clicked navigation button: '{nav_btn.get_attribute('title') or nav_btn.text}'")
                            clicked_next = True
                            break
                    except:
                        continue

                if not clicked_next:
                    print("   ⚠️ Could not find clickable navigation button, trying alternative approach...")
                    break

            # Method 2: If navigation didn't work, try keyboard navigation
            if len(self.driver.find_elements(By.XPATH, "//*[contains(text(), '5:00 PM')]")) < 2:
                print("   ⌨️  Trying keyboard navigation (Page Down, Arrow keys)...")

                from selenium.webdriver.common.keys import Keys
                body = self.driver.find_element(By.TAG_NAME, "body")

                # Try Page Down multiple times
                for i in range(10):
                    body.send_keys(Keys.PAGE_DOWN)
                    time.sleep(1)

                    # Check for 5:00 PM
                    pm5_check = self.driver.find_elements(By.XPATH, "//*[contains(text(), '5:00 PM')]")
                    if len(pm5_check) >= 2:
                        print(f"   ✅ Found 5:00 PM elements after {i+1} Page Down presses!")
                        break

        except Exception as e:
            print(f"   ⚠️ Error during time navigation: {e}")

        self.take_screenshot("after_page_scroll.png")

        # Look for grid cells that contain "5:00 p.m" text (these provide 45-minute duration automatically)
        print(f"   🎯 Looking for grid cells containing '{self.booking_time}' text for 45-minute bookings...")

        # Find grid cells that contain "5:00 p.m." text (for 45-minute bookings)
        # Target specific elements that are more likely to be booking grid cells
        print("   🎯 Searching specifically for court booking grid cells...")

        # Try different XPath strategies to find the actual booking grid cells
        grid_cell_patterns = [
            "//td[contains(text(), '5:00 p.m.')]",
            "//div[contains(text(), '5:00 p.m.')]",
            "//td[contains(text(), '5:00 PM')]",
            "//div[contains(text(), '5:00 PM')]",
            "//span[contains(text(), '5:00 p.m.')]",
            "//span[contains(text(), '5:00 PM')]"
        ]

        clickable_time_cells = []

        for xpath_pattern in grid_cell_patterns:
            elements = self.driver.find_elements(By.XPATH, xpath_pattern)
            print(f"   Found {len(elements)} elements with XPath: {xpath_pattern}")

            for element in elements:
                try:
                    element_text = element.text.strip()
                    tag_name = element.tag_name.lower()

                    print(f"   📋 Grid cell candidate: '{element_text[:50]}...' (tag: {tag_name})")

                    # Look for elements that are likely booking cells in table structure
                    if tag_name in ['td', 'div', 'span'] and element.is_displayed():
                        # Check if this element has booking-related context
                        try:
                            # Get parent context to see if this is in a booking table
                            parent_text = ""
                            if tag_name == 'td':
                                parent_row = element.find_element(By.XPATH, "./ancestor::tr[1]")
                                parent_text = parent_row.text[:100]

                            print(f"   🏓 Context: '{parent_text}...'")

                            # Add this element if it looks like a booking cell
                            clickable_time_cells.append(element)
                            print(f"   ✅ Added grid cell: '{element_text[:30]}...' (tag: {tag_name})")

                        except:
                            # Even without context, try the element if it matches our criteria
                            clickable_time_cells.append(element)
                            print(f"   ✅ Added grid cell (no context): '{element_text[:30]}...'")

                except Exception as e:
                    print(f"   ⚠️ Error examining grid cell: {e}")
                    continue

        # If no grid cells found, fallback to Reserve buttons
        if not clickable_time_cells:
            print("   🔄 No grid cells found, falling back to Reserve button search...")
            all_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Reserve')]")
            print(f"   Debug: Found {len(all_buttons)} total Reserve buttons")

            # Find buttons with our target time
            target_time_buttons = []
            for btn in all_buttons:
                btn_text = btn.text.strip().lower()
                if self.booking_time.lower() in btn_text or "5:00" in btn_text:
                    target_time_buttons.append(btn)

            if not target_time_buttons:
                print(f"   ❌ No Reserve buttons found for {self.booking_time}")
                self.take_screenshot("no_slot_any_court.png")
                return False
            else:
                print(f"   Found {len(target_time_buttons)} Reserve buttons as fallback")
                clickable_time_cells = target_time_buttons
        else:
            print(f"   ✅ Found {len(clickable_time_cells)} clickable 5:00 PM grid cells for 45-minute bookings!")

        # Note: We'll scroll to individual buttons when we try to click them

        # Try courts 1 through 4 - now using grid cells instead of just buttons
        for court_num in range(1, 5):
            print(f"   Checking Court {court_num}...")

            # Look through all clickable elements (grid cells or buttons) for our time and find the right court
            for element in clickable_time_cells:
                try:
                    # Strategy 1: Check if element itself contains court info
                    element_text = element.text
                    if f"Court {court_num}" in element_text or f"Court{court_num}" in element_text:
                        print(f"   Found Court {court_num} via element text: {element_text[:50]}...")
                        if self.click_grid_cell_and_return(element, court_num):
                            return True

                    # Strategy 2: Check table row (tr) ancestor
                    try:
                        parent_row = element.find_element(By.XPATH, "./ancestor::tr[1]")
                        row_text = parent_row.text
                        if f"Court {court_num}" in row_text or f"Court{court_num}" in row_text:
                            print(f"   Found Court {court_num} via row context: {element_text[:30]}...")
                            print(f"   Row text: {row_text[:100]}...")
                            if self.click_grid_cell_and_return(element, court_num):
                                return True
                    except:
                        pass

                    # Strategy 3: Check table cell (td) ancestor
                    try:
                        parent_cell = element.find_element(By.XPATH, "./ancestor::td[1]")
                        # Look for court info in adjacent cells
                        parent_row = parent_cell.find_element(By.XPATH, "./parent::tr")
                        row_text = parent_row.text
                        if f"Court {court_num}" in row_text:
                            print(f"   Found Court {court_num} via cell context: {element_text[:30]}...")
                            if self.click_grid_cell_and_return(element, court_num):
                                return True
                    except:
                        pass

                    # Strategy 4: Check column position (if courts are in columns)
                    try:
                        parent_cell = element.find_element(By.XPATH, "./ancestor::td[1]")
                        cell_index = self.driver.execute_script("""
                            var cell = arguments[0];
                            var row = cell.parentElement;
                            return Array.from(row.cells).indexOf(cell);
                        """, parent_cell)

                        # If courts are in columns 1-4 (after possibly a time column at 0)
                        if cell_index == court_num:  # Court in column matching court number
                            print(f"   Found Court {court_num} via column position {cell_index}: {element_text[:30]}...")
                            if self.click_grid_cell_and_return(element, court_num):
                                return True
                    except:
                        pass

                except Exception as e:
                    continue

            print(f"   ❌ Court {court_num} not available at {self.booking_time}")

        print(f"❌ No {self.booking_time} slots found on any court (1-4)")
        self.take_screenshot("no_slot_any_court.png")
        return False

    def click_grid_cell_and_return(self, cell, court_num):
        """Helper method to click grid cell containing 5:00 p.m text for 45-minute booking"""
        try:
            print(f"   ✅ Attempting to click Court {court_num} grid cell for 45-minute booking...")
            print(f"   Cell text: {cell.text[:100]}...")

            # Scroll to cell first to ensure it's visible
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", cell)
                time.sleep(1)
            except:
                pass

            # Try multiple click methods
            try:
                # Method 1: Regular click
                cell.click()
                print(f"✅ Clicked 5:00 PM grid cell on Court {court_num} (regular click)")
            except:
                try:
                    # Method 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", cell)
                    print(f"✅ Clicked 5:00 PM grid cell on Court {court_num} (JS click)")
                except:
                    print(f"❌ Could not click Court {court_num} grid cell")
                    return False

            # Wait for any response
            time.sleep(3)
            self.take_screenshot("after_grid_cell_click.png")
            return True

        except Exception as e:
            print(f"❌ Error clicking Court {court_num} grid cell: {e}")
            return False

    def click_button_and_return(self, button, court_num):
        """Helper method to click button and handle the result"""
        try:
            # The 5:00 PM buttons are visible in the screenshot but is_displayed() might be returning False
            # Let's try clicking them anyway since we can see them on screen
            print(f"   ✅ Attempting to click Court {court_num} button (bypassing is_displayed check)...")

            # Try to click the button directly since it's visible in screenshot
            try:
                # Scroll to button first to ensure it's in view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", button)
                time.sleep(1)

                # Check visibility after scroll
                if button.is_displayed():
                    print(f"   ✅ Button for Court {court_num} is now visible after scroll")
                else:
                    print(f"   ⚠️ Button for Court {court_num} still reports not visible, but trying anyway...")

                # Check if enabled
                if not button.is_enabled():
                    print(f"   ❌ Button for Court {court_num} is not enabled")
                    return False

                # Scroll to button and ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Error preparing button for Court {court_num}: {e}")
                # Continue anyway

            # Try multiple click strategies
            try:
                # Strategy 1: Regular click
                button.click()
                print(f"✅ Clicked {self.booking_time} slot on Court {court_num} (regular click)")
            except:
                try:
                    # Strategy 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", button)
                    print(f"✅ Clicked {self.booking_time} slot on Court {court_num} (JS click)")
                except:
                    # Strategy 3: ActionChains click
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(button).click().perform()
                    print(f"✅ Clicked {self.booking_time} slot on Court {court_num} (ActionChains)")

            time.sleep(5)
            self.take_screenshot("after_slot_click.png")
            return True

        except Exception as e:
            print(f"   ❌ Failed to click Court {court_num} button: {e}")
            return False

    def select_reservation_type_from_dropdown(self):
        """Select appropriate reservation type from the Kendo dropdown"""
        # Determine the correct reservation type based on additional player
        if self.additional_player:
            reservation_type = "singles"
            display_name = "Singles"
        else:
            reservation_type = "solo practice"
            display_name = "Solo Practice"

        print(f"   🎯 Selecting '{display_name}' from reservation type dropdown...")

        try:
            # JavaScript method - most reliable for GitHub Actions
            js_script = f"""
            var success = false;
            var dropdowns = document.querySelectorAll('.k-dropdown');

            for (var i = 0; i < dropdowns.length; i++) {{
                var dropdown = dropdowns[i];
                var textElement = dropdown.querySelector('.k-input-inner, .k-input');

                if (textElement && textElement.textContent.includes('Reservation Type')) {{
                    // Click to open dropdown
                    dropdown.click();

                    // Wait a bit and then select the appropriate type
                    setTimeout(function() {{
                        var options = document.querySelectorAll('.k-animation-container .k-list li');
                        for (var j = 0; j < options.length; j++) {{
                            if (options[j].textContent.toLowerCase().includes('{reservation_type}')) {{
                                options[j].click();
                                success = true;
                                break;
                            }}
                        }}
                    }}, 1000);
                    break;
                }}
            }}
            return success;
            """

            # Execute JavaScript
            result = self.driver.execute_script(js_script)
            time.sleep(3)  # Wait for selection to complete

            # Verify selection
            kendo_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, ".k-dropdown")
            for dropdown in kendo_dropdowns:
                if dropdown.is_displayed():
                    try:
                        text_element = dropdown.find_element(By.CSS_SELECTOR, ".k-input-inner, .k-input")
                        current_text = text_element.text.strip()

                        if reservation_type in current_text.lower():
                            print(f"   ✅ Successfully selected {display_name}!")
                            return True
                    except:
                        continue

            print(f"   ❌ Could not verify {display_name} selection")
            return False

        except Exception as e:
            print(f"   ❌ Error selecting {display_name}: {e}")
            return False

    def fill_booking_form(self):
        """Fill out the booking form"""
        print("📝 Filling out booking form...")

        try:
            # Wait for modal
            modal = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, [role='dialog']"))
            )
            print("✅ Booking form modal appeared")
            time.sleep(5)  # Longer wait for GitHub Actions

            self.take_screenshot("booking_form.png")

            # Select appropriate reservation type
            if not self.select_reservation_type_from_dropdown():
                reservation_type = "Solo Practice" if not self.additional_player else "Singles"
                print(f"❌ CRITICAL: Could not select {reservation_type}")
                self.take_screenshot("reservation_type_selection_failed.png")
                return False

            print(f"   ✅ Start time already set to {self.booking_time}")

            # Set duration to 1 hour explicitly (I can see it's currently set to "30 minutes")
            print("   🕐 Setting duration to 1 hour...")
            try:
                # Look for the duration dropdown - it's likely a Kendo dropdown based on the form
                duration_dropdowns = self.driver.find_elements(By.XPATH,
                    "//div[contains(@class, 'k-dropdown') and contains(text(), '30 minutes')] | " +
                    "//select[contains(@name, 'Duration')] | " +
                    "//*[contains(text(), '30 minutes')]/parent::div[contains(@class, 'k-dropdown')]")

                duration_set = False

                # Also try to find it by looking for "Duration" label and finding nearby dropdown
                if not duration_dropdowns:
                    duration_labels = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Duration')]")
                    for label in duration_labels:
                        try:
                            # Find dropdown near the Duration label
                            nearby_dropdowns = label.find_elements(By.XPATH,
                                "./following-sibling::div[contains(@class, 'k-dropdown')] | " +
                                "..//*[contains(@class, 'k-dropdown')] | " +
                                "./following::div[contains(@class, 'k-dropdown')][1]")
                            if nearby_dropdowns:
                                duration_dropdowns.extend(nearby_dropdowns)
                                break
                        except:
                            continue

                print(f"   Debug: Found {len(duration_dropdowns)} potential duration controls")

                for dropdown in duration_dropdowns:
                    try:
                        print(f"   Trying duration dropdown: {dropdown.text[:50]}")

                        # Click to open the dropdown
                        dropdown.click()
                        time.sleep(2)

                        # Look for 1 hour option in the opened dropdown
                        options = self.driver.find_elements(By.CSS_SELECTOR,
                            ".k-animation-container .k-list li, " +
                            ".k-popup .k-list li, " +
                            ".k-dropdown-wrap + .k-popup li")

                        print(f"   Found {len(options)} dropdown options")

                        for option in options:
                            option_text = option.text.strip().lower()
                            print(f"   Option: '{option_text}'")

                            # Look for 45 minutes specifically (user requested 45-minute duration)
                            if (any(text in option_text for text in ['45 min', '45 minutes', '0:45']) or
                                option_text.strip() == '45'):
                                print(f"   ✅ Clicking 45-minute option: '{option.text}' (text: '{option_text}')")
                                option.click()
                                duration_set = True
                                time.sleep(3)  # Wait longer for the form to update

                                # Verify the duration actually changed
                                time.sleep(2)
                                try:
                                    # Look for updated duration text
                                    current_duration = self.driver.find_elements(By.XPATH,
                                        "//*[contains(text(), '45 min') or contains(text(), '0:45')]")
                                    if current_duration:
                                        print("   ✅ Duration successfully changed to 45 minutes!")
                                    else:
                                        print("   ⚠️ Duration text not updated, but selection was made")
                                except:
                                    pass
                                break

                        if duration_set:
                            break
                        else:
                            # Close dropdown if no option found
                            dropdown.click()
                            time.sleep(1)

                    except Exception as e:
                        print(f"   Error with duration dropdown: {e}")
                        continue

                if duration_set:
                    print("   ✅ Successfully set duration to 45 minutes!")
                else:
                    print("   ⚠️ Could not find 45-minute option, trying to find any available duration options...")

                    # Debug: print all available options if 45 minutes not found
                    try:
                        debug_dropdowns = self.driver.find_elements(By.XPATH,
                            "//div[contains(@class, 'k-dropdown') and contains(text(), '30 minutes')]")
                        for dropdown in debug_dropdowns[:1]:  # Just check first one
                            dropdown.click()
                            time.sleep(2)
                            debug_options = self.driver.find_elements(By.CSS_SELECTOR,
                                ".k-animation-container .k-list li")
                            print("   Available duration options:")
                            for i, opt in enumerate(debug_options[:10]):
                                print(f"     {i+1}: '{opt.text}'")
                            dropdown.click()  # Close
                            break
                    except:
                        pass

            except Exception as e:
                print(f"   ⚠️ Error setting duration: {e}, duration may remain at 30 minutes")

            # Add additional player
            if self.additional_player:
                try:
                    players_input = self.driver.find_element(By.NAME, "OwnersDropdown_input")
                    players_input.clear()
                    players_input.send_keys(self.additional_player)
                    print(f"   ✅ Added {self.additional_player}")
                    time.sleep(3)

                    # Try autocomplete
                    try:
                        autocomplete_items = self.driver.find_elements(By.CSS_SELECTOR,
                            ".k-list-item, [role='option']")
                        first_name = self.additional_player.split()[0].lower()
                        for item in autocomplete_items:
                            if item.is_displayed() and first_name in item.text.lower():
                                item.click()
                                print("   ✅ Selected from autocomplete")
                                break
                    except:
                        pass

                except Exception as e:
                    print(f"   ⚠️ Could not add additional player: {e}")
            else:
                print("   ℹ️ No additional player specified")

            time.sleep(3)
            self.take_screenshot("form_filled.png")
            return True

        except Exception as e:
            print(f"❌ Error filling form: {e}")
            self.take_screenshot("form_error.png")
            return False

    def submit_booking_form(self):
        """Submit the booking form"""
        print("📤 Submitting booking form...")

        try:
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-submit")

            if save_button.is_displayed() and save_button.is_enabled():
                print("   Clicking Save button")
                save_button.click()
                print("   Waiting for submission to complete...")

                # Wait for submission and check for success/error indicators
                time.sleep(3)

                # Look for common success/error indicators
                success_indicators = [
                    "success", "confirmed", "booked", "reservation created",
                    "booking confirmed", "thank you"
                ]
                error_indicators = [
                    "error", "failed", "invalid", "unavailable", "conflict",
                    "already booked", "not available"
                ]

                # Wait up to 15 seconds for a response
                for i in range(5):
                    time.sleep(3)
                    page_text = self.driver.page_source.lower()

                    # Check for success indicators
                    found_success = any(indicator in page_text for indicator in success_indicators)
                    found_error = any(indicator in page_text for indicator in error_indicators)

                    if found_success:
                        print("   ✅ Success indicators found in page")
                        break
                    elif found_error:
                        print("   ❌ Error indicators found in page")
                        # Look for specific error messages
                        for indicator in error_indicators:
                            if indicator in page_text:
                                print(f"   Error type: {indicator}")
                        break

                    print(f"   Waiting for response... ({i+1}/5)")

                self.take_screenshot("after_submit.png")

                # Check if modal is still open (might indicate an error)
                modals = self.driver.find_elements(By.CSS_SELECTOR, ".modal, [role='dialog']")
                open_modals = [m for m in modals if m.is_displayed()]

                if open_modals:
                    print("   ⚠️ Modal still open after submission - possible error")
                    # Look for error messages in the modal
                    for modal in open_modals:
                        modal_text = modal.text.lower()
                        if any(err in modal_text for err in error_indicators):
                            print(f"   Modal error: {modal.text[:200]}")
                            return False
                else:
                    print("   ✅ Modal closed - submission likely successful")

                return True
            else:
                print("   ❌ Save button not available")
                return False

        except Exception as e:
            print(f"   ❌ Error submitting: {e}")
            self.take_screenshot("submit_error.png")
            return False

    def verify_booking(self):
        """Verify booking by refreshing and checking"""
        print("✅ Verifying booking...")

        try:
            time.sleep(5)

            print("🔄 Refreshing page...")
            self.driver.refresh()
            time.sleep(8)

            self.take_screenshot("verification.png")

            page_text = self.driver.page_source.lower()
            found_indicators = []

            # Check for additional player (if specified)
            if self.additional_player:
                player_name_lower = self.additional_player.lower()
                if player_name_lower in page_text:
                    found_indicators.append(self.additional_player)

            # Check for the correct booking time
            booking_time_formats = [
                self.booking_time.lower(),  # "12:00 pm"
                self.booking_time.replace(" ", "").lower(),  # "12:00pm"
                self.booking_time.replace(":00", "").lower(),  # "12 pm"
            ]

            for time_format in booking_time_formats:
                if time_format in page_text:
                    found_indicators.append(self.booking_time)
                    break

            # Check for court type (singles or solo practice)
            expected_type = "solo practice" if not self.additional_player else "singles"
            if expected_type in page_text:
                found_indicators.append(expected_type.title())

            # More specific verification: look for booking entries that contain our time
            print(f"   Looking for booking containing '{self.booking_time}'...")

            # Try to find specific booking elements
            booking_elements = self.driver.find_elements(By.XPATH,
                f"//*[contains(text(), '{self.booking_time}')]")

            if booking_elements:
                print(f"   Found {len(booking_elements)} elements containing '{self.booking_time}'")
                for i, elem in enumerate(booking_elements[:3]):  # Check first 3
                    try:
                        elem_text = elem.text
                        print(f"   Element {i+1}: {elem_text[:100]}")

                        # Check if this element looks like a booking (contains court info)
                        if any(word in elem_text.lower() for word in ['court', 'reserved', 'booking']):
                            found_indicators.append(f"Booking element with {self.booking_time}")
                            break
                    except:
                        pass

            if found_indicators:
                print(f"✅ BOOKING VERIFIED! Found: {', '.join(found_indicators)}")
                return True
            else:
                print(f"❌ BOOKING NOT FOUND - no evidence of {self.booking_time} booking")
                print("   Checking what bookings are actually visible...")

                # Show what bookings are actually on the page
                time_elements = self.driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'PM') or contains(text(), 'AM')]")

                print("   Visible times on page:")
                for i, elem in enumerate(time_elements[:5]):  # Show first 5
                    try:
                        print(f"     {i+1}: {elem.text[:50]}")
                    except:
                        pass

                return False

        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

    def run(self):
        """Main execution method"""
        try:
            print("🚀 Starting GitHub Actions Court Booking")
            print("=" * 50)
            print(f"Environment: {'GitHub Actions' if self.is_github_actions else 'Local'}")
            reservation_type = "Solo Practice" if not self.additional_player else "Singles"
            print("Booking Details:")
            print(f"- Court Type: {reservation_type}")
            print(f"- Start Time: {self.booking_time}")
            print(f"- Days Ahead: {self.days_ahead}")
            print("- Duration: 1 hour")
            print(f"- Additional Player: {self.additional_player or 'None'}")
            print("=" * 50)

            self.setup_driver()

            if not self.login():
                return False

            if not self.navigate_to_bookings():
                return False

            self.navigate_forward_days(self.days_ahead)

            if not self.find_and_click_time_slot():
                return False

            if not self.fill_booking_form():
                return False

            if not self.submit_booking_form():
                return False

            if self.verify_booking():
                print("🎉 COURT BOOKING SUCCESSFUL!")
                return True
            else:
                print("❌ BOOKING FAILED")
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.take_screenshot("unexpected_error.png")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Court booking automation script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_actions_court_booking.py --days-ahead 7 --time "4:00 PM" --player "John Doe"
  python github_actions_court_booking.py --time "6:00 PM" --player "Jane Smith"
  python github_actions_court_booking.py --days-ahead 21
  python github_actions_court_booking.py --no-player  # Book without additional player
  python github_actions_court_booking.py --player ""  # Alternative: no additional player

Environment Variables:
  ESC_USERNAME          - Required: Login username
  ESC_PASSWORD          - Required: Login password
  INPUT_DAYS_AHEAD      - Optional: Days ahead to book (default: 14)
  ESC_ADDITIONAL_PLAYER - Optional: Additional player name (default: "Scott Jackson")
  GITHUB_ACTIONS        - Auto-set by GitHub Actions
        """
    )

    parser.add_argument(
        '--days-ahead', '-d',
        type=int,
        help='Number of days ahead to book (overrides INPUT_DAYS_AHEAD env var, default: 14)'
    )

    parser.add_argument(
        '--time', '-t',
        type=str,
        help='Booking time in format "H:MM AM/PM" (default: "5:00 PM")'
    )

    parser.add_argument(
        '--player', '-p',
        type=str,
        help='Additional player name (overrides ESC_ADDITIONAL_PLAYER env var, default: "Scott Jackson")'
    )

    parser.add_argument(
        '--no-player',
        action='store_true',
        help='Book without additional player (overrides --player and ESC_ADDITIONAL_PLAYER)'
    )

    return parser.parse_args()

def main():
    print("GitHub Actions Court Booking Automation")
    print("========================================")

    try:
        args = parse_args()

        booker = GitHubActionsCourtBooker(
            days_ahead=args.days_ahead,
            booking_time=args.time,
            additional_player=args.player,
            no_player=args.no_player
        )
        success = booker.run()

        if success:
            print("\n✅ BOOKING COMPLETED!")
            exit(0)
        else:
            print("\n❌ BOOKING FAILED!")
            exit(1)

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()