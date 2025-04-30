from patchright.sync_api import Page, sync_playwright,ElementHandle, TimeoutError
import time # Import time for potential pauses

NEXUS_URL="https://www.nexusmods.com/"



def navigate_to_download(page: Page):
    """
    Initiates the manual download process for a mod on the Nexus Mod page.
    The page must have a specific Nexus mod page already open before calling this function.
    The function clicks through the download process including the slow download option.
    Args:
        page (Page): The Playwright Page object with an open Nexus mod page.
    Raises:
        TimeoutError: If any of the expected elements don't appear within timeout.
    """

    page.wait_for_selector("#action-manual",timeout=3000)
    time.sleep(1)
    download_popup_button:ElementHandle = page.query_selector('#action-manual') #type:ignore
    download_popup_button.click()
    # Wait for the download popup to appear
    requirement_popup = page.wait_for_selector('.widget-mod-requirements', timeout=2000)
    time.sleep(1) #for some reason it's needed
    requirement_popup =  requirement_popup or page.query_selector('.widget-mod-requirements')
    if requirement_popup:
        try:
            download_button = requirement_popup.query_selector('a.btn')


            # raw_reqs: list[ElementHandle] = requirement_popup.query_selector_all("li")

            # reqs = []
            # for req in raw_reqs:
            #     try:
            #         name = req.query_selector('a').query_selector('span').inner_text()
            #         href = req.query_selector('a').get_attribute('href')

            #         reqs.append(Requirement(name, href, "" ))
            #     except:
            #         ...
            # print(reqs)

            if not download_button:
                page.keyboard.press("Esc")
                print('couldnt find the download button! trying to proceed with Esc')
                raise

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
    slow_download_button.click()
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
        with page.expect_download() as download_info:
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

        download = download_info.value
        download.save_as("./" + download.suggested_filename)

    # The browser is automatically closed when exiting the 'with' block
    print("\n--- Script finished. ---")
