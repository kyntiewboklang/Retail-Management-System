from database import get_db_connection


def create_users_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Users table created successfully.")


def create_products_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            brand VARCHAR(100),
            price NUMERIC(10,2),
            quantity INTEGER,
            sku VARCHAR(100) UNIQUE,
            supplier VARCHAR(255),
            description TEXT
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Products table created successfully.")