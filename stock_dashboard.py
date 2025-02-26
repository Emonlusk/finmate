import streamlit as st
import requests
import pandas as pd
import feedparser
import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# Alpha Vantage API key and base URL
ALPHA_VANTAGE_API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"  # Replace with your API key
BASE_URL = "https://www.alphavantage.co/query"

# Function to fetch stock data from Alpha Vantage
def fetch_stock_data(ticker, start_date, end_date):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": "full"
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "Time Series (Daily)" in data:
            stock_data = pd.DataFrame(data["Time Series (Daily)"]).T
            stock_data.index = pd.to_datetime(stock_data.index)
            stock_data = stock_data.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            })
            stock_data = stock_data[["Open", "High", "Low", "Close", "Volume"]]
            stock_data = stock_data.sort_index()
            stock_data = stock_data.loc[start_date:end_date]
            return stock_data
        else:
            st.error(f"Error fetching data: {data.get('Note', 'Unknown error')}")
            return None
    else:
        st.error("Failed to fetch data from Alpha Vantage.")
        return None

# Function to fetch stock news from RSS feeds
def fetch_stock_news():
    # Yahoo Finance RSS feed
    rss_url = "https://finance.yahoo.com/news/rssindex"
    feed = feedparser.parse(rss_url)
    news_articles = []
    for entry in feed.entries[:10]:  # Get top 10 news
        news_articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })
    return news_articles

# Function to predict stock price using Linear Regression
def predict_stock_price(stock_data, future_date):
    # Prepare data for training
    stock_data['Days'] = (stock_data.index - stock_data.index[0]).days
    X = np.array(stock_data['Days']).reshape(-1, 1)
    y = np.array(stock_data['Close'])

    # Train Linear Regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict for the future date
    future_days = (future_date - stock_data.index[0]).days
    predicted_price = model.predict(np.array([[future_days]]))[0]
    return predicted_price

# Streamlit App
st.title("Stock Market Dashboard")

# Sidebar for user inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL")
start_date = st.sidebar.date_input("Start Date", datetime.date(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date(2023, 10, 1))

# Fetch stock data
if st.sidebar.button("Get Stock Data"):
    stock_data = fetch_stock_data(ticker, start_date, end_date)
    
    if stock_data is not None:
        # Convert the 'Close' column to numeric (float)
        stock_data['Close'] = pd.to_numeric(stock_data['Close'], errors='coerce')
        
        # Display stock data
        st.subheader(f"Stock Prices for {ticker}")
        st.line_chart(stock_data['Close'])
        
        # Display latest stock price
        latest_price = stock_data['Close'].iloc[-1]  # Use .iloc[-1] to get the last value
        st.write(f"Latest Closing Price for {ticker}: ${latest_price:.2f}")
        
        # Display stock data in a table
        st.subheader(f"Stock Data Table for {ticker}")
        st.dataframe(stock_data)  # Use st.dataframe for an interactive table

        # Stock Price Prediction
        st.subheader("Stock Price Prediction")
        future_date = st.date_input("Enter a future date for prediction:", datetime.date(2023, 12, 31))
        if st.button("Predict Stock Price"):
            predicted_price = predict_stock_price(stock_data, future_date)
            st.write(f"Predicted Closing Price for {ticker} on {future_date}: ${predicted_price:.2f}")

# Fetch and display top 10 stock news
st.subheader("Top 10 Stock News")
news_articles = fetch_stock_news()

if news_articles:
    for article in news_articles:
        st.write(f"**{article['title']}**")
        st.write(f"*Published on: {article['published']}*")
        st.write(f"[Read more]({article['link']})")
        st.write("---")
else:
    st.write("No news articles found.")