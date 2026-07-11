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

def create_orders_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (

        id SERIAL PRIMARY KEY,

        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        total_amount NUMERIC(10,2) NOT NULL,

        payment_method VARCHAR(50) NOT NULL

    )
""")

    conn.commit()
    cursor.close()
    conn.close()
        
    print("order table create successfuly")

def create_order_items_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (

            id SERIAL PRIMARY KEY,

            order_id INT NOT NULL,

            product_id INT NOT NULL,

            quantity INT NOT NULL,

            price NUMERIC(10,2) NOT NULL,

            subtotal NUMERIC(10,2) NOT NULL,

            FOREIGN KEY (order_id) REFERENCES orders(id),

            FOREIGN KEY (product_id) REFERENCES products(id)

        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("order item created successfully")