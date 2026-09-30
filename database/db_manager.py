"""
AEMG Star-Schema Enterprise Data Warehouse Manager
Provides schema catalog introspection and query execution with SQLite fallback and PostgreSQL support.
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "datawarehouse.db", pg_conn_str: Optional[str] = None):
        self.db_path = db_path
        self.pg_conn_str = pg_conn_str
        self.is_postgres = False
        self.active_engine = "SQLite (Fallback/Demo)"
        
        if pg_conn_str:
            self.set_postgres_db(pg_conn_str)
        else:
            self.set_sqlite_db(db_path)

    def set_sqlite_db(self, db_path: str):
        """Switches the active database to a specific SQLite file."""
        self.db_path = db_path
        self.is_postgres = False
        self.active_engine = f"SQLite: {os.path.basename(db_path)}"
        self.init_sqlite_warehouse()

    def set_postgres_db(self, conn_str: str) -> Tuple[bool, Optional[str]]:
        """
        Attempts to connect to PostgreSQL. If psycopg2 is available and connection succeeds,
        sets PostgreSQL as the active primary engine. Otherwise falls back to SQLite.
        """
        try:
            import psycopg2
            conn = psycopg2.connect(conn_str)
            conn.close()
            self.pg_conn_str = conn_str
            self.is_postgres = True
            self.active_engine = "PostgreSQL (Enterprise Warehouse)"
            return True, None
        except ImportError:
            self.is_postgres = False
            self.active_engine = "SQLite (Fallback: psycopg2 not installed)"
            return False, "psycopg2 is not installed. To connect to PostgreSQL run: pip install psycopg2-binary"
        except Exception as e:
            self.is_postgres = False
            self.active_engine = "SQLite (Fallback: PostgreSQL unreachable)"
            return False, f"PostgreSQL connection failed: {str(e)}"

    def init_sqlite_warehouse(self, force_recreate: bool = False):
        """Initializes the Star-Schema Sales Data Warehouse with sample records."""
        need_seed = force_recreate or not os.path.exists(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if need_seed:
            cursor.executescript("""
                DROP TABLE IF EXISTS fact_sales;
                DROP TABLE IF EXISTS dim_customer;
                DROP TABLE IF EXISTS dim_product;
                DROP TABLE IF EXISTS dim_store;
                DROP TABLE IF EXISTS dim_date;
            """)
            
            cursor.execute("""
                CREATE TABLE dim_customer (
                    customer_id INTEGER PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    customer_segment TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE dim_product (
                    product_id INTEGER PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sub_category TEXT NOT NULL,
                    unit_cost REAL NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE dim_store (
                    store_id INTEGER PRIMARY KEY,
                    store_name TEXT NOT NULL,
                    region TEXT NOT NULL,
                    market_type TEXT NOT NULL,
                    store_size TEXT NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE dim_date (
                    date_id INTEGER PRIMARY KEY,
                    full_date TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    month_name TEXT NOT NULL,
                    day_of_week TEXT NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE fact_sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    store_id INTEGER NOT NULL,
                    date_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    discount REAL NOT NULL,
                    gross_revenue REAL NOT NULL,
                    profit REAL NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
                    FOREIGN KEY (product_id) REFERENCES dim_product (product_id),
                    FOREIGN KEY (store_id) REFERENCES dim_store (store_id),
                    FOREIGN KEY (date_id) REFERENCES dim_date (date_id)
                );
            """)
            
            customers = [
                (1, "Acme Corp", "Corporate", "USA", "New York", "NY"),
                (2, "Apex Logistics", "Corporate", "USA", "Chicago", "IL"),
                (3, "John Doe", "Consumer", "USA", "Seattle", "WA"),
                (4, "Jane Smith", "Consumer", "UK", "London", "Greater London"),
                (5, "Quantum Dynamics", "Enterprise", "Germany", "Munich", "Bavaria"),
                (6, "Global Reach Media", "Corporate", "Canada", "Toronto", "ON"),
                (7, "Emily Davis", "Home Office", "USA", "Austin", "TX"),
                (8, "TechNova Labs", "Enterprise", "Japan", "Tokyo", "Kanto"),
                (9, "Carlos Mendez", "Consumer", "Mexico", "Mexico City", "CDMX"),
                (10, "Nordic Soft", "Corporate", "Sweden", "Stockholm", "Stockholm")
            ]
            cursor.executemany("INSERT INTO dim_customer VALUES (?, ?, ?, ?, ?, ?)", customers)
            
            products = [
                (101, "UltraBook Pro 15", "Technology", "Laptops", 850.0),
                (102, "CloudServer Blade X", "Technology", "Servers", 2200.0),
                (103, "Ergonomic Mesh Chair", "Furniture", "Chairs", 140.0),
                (104, "Standing Desk Executive", "Furniture", "Desks", 310.0),
                (105, "Wireless Noise-Canceling Headset", "Technology", "Accessories", 65.0),
                (106, "Heavy-Duty Archival Binder", "Office Supplies", "Binders", 4.5),
                (107, "Laser Toner Multi-Pack", "Office Supplies", "Consumables", 75.0),
                (108, "Conference Hub 4K", "Technology", "Conferencing", 450.0),
                (109, "Modular Lounge Ottoman", "Furniture", "Furnishings", 110.0),
                (110, "Security Badge Scanner", "Technology", "Security", 195.0)
            ]
            cursor.executemany("INSERT INTO dim_product VALUES (?, ?, ?, ?, ?)", products)
            
            stores = [
                (1, "North Metro Flagship", "North America", "Enterprise", "Large"),
                (2, "Midwest Hub Store", "North America", "Retail", "Medium"),
                (3, "Pacific Rim Direct", "APAC", "Online", "Large"),
                (4, "EMEA Central Depot", "EMEA", "Enterprise", "Large"),
                (5, "London Tech Center", "EMEA", "Retail", "Medium"),
                (6, "LATAM Wholesale Hub", "LATAM", "Wholesale", "Large"),
                (7, "Nordic Outlet", "EMEA", "Retail", "Small"),
                (8, "Tokyo Cyber Mall", "APAC", "Retail", "Large")
            ]
            cursor.executemany("INSERT INTO dim_store VALUES (?, ?, ?, ?, ?)", stores)
            
            start_date = datetime(2025, 1, 1)
            date_records = []
            for d in range(365):
                curr = start_date + timedelta(days=d)
                d_id = int(curr.strftime("%Y%m%d"))
                month_name = curr.strftime("%B")
                dow = curr.strftime("%A")
                quarter = (curr.month - 1) // 3 + 1
                date_records.append((d_id, curr.strftime("%Y-%m-%d"), curr.year, quarter, curr.month, month_name, dow))
            cursor.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?)", date_records)
            
            random.seed(42)
            sales_records = []
            prod_costs = {p[0]: p[4] for p in products}
            
            for s_id in range(1, 5001):
                c_id = random.choice(customers)[0]
                p_id = random.choice(products)[0]
                st_id = random.choice(stores)[0]
                dt_id = random.choice(date_records)[0]
                
                qty = random.randint(1, 15)
                base_cost = prod_costs[p_id]
                markup = random.uniform(1.25, 1.85)
                unit_price = round(base_cost * markup, 2)
                discount = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])
                gross_revenue = round(qty * unit_price, 2)
                net_revenue = gross_revenue * (1.0 - discount)
                total_cost = round(qty * base_cost, 2)
                profit = round(net_revenue - total_cost, 2)
                
                sales_records.append((s_id, c_id, p_id, st_id, dt_id, qty, unit_price, discount, gross_revenue, profit))
                
            cursor.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sales_records)
            conn.commit()
            
        conn.close()

    def get_catalog_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Agent 1: Schema Introspection.
        Directly reads database catalog without LLM overhead.
        Supports both PostgreSQL information_schema and SQLite catalogs.
        """
        if self.is_postgres and self.pg_conn_str:
            try:
                import psycopg2
                conn = psycopg2.connect(self.pg_conn_str)
                cursor = conn.cursor()
                
                # Fetch tables in public schema
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
                """)
                tables = [r[0] for r in cursor.fetchall()]
                
                schema = {}
                for tbl in tables:
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable 
                        FROM information_schema.columns 
                        WHERE table_name = %s;
                    """, (tbl,))
                    cols_raw = cursor.fetchall()
                    
                    columns = [{
                        "name": c[0],
                        "type": c[1],
                        "notnull": c[2] == 'NO',
                        "pk": False
                    } for c in cols_raw]
                    
                    schema[tbl] = {
                        "columns": columns,
                        "column_names": [c["name"] for c in columns],
                        "foreign_keys": []
                    }
                conn.close()
                return schema
            except Exception:
                # If Postgres introspection fails, fall back to SQLite
                self.is_postgres = False

        # SQLite Schema Introspection
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        
        schema = {}
        for tbl in tables:
            cursor.execute(f"PRAGMA table_info({tbl});")
            col_info = cursor.fetchall()
            cursor.execute(f"PRAGMA foreign_key_list({tbl});")
            fk_info = cursor.fetchall()
            
            columns = []
            for col in col_info:
                columns.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "dflt_value": col[4],
                    "pk": bool(col[5])
                })
                
            foreign_keys = []
            for fk in fk_info:
                foreign_keys.append({
                    "from_column": fk[3],
                    "target_table": fk[2],
                    "target_column": fk[4]
                })
                
            schema[tbl] = {
                "columns": columns,
                "column_names": [c["name"] for c in columns],
                "foreign_keys": foreign_keys
            }
            
        conn.close()
        return schema

    def execute_query(self, sql_query: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Agent 5: Execution Agent.
        Executes query against the active database and returns (result_rows, error_message).
        """
        if self.is_postgres and self.pg_conn_str:
            try:
                import psycopg2
                import psycopg2.extras
                conn = psycopg2.connect(self.pg_conn_str)
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                conn.close()
                return results, None
            except Exception as e:
                # If error is a connection failure, fall back to SQLite
                if "connection" in str(e).lower():
                    self.is_postgres = False
                else:
                    return None, str(e)

        # SQLite execution
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()
            return results, None
        except Exception as e:
            return None, str(e)
