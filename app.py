from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, make_response, session
import os
import sys
from datetime import datetime
import json
import csv
from io import StringIO
from functools import wraps

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from invoice_calculator import InvoiceCalculator, InvoiceValidator
from pdf_generator import InvoicePDFGenerator

app = Flask(__name__)
app.secret_key = 'invoice-mgmt-system-2025-change-in-production'  # Change this in production

# Initialize managers
db_manager = DatabaseManager()
calculator = InvoiceCalculator()
pdf_generator = InvoicePDFGenerator()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ensure static and templates directories exist
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('invoices', exist_ok=True)
os.makedirs('uploads', exist_ok=True)  # For CSV uploads

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        success, user_data = db_manager.authenticate_user(username, password)
        
        if success:
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['full_name'] = user_data['full_name'] or username
            flash(f'Welcome back, {session["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/invoice')
@login_required
def invoice_page():
    """Invoice generation page"""
    products = db_manager.get_all_products()
    return render_template('invoice.html', products=products)

@app.route('/invoice/preview')
@login_required
def invoice_preview():
    """Invoice preview page"""
    return render_template('invoice_preview.html')

@app.route('/stock')
@login_required
def stock_page():
    """Stock management page"""
    products = db_manager.get_all_products()
    return render_template('stock.html', products=products)

@app.route('/reports')
@login_required
def reports_page():
    """Reports page"""
    return render_template('reports.html')

@app.route('/database-management')
@login_required
def database_management():
    """Database management page for CSV uploads"""
    return render_template('database_management.html')

