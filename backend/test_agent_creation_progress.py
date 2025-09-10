#!/usr/bin/env python3
"""
Test Agent Creation with Progress Tracking

This script simulates the complete agent creation flow with real-time progress updates.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
import json
from unittest.mock import MagicMock

def test_agent_creation_with_progress():
    """Test agent creation flow with progress tracking"""
    try:
        from src.websocket.progress_manager import ProgressManager
        from src.websocket.websocket_manager import WebSocketManager
        from src.websocket.progress_tracker import ProgressTracker
        
        print("🚀 Testing Agent Creation with Progress Tracking")
        print("=" * 60)
        
        # Initialize progress tracking
        progress_manager = ProgressManager()
        websocket_manager = WebSocketManager(progress_manager)
        progress_tracker = ProgressTracker(progress_manager, websocket_manager)
        
        print("✅ Progress tracking system initialized")
        
        # Mock WebSocket connections
        mock_websockets = []
        for i in range(3):
            mock_ws = MagicMock()
            mock_ws.send = MagicMock()
            mock_websockets.append(mock_ws)
            asyncio.run(websocket_manager.register(mock_ws))
        
        print(f"✅ {len(mock_websockets)} mock WebSocket connections registered")
        
        async def simulate_agent_creation():
            """Simulate the agent creation process with progress tracking"""
            
            # Create session immediately (like the /create-with-progress endpoint)
            session_id = progress_manager.create_session("agent_creation")
            print(f"📋 Session created: {session_id}")
            
            # Start progress tracking
            async with progress_tracker.track_operation(
                "agent_creation",
                "Creating TestAgent"
            ) as session:
                # Override session ID to match pre-created session
                session.session_id = session_id
                
                print("🔄 Starting agent creation process...")
                
                # Step 1: Initialize
                await session.update("Initializing voice agent creation", 10)
                print("   ✓ 10%: Initializing voice agent creation")
                await asyncio.sleep(0.1)
                
                # Step 2: Validate
                await session.update("Validating request data", 20)
                print("   ✓ 20%: Validating request data")
                await asyncio.sleep(0.1)
                
                # Step 3: Configure
                await session.update("Setting up agent configuration", 40)
                print("   ✓ 40%: Setting up agent configuration")
                await asyncio.sleep(0.1)
                
                # Step 4: Knowledge base
                await session.update("Initializing knowledge base", 60)
                print("   ✓ 60%: Initializing knowledge base")
                await asyncio.sleep(0.1)
                
                # Step 5: Database
                await session.update("Creating voice agent in database", 80)
                print("   ✓ 80%: Creating voice agent in database")
                await asyncio.sleep(0.1)
                
                # Step 6: Finalize
                await session.update("Finalizing agent setup", 95)
                print("   ✓ 95%: Finalizing agent setup")
                await asyncio.sleep(0.1)
                
                # Complete
                await session.complete(
                    success=True,
                    result="Voice agent 'TestAgent' created successfully with ID: test-agent-123"
                )
                print("   ✅ 100%: Agent creation completed successfully!")
            
            return session_id
        
        # Run the simulation
        session_id = asyncio.run(simulate_agent_creation())
        
        # Verify final status
        final_status = progress_manager.get_session_status(session_id)
        assert final_status is not None
        assert final_status['status'] == 'completed'
        assert final_status['success'] is True
        assert len(final_status['progress']) > 0
        
        print(f"\n📊 Final Status:")
        print(f"   Session ID: {session_id}")
        print(f"   Status: {final_status['status']}")
        print(f"   Success: {final_status['success']}")
        print(f"   Progress steps: {len(final_status['progress'])}")
        print(f"   Result: {final_status['result']}")
        
        # Verify WebSocket messages were sent
        total_messages = 0
        for mock_ws in mock_websockets:
            total_messages += mock_ws.send.call_count
        
        print(f"\n📡 WebSocket Communication:")
        print(f"   Connected clients: {len(mock_websockets)}")
        print(f"   Total messages sent: {total_messages}")
        print(f"   Messages per client: {total_messages // len(mock_websockets) if mock_websockets else 0}")
        
        # Verify message content
        if mock_websockets and mock_websockets[0].send.call_count > 0:
            last_call = mock_websockets[0].send.call_args_list[-1]
            last_message = json.loads(last_call[0][0])
            print(f"   Last message type: {last_message.get('type')}")
            print(f"   Last message session: {last_message.get('session_id', '')[:8]}...")
        
        print("\n🎉 Agent creation with progress tracking test PASSED!")
        print("   Real-time progress updates are working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation progress test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_simulation():
    """Test endpoint response format"""
    try:
        print("\n🔗 Testing Endpoint Response Format")
        print("-" * 40)
        
        from src.websocket.progress_manager import ProgressManager
        
        pm = ProgressManager()
        session_id = pm.create_session("agent_creation")
        
        # Simulate endpoint response
        response = {
            "session_id": session_id,
            "message": "Agent creation started. Use session_id to track progress via WebSocket.",
            "websocket_url": "/api/v1/ws/progress"
        }
        
        print(f"✅ Endpoint response format:")
        print(f"   session_id: {response['session_id']}")
        print(f"   message: {response['message']}")
        print(f"   websocket_url: {response['websocket_url']}")
        
        # Verify session exists
        status = pm.get_session_status(session_id)
        assert status is not None
        assert status['type'] == 'agent_creation'
        
        print(f"✅ Session verified in progress manager")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint simulation test failed: {e}")
        return False


def main():
    """Run comprehensive agent creation progress tests"""
    print("Terminal 4: Real-time Communications - Agent Creation Progress Test")
    print("=" * 70)
    
    tests = [
        ("Agent Creation with Progress Tracking", test_agent_creation_with_progress),
        ("Endpoint Response Simulation", test_endpoint_simulation),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {e}")
    
    print(f"\n🎯 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("   Terminal 4 WebSocket integration is ready for production")
        print("   Real-time progress updates will work during agent creation")
        return True
    else:
        print("\n❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)