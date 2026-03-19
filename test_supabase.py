"""
Quick Supabase Connection Test

Run this to verify Supabase connection after setup.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test Supabase connection"""
    
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        return False
    else:
        print(f"✓ SUPABASE_URL: {supabase_url}")
    
    if not supabase_anon_key:
        print("❌ SUPABASE_ANON_KEY not found in .env")
        return False
    else:
        print(f"✓ SUPABASE_ANON_KEY: {supabase_anon_key[:20]}...")
    
    if not supabase_service_key:
        print("❌ SUPABASE_SERVICE_KEY not found in .env")
        return False
    else:
        print(f"✓ SUPABASE_SERVICE_KEY: {supabase_service_key[:20]}...")
    
    # Test connection
    print("\n2. Testing Supabase connection...")
    
    try:
        from supabase_config import get_supabase_client
        
        client = get_supabase_client()
        print("✓ Supabase client created successfully")
        print(f"  Project URL: {client.supabase_url}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test database access
    print("\n3. Testing database access...")
    
    try:
        from supabase_config import get_supabase_admin_client
        
        admin_client = get_supabase_admin_client()
        
        # Try to query a table
        result = admin_client.table("user_profiles").select("*").limit(1).execute()
        
        print("✓ Database query successful")
        print(f"  Tables accessible: user_profiles ✓")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("   Make sure you ran schema.sql in Supabase SQL Editor")
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ SUPABASE CONNECTION TEST PASSED!")
    print("=" * 60)
    print("\nYour Supabase is configured correctly and ready to use!")
    print("\nNext steps:")
    print("  1. Run API server: python main.py")
    print("  2. Test endpoints: http://localhost:8000/docs")
    print("  3. Deploy to Railway")
    
    return True


if __name__ == "__main__":
    try:
        success = test_connection()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        exit(1)
