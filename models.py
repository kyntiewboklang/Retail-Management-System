from database import get_db_connection


def create_users_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL
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
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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

            user_id INTEGER NOT NULL,

            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            total_amount NUMERIC(10,2) NOT NULL,

            payment_method VARCHAR(50) NOT NULL,

            FOREIGN KEY (user_id) REFERENCES users(id)

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

            user_id INT NOT NULL,

            product_id INT NOT NULL,

            quantity INT NOT NULL,

            price NUMERIC(10,2) NOT NULL,

            subtotal NUMERIC(10,2) NOT NULL,

            FOREIGN KEY (order_id) REFERENCES orders(id),

            FOREIGN KEY (product_id) REFERENCES products(id),

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("order item created successfully")

def create_staff_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (

            id SERIAL PRIMARY KEY,

            admin_id INTEGER NOT NULL,

            username VARCHAR(100) NOT NULL,

            email VARCHAR(100) UNIQUE NOT NULL,

            phone VARCHAR(20) NOT NULL,

            password VARCHAR(255) NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (admin_id)
                REFERENCES users(id)
                ON DELETE CASCADE

        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Staff table created successfully.")