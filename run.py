#!/usr/bin/env python3
"""
GreenBin - Smart Plastic Recycling App
Startup script for easy deployment
"""

import os
import sys
from app import create_app

def main():
    """Main function to run the Flask application"""
    print("🌍 Starting GreenBin - Smart Plastic Recycling App")
    print("=" * 50)
    
    # Create the Flask app
    app = create_app()
    
    # Print startup information
    print("✅ Application initialized successfully!")
    print("📊 Database tables created")
    print("🎯 Sample data loaded")
    print("\n🚀 Demo Accounts:")
    print("   👤 User: demo_user / password123")
    print("   🔧 Admin: admin / admin123")
    print("\n🌐 Access the application at: http://localhost:5000")
    print("=" * 50)
    
    # Run the application
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using GreenBin! Keep recycling! 🌱")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
