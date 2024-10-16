import psycopg2
import time
import json
from flask import Flask, request, jsonify
# Import required functions from LLM_RAG.py
from LLM_RAG import extract_data, generate_response_with_groq

app = Flask(__name__)

# Function to connect to PostgreSQL database
def get_db_connection():
    return psycopg2.connect(
        dbname="amznwatchesdb",
        user="amznwatchuser",
        password="amznwatchpass",
        host="localhost"
    )

# Utility function to parse ratings from string
def parse_rating(rating_str):
    try:
        if rating_str == "N/A":
            return None
        return float(rating_str.split(" ")[0])
    except:
        return None

# REST API: GET /products
@app.route('/products', methods=['GET'])
def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Extract query parameters
        brand = request.args.get('brand')
        model = request.args.get('model')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        min_rating = request.args.get('min_rating')
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))

        # Construct the query with filtering, sorting, and pagination
        query = "SELECT * FROM products WHERE TRUE"
        params = []

        if brand:
            query += " AND store_name ILIKE %s AND store_name != 'N/A'"
            params.append(f"%{brand}%")
        if model:
            query += " AND name ILIKE %s AND name != 'N/A'"
            params.append(f"%{model}%")
        if min_price:
            query += " AND discounted_price != 'N/A' AND discounted_price::float >= %s"
            params.append(min_price)
        if max_price:
            query += " AND discounted_price != 'N/A' AND discounted_price::float <= %s"
            params.append(max_price)
        if min_rating:
            query += " AND ratings != 'N/A' AND CAST(NULLIF(regexp_replace(ratings, '[^0-9.]', '', 'g'), '') AS FLOAT) >= %s"
            params.append(min_rating)

        query += f" ORDER BY {sort_by} {order}"
        offset = (page - 1) * limit
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        products = cursor.fetchall()

        # Return product details as JSON
        product_list = [
            {
                "id": product[0],
                "asin": product[1],
                "name": product[2] if product[2] != "N/A" else None,
                "original_price": product[3] if product[3] != "N/A" else None,
                "discounted_price": product[4] if product[4] != "N/A" else None,
                "delivery_price": product[5] if product[5] != "N/A" else None,
                "ratings": parse_rating(product[6]),
                "ratings_num": product[7] if product[7] != "N/A" else None,
                "link": product[8] if product[8] != "N/A" else None,
                "ratings_link": product[9] if product[9] != "N/A" else None,
                "category": product[10] if product[10] != "N/A" else None,
                "page_number": product[11],
                "image_link": product[12] if product[12] != "N/A" else None,
                "store_name": product[13] if product[13] != "N/A" else None,
                "store_url": product[14] if product[14] != "N/A" else None,
                "purchase_num": product[15] if product[15] != "N/A" else None,
                "shipping_import_fees": product[16] if product[16] != "N/A" else None,
                "colors": product[17] if product[17] != "N/A" else None,
                "product_details": product[18] if product[18] != "N/A" else None,
                "customer_say": product[19] if product[19] != "N/A" else None
            } for product in products
        ]

        cursor.close()
        conn.close()

        return jsonify(product_list)

    except Exception as e:
        return jsonify({"error": str(e)})

# REST API: GET /products/top
@app.route('/products/top', methods=['GET'])
def get_top_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get top products based on ratings and number of reviews
        cursor.execute("""
            SELECT * FROM products
            WHERE ratings != 'N/A' AND ratings_num != 'N/A' AND ratings_num::int >= 50
            ORDER BY CAST(NULLIF(regexp_replace(ratings, '[^0-9.]', '', 'g'), '') AS FLOAT) DESC, ratings_num::int DESC
            LIMIT 10
        """)
        products = cursor.fetchall()

        top_products = []
        for product in products:
            product_dict = {
                "id": product[0],
                "asin": product[1],
                "name": product[2] if product[2] != "N/A" else None,
                "original_price": product[3] if product[3] != "N/A" else None,
                "discounted_price": product[4] if product[4] != "N/A" else None,
                "delivery_price": product[5] if product[5] != "N/A" else None,
                "ratings": parse_rating(product[6]),
                "ratings_num": product[7] if product[7] != "N/A" else None,
                "link": product[8] if product[8] != "N/A" else None,
                "ratings_link": product[9] if product[9] != "N/A" else None,
                "category": product[10] if product[10] != "N/A" else None,
                "page_number": product[11],
                "image_link": product[12] if product[12] != "N/A" else None,
                "store_name": product[13] if product[13] != "N/A" else None,
                "store_url": product[14] if product[14] != "N/A" else None,
                "purchase_num": product[15] if product[15] != "N/A" else None,
                "shipping_import_fees": product[16] if product[16] != "N/A" else None,
                "colors": product[17] if product[17] != "N/A" else None,
                "product_details": product[18] if product[18] != "N/A" else None,
                "customer_say": product[19] if product[19] != "N/A" else None,
                "reviews": []
            }

            # Get reviews for each product
            cursor.execute("SELECT * FROM reviews WHERE product_id = %s", (product[0],))
            reviews = cursor.fetchall()
            product_dict["reviews"] = [
                {
                    "id": review[0],
                    "product_id": review[1],
                    "name": review[2],
                    "url": review[3],
                    "rating": review[4] if review[4] != "N/A" else None,
                    "title": review[5],
                    "date": review[6],
                    "color": review[7],
                    "verified_purchase": review[8],
                    "review_text": review[9],
                    "helpful_count": review[10],
                    "image_link": review[11]
                } for review in reviews
            ]

            top_products.append(product_dict)

        cursor.close()
        conn.close()

        return jsonify(top_products)

    except Exception as e:
        return jsonify({"error": str(e)})

# REST API: GET /products/{product_id}/reviews
@app.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Extract pagination parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        # Query to get reviews for the product
        cursor.execute("SELECT * FROM reviews WHERE product_id = %s LIMIT %s OFFSET %s", (product_id, limit, offset))
        reviews = cursor.fetchall()

        review_list = [
            {
                "id": review[0],
                "product_id": review[1],
                "name": review[2],
                "url": review[3],
                "rating": review[4] if review[4] != "N/A" else None,
                "title": review[5],
                "date": review[6],
                "color": review[7],
                "verified_purchase": review[8],
                "review_text": review[9],
                "helpful_count": review[10],
                "image_link": review[11]
            } for review in reviews
        ]

        cursor.close()
        conn.close()

        return jsonify(review_list)

    except Exception as e:
        return jsonify({"error": str(e)})

# REST API: POST /ask_query
@app.route('/ask_query', methods=['POST'])
def ask_query():
    try:
        # Extract the query from the POST request
        data = request.get_json()
        user_query = data.get('query', '')

        if not user_query:
            return jsonify({"error": "Query is required"}), 400

        # Step 1: Extract data from PostgreSQL based on the user's query
        products = extract_data(user_query)

        if not products:
            return jsonify({"error": "No products retrieved from the database"}), 404

        # Step 2: Use the complete product list as context to generate response
        context = "\n".join(products)

        # Step 3: Generate response using Groq API
        response = generate_response_with_groq(user_query, context)

        # Return the response
        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
