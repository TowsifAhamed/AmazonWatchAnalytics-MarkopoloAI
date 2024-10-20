import psycopg2
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
from transformers import AutoTokenizer

# Step 1: Set up environment
groq_api_key = None
client = Groq(api_key=groq_api_key)

# Initialize the SentenceTransformer model for embedding generation
embedding_model = SentenceTransformer('distilbert-base-nli-mean-tokens')

# Tokenizer to estimate token counts
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Constants for LLM constraints
MAX_TOKENS = 30000
CONTEXT_TOKEN_LIMIT = 4000

# Step 2: Extract watch data from PostgreSQL
def extract_watch_data():
    conn = psycopg2.connect(
        dbname="amznwatchesdb",
        user="amznwatchuser",
        password="amznwatchpass",
        host="localhost"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, discounted_price, product_details, category, ratings, store_name, customer_say FROM products")
    products = cursor.fetchall()
    conn.close()

    processed_products = []
    for product in products:
        id, name, discounted_price, product_details, category, ratings, store_name, customer_say = product
        processed_products.append({
            "id": id,
            "content": f"Product: {name}, Price: ${discounted_price}, Category: {category}, Ratings: {ratings}, Store: {store_name}, Details: {product_details}, Customer Reviews: {customer_say}"
        })

    return processed_products

# Step 3: Create embeddings for watch data and store them in a Faiss index
def create_faiss_index(product_data):
    texts = [product['content'] for product in product_data]
    embeddings = embedding_model.encode(texts)

    # Create a Faiss index for similarity search
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))

    return faiss_index, product_data

# Step 4: Retrieve relevant documents based on query
def retrieve_relevant_documents(query, faiss_index, product_data):
    # Convert the query to an embedding
    query_embedding = embedding_model.encode([query])

    # Use Faiss to search for similar embeddings
    _, indices = faiss_index.search(np.array(query_embedding), k=15)

    # Extract the relevant product content
    relevant_docs = [product_data[idx]['content'] for idx in indices[0]]
    
    return relevant_docs

# Step 5: Generate response with Groq API using retrieved documents as context
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

# Step 6: Main function to run the end-to-end process
def main():
    # User query
    query = "Can you suggest some water-resistant ladies watches under $200?"

    # Extract watch data from PostgreSQL
    product_data = extract_watch_data()

    # Create Faiss index with embeddings for product data
    faiss_index, product_data = create_faiss_index(product_data)

    # Retrieve relevant documents based on the query
    relevant_docs = retrieve_relevant_documents(query, faiss_index, product_data)
    print(relevant_docs)

    # Use the retrieved documents as context for the LLM
    context = "\n".join(relevant_docs)

    # Generate a response using Groq API with the retrieved context
    response = generate_response_with_groq(query, context)

    # Print the response
    print("\nGenerated Response:\n", response)

if __name__ == "__main__":
    main()


# Generated Response:
#  Based on the provided context, here are some water-resistant ladies' watches under $200:

# 1. Casio Women's LRW200H-7BVCF Dive Series Sport Watch - Price: $22.80, Water-resistant up to 100m (330 feet)
# 2. Armitron Sport Women's Digital Chronograph Resin Strap Watch, 45/7012 - Price: $12.98, Water-resistant up to 100m (330 feet)
# 3. Armitron Women's Easy to Read Bracelet Watch, 75-5304 - Price: $32.99, Water-resistant up to 50m (165 feet)
# 4. Anne Klein Women's Date Function Bracelet Watch - Price: $25.86, Water-resistant up to 30m (99 feet)
# 5. Timex Women's Easy Reader Watch - Price: $39.00, Water-resistant up to 30m (100 feet)

# Note that the water resistance levels of these watches are:

# * Casio and Armitron watch series: 100m (330 feet)
# * Armitron Women's Easy to Read Bracelet Watch: 50m (165 feet)
# * Anne Klein Women's Date Function Bracelet Watch and Timex Women's Easy Reader Watch: 30m (99/100 feet)

# Please keep in mind that while these watches are water-resistant, they are not intended for deep-sea diving or swimming in rough waters. Additionally, it's always a good idea to check the manufacturer's specifications and reviews from other customers to ensure that the watch is suitable for your needs.