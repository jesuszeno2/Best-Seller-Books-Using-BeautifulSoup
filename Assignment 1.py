"""
Jesus Zeno. Assignment 1. We will be scraping a site for best selling books and putting certain data
points into a data frame. Then we will be cleaning up the data so it can be visualized.
"""

from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np

# This method allows us to not have to say the path of the driver or worry about the version.
# It will default to latest version.
# For specific version of driver, do GeckoDriverManager("Driver version")
# Open web browser and wait
driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
time.sleep(1)

# Define time to stall on webpage
stall_time = 2

# Create dataframe for uncleaned data
book_info_df = pd.DataFrame({'title': pd.Series(dtype='str'), 'author': pd.Series(dtype='str'),
                             'publication date': pd.Series(dtype='str'), 'format': pd.Series(dtype='str'),
                             'current price': pd.Series(dtype='str'), 'original price': pd.Series(dtype='str')})
# Initialize web page counter
page = 1

# Run loop to scrape all pages on website and put into df
while page < 35:
    # Define website and tell driver to go there
    url = "https://www.bookdepository.com/bestsellers?page="
    url = url + str(page)
    driver.get(url)

    # Scrape page code
    response = requests.get(url)
    html = response.content

    # Format html in human friendly style
    soup = bs(html, 'lxml')

    # Sleep for timeframe to not arouse suspicion
    time.sleep(stall_time)

    # Get all book info and append to df
    item_info = soup.select("div.book-item div.item-info")
    for item in item_info:
        # Get title
        all_h3 = item.select("div.item-info h3.title")
        for h3 in all_h3:
            new_title = h3.get_text(strip=True)

        # Get author
        all_p = item.select("div.item-info p.author")
        for p in all_p:
            new_author = p.get_text(strip=True)

        # Get publish date
        pub_p = item.select("div.item-info p.published")
        for pub in pub_p:
            new_publish_date = pub.get_text(strip=True)

        # Get format
        form_p = item.select("div.item-info p.format")
        for form in form_p:
            new_format = form.get_text(strip=True)

        # Get current price and original price
        prices = item.find_all("p", class_="price")
        for price in prices:
            original_price = price.find("span", class_="rrp")
            # If book is on sale, take the listed price as current price and crossed out as original price
            if original_price:
                new_current_price = str(original_price.previousSibling).strip()
                new_original_price = str(original_price.get_text(strip=True))
            # If the book isn't on sale put the same price for the original and current price
            else:
                new_current_price = str(price.get_text(strip=True))
                new_original_price = str(price.get_text(strip=True))

        # Append all appropriate info to df
        book_info_df = book_info_df.append({'title': new_title, 'author': new_author,
                                            'publication date': new_publish_date, 'format': new_format,
                                            'current price': new_current_price,
                                            'original price': new_original_price}, ignore_index=True)

    # Add to the page counter
    page += 1

# Close out driver and quit so window goes away.
driver.close()
driver.quit()

# Save unclean df into .csv file
book_info_df.to_csv('bestsellers.csv')

# Read in unclean .csv file into new df to be cleaned.
clean_book_info_df = pd.read_csv('bestsellers.csv', index_col=0)

# Eliminate any rows that have NaN values or duplicate rows in them.
clean_book_info_df = clean_book_info_df.dropna()
clean_book_info_df = clean_book_info_df.drop_duplicates()

# Find number of rows so we can iterate through rows in data frame
rows_index = clean_book_info_df.index
number_of_rows = len(rows_index)

# Clean up the publish date. Leave only the year in one column and make two columns with just the day
# and month in each column respectively.
# Define some initial values and lists
current_row = 0
published_date_list = clean_book_info_df['publication date'].tolist()
published_year = []
published_month = []
published_day = []
dirty_current_price_list = clean_book_info_df['current price'].tolist()
clean_current_price = []
dirty_original_price_list = clean_book_info_df['original price'].tolist()
clean_original_price = []

# Iterate over each row to isolate desired part of published date text
while current_row < number_of_rows:
    published_year_value = published_date_list[current_row]
    published_year.append(published_year_value[-4:])
    published_month_value = published_date_list[current_row]
    published_month.append(published_month_value[3:6])
    published_day_value = published_date_list[current_row]
    published_day.append(published_day_value[:2])
    current_price_value = dirty_current_price_list[current_row]
    clean_current_price.append(current_price_value[3:])
    original_price_value = dirty_original_price_list[current_row]
    clean_original_price.append(original_price_value[3:])
    current_row += 1

# Add, insert, or update columns to data frame
clean_book_info_df.insert(3, 'publication month', published_month)
clean_book_info_df.insert(4, 'publication day', published_day)
clean_book_info_df['publication date'] = published_year
clean_book_info_df['current price'] = clean_current_price
clean_book_info_df['original price'] = clean_original_price

# Rename publication date to more accurate name
# inplace=True is necessary to keep the change permanently
clean_book_info_df.rename(columns={"publication date": "publication year"}, inplace=True)

# Make original and current prices data types float after clean up
clean_book_info_df = clean_book_info_df.astype({'current price': 'float', 'original price': 'float',
                                                'publication year': 'int', 'publication day': 'int'})
clean_book_info_df.round({'current price': 2, 'original price': 2})

# Write df to cleaned csv file
clean_book_info_df.to_csv('bestsellers-cleaned.csv')

# Make new 2019 df with upon condition that books were published in 2019 or later
books_2019_df = clean_book_info_df[clean_book_info_df['publication year'] > 2018]

# Get rid of extra columns not needed for the answer and save to .csv
books_2019_df.pop('publication year')
books_2019_df.pop('publication month')
books_2019_df.pop('publication day')
books_2019_df.pop('format')
books_2019_df.pop('original price')
books_2019_df.to_csv('2019-books.csv')

# Create a scatter plot of the current price (y axis) versus the original price (x axis)
# for the bestselling books
current_v_original_price_plot = clean_book_info_df.plot(x='original price', y='current price',
                                                        kind='scatter', figsize=(10, 6),
                                                        title='current price vs. original price')
plt.tight_layout()
plt.savefig('current_v_original_price_plot.png')
plt.show()
plt.close()

# Create a histogram to visualize the distribution of the current prices of the bestselling books
current_price_plot_list_df = clean_book_info_df['current price']
plt.figure(figsize=(10, 6))
plt.xticks(np.arange(0, 200, step=15))
plt.yticks(np.arange(0, 350, step=25))
plt.xlabel("Book prices in $US", fontsize=12)
plt.ylabel("Number of books", fontsize=12)
plt.title('Distribution of prices')
current_price_plot_list_df.hist(bins=50)
plt.tight_layout()
plt.savefig('distribution_of_current_prices.png')
plt.show()
plt.close()

# Create a bar plot to visualize the average current price of the bestselling books for
# each publication year
clean_book_info_df[['current price', 'publication year']].groupby('publication year').mean().sort_values(
    by='current price', ascending=False).plot.bar(figsize=(10, 6),
                                                  rot=45,
                                                  title='average current price by each published year')
plt.legend(['average current price in $US'], loc='best')
plt.tight_layout()
plt.savefig('current-price-by-year-published.png')
plt.show()
plt.close()
