import psycopg2
import numpy as np
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from groq import Groq
import re

# Step 1: Set up environment
# Initialize Groq client with the API key
groq_api_key = 
client = Groq(api_key=groq_api_key)

# Step 2: Extract data from PostgreSQL
def extract_data():
    conn = psycopg2.connect(
        dbname="amznwatchesdb",
        user="amznwatchuser",
        password="amznwatchpass",
        host="localhost"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, discounted_price, product_details, category, ratings, ratings_num, store_name, customer_say FROM products")
    products = cursor.fetchall()
    conn.close()

    processed_products = []
    for product in products:
        id, name, discounted_price, product_details, category, ratings, ratings_num, store_name, customer_say = product
        ratings = 0.0 if ratings == "N/A" else float(re.search(r"\d+\.\d+", ratings).group()) if re.search(r"\d+\.\d+", ratings) else 0.0
        ratings_num = 0 if ratings_num == "N/A" else int(ratings_num)
        processed_products.append(f"Product: {name}, Price: ${discounted_price}, Category: {category}, Ratings: {ratings}, Ratings Count: {ratings_num}, Store: {store_name}, Details: {product_details}, Customer Review Summary: {customer_say}")
    
    return processed_products

# Step 3: Create FAISS index using LangChain
def create_faiss_index(docs):
    embeddings = HuggingFaceEmbeddings(model_name='distilbert-base-nli-mean-tokens')
    faiss_index = FAISS.from_texts(docs, embeddings)
    return faiss_index

# Step 4: Retrieve documents based on query
def retrieve_documents(query, faiss_index):
    retriever = faiss_index.as_retriever()
    results = retriever.get_relevant_documents(query)
    return results

# Step 5: Generate response with Groq API
def generate_response_with_groq(query, context):
    prompt = f"""
    Below is the context of several products and a question. Use the context to provide an answer to the question.
    
    Context:
    {context}
    
    Question: {query}
    Answer:
    """

    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192"
    )

    # Extract the relevant response text
    response_text = response.choices[0].message.content.strip()
    return response_text

# Step 6: Main function
def main():
    # Extract data from PostgreSQL
    products = extract_data()

    # Create FAISS index with LangChain
    faiss_index = create_faiss_index(products)

    # User query
    query = "What are the best smartwatches under $300?"

    # Retrieve documents
    retrieved_docs = retrieve_documents(query, faiss_index)
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    print("context: ", context)

    # Generate response using Groq API with LLaMA 3
    response = generate_response_with_groq(query, context)

    # Print the response
    print("\nGenerated Response:\n", response)

if __name__ == "__main__":
    main()