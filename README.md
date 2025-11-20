# Invoice Management System 📄💼

A comprehensive invoice generation and inventory management system built with Flask, featuring authentication, stock management, damaged products tracking, and detailed reporting.

## ✨ Features

### 🔐 Authentication System
- Secure login/logout functionality
- Session management
- Password hashing (SHA-256)
- Default admin user (username: `admin`, password: `admin123`)

### 📋 Invoice Management
- Professional invoice generation with PDF output
- Customer information management
- Automatic stock reduction
- GST calculation (CGST/SGST)
- Sequential invoice numbering

### 📦 Stock Management
- Product inventory tracking
- Add/update products with cost and selling prices
- Real-time stock updates
- Low stock alerts
- Stock export functionality

### ⚠️ Damaged Products Management
- Track damaged inventory separately from sellable stock
- Mark products as damaged (removes from available stock)
- Restore damaged products back to available stock
- Calculate financial impact of damaged inventory
- Comprehensive damaged products reporting

### 📊 Reports & Analytics
- **Dashboard Overview:** Total invoices, revenue, profit, products sold
- **Sales Reports:** Product-wise sales analysis
- **Profit Analysis:** Cost vs revenue with margins
- **Top Products:** Best-selling products ranking
- **Damaged Products Report:** Track inventory shrinkage and value lost
- Multiple time periods (daily, weekly, monthly)

### 💾 Database Management
- CSV upload interface for bulk product updates
- Automatic database backups
- Data validation and error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Flask and dependencies (see `requirements.txt`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd invoice-management-system
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open browser to `http://localhost:5000`
   - Login with: `admin` / `admin123`

## 📁 Project Structure

```
invoice-management-system/
│
├── app.py                    # Main Flask application
├── database.py              # Database operations and models
├── invoice_calculator.py    # Invoice calculations and validation
├── pdf_generator.py         # PDF generation functionality
├── rebuild_database_v2.py   # CSV import and database rebuilding
├── requirements.txt         # Python dependencies
│
├── templates/               # HTML templates
│   ├── base.html           # Base template with navigation
│   ├── login.html          # Authentication page
│   ├── index.html          # Dashboard
│   ├── invoice.html        # Invoice generation
│   ├── stock.html          # Stock management
│   ├── reports.html        # Analytics and reports
│   └── database_management.html  # CSV upload interface
│
├── static/                 # Static assets
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
│
├── invoices/              # Generated PDF invoices
└── uploads/               # Temporary CSV uploads
```

## 🗄️ Database Schema

### Products Table
- `product_name` - Product identifier
- `weight` - Size/weight specification
- `full_product_name` - Complete name with weight
- `quantity` - Available stock for sale
- `damaged_quantity` - Damaged/unsellable stock
- `cost_price` - Purchase price per unit
- `selling_price` - Sale price per unit

### Invoices Table
- Customer information (name, phone, address)
- Financial details (subtotal, GST, total)
- Timestamps and invoice numbers

### Invoice Items Table
- Product details per invoice
- Quantities and prices
- Links to main invoice

### Users Table
- Authentication credentials
- User management
- Session tracking

## 🔧 Configuration

### Default Settings
- **Database:** SQLite (`invoice_system.db`)
- **Port:** 5000
- **Debug Mode:** Enabled (development)
- **Authentication:** Required for all operations

### Security Notes
- Change default admin password in production
- Update secret key in `app.py`
- Use environment variables for sensitive data
- Consider using PostgreSQL for production

## 💡 Usage Examples

### Adding Products
1. Navigate to **Stock Management**
2. Use "Add New Product" form
3. Specify name, weight, quantities, and prices

### Generating Invoices
1. Go to **Invoice** page
2. Enter customer details
3. Add products and quantities
4. System calculates totals automatically
5. Generate PDF invoice

### Managing Damaged Stock
1. **Stock Management** → Mark products as damaged
2. **Reports** → View damaged products report
3. Restore products if they become sellable again

### Bulk Updates
1. **Database Management** → Upload CSV
2. Preview data before import
3. System creates backup before updating

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check existing documentation
- Review code comments for implementation details

## 🔄 Version History

- **v2.0** - Added damaged products management, enhanced reporting
- **v1.5** - Authentication system, database management
- **v1.0** - Basic invoice generation and stock management

---
**Built with ❤️ using Flask and Bootstrap**