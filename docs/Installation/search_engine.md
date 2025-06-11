# search Engine setup

To use the search engine capabilities of Agent, you need to set up the search engine API keys. Currently, Agent supports Bing, Google and DuckDuckGo search engines. If you want to use duckduckgo, you don't need to set up any API keys.

## Setting up Bing Search

1. Go to the [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) page.
2. Click on "Try Now" or "Get Started".
3. Sign in with your Microsoft account.
4. Create a new resource or use an existing one.
5. Get your API key from the "Keys and Endpoint" section.
6. Copy the API key and paste it in the API_KEYS field with the name `BING` in the `config.toml` file located in the root directory of Agent, or you can set it via the UI.

## Setting up Google Search

1. Go to the [Google Programmable Search Engine](https://programmablesearchengine.google.com/) page.
2. Click on "Get Started".
3. Create a new search engine.
4. Get your API key from the [Google Cloud Console](https://console.cloud.google.com/).
5. Copy the API key and paste it in the API_KEYS field with the name `GOOGLE_SEARCH` in the `config.toml` file in the root directory of Agent or you can set it via UI.

## Setting up DuckDuckGo Search

DuckDuckGo doesn't require an API key, so you can use it without any setup. However, if you want to use the official API, you can get an API key from the [DuckDuckGo API](https://duckduckgo.com/api) page.

## Setting up Tavily Search

1. Go to the [Tavily AI](https://tavily.com/) website.
2. Sign up for an account.
3. Get your API key from the dashboard.
4. Copy the API key and paste it in the API_KEYS field with the name `TAVILY` in the `config.toml` file in the root directory of Agent or you can set it via UI.
