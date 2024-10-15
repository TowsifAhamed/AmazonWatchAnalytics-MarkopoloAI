from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psycopg2
import time
import json

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

# Function to scrape data based on the keyword
def getting_data(keyword, driver):
    try:
        # Open Amazon and search for the keyword
        driver.get("https://www.amazon.com/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'twotabsearchtextbox')))

        search = driver.find_element(By.ID, 'twotabsearchtextbox')
        search.send_keys(keyword)
        search_button = driver.find_element(By.ID, 'nav-search-submit-button')
        search_button.click()

        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))

        # Initialize list to store scraped data
        product_data = []

        # Loop through pages (up to 5 pages)
        for page in range(4):
            # Wait until products are loaded and locate them
            items = driver.find_elements(By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')

            for item in items:
                product = {
                    "asin": "N/A",
                    "name": "N/A",
                    "original_price": "N/A",
                    "discounted_price": "N/A",
                    "delivery_price": "N/A",
                    "ratings": "N/A",
                    "ratings_num": "N/A",
                    "link": "N/A",
                    "ratings_link": "N/A",
                    "category": keyword,
                    "page_number": page + 1,
                    "image_link": "N/A",
                    "store_name": "N/A",
                    "store_url": "N/A",
                    "purchase_num": "N/A",
                    "shipping_import_fees": "N/A",
                    "colors": "N/A",
                    "product_details": "N/A",
                    "customer_say": "N/A"
                }
                try:
                    # Get ASIN
                    data_asin = item.get_attribute("data-asin")
                    if data_asin:
                        product["asin"] = data_asin

                    # Get product name
                    try:
                        name = item.find_element(By.XPATH, './/h2/a/span')
                        product["name"] = name.text
                    except:
                        pass

                    # Get discounted price
                    try:
                        whole_price = item.find_element(By.XPATH, './/span[@class="a-price-whole"]').text
                        fraction_price = item.find_element(By.XPATH, './/span[@class="a-price-fraction"]').text
                        product["discounted_price"] = f"{whole_price}.{fraction_price}"
                    except:
                        pass

                    # Get original price
                    try:
                        original_price = item.find_element(By.XPATH, './/span[@class="a-price a-text-price"]/span[@class="a-offscreen"]').get_attribute("innerHTML").replace("$", "")
                        product["original_price"] = original_price
                    except:
                        pass

                    # Get delivery price
                    try:
                        delivery_price = item.find_element(By.XPATH, './/div[@data-cy="delivery-recipe"]//span[@aria-label]').get_attribute("innerText")
                        product["delivery_price"] = delivery_price
                    except:
                        pass

                    # Get ratings
                    try:
                        ratings = item.find_element(By.XPATH, './/i[@data-cy="reviews-ratings-slot"]/span[@class="a-icon-alt"]').get_attribute("innerHTML")
                        product["ratings"] = ratings
                    except:
                        pass

                    # Get number of ratings
                    try:
                        ratings_num_element = item.find_element(By.XPATH, './/span[@data-component-type="s-client-side-analytics"]//span[@aria-label]')
                        product["ratings_num"] = ratings_num_element.find_element(By.XPATH, './/span[@class="a-size-base s-underline-text"]').get_attribute("innerHTML").replace(",", "")
                        product["ratings_link"] = ratings_num_element.find_element(By.XPATH, './a').get_attribute("href")
                    except:
                        pass

                    # Get product link
                    try:
                        link = item.find_element(By.XPATH, './/a[@class="a-link-normal s-no-outline"]').get_attribute("href")
                        product["link"] = link
                    except:
                        pass

                    # Get image link
                    try:
                        image_link = item.find_element(By.XPATH, './/img[@class="s-image"]').get_attribute("src")
                        product["image_link"] = image_link
                    except:
                        pass

                    product_data.append(product)

                except Exception as e:
                    print(f"Error while processing item: {e}")

            # Click to the next page if available
            try:
                next_page_button = driver.find_element(By.XPATH, '//a[contains(@class, "s-pagination-next")]')
                next_page_button.click()
                WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))
            except:
                print("No more pages available or an error occurred while navigating to the next page.")
                break

            time.sleep(2)  # Optional: to avoid triggering bot detection

        return product_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to insert or update data into PostgreSQL
