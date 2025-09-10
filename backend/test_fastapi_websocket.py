#!/usr/bin/env python3
"""
Test FastAPI WebSocket Integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_fastapi_websocket_integration():
    """Test FastAPI app with WebSocket routes"""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a minimal FastAPI app with just WebSocket routes
        app = FastAPI(title="WebSocket Test App")
        
        # Import and include WebSocket routes
        from src.api.websocket_routes import router as websocket_router
        app.include_router(websocket_router, prefix="/api/v1", tags=["websocket"])
        
        # Add health endpoint
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        print("✅ FastAPI app created with WebSocket routes")
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ Health endpoint working")
        
        # Test WebSocket status endpoint
        response = client.get("/api/v1/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"
        print("✅ WebSocket status endpoint working")
        
        # Test WebSocket test page
        response = client.get("/api/v1/ws/test-page")
        assert response.status_code == 200
        assert "WebSocket Progress Test" in response.text
        print("✅ WebSocket test page working")
        
        print(f"✅ FastAPI WebSocket integration successful")
        print(f"   Available routes:")
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"     - {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI WebSocket integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test FastAPI WebSocket integration"""
    print("🚀 FastAPI WebSocket Integration Test")
    print("=" * 50)
    
    if test_fastapi_websocket_integration():
        print("\n🎉 FastAPI WebSocket integration test PASSED!")
        print("   WebSocket endpoints are properly integrated and accessible")
        return True
    else:
        print("\n❌ FastAPI WebSocket integration test FAILED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)