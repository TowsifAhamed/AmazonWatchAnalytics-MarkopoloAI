from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import psycopg2

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
        for page in range(1):
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
                    "image_link": "N/A"
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
                INSERT INTO products (asin, name, original_price, discounted_price, delivery_price, ratings, ratings_num, link, ratings_link, category, page_number, image_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link)
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
                product['ratings_link'], product['category'], product['page_number'], product['image_link']
            ))

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Failed to insert or update data into PostgreSQL: {e}")

# Main function to gather products for all keywords
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