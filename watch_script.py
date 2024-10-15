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

# Function to get data from PostgreSQL
def get_product_links():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname="amznwatchesdb",
            user="amznwatchuser",
            password="amznwatchpass",
            host="localhost"
        )
        cursor = conn.cursor()

        # Get the first 10 product links
        cursor.execute("SELECT link FROM products LIMIT 10;")
        links = cursor.fetchall()

        cursor.close()
        conn.close()

        return [link[0] for link in links]

    except Exception as e:
        print(f"Failed to get product links from PostgreSQL: {e}")
        return []

# Function to scrape additional data from the product link
def scrape_additional_data(driver, link):
    driver.get(link)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    
    product_details = {
        "store_name": "N/A",
        "store_url": "N/A",
        "purchase_num": "N/A",
        "shipping_import_fees": "N/A",
        "colors": "N/A",
        "product_details": "N/A",
        "customer_say": "N/A",
        "reviews": []
    }
    
    try:
        # Get store name and store URL
        try:
            store_element = driver.find_element(By.ID, 'bylineInfo')
            product_details["store_name"] = store_element.text.replace("Visit the ", "")
            product_details["store_url"] = store_element.get_attribute("href")
        except:
            pass
        
        # Get purchase number
        try:
            purchase_element = driver.find_element(By.XPATH, '//span[@id="social-proofing-faceout-title-tk_bought"]')
            product_details["purchase_num"] = purchase_element.text
        except:
            pass
        
        # Get shipping and import fees
        try:
            shipping_fees_element = driver.find_element(By.XPATH, '//span[contains(text(), "Shipping & Import Fees")]')
            product_details["shipping_import_fees"] = shipping_fees_element.text
        except:
            pass
        
        # Get color variations
        try:
            color_elements = driver.find_elements(By.XPATH, '//ul[@class="a-unordered-list a-nostyle a-button-list a-declarative a-button-toggle-group a-horizontal a-spacing-top-micro swatches swatchesRectangle imageSwatches"]//li')
            colors = []
            for color_element in color_elements:
                color_name = color_element.get_attribute("title").replace("Click to select ", "")
                colors.append(color_name)
            product_details["colors"] = ",".join(colors)
        except:
            pass
        
        # Get product details
        try:
            product_details_element = driver.find_element(By.ID, 'productFactsDesktop_feature_div')
            product_details["product_details"] = product_details_element.text.replace("\nSee more", "")
        except:
            pass
        
        # Get "customer say" summary
        try:
            customer_say_element = driver.find_element(By.XPATH, '//div[@id="product-summary"]//p[1]')
            product_details["customer_say"] = customer_say_element.text
        except:
            pass
        
        # Get customer reviews
        try:
            review_elements = driver.find_elements(By.XPATH, '//div[contains(@id, "customer_review-")]')
            for review_element in review_elements:
                review = {
                    "name": "N/A",
                    "url": "N/A",
                    "rating": "N/A",
                    "title": "N/A",
                    "date": "N/A",
                    "color": "N/A",
                    "verified_purchase": False,
                    "review_text": "N/A",
                    "helpful_count": 0,
                    "image_link": "N/A"
                }
                
                try:
                    # Reviewer name and profile URL
                    reviewer_element = review_element.find_element(By.XPATH, './/div[@data-hook="genome-widget"]')
                    review["name"] = reviewer_element.text
                    review["url"] = reviewer_element.find_element(By.XPATH, './/a').get_attribute("href")
                except:
                    pass
                
                try:
                    # Rating
                    rating_element = review_element.find_element(By.XPATH, './/i[@data-hook="review-star-rating"]//span').get_attribute("innerHTML")
                    review["rating"] = rating_element
                except:
                    pass
                
                try:
                    # Review title
                    title_element = review_element.find_element(By.XPATH, './/a[@data-hook="review-title"]')
                    review["title"] = title_element.text
                except:
                    pass
                
                try:
                    # Color information
                    color_element = review_element.find_element(By.XPATH, './/span[@data-hook="format-strip-linkless"]')
                    review["color"] = color_element.text
                except:
                    pass
                
                try:
                    # Verified purchase
                    review["verified_purchase"] = bool(review_element.find_element(By.XPATH, './/span[@data-hook="avp-badge-linkless"]'))
                except:
                    pass
                
                try:
                    # Review text
                    review_date = review_element.find_element(By.XPATH, './/span[@data-hook="review-date"]')
                    review["date"] = review_date.text
                except:
                    pass
                
                try:
                    # Review text
                    review_text_element = review_element.find_element(By.XPATH, './/span[@data-hook="review-body"]')
                    review["review_text"] = review_text_element.text
                except:
                    pass
                
                try:
                    # Helpful count
                    helpful_element = review_element.find_element(By.XPATH, './/span[@data-hook="helpful-vote-statement"]')
                    review["helpful_count"] = int(helpful_element.text.split()[0])
                except:
                    pass
                
                try:
                    # Image link
                    image_element = review_element.find_element(By.XPATH, './/img[@data-hook="review-image-tile"]')
                    review["image_link"] = image_element.get_attribute("data-src")
                except:
                    pass
                
                product_details["reviews"].append(review)
        except:
            pass

    except Exception as e:
        print(f"Error while scraping product details: {e}")

    return product_details

# Main function to scrape additional data for products
def main():
    service = Service('/usr/lib/chromium-browser/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Get product links from PostgreSQL
        product_links = get_product_links()
        scraped_data = []
        
        # Loop through each product link and scrape additional data
        for link in product_links:
            additional_data = scrape_additional_data(driver, link)
            scraped_data.append(additional_data)
            # print(json.dumps(additional_data, indent=4))
        
        # Save all scraped data to a JSON file
        with open("scraped_product_data.json", "w") as f:
            json.dump(scraped_data, f, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

# Start scraping additional data
main()