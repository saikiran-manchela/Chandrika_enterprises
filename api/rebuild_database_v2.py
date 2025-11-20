import sqlite3
import csv
import os
from datetime import datetime

class DatabaseRebuilderV2:
    def __init__(self, db_name="invoice_system.db", csv_file="db.csv"):
        self.db_name = db_name
        self.csv_file = csv_file
        
    def backup_old_database(self):
        """Backup existing database"""
        if os.path.exists(self.db_name):
            backup_name = f"{self.db_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.db_name, backup_name)
            print(f"Existing database backed up to: {backup_name}")
        
    def create_new_database(self):
        """Create new database with updated schema for distinct product-weight combinations"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create products table - each product-weight combination is a separate record
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                weight TEXT,
                full_product_name TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price REAL NOT NULL DEFAULT 0,
                selling_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create invoices table
        cursor.execute('''
            CREATE TABLE invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                customer_address TEXT,
                subtotal REAL NOT NULL,
                cgst_amount REAL NOT NULL,
                sgst_amount REAL NOT NULL,
                total_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create invoice_items table with weight column
        cursor.execute('''
            CREATE TABLE invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                weight TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("New database schema created successfully!")
    
    def import_csv_data(self):
        """Import data from CSV file - each product-weight combination as separate record"""
        if not os.path.exists(self.csv_file):
            print(f"CSV file {self.csv_file} not found!")
            return False
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                
                print(f"CSV columns: {csv_reader.fieldnames}")
                
                for row in csv_reader:
                    # Skip empty rows
                    if not row['Product'].strip():
                        skipped_count += 1
                        continue
                    
                    product_name = row['Product'].strip()
                    weight = row['Weight'].strip() if row['Weight'] else ''
                    quantity = int(row['Quantity']) if row['Quantity'].strip() else 0
                    cost_price = float(row['Cost Price']) if row['Cost Price'].strip() else 0.0
                    selling_price = float(row['Selling Price']) if row['Selling Price'].strip() else 0.0
                    
                    # Create full product name (product + weight combination)
                    if weight:
                        full_product_name = f"{product_name} ({weight})"
                    else:
                        full_product_name = product_name
                    
                    # Skip if essential data is missing
                    if not product_name or selling_price <= 0:
                        skipped_count += 1
                        continue
                    
                    try:
                        cursor.execute('''
                            INSERT INTO products (product_name, weight, full_product_name, quantity, cost_price, selling_price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (product_name, weight, full_product_name, quantity, cost_price, selling_price))
                        imported_count += 1
                        
                        if imported_count <= 5:
                            print(f"Imported: {full_product_name} - Qty: {quantity}, Price: ₹{selling_price}")
                        
                    except sqlite3.IntegrityError:
                        # Skip duplicates
                        skipped_count += 1
                        if imported_count <= 10:
                            print(f"Skipped duplicate: {full_product_name}")
                
                conn.commit()
                print(f"\nData import completed!")
                print(f"Products imported: {imported_count}")
                print(f"Rows skipped: {skipped_count}")
                return True
                
        except Exception as e:
            print(f"Error importing data: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def verify_import(self):
        """Verify the imported data"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE weight IS NOT NULL AND weight != ""')
        products_with_weight = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE cost_price > 0')
        products_with_cost = cursor.fetchone()[0]
        
        # Count unique base product names
        cursor.execute('SELECT COUNT(DISTINCT product_name) FROM products')
        unique_base_products = cursor.fetchone()[0]
        
        print(f"\n=== IMPORT VERIFICATION ===")
        print(f"Total product records in database: {total_products}")
        print(f"Unique base products: {unique_base_products}")
        print(f"Products with weight information: {products_with_weight}")
        print(f"Products with cost price: {products_with_cost}")
        
        # Show sample products by base product name
        cursor.execute('''
            SELECT product_name, weight, full_product_name, quantity, cost_price, selling_price 
            FROM products 
            ORDER BY product_name, weight 
            LIMIT 10
        ''')
        sample_products = cursor.fetchall()
        
        print(f"\n=== SAMPLE PRODUCTS ===")
        current_base_product = ""
        for product in sample_products:
            if product[0] != current_base_product:
                current_base_product = product[0]
                print(f"\n{current_base_product}:")
            print(f"  {product[2]} - Qty: {product[3]}, Cost: ₹{product[4]}, Selling: ₹{product[5]}")
        
        # Show product count by base name
        cursor.execute('''
            SELECT product_name, COUNT(*) as variant_count
            FROM products 
            GROUP BY product_name 
            HAVING COUNT(*) > 1
            ORDER BY variant_count DESC
            LIMIT 5
        ''')
        multi_variant_products = cursor.fetchall()
        
        print(f"\n=== PRODUCTS WITH MULTIPLE SIZES/WEIGHTS ===")
        for product, count in multi_variant_products:
            print(f"{product}: {count} variants")
        
        conn.close()
    
    def rebuild_database(self):
        """Complete database rebuild process"""
        print("=== STARTING DATABASE REBUILD V2 (PRODUCT-WEIGHT COMBINATIONS) ===")
        
        # Step 1: Backup existing database
        self.backup_old_database()
        
        # Step 2: Create new database
        self.create_new_database()
        
        # Step 3: Import CSV data
        if self.import_csv_data():
            # Step 4: Verify import
            self.verify_import()
            print("\n=== DATABASE REBUILD V2 COMPLETED SUCCESSFULLY! ===")
            print("\nNow each product-weight combination is stored as a separate inventory item.")
            print("This allows proper tracking of different sizes/weights of the same product.")
        else:
            print("\n=== DATABASE REBUILD V2 FAILED! ===")

if __name__ == "__main__":
    rebuilder = DatabaseRebuilderV2()
    rebuilder.rebuild_database()