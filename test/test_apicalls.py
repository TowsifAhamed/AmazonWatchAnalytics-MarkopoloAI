import requests
import json
import time

BASE_URL = "http://localhost:3001"

# Function to call the /products API
def call_get_products():
    try:
        params = {
            "brand": "citizen",
            "min_price": "20",
            "max_price": "5000",
            "min_rating": "3",
            "sort_by": "discounted_price",
            "order": "asc",
            "page": 2,
            "limit": 5
        }
        response = requests.get(f"{BASE_URL}/products", params=params)
        if response.status_code == 200:
            products = response.json()
            with open('products_response.json', 'w') as f:
                json.dump(products, f, indent=4)
            print("\n--- Products ---\n")
            print(json.dumps(products, indent=4))
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to call /products: {e}")

# Function to call the /products/top API
def call_get_top_products():
    try:
        response = requests.get(f"{BASE_URL}/products/top")
        if response.status_code == 200:
            top_products = response.json()
            with open('top_products_response.json', 'w') as f:
                json.dump(top_products, f, indent=4)
            print("\n--- Top Products ---\n")
            print(json.dumps(top_products, indent=4))
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to call /products/top: {e}")

# Function to call the /products/{product_id}/reviews API
def call_get_product_reviews(product_id):
    try:
        params = {
            "page": 1,
            "limit": 5
        }
        response = requests.get(f"{BASE_URL}/products/{product_id}/reviews", params=params)
        if response.status_code == 200:
            reviews = response.json()
            with open(f'product_{product_id}_reviews_response.json', 'w') as f:
                json.dump(reviews, f, indent=4)
            print("\n--- Product Reviews ---\n")
            print(json.dumps(reviews, indent=4))
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to call /products/{product_id}/reviews: {e}")

# Function to call the /ask_query API
def call_ask_query(query):
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "query": query
        }
        response = requests.post(f"{BASE_URL}/ask_query", headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            response_data["query"] = query

            # Create a unique filename by hashing the query and adding a timestamp
            timestamp = int(time.time())
            filename = f'ask_query_response_{timestamp}.json'

            with open(filename, 'w') as f:
                json.dump(response_data, f, indent=4)
            print(f"\n--- Ask Query Response for '{query}' ---\n")
            print(json.dumps(response_data, indent=4))
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to call /ask_query: {e}")

if __name__ == "__main__":
    # Call each API and display the responses
    call_get_products()
    call_get_top_products()
    # For demonstration, calling the reviews API for product ID 1
    call_get_product_reviews(101)

    # Call the ask_query endpoint with different queries
    call_ask_query("What are the best smartwatches under $300?")
    call_ask_query("Can you suggest some water resistant ladies watches under $50?")
