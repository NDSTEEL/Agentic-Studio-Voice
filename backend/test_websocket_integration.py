#!/usr/bin/env python3
"""
Test WebSocket Integration without Firebase dependencies
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_websocket_modules():
    """Test that WebSocket modules can be imported and instantiated"""
    try:
        # Test core WebSocket modules
        from src.websocket.progress_manager import ProgressManager
        from src.websocket.websocket_manager import WebSocketManager
        from src.websocket.progress_tracker import ProgressTracker
        
        print("✅ Core WebSocket modules imported successfully")
        
        # Test instantiation
        pm = ProgressManager()
        wm = WebSocketManager(pm)
        pt = ProgressTracker(pm, wm)
        
        print("✅ WebSocket objects created successfully")
        
        # Test basic functionality
        session_id = pm.create_session("test_session")
        pm.update_progress(session_id, "Test message", 50)
        status = pm.get_session_status(session_id)
        
        assert status is not None
        assert status['type'] == "test_session"
        assert len(status['progress']) == 1
        assert status['progress'][0]['message'] == "Test message"
        
        print("✅ Basic WebSocket functionality working")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_websocket_routes():
    """Test that WebSocket routes can be imported"""
    try:
        from src.api.websocket_routes import router, get_progress_manager, get_websocket_manager
        
        print("✅ WebSocket routes imported successfully")
        
        # Test manager functions
        pm = get_progress_manager()
        wm = get_websocket_manager()
        
        print(f"✅ Progress Manager: {type(pm).__name__}")
        print(f"✅ WebSocket Manager: {type(wm).__name__}")
        
        # Test router has expected routes
        route_paths = []
        for route in router.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
            elif hasattr(route, 'path_regex'):
                route_paths.append(str(route.path_regex.pattern))
        
        print(f"✅ Router has {len(router.routes)} routes:")
        for path in route_paths:
            print(f"   - {path}")
        
        # Check for WebSocket endpoint
        has_ws_endpoint = any('/ws/progress' in path for path in route_paths)
        if has_ws_endpoint:
            print("✅ WebSocket endpoint found")
        else:
            print("⚠️  WebSocket endpoint not found in routes")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_websocket_functionality():
    """Test async WebSocket functionality"""
    try:
        from src.websocket.progress_manager import ProgressManager
        from src.websocket.websocket_manager import WebSocketManager
        from src.websocket.progress_tracker import ProgressTracker
        
        pm = ProgressManager()
        wm = WebSocketManager(pm)
        pt = ProgressTracker(pm, wm)
        
        # Test async progress tracking
        async with pt.track_operation("test_operation", "Testing async") as session:
            await session.update("Step 1", 25)
            await session.update("Step 2", 50)
            await session.update("Step 3", 75)
            # Auto-completion will happen
        
        print("✅ Async WebSocket functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Async WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all WebSocket integration tests"""
    print("🚀 WebSocket Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic WebSocket Modules", test_websocket_modules),
        ("WebSocket Routes", test_websocket_routes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    # Test async functionality
    print(f"\n📋 Running: Async WebSocket Functionality")
    print("-" * 30)
    
    import asyncio
    try:
        if asyncio.run(test_async_websocket_functionality()):
            passed += 1
            total += 1
            print(f"✅ Async WebSocket Functionality PASSED")
        else:
            total += 1
            print(f"❌ Async WebSocket Functionality FAILED")
    except Exception as e:
        total += 1
        print(f"❌ Async WebSocket Functionality ERROR: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All WebSocket integration tests PASSED!")
        print("   Real-time progress updates are ready for agent creation")
        return True
    else:
        print("❌ Some WebSocket integration tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)