def insert_or_update_data_to_postgresql(data):
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
          dbname="amznwatchesdb",
          user="amznwatchuser",
          password="amznwatchpass",
          host="localhost"
        )
        cursor = conn.cursor()

        # Insert or update each product into the table
        for product in data:
            cursor.execute("""
                INSERT INTO products (asin, name, original_price, discounted_price, delivery_price, ratings, ratings_num, link, ratings_link, category, page_number, image_link, store_name, store_url, purchase_num, shipping_import_fees, colors, product_details, customer_say)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (asin)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    original_price = EXCLUDED.original_price,
                    discounted_price = EXCLUDED.discounted_price,
                    delivery_price = EXCLUDED.delivery_price,
                    ratings = EXCLUDED.ratings,
                    ratings_num = EXCLUDED.ratings_num,
                    ratings_link = EXCLUDED.ratings_link,
                    category = EXCLUDED.category,
                    page_number = EXCLUDED.page_number,
                    image_link = EXCLUDED.image_link
            """, (
                product['asin'], product['name'], product['original_price'], product['discounted_price'],
                product['delivery_price'], product['ratings'], product['ratings_num'], product['link'],
                product['ratings_link'], product['category'], product['page_number'], product['image_link'],
                product['store_name'], product['store_url'], product['purchase_num'], product['shipping_import_fees'],
                product['colors'], product['product_details'], product['customer_say']
            ))

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Failed to insert or update data into PostgreSQL: {e}")

# Function to insert or update reviews data into PostgreSQL
def insert_reviews_data_to_postgresql(reviews, product_asin):
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname="amznwatchesdb",
            user="amznwatchuser",
            password="amznwatchpass",
            host="localhost"
        )
        cursor = conn.cursor()

        # Insert or update each review into the reviews table
        for review in reviews:
            cursor.execute("""
                INSERT INTO reviews (product_id, name, url, rating, title, date, color, verified_purchase, review_text, helpful_count, image_link)
                VALUES ((SELECT id FROM products WHERE asin = %s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id, url)
                DO UPDATE SET
                    rating = EXCLUDED.rating,
                    title = EXCLUDED.title,
                    date = EXCLUDED.date,
                    color = EXCLUDED.color,
                    verified_purchase = EXCLUDED.verified_purchase,
                    review_text = EXCLUDED.review_text,
                    helpful_count = EXCLUDED.helpful_count,
                    image_link = EXCLUDED.image_link
            """, (
                product_asin, review['name'], review['url'], review['rating'], review['title'], review['date'],
                review['color'], review['verified_purchase'], review['review_text'], review['helpful_count'], review['image_link']
            ))

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Failed to insert review data into PostgreSQL: {e}")

# Main function to gather products and reviews
def main():
    service = Service('/usr/lib/chromium-browser/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    all_product_data = []

    try:
        # Loop through each keyword and gather product data
        for keyword in keywords:
            product_data = getting_data(keyword, driver)
            all_product_data.extend(product_data)

        # Insert or update data into PostgreSQL
        insert_or_update_data_to_postgresql(all_product_data)

        # Optionally: Output scraped data as JSON for local verification
        with open('scraped_data.json', 'w') as json_file:
            json.dump(all_product_data, json_file, indent=4)

        # Now scrape additional details for the products
        product_links = get_product_links()

        # Print number of product links in the table
        print(f"Total number of product links in the table: {len(product_links)}")

        # Check for duplicate links
        unique_links = set(product_links)
        if len(unique_links) < len(product_links):
            print("Warning: Duplicate product links found in the database.")

        # Loop through only non-scraped product links
        for link in product_links:
            # Connect to PostgreSQL to check if the product has been fully scraped
            conn = psycopg2.connect(
                dbname="amznwatchesdb",
                user="amznwatchuser",
                password="amznwatchpass",
                host="localhost"
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT store_name, store_url, purchase_num, shipping_import_fees, colors, product_details, customer_say
                FROM products
                WHERE link = %s
            """, (link,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            scraped_data = []

            if result and result[0] == "N/A" and result[1] == "N/A" and result[2] == "N/A" and result[3] == "N/A" and result[4] == "N/A" and result[5] == "N/A" and result[6] == "N/A":
                # Only scrape additional data if the product hasn't been fully scraped
                additional_data = scrape_additional_data(driver, link)
                scraped_data.append(additional_data)

                # Insert additional product details into PostgreSQL
                conn = psycopg2.connect(
                    dbname="amznwatchesdb",
                    user="amznwatchuser",
                    password="amznwatchpass",
                    host="localhost"
                )
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products SET
                    store_name = %s,
                    store_url = %s,
                    purchase_num = %s,
                    shipping_import_fees = %s,
                    colors = %s,
                    product_details = %s,
                    customer_say = %s
                    WHERE link = %s
                """, (
                    additional_data['store_name'], additional_data['store_url'], additional_data['purchase_num'],
                    additional_data['shipping_import_fees'], additional_data['colors'], additional_data['product_details'],
                    additional_data['customer_say'], link
                ))
                conn.commit()
                cursor.close()
                conn.close()

                # Insert or update reviews data
                insert_reviews_data_to_postgresql(additional_data['reviews'], additional_data['asin'])

        # Save all scraped data to a JSON file
        with open("scraped_product_data.json", "w") as f:
            json.dump(scraped_data, f, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

# Keywords to search for
keywords = [
    "Men's Wrist Watches",
    "Pocket Watches",
    "Smartwatches",
    "Women's Wrist Watches",
    "Activity & Fitness Trackers",
    "Girls' Wrist Watches",
    "Boys' Wrist Watches"
]

# Start scraping with all keywords
main()
