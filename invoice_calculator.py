from datetime import datetime
import uuid

class InvoiceCalculator:
    def __init__(self):
        """
        Initialize invoice calculator 
        No GST calculations since GST is already included in selling prices
        """
        pass
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"INV-{timestamp}-{unique_id}"
    
    def calculate_item_total(self, unit_price, quantity):
        """Calculate total for a single item"""
        return round(unit_price * quantity, 2)
    
    def calculate_subtotal(self, items):
        """Calculate total amount (prices already include GST)"""
        total = sum(item['total_price'] for item in items)
        return round(total, 2)
    
    def calculate_total_amount(self, subtotal):
        """Calculate final total amount (no additional GST)"""
        return round(subtotal, 2)
    
    def create_invoice_item(self, product_name, quantity, unit_price):
        """Create an invoice item with calculations"""
        total_price = self.calculate_item_total(unit_price, quantity)
        
        return {
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price
        }
    
    def calculate_invoice_totals(self, items):
        """Calculate invoice totals (no GST since already included in prices)"""
        total_amount = self.calculate_subtotal(items)
        
        return {
            'subtotal': total_amount,
            'cgst_rate': 0,
            'sgst_rate': 0,
            'cgst_amount': 0,
            'sgst_amount': 0,
            'total_gst_rate': 0,
            'total_amount': total_amount
        }
    
    def create_complete_invoice(self, customer_info, items_data):
        """Create a complete invoice with all calculations (no GST since included in prices)"""
        # Generate invoice number
        invoice_number = self.generate_invoice_number()
        
        # Create invoice items with calculations
        invoice_items = []
        for item_data in items_data:
            item = self.create_invoice_item(
                item_data['product_name'],
                item_data['quantity'],
                item_data['unit_price']
            )
            invoice_items.append(item)
        
        # Calculate totals
        totals = self.calculate_invoice_totals(invoice_items)
        
        # Create complete invoice data
        invoice_data = {
            'invoice_number': invoice_number,
            'customer_name': customer_info.get('name', ''),
            'customer_phone': customer_info.get('phone', ''),
            'customer_address': customer_info.get('address', ''),
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'items': invoice_items,
            **totals
        }
        
        return invoice_data

class InvoiceValidator:
    """Validate invoice data before processing"""
    
    @staticmethod
    def validate_customer_info(customer_info):
        """Validate customer information"""
        errors = []
        
        if not customer_info.get('name', '').strip():
            errors.append("Customer name is required")
        
        phone = customer_info.get('phone', '').strip()
        if phone and not phone.isdigit():
            errors.append("Phone number should contain only digits")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_invoice_items(items_data):
        """Validate invoice items"""
        errors = []
        
        if not items_data:
            errors.append("At least one item is required")
            return False, errors
        
        for i, item in enumerate(items_data, 1):
            if not item.get('product_name', '').strip():
                errors.append(f"Item {i}: Product name is required")
            
            try:
                quantity = int(item.get('quantity', 0))
                if quantity <= 0:
                    errors.append(f"Item {i}: Quantity must be greater than 0")
            except (ValueError, TypeError):
                errors.append(f"Item {i}: Invalid quantity")
            
            try:
                unit_price = float(item.get('unit_price', 0))
                if unit_price <= 0:
                    errors.append(f"Item {i}: Unit price must be greater than 0")
            except (ValueError, TypeError):
                errors.append(f"Item {i}: Invalid unit price")
        
        return len(errors) == 0, errors

if __name__ == "__main__":
    # Test the invoice calculator
    calculator = InvoiceCalculator()
    
    # Sample customer info
    customer_info = {
        'name': 'John Doe',
        'phone': '9876543210',
        'address': '123 Main Street, City, State - 12345'
    }
    
    # Sample items
    items_data = [
        {'product_name': 'Laptop', 'quantity': 2, 'unit_price': 45000.00},
        {'product_name': 'Mouse', 'quantity': 2, 'unit_price': 500.00},
        {'product_name': 'Keyboard', 'quantity': 1, 'unit_price': 1500.00}
    ]
    
    # Create invoice
    invoice = calculator.create_complete_invoice(customer_info, items_data)
    
    # Print invoice details
    print("=== INVOICE DETAILS ===")
    print(f"Invoice Number: {invoice['invoice_number']}")
    print(f"Customer: {invoice['customer_name']}")
    print(f"Date: {invoice['date']} {invoice['time']}")
    print("\n=== ITEMS ===")
    for item in invoice['items']:
        print(f"{item['product_name']}: {item['quantity']} x ₹{item['unit_price']} = ₹{item['total_price']}")
    
    print(f"\n=== TOTALS ===")
    print(f"Subtotal: ₹{invoice['subtotal']}")
    print(f"CGST ({invoice['cgst_rate']}%): ₹{invoice['cgst_amount']}")
    print(f"SGST ({invoice['sgst_rate']}%): ₹{invoice['sgst_amount']}")
    print(f"Total Amount: ₹{invoice['total_amount']}")