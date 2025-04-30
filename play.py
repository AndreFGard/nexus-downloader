from genericpath import exists
from patchright.sync_api import BrowserContext, Page, sync_playwright,ElementHandle, TimeoutError
import time # Import time for potential pauses
import urllib.parse
import os
import duckduckgo_search
Searcher = duckduckgo_search.DDGS().text

from pydantic import BaseModel

#todo use  configdict to read from .env or a config file
class Config(BaseModel):
    NEXUS_URL:str= "https://www.nexusmods.com/"
    DOWNLOAD_DIRECTORY:str ='./'
    IS_LOGGED_IN:bool =True
    MODS:list[str] =["Valhalla combat"]
    USER_DATA_DIR:str =f'{os.environ['HOME']}/.config/google-chrome/Default'
    CHROME_PATH:str ='/bin/google-chrome-stable'


def navigate_to_download(page: Page, config:Config):
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


def slow_download(page: Page, config:Config):
    time.sleep(2)  # give some time to see stuff
    # Wait for the slow download page to load and button to be visible
    print("Waiting for slow download button...")
    page.wait_for_selector('#slowDownloadButton', timeout=5000)
    slow_download_button = page.locator('#slowDownloadButton')

    with page.expect_download() as download_info:
        print("Downloading")
        slow_download_button.click()
        download = download_info.value
        download.save_as(config.DOWNLOAD_DIRECTORY + download.suggested_filename,)
        print(f"Downloaded successfully: {download.suggested_filename}")

    return page


def find_mod_page_url(page: Page, mod_name: str, config:Config) -> str:
    """Return mod page url. could use a search engine instead of nexus's own unreliable search"""

    encoded_name = urllib.parse.quote_plus(mod_name)
    url = f"https://www.nexusmods.com/games/skyrimspecialedition/mods?keyword={encoded_name}&sort=endorsements"
    page.goto(url)

    print("Waiting for mod search results: " + encoded_name)
    time.sleep(5)
    page.wait_for_selector('.mods-grid [data-e2eid="mod-tile"] a[data-e2eid="mod-tile-title"]')

    mod_page: ElementHandle = page.query_selector('.mods-grid [data-e2eid="mod-tile"] a[data-e2eid="mod-tile-title"]')#type: ignore
    with page.expect_navigation() as popup_info:
        mod_page.click()
        popup = popup_info.value
        print("Moving to modpage")

    return popup.url

def __search_modpage_with_ddg_api(mod_name:str, config:Config) -> str:
    """not working due to ratelimits"""
    try:
        results = Searcher(
            f"Skyrim Special Edition {mod_name} mod site:nexusmods.com" ,
            backend="lite",
            max_results=2,
        )
        first_result = results[0]["href"]
        return first_result
    except Exception as err:
        print(err)
        return ""

def search_mod_page(page:Page, mod_name:str, config:Config):
    page.goto('https://lite.duckduckgo.com')
    page.fill('input[name="q"]', f"Skyrim Special Edition {mod_name} mod site:nexusmods.com")
    page.locator('input[type="submit"]').click()
    try:
      loc = page.locator('.result-link')
      loc.first.wait_for(state="attached", timeout=2000)
      with page.expect_navigation() as navinfo:
        loc.first.click()
        url = navinfo.value.url
      return url or ''
    except Exception as err:
      print(err)
      time.sleep(20)




def download_mod(mod:str, browser:BrowserContext, config:Config):
        page = browser.new_page()

        print(f"\n--- Searching Nexus for: {mod} ---")

        try:
            try:
              url = search_mod_page(page, mod, config) or ''
              if "nexusmods" not in url:
                print(f"using nexus mods search (ddg was: {url}")
                raise
              print("got results from duckduckgo")

            except:
              url = find_mod_page_url(page,mod, config)

            page.goto(url)
            mod_page = page


            if not mod_page:
                err = f"ERROR: No nexusmods.com link found in search results for '{mod}'."
                print(err)
                raise


            download_page = navigate_to_download(mod_page,config)
            slow_download(download_page,config)
            print("OK!")

        except TimeoutError as e:
            print(f"Timeout error during search for '{mod}': {e}")

        except Exception as e:
            print(f"""An unexpected error occurred during the search for '{mod}': {e}!
                \n\nDownload the mod and or press enter to proceed""")
            input()

        time.sleep(3) # Wait for 3 seconds


def start_downloads(config:Config):
    os.system(f'mkdir -p {config.DOWNLOAD_DIRECTORY}')

    with sync_playwright() as p:

        user_data_dir=config.USER_DATA_DIR
        browser = p.chromium.launch_persistent_context(
            executable_path=config.CHROME_PATH,
            user_data_dir=user_data_dir,
            headless=False,  # See what's going on
            args=["--start-maximized --remote-debugging-port=9222"],
            channel="chrome",
            no_viewport=True
        )

        if not config.IS_LOGGED_IN:
            print("Please log in to Nexus now and press enter to continue.")
            input()

        for mod in config.MODS:
            try:
                download_mod(mod, browser, config)
            except:
                print(f"trying {mod} again...")
                download_mod(mod, browser, config)
            print("-"*20+'#'*10+"-"*20+'\n\n')



with open("modlist.txt", "r") as f:
  modlist = f.readlines()

config = Config(
    IS_LOGGED_IN=True,
    MODS=modlist,
    DOWNLOAD_DIRECTORY='./downloads/',
    )

start_downloads(config)
