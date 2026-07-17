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
            barcode VARCHAR(50) UNIQUE,
            supplier VARCHAR(255)
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

def create_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    #Sale table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sales(
            id SERIAL PRIMARY KEY,
            staff_id INTEGER,
            payment_method VARCHAR(20),
            total DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)

    #Sale Items table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sale_items(
            id SERIAL PRIMARY KEY,
            sale_id INTEGER REFERENCES sales(id),
            product_id INTEGER,
            quantity INTEGER,
            price DECIMAL(10,2)
        )
    """)

    #Job vacancieq table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS job_vacancies (
            id SERIAL PRIMARY KEY,
            position VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            vacancies INTEGER NOT NULL,
            salary DECIMAL(10,2),
            requirements TEXT,
            deadline DATE,
            status VARCHAR(20) DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    #Job Application table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS job_applications (
            id SERIAL PRIMARY KEY,
            vacancy_id INTEGER REFERENCES job_vacancies(id),
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            qualification VARCHAR(100),
            experience TEXT,
            resume VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    #Interview table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            application_id INTEGER REFERENCES job_applications(id),
            interview_date DATE,
            interview_time TIME,
            interviewer VARCHAR(100),
            interview_type VARCHAR(50),
            location VARCHAR(255),
            remarks TEXT,
            status VARCHAR(20) DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Table created successfully.")