from patchright.sync_api import Page, sync_playwright, TimeoutError as PlaywrightTimeoutError, BrowserType
import time # Import time for potential pauses

NEXUS_URL="https://www.nexusmods.com/"



def download_mod_manually(page: Page):
    """
    Initiates the manual download process for a mod on the Nexus Mod page.
    The page must have a specific Nexus mod page already open before calling this function.
    The function clicks through the download process including the slow download option.
    Args:
        page (Page): The Playwright Page object with an open Nexus mod page.
    Raises:
        TimeoutError: If any of the expected elements don't appear within timeout.
    """
    
    download_popup_button = page.locator('#action-manual')
    download_popup_button.click()
    # Wait for the download popup to appear
    page.wait_for_selector('.mfp-content', timeout=5000)
    download_button = page.locator('a.btn:has-text("Download")')
    download_button.click()
    
    time.sleep(2)  # give some time to see stuff
    # Wait for the slow download page to load and button to be visible
    print("Waiting for slow download button...")
    page.wait_for_selector('#slowDownloadButton', timeout=10000)
    slow_download_button = page.locator('#slowDownloadButton')
    slow_download_button.click()
    print("Clicked slow download button")


global mods
mods = [
    "Cloaks of Skyrim",
    "Valhalla Combat",
    "SkyUI_5_2_SE",
    "A Mod That Doesn't Exist Hopefully" # Example of a mod that might not be found
]

# Use a standard launch instead of connect_over_cdp for simplicity
# Set headless=False to watch the browser execution

import os
with sync_playwright() as p:
    user_data_dir=f'{os.environ['HOME']}/.config/google-chrome/Default'
    #browser = p.chromium.connect_over_cdp("http://localhost:9222")
    browser = p.chromium.launch_persistent_context(
        executable_path='/bin/google-chrome-stable',
        user_data_dir=user_data_dir,
        headless=False,  # See what's going on
        args=["--start-maximized --remote-debugging-port=9222"],
        channel="chrome",
        no_viewport=True
    )
    page = browser.new_page()

    for mod in mods:
        page = browser.new_page()
        print(f"\n--- Searching Google for: {mod} ---")
        try:
            # 1. Go to Google
            print("Navigating to Google...")
            page.goto("https://www.google.com/")

            # 2. Handle potential Google cookie consent (adjust selector if needed)
            # This tries to click the 'Accept all' button if it appears within 5 seconds
            try:
                print("Attempting to accept Google cookies...")
                page.locator('button:has-text("Accept all")').click(timeout=2000)
                print("Cookies accepted (if present).")
            except PlaywrightTimeoutError:
                print("No cookie consent banner found or already accepted.")
            except Exception as e:
                 print(f"An unexpected error occurred while handling cookies: {e}") # Catch other errors

            # 3. Construct and enter the search query
            search_query = f"{mod} nexus mods skyrim special edition"
            print(f"Entering search query: '{search_query}'")

            # Google's search input is often a textarea with name='q'
            search_input_selector = 'textarea[name="q"]'
            page.wait_for_selector(search_input_selector)
            page.fill(search_input_selector, search_query)

            # 4. Submit the search (by pressing Enter)
            page.press(search_input_selector, 'Enter')
            print("Search submitted.")

            # 5. Wait for search results to load
            # Wait for the main search results container to be visible
            page.wait_for_selector('div#search', timeout=15000) # Increased timeout just in case
            print("Search results page loaded.")

            # 6. Find the first Nexus Mods link
            nexus_link_found = False
            # Get all potential link elements within the main search results area
            # Note: This selector might need minor adjustments based on Google's layout variations
            search_result_links = page.locator('div#search a').all()

            print(f"Checking {len(search_result_links)} potential result links...")

            for link_locator in search_result_links:
                # Get the href attribute of the link
                href = link_locator.get_attribute('href')

                # Check if href exists and starts with the Nexus Mods domain
                if href and href.startswith(NEXUS_URL):
                    print(f"Found Nexus Mods link: {href}")
                    # 7. Click the link
                    link_locator.click()
                    nexus_link_found = True
                    print(f"Navigated to: {page.url}") # Confirm navigation URL
                    # Optional: Wait for the new page to start loading
                    # page.wait_for_load_state('domcontentloaded')
                    download_mod_manually(page) # Call the download function
                    break # Exit the loop once the first valid link is found

            if not nexus_link_found:
                print(f"ERROR: No nexusmods.com link found in search results for '{mod}'.")
                # Optionally, you might want to take a screenshot here for debugging
                # page.screenshot(path=f"no_link_found_{mod.replace(' ', '_')}.png")

        except PlaywrightTimeoutError as e:
             print(f"Timeout error during search for '{mod}': {e}")
             # Optionally, take a screenshot on timeout
             # page.screenshot(path=f"timeout_error_{mod.replace(' ', '_')}.png")
        except Exception as e:
            print(f"An unexpected error occurred during the search for '{mod}': {e}")
            # Optionally, take a screenshot on general error
            # page.screenshot(path=f"general_error_{mod.replace(' ', '_')}.png")


        # Optional: Add a short pause between processing each mod
        # This makes it easier to follow visually when headless=False
        # and can help prevent hitting rate limits or looking like a bot too quickly.
        time.sleep(3) # Wait for 3 seconds

    # The browser is automatically closed when exiting the 'with' block
    print("\n--- Script finished. ---")