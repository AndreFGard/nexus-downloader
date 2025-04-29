from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from browser_use import Agent, Browser, BrowserConfig

load_dotenv()

import asyncio

task = """
### Prompt for Mod Installation Agent – Skyrim Special Edition (AE) Mods from NexusMods

**Objective:**
Discuss in a telegram chat about whatever topic others are talking about. Reply to them naturally, as a person would.
Engange in the conversation and be gentle. Occasionally, mention linux. Reply to all messages sent by other people. Rememeber that your name is Andre.

--

## Step 1: open telegram in the eosfriends channel

- Open a new tab with the link https://web.telegram.org/k/#@eosfriends
- select the eosfriends telegram chat


## Step 2: engage in the conversation:

- Read the messages in the telegram chat and reply to them naturally, as a person would.
- Be sure to not confuse the search box with the message box.
- Reply to any message that arrives.
- To reply, click on the message box, type your message and then press the send button

## Step 3: continue the conversation
come back to step 2 indefinetely. Wait for others to reply.
"""

browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        browser_binary_path='/usr/bin/google-chrome-stable',  # macOS path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)


from dotenv import load_dotenv
load_dotenv()

async def main():
	agent = Agent(
		task=task,
		llm=ChatGoogleGenerativeAI(model='gemini-2.0-flash'),
		browser=browser,
			use_vision=False,

			
			)
	await agent.run()
	input('Press Enter to close the browser...')
	await browser.close()


if __name__ == '__main__':
	asyncio.run(main())