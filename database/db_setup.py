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
            id INT AUTO_INCREMENT PRIMARY KEY,
            model VARCHAR(255),
            year INT,
            vin VARCHAR(17),
            current_mileage FLOAT,
            battery_level FLOAT,
            tire_pressure JSON,
            engine_oil_life FLOAT,
            last_service_date DATE
        )
    """)

    # Create maintenance_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_id INT,
            service_date DATE,
            service_type VARCHAR(255),
            mileage FLOAT,
            description TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)

    # Insert sample vehicle data
    sample_vehicle = """
        INSERT INTO vehicles (model, year, vin, current_mileage, battery_level, 
                            tire_pressure, engine_oil_life, last_service_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    vehicle_data = [
        ('ID.4', 2024, 'WVGZZZE2ZMP123456', 15000.5, 85.5, 
         '{"FL": 32, "FR": 32, "RL": 32, "RR": 32}', 75.0, '2024-01-15'),
        ('Golf GTI', 2023, 'WVWZZZ1KZNW987654', 22000.0, None,
         '{"FL": 35, "FR": 35, "RL": 35, "RR": 34}', 45.0, '2023-12-01')
    ]

    try:
        cursor.executemany(sample_vehicle, vehicle_data)
        connection.commit()
    except Error as e:
        print(f"Error inserting sample data: {e}")

    cursor.close()
    connection.close()