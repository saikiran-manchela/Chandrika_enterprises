sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for Vercel
os.environ['VERCEL'] = '1'
os.environ['FLASK_ENV'] = 'production'

# Import Flask app
from app import app

# Export app for Vercel Python runtime
# Vercel will automatically detect and use the Flask app
__all__ = ['app']