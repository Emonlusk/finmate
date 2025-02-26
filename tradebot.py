from wit import Wit
import streamlit as st
import alpaca_trade_api as tradeapi

# Initialize Wit.ai client
WIT_ACCESS_TOKEN = ""
wit_client = Wit(WIT_ACCESS_TOKEN)

# Initialize Alpaca API
ALPACA_KEY_ID = ""
ALPACA_SECRET_KEY = ""
alpaca_api = tradeapi.REST(ALPACA_KEY_ID, ALPACA_SECRET_KEY, base_url="https://paper-api.alpaca.markets/v2")

def handle_message(text):
    # Send user message to Wit.ai
    response = wit_client.message(text)
    intent = response['intents'][0]['name'] if response['intents'] else None
    entities = response['entities']

    # Lookup table for company names and ticker symbols
    COMPANY_TO_TICKER = {
        "apple": "AAPL",
        "tesla": "TSLA",
        "google": "GOOGL",
        "amazon": "AMZN",
        "microsoft": "MSFT"
    }

    # Extract company name and ticker symbol
    company_name = entities.get('company_name:company_name', [{}])[0].get('value', '').lower()
    ticker_symbol = entities.get('symbol:symbol', [{}])[0].get('value', '').upper()

    # If company_name is provided but ticker_symbol is not, autofill the ticker_symbol
    if company_name and not ticker_symbol:
        ticker_symbol = COMPANY_TO_TICKER.get(company_name, '')

    # Handle finance-specific intents
    if intent in ["get_stock_price", "buy_stock", "sell_stock", "get_portfolio", "get_market_news", "get_investment_recommendation", "get_historical_data"]:
        if intent == "get_stock_price":
            if not ticker_symbol:
                return f"Sorry, I couldn't find the ticker symbol for {company_name.capitalize()}."
            try:
                # Fetch real-time data (1-minute bars)
                bars = alpaca_api.get_bars(ticker_symbol, "1Min", limit=1)
                if bars:
                    price = bars[0].c  # Access the first bar's close price
                    return f"The current price of {company_name.capitalize()} ({ticker_symbol}) is ${price:.2f}."
                else:
                    # Fallback to historical data (1-day bars)
                    bars = alpaca_api.get_bars(ticker_symbol, "1D", limit=1)
                    if bars:
                        price = bars[0].c  # Close price of the last trading day
                        return f"The latest price of {company_name.capitalize()} ({ticker_symbol}) is ${price:.2f}."
                    else:
                        return f"No data found for {company_name.capitalize()} ({ticker_symbol})."
            except Exception as e:
                return f"Failed to fetch price: {str(e)}"

        elif intent == "get_historical_data":
            if not ticker_symbol:
                return f"Sorry, I couldn't find the ticker symbol for {company_name.capitalize()}."
            # Extract timeframe and interval (default to 1 day if not specified)
            timeframe = entities.get('timeframe', [{}])[0].get('value', '1D')  # Default: 1 day
            interval = entities.get('interval', [{}])[0].get('value', '1D')  # Default: 1 day

            # Convert user-friendly timeframe to Alpaca-supported timeframe
            if "day" in timeframe.lower():
                timeframe = "1D"  # Fetch daily data
                limit = 1  # Fetch last 1 day
            elif "week" in timeframe.lower():
                timeframe = "1D"  # Fetch daily data for the past week
                limit = 7  # Fetch last 7 days
            elif "month" in timeframe.lower():
                timeframe = "1D"  # Fetch daily data for the past month
                limit = 30  # Fetch last 30 days
            elif "year" in timeframe.lower():
                timeframe = "1D"  # Fetch daily data for the past year
                limit = 365  # Fetch last 365 days
            else:
                # Default to 1 day
                timeframe = "1D"
                limit = 1

            try:
                # Fetch historical data
                bars = alpaca_api.get_bars(ticker_symbol, timeframe, limit=limit)  # Fetch last N bars
                print(bars)  # Debug the API response
                if bars:
                    historical_data = "\n".join([f"{bar.t}: ${bar.c:.2f}" for bar in bars])
                    return f"Historical data for {company_name.capitalize()} ({ticker_symbol}):\n{historical_data}"
                else:
                    return f"No historical data found for {company_name.capitalize()} ({ticker_symbol})."
            except Exception as e:
                return f"Failed to fetch historical data: {str(e)}"

        # Add other intents here (buy_stock, sell_stock, etc.)
        elif intent == "get_investment_recommendation":
            # Extract timeframe and risk level
            timeframe = entities.get('timeframe', [{}])[0].get('value', 'long-term')  # Default: long-term
            risk_level = entities.get('risk_level', [{}])[0].get('value', 'medium')  # Default: medium

            # Provide investment recommendations based on timeframe and risk level
            if timeframe == "short-term" and risk_level == "low":
                return "For low-risk short-term investments, consider Treasury Bills or Money Market Funds."
            elif timeframe == "short-term" and risk_level == "medium":
                return "For medium-risk short-term investments, consider Corporate Bonds or Dividend Stocks."
            elif timeframe == "short-term" and risk_level == "high":
                return "For high-risk short-term investments, consider Growth Stocks or Cryptocurrencies."
            elif timeframe == "long-term" and risk_level == "low":
                return "For low-risk long-term investments, consider Index Funds or Municipal Bonds."
            elif timeframe == "long-term" and risk_level == "medium":
                return "For medium-risk long-term investments, consider Blue-Chip Stocks or REITs."
            elif timeframe == "long-term" and risk_level == "high":
                return "For high-risk long-term investments, consider Tech Stocks or Emerging Markets."
            else:
                return "For a balanced portfolio, consider a mix of ETFs and Mutual Funds."    

    # Handle non-finance queries
    else:
        return "Sorry, I can only help with finance-related queries."

# Streamlit App
def main():
    st.title("Finance Chatbot 💬📈")
    st.write("Welcome to the Finance Chatbot! Ask me about stock prices, historical data, or investment recommendations.")

    # Initialize session state to store chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask me anything about finance..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        response = handle_message(prompt)

        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# Run the Streamlit app
if __name__ == "__main__":
    main()
# Example usage
if __name__ == "__main__":
    while True:
        user_message = input("You: ")
        if user_message.lower() in ["exit", "quit"]:
            break
        response = handle_message(user_message)
        print(f"Bot: {response}")
          # Debug the API response
  # Debug the API response