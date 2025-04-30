from patchright.sync_api import Page, sync_playwright,ElementHandle, TimeoutError
import time # Import time for potential pauses

NEXUS_URL="https://www.nexusmods.com/"
DOWNLOAD_DIRECTORY='./'


def navigate_to_download(page: Page):
    # Use Locator instead of query_selector
    download_popup_button = page.locator('#action-manual')


    download_popup_button.wait_for(state="visible", timeout=3000)
    time.sleep(1)  # if required by site animation/JS
    download_popup_button.click()

    try:
        requirement_popup = page.locator('.widget-mod-requirements')
        requirement_popup.wait_for(state="visible", timeout=2000)
        time.sleep(1)

        download_button = requirement_popup.locator('a.btn')
        download_button.wait_for(state="attached", timeout=2000)

        if not download_button.is_visible():
            page.keyboard.press("Escape")
            print('Could not find the download button! Trying to proceed with Esc.')
            raise Exception("Download button not visible")

        download_button.click()
    except:
        ...
    return page


def slow_download(page: Page):
    time.sleep(2)  # give some time to see stuff
    # Wait for the slow download page to load and button to be visible
    print("Waiting for slow download button...")
    page.wait_for_selector('#slowDownloadButton', timeout=5000)
    slow_download_button = page.locator('#slowDownloadButton')
    with page.expect_download() as download_info:
        slow_download_button.click()
        download = download_info.value
        download.save_as(DOWNLOAD_DIRECTORY + download.suggested_filename)
    print("Clicked slow download button")
    return page

import urllib.parse
def find_mod_page_with_nexus(page: Page, mod_name):
    """We could use google or duck duck go's api """

    encoded_name = urllib.parse.quote_plus(mod_name)
    url = f"https://www.nexusmods.com/games/skyrimspecialedition/mods?keyword={encoded_name}&sort=endorsements"
    page.goto(url)

    print("Waiting for mod search results: " + encoded_name)
    time.sleep(5)
    page.wait_for_selector('.mods-grid [data-e2eid="mod-tile"] a[data-e2eid="mod-tile-title"]')

    mod_page: ElementHandle = page.query_selector('.mods-grid [data-e2eid="mod-tile"] a[data-e2eid="mod-tile-title"]')#type: ignore
    page_link = mod_page.get_attribute('href')
    mod_page.click()
    return page



global mods
mods = [
    "CLoaks of skyrim",
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


        print(f"\n--- Searching Nexus for: {mod} ---")

        try:
            nexus_link_found = False
            mod_page = find_mod_page_with_nexus(page, mod)

            requirements = []

            if not mod_page:
                err = f"ERROR: No nexusmods.com link found in search results for '{mod}'."
                print(err)
                raise


            download_page = navigate_to_download(mod_page)
            slow_download(download_page)
            print("OK!")

        except TimeoutError as e:
            print(f"Timeout error during search for '{mod}': {e}")

        except Exception as e:
            print(f"""An unexpected error occurred during the search for '{mod}': {e}!
                \n\nDownload the mod and or press enter to proceed""")
            input()

        time.sleep(3) # Wait for 3 seconds



    # The browser is automatically closed when exiting the 'with' block
    print("\n--- Script finished. ---")
