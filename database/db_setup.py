import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_server_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Server: {e}")
        return None

def create_database():
    connection = create_server_connection()
    if connection is None:
        return

    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('MYSQL_DATABASE')}")
        connection.commit()
    except Error as e:
        print(f"Error creating database: {e}")
    cursor.close()
    connection.close()

def create_database_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def initialize_database():
    create_database()
    connection = create_database_connection()
    if connection is None:
        return

    cursor = connection.cursor()

    # Create vehicles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INT NOT NULL AUTO_INCREMENT,
            model VARCHAR(255),
            year INT,
            vin VARCHAR(17),
            current_mileage FLOAT,
            battery_level FLOAT,
            tire_pressure JSON,
            engine_oil_life FLOAT,
            last_service_date DATE,
            PRIMARY KEY (id)
        )
    """)

    # Create maintenance_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id INT NOT NULL AUTO_INCREMENT,
            vehicle_id INT,
            service_date DATE,
            service_type VARCHAR(255),
            mileage FLOAT,
            description TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)

    # Create emergency_contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            relation VARCHAR(50) NOT NULL,
            PRIMARY KEY (id)
        )
    """)

    # Create police_stations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS police_stations (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(255) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            latitude DECIMAL(10,8) NOT NULL,
            longitude DECIMAL(11,8) NOT NULL,
            PRIMARY KEY (id)
        )
    """)

    # Insert sample data
    try:
        # Insert vehicles
        cursor.executemany("""
            INSERT INTO vehicles (model, year, vin, current_mileage, battery_level, 
                                tire_pressure, engine_oil_life, last_service_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            ('ID.4', 2024, 'WVGZZZE2ZMP123456', 15000.5, 85.5, 
             '{"FL": 32, "FR": 32, "RL": 32, "RR": 32}', 75.0, '2024-01-15'),
            ('Golf GTI', 2023, 'WVWZZZ1KZNW987654', 22000.0, None,
             '{"FL": 35, "FR": 35, "RL": 35, "RR": 34}', 45.0, '2023-12-01')
        ])

        # Insert emergency contacts
        cursor.execute("""
            INSERT INTO emergency_contacts (name, phone_number, relation)
            VALUES ('Himanshu Mohanty', '+917008719907', 'brother')
        """)

        # Insert police stations
        cursor.executemany("""
            INSERT INTO police_stations (name, address, phone_number, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
        """, [
            ('Patia Police Station', 'Patia Square, Bhubaneswar', '+917008719907', 
             20.351829, 85.824936),
            ('Chandrasekharpur Police Station', 'Chandrasekharpur, Bhubaneswar', 
             '+917008719907', 20.343242, 85.819873)
        ])

        connection.commit()
    except Error as e:
        print(f"Error inserting sample data: {e}")

    cursor.close()
    connection.close()