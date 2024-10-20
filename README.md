# AmazonWatchAnalytics-MarkopoloAI
Python-based project featuring web scraping of Amazon watch data, REST API with FastAPI/Flask, and a fine-tuned LLM/RAG for insights. Scraping collects product and review details, stores in PostgreSQL, while the REST API supports search, filter, and data viewing. LLM offers conversational insights.

# Solution: Amazon Watch Scraper, REST API, and LLM-based Insights

## Overview
This project consists of three parts:

1. **Web Scraping**: A script that periodically scrapes watch data from Amazon and saves it into a PostgreSQL database.
2. **REST API**: A RESTful API built using Flask to serve watch data with filtering, sorting, and pagination functionalities.
3. **LLM-Based Insights**: A Retrieval-Augmented Generation (RAG) implementation to enable conversational insights from the scraped data using a fine-tuned LLM model.

## 1. Web Scraping
The `main_scraping.py` script automates the browser using Selenium and scrapes various details about watches from Amazon. It navigates through pages, collects watch details, user reviews, and additional information like images and links. The data is stored in PostgreSQL, with error handling in place to manage missing data or exceptions during scraping, the data includes:

- **Watch details**: Brand, Model, Price (original and discounted), Delivery price, Specifications (such as material, water resistance), Ratings, and Review Count.
- **User reviews**: Rating, Review Text, Reviewer Name, and Review Date.
- **Additional information**: Images, product links, categories, and more.

### Key Features
- **Automated Intervals**: The script is configured to run periodically, scraping updated data.
- **Data Storage**: The scraped data is saved into a PostgreSQL database with the appropriate fields for efficient retrieval.

### Insights
The scraping process runs iteratively, navigating through multiple product pages for predefined keywords like "Men's Wrist Watches," "Smartwatches," and more. For each product, the script gathers all available data and stores it in a PostgreSQL database using the `psycopg2` library.

The script also handles exceptions for missing data and continues scraping while collecting as much information as possible. At the end of the scraping process, the collected data is also saved to a JSON file for backup or further use.

### Usage
To run the scraping script:

```bash
python main_scraping.py
```

Ensure that you have a PostgreSQL server running and accessible, and update the database connection settings in the script accordingly.

## 2. REST API
The `flask_app.py` script creates a RESTful API using Flask, providing endpoints to interact with the scraped watch data.

### Endpoints
- **GET /products**:
  - Implements search by brand or model.
  - Filtering capabilities by price range and rating.
  - Sorting functionalities by price or rating.
  - Pagination support (using `page` and `limit` parameters).
- **GET /products/top**:
  - Returns the top products based on average rating and number of reviews.
  - Includes a list of reviews for each top product.
- **GET /products/{product_id}/reviews**:
  - Retrieves all reviews for a specific product.
  - Supports pagination for reviews.

### Usage
To run the Flask API:

```bash
python flask_app.py
```

This will start the server on `http://127.0.0.1:3001`. You can use tools like Postman or cURL to interact with the endpoints.

## 3. LLM-Based Insights (RAG)
The `LLM_RAG.py` script implements a Retrieval-Augmented Generation (RAG) model, which provides conversational insights from the data.

### Key Features
- **SQL Query Generation**: Uses Groq API to generate SQL queries to retrieve relevant data from the database.
- **Data Retrieval**: Retrieves relevant product information from the PostgreSQL database based on the user query.
- **LLM-Based Response Generation**: Uses the retrieved data as context to generate insightful responses via the LLaMA3 model.

### Usage
To run the LLM-based insights generator:

```bash
python LLM_RAG.py
```

This script will allow you to ask questions such as "What are the best smartwatches under $300?" and receive responses generated using the data in the database.

## 4. Testing the API
The `test_apicalls.py` script is used to test the API endpoints.

### Usage
To run the tests:

```bash
cd test
python test_apicalls.py
```

This script will perform various calls to the REST API, ensuring the endpoints function as expected, including testing search, filter, sorting, and pagination functionalities. And also includes responses from the LLM RAG with placeholder queries. 

## Requirements
- **Python 3.8+**
- **Libraries**: Selenium, requests, Flask, psycopg2, numpy, faiss, langchain-community, groq
- **PostgreSQL**: Ensure PostgreSQL is installed and a server is running.

## Setup Instructions
1. Clone the repository.
2. Install the required Python libraries:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your PostgreSQL database and update connection parameters in the scripts.
4. Run the scraping script to populate the database.
5. Start the Flask API to serve the data.
6. Run the LLM insights script for conversational analysis.



### Explanation Video: 
https://drive.google.com/file/d/145UWBvlBpB5ACpmitpspC2P_9ESCyvqO/view?usp=sharing
Forgot to tell - 1. Will find the commands I used to set up the postgresql db in debug folder

Additional Recordings about running the scripts:
https://drive.google.com/file/d/1M8xVABx2U4B5nINJZZZDzd9UdJ0PTPZu/view?usp=sharing
https://drive.google.com/file/d/1yTiOi4Rb3esuN77hZqdvzFWreE6mk-4K/view?usp=sharing
