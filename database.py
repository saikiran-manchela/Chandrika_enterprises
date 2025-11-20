import sqlite3
import os
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="invoice_system.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                weight TEXT,
                full_product_name TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                damaged_quantity INTEGER NOT NULL DEFAULT 0,
                cost_price REAL NOT NULL DEFAULT 0,
                selling_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add damaged_quantity column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN damaged_quantity INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
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
        
        # Create invoice_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
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
        
        # Create users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create default admin user if no users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            default_password = "admin123"  # You should change this
            password_hash = self._hash_password(default_password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name)
                VALUES (?, ?, ?, ?)
            ''', ("admin", password_hash, "admin@company.com", "Administrator"))
            print(f"Default admin user created. Username: admin, Password: {default_password}")
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, email=None, full_name=None):
        """Create a new user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, full_name))
            conn.commit()
            return True, "User created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists!"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute('''
                SELECT id, username, email, full_name, is_active 
                FROM users 
                WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            if user:
                # Update last login time
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                return True, {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3],
                    'is_active': user[4]
                }
            else:
                return False, None
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False, None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, email, full_name, created_at, last_login, is_active
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3],
                    'created_at': user[4],
                    'last_login': user[5],
                    'is_active': user[6]
                }
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
        finally:
            conn.close()
    
    def add_product(self, product_name, quantity, selling_price, weight=None, cost_price=0):
        """Add a new product to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create full product name
        if weight:
            full_product_name = f"{product_name} ({weight})"
        else:
            full_product_name = product_name
        
        try:
            cursor.execute('''
                INSERT INTO products (product_name, weight, full_product_name, quantity, cost_price, selling_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_name, weight, full_product_name, quantity, cost_price, selling_price))
            conn.commit()
            return True, "Product added successfully!"
        except sqlite3.IntegrityError:
            return False, "Product already exists!"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def get_product(self, full_product_name):
        """Get product details by full product name (includes weight)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products WHERE full_product_name = ?
        ''', (full_product_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'product_name': result[1],
                'weight': result[2],
                'full_product_name': result[3],
                'quantity': result[4],
                'cost_price': result[5],
                'selling_price': result[6],
                'created_at': result[7],
                'updated_at': result[8],
                'damaged_quantity': result[9] if len(result) > 9 else 0
            }
        return None
    
    def get_all_products(self):
        """Get all products from database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products ORDER BY product_name, weight')
        results = cursor.fetchall()
        conn.close()
        
        products = []
        for result in results:
            products.append({
                'id': result[0],
                'product_name': result[1],
                'weight': result[2],
                'full_product_name': result[3],
                'quantity': result[4],
                'cost_price': result[5],
                'selling_price': result[6],
                'created_at': result[7],
                'updated_at': result[8],
                'damaged_quantity': result[9] if len(result) > 9 else 0
            })
        
        return products
    
    def update_product_quantity(self, full_product_name, new_quantity):
        """Update product quantity using full product name"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE products 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE full_product_name = ?
            ''', (new_quantity, full_product_name))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "Product quantity updated successfully!"
            else:
                return False, "Product not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def reduce_stock(self, full_product_name, quantity_sold):
        """Reduce stock after sale using full product name"""
        product = self.get_product(full_product_name)
        if not product:
            return False, "Product not found!"
        
        if product['quantity'] < quantity_sold:
            return False, "Insufficient stock!"
        
        new_quantity = product['quantity'] - quantity_sold
        return self.update_product_quantity(full_product_name, new_quantity)
    
    def update_damaged_quantity(self, full_product_name, damaged_quantity):
        """Update damaged quantity for a product"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE products 
                SET damaged_quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE full_product_name = ?
            ''', (damaged_quantity, full_product_name))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "Damaged quantity updated successfully!"
            else:
                return False, "Product not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def mark_as_damaged(self, full_product_name, damaged_qty):
        """Mark products as damaged, reducing available stock and increasing damaged count"""
        product = self.get_product(full_product_name)
        if not product:
            return False, "Product not found!"
        
        if product['quantity'] < damaged_qty:
            return False, "Not enough stock to mark as damaged!"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Reduce regular quantity and increase damaged quantity
            new_quantity = product['quantity'] - damaged_qty
            new_damaged_quantity = product['damaged_quantity'] + damaged_qty
            
            cursor.execute('''
                UPDATE products 
                SET quantity = ?, damaged_quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE full_product_name = ?
            ''', (new_quantity, new_damaged_quantity, full_product_name))
            
            conn.commit()
            return True, f"Marked {damaged_qty} units as damaged. Available: {new_quantity}, Damaged: {new_damaged_quantity}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def restore_damaged(self, full_product_name, restore_qty):
        """Restore damaged products back to available stock"""
        product = self.get_product(full_product_name)
        if not product:
            return False, "Product not found!"
        
        if product['damaged_quantity'] < restore_qty:
            return False, "Not enough damaged stock to restore!"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Increase regular quantity and reduce damaged quantity
            new_quantity = product['quantity'] + restore_qty
            new_damaged_quantity = product['damaged_quantity'] - restore_qty
            
            cursor.execute('''
                UPDATE products 
                SET quantity = ?, damaged_quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE full_product_name = ?
            ''', (new_quantity, new_damaged_quantity, full_product_name))
            
            conn.commit()
            return True, f"Restored {restore_qty} units from damaged. Available: {new_quantity}, Damaged: {new_damaged_quantity}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def get_damaged_products_report(self):
        """Get all products with damaged quantities"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT product_name, weight, full_product_name, quantity, damaged_quantity, 
                       cost_price, selling_price, updated_at
                FROM products 
                WHERE damaged_quantity > 0
                ORDER BY damaged_quantity DESC, product_name
            ''')
            
            results = cursor.fetchall()
            
            damaged_products = []
            for result in results:
                damaged_products.append({
                    'product_name': result[0],
                    'weight': result[1],
                    'full_product_name': result[2],
                    'available_quantity': result[3],
                    'damaged_quantity': result[4],
                    'cost_price': result[5],
                    'selling_price': result[6],
                    'total_value_lost': result[4] * result[5],  # damaged_qty * cost_price
                    'updated_at': result[7]
                })
            
            return damaged_products
            
        except Exception as e:
            print(f"Error getting damaged products report: {str(e)}")
            return []
        finally:
            conn.close()
    
    def save_invoice(self, invoice_data, invoice_items):
        """Save invoice to database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Insert invoice
            cursor.execute('''
                INSERT INTO invoices (invoice_number, customer_name, customer_phone, 
                                    customer_address, subtotal, cgst_amount, sgst_amount, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['invoice_number'],
                invoice_data['customer_name'],
                invoice_data['customer_phone'],
                invoice_data['customer_address'],
                invoice_data['subtotal'],
                invoice_data['cgst_amount'],
                invoice_data['sgst_amount'],
                invoice_data['total_amount']
            ))
            
            invoice_id = cursor.lastrowid
            
            # Insert invoice items
            for item in invoice_items:
                cursor.execute('''
                    INSERT INTO invoice_items (invoice_id, product_name, weight, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (invoice_id, item['product_name'], item.get('weight', ''), item['quantity'], item['unit_price'], item['total_price']))
            
            conn.commit()
            return True, "Invoice saved successfully!"
        except Exception as e:
            conn.rollback()
            return False, f"Error saving invoice: {str(e)}"
        finally:
            conn.close()
    
    def get_sales_report_data(self, period='daily', start_date=None, end_date=None):
        """Get sales report data for specified period"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Base query to get sales data with product information
            base_query = '''
                SELECT 
                    ii.product_name,
                    ii.weight,
                    ii.quantity,
                    ii.unit_price,
                    ii.total_price,
                    i.created_at,
                    p.cost_price
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                LEFT JOIN products p ON ii.product_name = p.full_product_name
            '''
            
            params = []
            
            # Add date filtering
            if start_date and end_date:
                base_query += " WHERE date(i.created_at) BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif period == 'daily':
                base_query += " WHERE date(i.created_at) = date('now')"
            elif period == 'weekly':
                base_query += " WHERE date(i.created_at) >= date('now', '-7 days')"
            elif period == 'monthly':
                base_query += " WHERE date(i.created_at) >= date('now', '-30 days')"
            
            base_query += " ORDER BY i.created_at DESC"
            
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            return results
            
        except Exception as e:
            print(f"Error getting sales report data: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_profit_report(self, period='daily'):
        """Get profit report for specified period"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            date_filter = ""
            if period == 'daily':
                date_filter = "WHERE date(i.created_at) = date('now')"
            elif period == 'weekly':
                date_filter = "WHERE date(i.created_at) >= date('now', '-7 days')"
            elif period == 'monthly':
                date_filter = "WHERE date(i.created_at) >= date('now', '-30 days')"
            
            query = f'''
                SELECT 
                    ii.product_name,
                    ii.weight,
                    SUM(ii.quantity) as total_sold,
                    SUM(ii.total_price) as total_revenue,
                    AVG(p.cost_price) as avg_cost_price,
                    SUM(ii.quantity * p.cost_price) as total_cost,
                    SUM(ii.total_price) - SUM(ii.quantity * p.cost_price) as profit
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                LEFT JOIN products p ON ii.product_name = p.full_product_name
                {date_filter}
                GROUP BY ii.product_name, ii.weight
                ORDER BY profit DESC
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            return results
            
        except Exception as e:
            print(f"Error getting profit report: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_top_selling_products(self, period='monthly', limit=10):
        """Get most sold products for specified period"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            date_filter = ""
            if period == 'daily':
                date_filter = "WHERE date(i.created_at) = date('now')"
            elif period == 'weekly':
                date_filter = "WHERE date(i.created_at) >= date('now', '-7 days')"
            elif period == 'monthly':
                date_filter = "WHERE date(i.created_at) >= date('now', '-30 days')"
            
            query = f'''
                SELECT 
                    ii.product_name,
                    ii.weight,
                    SUM(ii.quantity) as total_sold,
                    SUM(ii.total_price) as total_revenue,
                    COUNT(DISTINCT i.id) as times_ordered
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                {date_filter}
                GROUP BY ii.product_name, ii.weight
                ORDER BY total_sold DESC
                LIMIT ?
            '''
            
            cursor.execute(query, [limit])
            results = cursor.fetchall()
            
            return results
            
        except Exception as e:
            print(f"Error getting top selling products: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_summary_stats(self, period='monthly'):
        """Get summary statistics for dashboard"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            date_filter = ""
            if period == 'daily':
                date_filter = "WHERE date(created_at) = date('now')"
            elif period == 'weekly':
                date_filter = "WHERE date(created_at) >= date('now', '-7 days')"
            elif period == 'monthly':
                date_filter = "WHERE date(created_at) >= date('now', '-30 days')"
            
            # Total invoices
            cursor.execute(f"SELECT COUNT(*) FROM invoices {date_filter}")
            total_invoices = cursor.fetchone()[0]
            
            # Total revenue
            cursor.execute(f"SELECT COALESCE(SUM(total_amount), 0) FROM invoices {date_filter}")
            total_revenue = cursor.fetchone()[0]
            
            # Total products sold
            cursor.execute(f'''
                SELECT COALESCE(SUM(ii.quantity), 0) 
                FROM invoice_items ii 
                JOIN invoices i ON ii.invoice_id = i.id 
                {date_filter.replace('created_at', 'i.created_at') if date_filter else ''}
            ''')
            total_products_sold = cursor.fetchone()[0]
            
            # Total damaged products
            cursor.execute("SELECT COALESCE(SUM(damaged_quantity), 0) FROM products")
            total_damaged_products = cursor.fetchone()[0]
            
            # Total value of damaged products
            cursor.execute("SELECT COALESCE(SUM(damaged_quantity * cost_price), 0) FROM products WHERE damaged_quantity > 0")
            damaged_value = cursor.fetchone()[0]
            
            # Unique customers
            cursor.execute(f"SELECT COUNT(DISTINCT customer_name) FROM invoices {date_filter}")
            unique_customers = cursor.fetchone()[0]
            
            # Total profit calculation
            profit_query = f'''
                SELECT COALESCE(SUM(ii.quantity * (ii.unit_price - p.cost_price)), 0) as total_profit
                FROM invoice_items ii 
                JOIN invoices i ON ii.invoice_id = i.id 
                JOIN products p ON ii.product_name = p.full_product_name 
                {date_filter.replace('created_at', 'i.created_at') if date_filter else ''}
            '''
            cursor.execute(profit_query)
            total_profit = cursor.fetchone()[0] or 0
            
            return {
                'total_invoices': total_invoices,
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_products_sold': total_products_sold,
                'total_damaged_products': total_damaged_products,
                'damaged_value': damaged_value,
                'unique_customers': unique_customers
            }
            
        except Exception as e:
            print(f"Error getting summary stats: {str(e)}")
            return {
                'total_invoices': 0,
                'total_revenue': 0,
                'total_profit': 0,
                'total_products_sold': 0,
                'total_damaged_products': 0,
                'damaged_value': 0,
                'unique_customers': 0
            }
        finally:
            conn.close()

if __name__ == "__main__":
    # Initialize database and add sample data
    db = DatabaseManager()
    
    # Add sample products
    sample_products = [
        ("Laptop", 10, 45000.00),
        ("Mouse", 50, 500.00),
        ("Keyboard", 30, 1500.00),
        ("Monitor", 15, 12000.00),
        ("Headphones", 25, 2500.00),
        ("USB Cable", 100, 200.00),
        ("Power Bank", 20, 1800.00),
        ("Smartphone", 8, 25000.00),
        ("Tablet", 12, 18000.00),
        ("Webcam", 18, 3500.00)
    ]
    
    for product_name, quantity, price in sample_products:
        success, message = db.add_product(product_name, quantity, price)
        print(f"{product_name}: {message}")