import psycopg2
import numpy as np
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from groq import Groq
import re
import time
import os
from transformers import GPT2Tokenizer

# Step 1: Set up environment
# Initialize Groq client with the API key
groq_api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=groq_api_key)

# Tokenizer to estimate token counts
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Maximum allowed tokens for the model response
MAX_TOKENS = 30000
CONTEXT_TOKEN_LIMIT = 4000  # Limit context tokens to a manageable size

# Step 2: Generate SQL query using Groq
def generate_sql_query(query):
    schema = """
    Table: products
    Columns:
    - id (integer)
    - name (text)
    - discounted_price (float)
    - product_details (text)
    - category (text)
    - ratings (text)
    - ratings_num (integer)
    - store_name (text)
    - customer_say (text)

    Value of category: "Men's Wrist Watches", "Pocket Watches", "Smartwatches", "Women's Wrist Watches", "Activity & Fitness Trackers", "Girls' Wrist Watches", "Boys' Wrist Watches"
    """

    prompt = f"""
    Below is the schema of a table and a user query. Generate an appropriate SQL query to retrieve relevant data from the table products. Please remember that discounted_price is stored as text and needs to be cast to a float type for comparison and prefer to use ilike for texual data as category, brand etc. check fo value not "N/A" and give single query without any comments as response.

    Schema:
    {schema}

    User Query: {query}
    SQL Query:
    """

    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192"
    )

    # Extract the relevant SQL query using regex to remove any extra text
    sql_query = response.choices[0].message.content.strip()
    sql_query_lines = sql_query.splitlines()

    # Extract the SQL query block using markers (between SELECT and the ending semicolon)
    in_sql_block = False
    filtered_lines = []

    for line in sql_query_lines:
        if line.strip().startswith("SELECT"):
            in_sql_block = True
        if in_sql_block:
            filtered_lines.append(line)
        if ";" in line:
            break

    sql_query = " ".join(filtered_lines).strip()
    
    print("SQL QUERY:", sql_query)
    
    return sql_query

# Step 3: Extract data from PostgreSQL using generated SQL query
def extract_data(query):
    retry_attempts = 5
    for attempt in range(retry_attempts):
        sql_query = generate_sql_query(query)

        # Ensure only relevant columns are selected to match unpacking structure
        if "SELECT *" in sql_query:
            sql_query = sql_query.replace("SELECT *", "SELECT id, name, discounted_price, product_details, category, ratings, ratings_num, store_name, customer_say")

        conn = psycopg2.connect(
            dbname="amznwatchesdb",
            user="amznwatchuser",
            password="amznwatchpass",
            host="localhost"
        )
        cursor = conn.cursor()
        try:
            cursor.execute(sql_query)
        except psycopg2.Error as e:
            print("Error executing SQL query:", e)
            conn.close()
            time.sleep(2)  # Adding delay before retrying
            continue
        products = cursor.fetchall()
        conn.close()

        if products:
            processed_products = []
            for product in products:
                id, name, discounted_price, product_details, category, ratings, ratings_num, store_name, customer_say = product
                ratings = 0.0 if ratings == "N/A" else float(re.search(r"\d+\.\d+", ratings).group()) if re.search(r"\d+\.\d+", ratings) else 0.0
                ratings_num = 0 if ratings_num == "N/A" else int(ratings_num)
                processed_products.append(f"Product: {name}, Price: ${discounted_price}, Category: {category}, Ratings: {ratings}, Ratings Count: {ratings_num}, Store: {store_name}, Details: {product_details}, Customer Review Summary: {customer_say}")
            return processed_products

        print("No products found for the given query. Retrying...")
        time.sleep(2)  # Adding delay before retrying

    print("No products retrieved after multiple attempts.")
    return []

# Step 6: Generate response with Groq API
def generate_response_with_groq(query, context):
    if not context:
        return "No relevant documents found to answer the query."

    # Estimate token length and truncate context if necessary
    prompt_template = f"""
    Below is the context of several products and a question. Use the context to provide an answer to the question.
    
    Context:
    {{}}
    
    Question: {query}
    Answer:
    """
    prompt_without_context = prompt_template.format("")
    base_token_length = len(tokenizer(prompt_without_context)['input_ids'])
    context_lines = context.split('\n')

    # Truncate context if it exceeds the allowed token limit
    while True:
        truncated_context = "\n".join(context_lines)
        total_token_length = len(tokenizer(truncated_context)['input_ids']) + base_token_length
        if total_token_length <= CONTEXT_TOKEN_LIMIT or not context_lines:
            break
        context_lines.pop()

    prompt = prompt_template.format(truncated_context)
    
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192"
    )

    # Extract the relevant response text
    response_text = response.choices[0].message.content.strip()
    return response_text

# Step 7: Main function
def main():
    # User query
    query = "Can you suggest some water resistant ladies watches under $200?"

    # Extract data from PostgreSQL using generated SQL query
    products = extract_data(query)

    if not products:
        print("No products retrieved from the database.")
        return

    # Instead of using FAISS to retrieve a limited number of documents, use the complete product list as context
    context = "\n".join(products)

    # Generate response using Groq API with LLaMA 3
    response = generate_response_with_groq(query, context)

    # Print the response
    print("\nGenerated Response:\n", response)

if __name__ == "__main__":
    main()