@app.route('/api/reports/summary/<period>')
@login_required
def get_summary_stats_api(period):
    """Get summary statistics for dashboard"""
    try:
        if period not in ['daily', 'weekly', 'monthly']:
            return jsonify({'success': False, 'error': 'Invalid period'}), 400
        
        stats = db_manager.get_summary_stats(period)
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/sales/<period>')
@login_required
def get_sales_report_api(period):
    """Get sales report for products sold"""
    try:
        if period not in ['daily', 'weekly', 'monthly']:
            return jsonify({'success': False, 'error': 'Invalid period'}), 400
        
        sales_data = db_manager.get_sales_report_data(period)
        
        # Process data to group by product
        product_sales = {}
        for row in sales_data:
            product_name = row[0]
            weight = row[1] or ''
            quantity = row[2]
            unit_price = row[3]
            total_price = row[4]
            created_at = row[5]
            cost_price = row[6] or 0
            
            full_name = f"{product_name} ({weight})" if weight else product_name
            
            if full_name not in product_sales:
                product_sales[full_name] = {
                    'product_name': full_name,
                    'total_quantity': 0,
                    'total_revenue': 0,
                    'times_sold': 0,
                    'avg_price': 0
                }
            
            product_sales[full_name]['total_quantity'] += quantity
            product_sales[full_name]['total_revenue'] += total_price
            product_sales[full_name]['times_sold'] += 1
        
        # Calculate average price
        for product in product_sales.values():
            if product['total_quantity'] > 0:
                product['avg_price'] = product['total_revenue'] / product['total_quantity']
        
        # Convert to list and sort by quantity
        result = sorted(product_sales.values(), key=lambda x: x['total_quantity'], reverse=True)
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/profit/<period>')
@login_required
def get_profit_report_api(period):
    """Get profit report"""
    try:
        if period not in ['daily', 'weekly', 'monthly']:
            return jsonify({'success': False, 'error': 'Invalid period'}), 400
        
        profit_data = db_manager.get_profit_report(period)
        
        result = []
        for row in profit_data:
            product_name = row[0]
            weight = row[1] or ''
            total_sold = row[2]
            total_revenue = row[3]
            avg_cost_price = row[4] or 0
            total_cost = row[5] or 0
            profit = row[6] or 0
            
            full_name = f"{product_name} ({weight})" if weight else product_name
            
            result.append({
                'product_name': full_name,
                'total_sold': total_sold,
                'total_revenue': total_revenue,
                'total_cost': total_cost,
                'profit': profit,
                'profit_margin': (profit / total_revenue * 100) if total_revenue > 0 else 0
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/top-products/<period>')
@login_required
def get_top_products_api(period):
    """Get most sold products"""
    try:
        if period not in ['daily', 'weekly', 'monthly']:
            return jsonify({'success': False, 'error': 'Invalid period'}), 400
        
        top_products = db_manager.get_top_selling_products(period, 10)
        
        result = []
        for row in top_products:
            product_name = row[0]
            weight = row[1] or ''
            total_sold = row[2]
            total_revenue = row[3]
            times_ordered = row[4]
            
            full_name = f"{product_name} ({weight})" if weight else product_name
            
            result.append({
                'product_name': full_name,
                'total_sold': total_sold,
                'total_revenue': total_revenue,
                'times_ordered': times_ordered,
                'avg_quantity_per_order': total_sold / times_ordered if times_ordered > 0 else 0
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API Routes

@app.route('/api/products')
@login_required
def get_products():
    """Get all products"""
    try:
        products = db_manager.get_all_products()
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<product_name>')
@login_required
def get_product(product_name):
    """Get specific product details"""
    try:
        product = db_manager.get_product(product_name)
        if product:
            return jsonify({'success': True, 'product': product})
        else:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    """Add a new product"""
    try:
        data = request.get_json()
        product_name = data.get('product_name', '').strip()
        weight = data.get('weight', '').strip()
        quantity = int(data.get('quantity', 0))
        cost_price = float(data.get('cost_price', 0))
        selling_price = float(data.get('selling_price', 0))
        
        if not product_name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        if quantity < 0:
            return jsonify({'success': False, 'error': 'Quantity cannot be negative'}), 400
        
        if selling_price <= 0:
            return jsonify({'success': False, 'error': 'Selling price must be greater than 0'}), 400
        
        success, message = db_manager.add_product(product_name, quantity, selling_price, weight, cost_price)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid number format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/stock', methods=['PUT'])
@login_required
def update_stock():
    """Update product stock"""
    try:
        data = request.get_json()
        full_product_name = data.get('full_product_name', '').strip()
        new_quantity = int(data.get('quantity', 0))
        
        if not full_product_name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        if new_quantity < 0:
            return jsonify({'success': False, 'error': 'Quantity cannot be negative'}), 400
        
        success, message = db_manager.update_product_quantity(full_product_name, new_quantity)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid quantity format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/damaged', methods=['PUT'])
@login_required
def mark_as_damaged():
    """Mark products as damaged"""
    try:
        data = request.get_json()
        full_product_name = data.get('full_product_name', '').strip()
        damaged_qty = int(data.get('damaged_quantity', 0))
        
        if not full_product_name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        if damaged_qty <= 0:
            return jsonify({'success': False, 'error': 'Damaged quantity must be greater than 0'}), 400
        
        success, message = db_manager.mark_as_damaged(full_product_name, damaged_qty)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid quantity format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/restore', methods=['PUT'])
@login_required
def restore_damaged():
    """Restore damaged products back to available stock"""
    try:
        data = request.get_json()
        full_product_name = data.get('full_product_name', '').strip()
        restore_qty = int(data.get('restore_quantity', 0))
        
        if not full_product_name:
            return jsonify({'success': False, 'error': 'Product name is required'}), 400
        
        if restore_qty <= 0:
            return jsonify({'success': False, 'error': 'Restore quantity must be greater than 0'}), 400
        
        success, message = db_manager.restore_damaged(full_product_name, restore_qty)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid quantity format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/damaged-report')
@login_required
def get_damaged_report():
    """Get damaged products report"""
    try:
        damaged_products = db_manager.get_damaged_products_report()
        return jsonify({'success': True, 'data': damaged_products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/calculate', methods=['POST'])
@login_required
def calculate_invoice():
    """Calculate invoice totals"""
    try:
        data = request.get_json()
        items_data = data.get('items', [])
        
        if not items_data:
            return jsonify({'success': False, 'error': 'No items provided'}), 400
        
        # Validate and process items
        invoice_items = []
        for item_data in items_data:
            try:
                product_name = item_data.get('product_name', '').strip()
                quantity = int(item_data.get('quantity', 0))
                unit_price = float(item_data.get('unit_price', 0))
                
                if not product_name or quantity <= 0 or unit_price <= 0:
                    continue
                
                # Check stock availability
                product = db_manager.get_product(product_name)
                if not product:
                    return jsonify({'success': False, 'error': f'Product "{product_name}" not found'}), 400
                
                if product['quantity'] < quantity:
                    return jsonify({'success': False, 'error': f'Insufficient stock for "{product_name}". Available: {product["quantity"]}'}), 400
                
                # Get weight from product data
                weight = product.get('weight', '')
                
                # Create invoice item with weight information
                item = {
                    'product_name': product_name,
                    'weight': weight,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': quantity * unit_price
                }
                invoice_items.append(item)
                
            except (ValueError, TypeError):
                continue
        
        if not invoice_items:
            return jsonify({'success': False, 'error': 'No valid items to calculate'}), 400
        
        # Calculate totals
        totals = calculator.calculate_invoice_totals(invoice_items)
        
        return jsonify({
            'success': True,
            'items': invoice_items,
            'totals': totals
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/generate', methods=['POST'])
@login_required
def generate_invoice():
    """Generate invoice and PDF"""
    try:
        print("DEBUG: Invoice generation started")
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
        # Extract customer info
        customer_info = {
            'name': data.get('customer_name', '').strip(),
            'phone': data.get('customer_phone', '').strip(),
            'address': data.get('customer_address', '').strip()
        }
        print(f"DEBUG: Customer info: {customer_info}")
        
        # Validate customer info
        valid, errors = InvoiceValidator.validate_customer_info(customer_info)
        if not valid:
            print(f"DEBUG: Customer validation failed: {errors}")
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400
        
        # Extract items
        items_data = data.get('items', [])
        if not items_data:
            return jsonify({'success': False, 'error': 'No items provided'}), 400
        
        # Validate items
        valid, errors = InvoiceValidator.validate_invoice_items(items_data)
        if not valid:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400
        
        # Check stock for all items first
        for item_data in items_data:
            product_name = item_data.get('product_name', '').strip()
            quantity = int(item_data.get('quantity', 0))
            
            product = db_manager.get_product(product_name)
            if not product:
                return jsonify({'success': False, 'error': f'Product "{product_name}" not found'}), 400
            
            if product['quantity'] < quantity:
                return jsonify({'success': False, 'error': f'Insufficient stock for "{product_name}". Available: {product["quantity"]}'}), 400
        
        # Create complete invoice
        invoice_data = calculator.create_complete_invoice(customer_info, items_data)
        
        # Reduce stock for all items
        for item_data in items_data:
            product_name = item_data.get('product_name', '').strip()
            quantity = int(item_data.get('quantity', 0))
            
            success, message = db_manager.reduce_stock(product_name, quantity)
            if not success:
                return jsonify({'success': False, 'error': message}), 400
        
        # Save invoice to database
        success, message = db_manager.save_invoice(invoice_data, invoice_data['items'])
        if not success:
            return jsonify({'success': False, 'error': f'Failed to save invoice: {message}'}), 500
        
        # Generate PDF (optional - keep for records but don't force download)
        pdf_filename = f"invoice_{invoice_data['invoice_number']}.pdf"
        pdf_path = os.path.join('invoices', pdf_filename)
        print(f"DEBUG: Generating PDF at: {pdf_path}")
        pdf_generator.generate_invoice_pdf(invoice_data, pdf_path)
        print(f"DEBUG: PDF generated successfully")
        
        # Return invoice data for display instead of PDF download
        response_data = {
            'success': True,
            'message': 'Invoice generated successfully!',
            'invoice_data': {
                'invoice_number': invoice_data['invoice_number'],
                'date': invoice_data['date'],
                'time': invoice_data['time'],
                'customer_name': invoice_data['customer_name'],
                'customer_phone': invoice_data['customer_phone'],
                'customer_address': invoice_data['customer_address'],
                'items': invoice_data['items'],
                'subtotal': invoice_data['subtotal'],
                'cgst_amount': invoice_data['cgst_amount'],
                'sgst_amount': invoice_data['sgst_amount'],
                'total_amount': invoice_data['total_amount']
            },
            'pdf_available': True,
            'pdf_url': f'/download/{pdf_filename}'
        }
        print(f"DEBUG: Sending response: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download generated PDF"""
    try:
        pdf_path = os.path.join('invoices', filename)
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/invoices')
@login_required
def get_invoices():
    """Get all invoices - placeholder for future implementation"""
    # This would require extending the database manager to fetch invoices
    return jsonify({'success': True, 'invoices': []})

@app.route('/api/products/export')
@login_required
def export_products():
    """Export all products to CSV"""
    try:
        products = db_manager.get_all_products()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Product Name', 'Quantity', 'Selling Price (₹)', 'Status', 'Last Updated'])
        
        # Write data
        for product in products:
            # Determine status
            if product['quantity'] == 0:
                status = 'Out of Stock'
            elif product['quantity'] <= 10:
                status = 'Low Stock'
            else:
                status = 'In Stock'
            
            # Format updated date
            updated_at = product.get('updated_at', 'N/A')
            if updated_at and updated_at != 'N/A':
                try:
                    updated_at = datetime.fromisoformat(updated_at).strftime('%Y-%m-%d')
                except:
                    updated_at = 'N/A'
            
            writer.writerow([
                product['product_name'],
                product['quantity'],
                f"₹{product['selling_price']:.2f}",
                status,
                updated_at
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=stock_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/upload', methods=['POST'])
@login_required
def upload_csv():
    """Handle CSV file upload and database update"""
    try:
        if 'csvFile' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file = request.files['csvFile']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Please upload a CSV file'}), 400
        
        # Save uploaded file
        upload_path = os.path.join('uploads', 'uploaded_data.csv')
        file.save(upload_path)
        
        # Import the rebuild functionality
        from rebuild_database_v2 import DatabaseRebuilderV2
        
        # Create rebuilder with uploaded file
        rebuilder = DatabaseRebuilderV2(csv_file=upload_path)
        
        # Backup existing database
        rebuilder.backup_old_database()
        
        # Create new database
        rebuilder.create_new_database()
        
        # Import CSV data
        success = rebuilder.import_csv_data()
        
        if success:
            # Clean up uploaded file
            os.remove(upload_path)
            return jsonify({
                'success': True, 
                'message': 'Database updated successfully!',
                'redirect': True
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to import CSV data'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/database/preview', methods=['POST'])
@login_required
def preview_csv():
    """Preview CSV file before upload"""
    try:
        if 'csvFile' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file = request.files['csvFile']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Read CSV content
        stream = StringIO(file.read().decode('utf-8-sig'))
        csv_reader = csv.DictReader(stream)
        
        # Get first 5 rows as preview
        preview_data = []
        for i, row in enumerate(csv_reader):
            if i >= 5:  # Limit to 5 rows
                break
            preview_data.append(dict(row))
        
        return jsonify({
            'success': True,
            'columns': csv_reader.fieldnames,
            'preview': preview_data,
            'total_rows': i + 1
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Preview failed: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create invoices directory if it doesn't exist
    if not os.path.exists('invoices'):
        os.makedirs('invoices')
    
    print("Starting Invoice Generation System Web Application...")
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)