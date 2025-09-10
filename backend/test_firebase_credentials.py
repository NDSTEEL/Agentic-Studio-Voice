#!/usr/bin/env python3
"""
Test Firebase credentials loading to diagnose deserialization error
"""
import os
import json
import sys
from pathlib import Path

def test_firebase_credentials():
    """Test Firebase credential loading with detailed error reporting"""
    
    # Add the src directory to Python path
    sys.path.append(str(Path(__file__).parent / "src"))
    
    try:
        # Test 1: Load JSON file directly
        print("🔍 Test 1: Loading JSON file...")
        cred_path = Path(__file__).parent / "firebase-service-account.json"
        
        if not cred_path.exists():
            print("❌ firebase-service-account.json not found!")
            return False
            
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
            print(f"✅ JSON loaded successfully")
            print(f"   - Project ID: {cred_data.get('project_id')}")
            print(f"   - Client Email: {cred_data.get('client_email')}")
            print(f"   - Private Key length: {len(cred_data.get('private_key', ''))}")
            
        # Test 2: Check private key format
        print("\n🔍 Test 2: Checking private key format...")
        private_key = cred_data.get('private_key', '')
        
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key missing BEGIN marker")
            return False
            
        if not private_key.endswith('-----END PRIVATE KEY-----\n'):
            print("❌ Private key missing proper END marker")
            return False
            
        # Count lines in private key
        key_lines = private_key.split('\n')
        print(f"✅ Private key format appears correct ({len(key_lines)} lines)")
        
        # Test 3: Try Firebase credentials
        print("\n🔍 Test 3: Testing Firebase credentials...")
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            # Initialize credentials
            cred = credentials.Certificate(str(cred_path))
            print("✅ Firebase credentials object created successfully")
            
            # Test Firebase app initialization
            if firebase_admin._apps:
                # Delete existing app if any
                for app in firebase_admin._apps.values():
                    firebase_admin.delete_app(app)
            
            app = firebase_admin.initialize_app(cred, name='test-app')
            print("✅ Firebase app initialized successfully")
            
            # Clean up
            firebase_admin.delete_app(app)
            print("✅ Firebase test completed successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check for specific error patterns
            error_str = str(e)
            if "Could not deserialize key data" in error_str:
                print("🔧 DETECTED: Key deserialization error")
                print("   This suggests the private key format is corrupted")
            elif "No such file or directory" in error_str:
                print("🔧 DETECTED: File path issue")
            elif "Invalid key format" in error_str:
                print("🔧 DETECTED: Key format issue")
                
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FIREBASE-FIXER: Testing Firebase credentials...")
    success = test_firebase_credentials()
    
    if success:
        print("\n✅ FIREBASE-FIXER: SUCCESS - Credentials are working!")
    else:
        print("\n❌ FIREBASE-FIXER: FAILED - Credentials need fixing!")
        
    print("\n🔍 Next: Testing VoiceAgentService...")