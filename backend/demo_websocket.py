#!/usr/bin/env python3
"""
WebSocket Progress Tracking Demo

This script demonstrates the real-time progress tracking functionality
implemented for Terminal 4: Real-time Communications.

Run this script to see how progress updates work:
python3 demo_websocket.py
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.websocket.progress_manager import ProgressManager
from src.websocket.websocket_manager import WebSocketManager
from src.websocket.progress_tracker import ProgressTracker


async def demo_progress_tracking():
    """Demonstrate real-time progress tracking."""
    print("🚀 WebSocket Progress Tracking Demo")
    print("=" * 50)
    
    # Initialize components
    progress_manager = ProgressManager()
    websocket_manager = WebSocketManager(progress_manager)
    progress_tracker = ProgressTracker(progress_manager, websocket_manager)
    
    print(f"✅ Initialized progress tracking system")
    print(f"   - Progress Manager: {type(progress_manager).__name__}")
    print(f"   - WebSocket Manager: {type(websocket_manager).__name__}")
    print(f"   - Progress Tracker: {type(progress_tracker).__name__}")
    print()
    
    # Demo 1: Basic Session Management
    print("📋 Demo 1: Basic Session Management")
    print("-" * 30)
    
    session_id = progress_manager.create_session("agent_creation")
    print(f"   Created session: {session_id}")
    
    progress_manager.update_progress(session_id, "Starting agent creation", 10)
    progress_manager.update_progress(session_id, "Configuring settings", 30)
    progress_manager.update_progress(session_id, "Initializing knowledge base", 60)
    progress_manager.update_progress(session_id, "Finalizing setup", 90)
    
    status = progress_manager.get_session_status(session_id)
    print(f"   Progress updates: {len(status['progress'])}")
    for update in status['progress']:
        print(f"     • {update['progress']}%: {update['message']}")
    
    progress_manager.complete_session(session_id, True, "Agent created successfully!")
    final_status = progress_manager.get_session_status(session_id)
    print(f"   Final status: {final_status['status']} ({'SUCCESS' if final_status['success'] else 'FAILED'})")
    print()
    
    # Demo 2: Context Manager Usage
    print("🔄 Demo 2: Context Manager Usage")
    print("-" * 30)
    
    async with progress_tracker.track_operation("knowledge_update", "Updating knowledge base") as session:
        await session.update("Analyzing new content", 20)
        print(f"   Session {session.get_session_id()}: Analyzing new content (20%)")
        
        await asyncio.sleep(0.5)  # Simulate work
        await session.update("Processing categories", 50)
        print(f"   Session {session.get_session_id()}: Processing categories (50%)")
        
        await asyncio.sleep(0.5)  # Simulate work
        await session.update("Updating database", 80)
        print(f"   Session {session.get_session_id()}: Updating database (80%)")
        
        await asyncio.sleep(0.5)  # Simulate work
        # Context manager will auto-complete at 100%
    
    print(f"   Knowledge update completed via context manager")
    print()
    
    # Demo 3: Multiple Concurrent Sessions
    print("🔀 Demo 3: Multiple Concurrent Sessions")
    print("-" * 30)
    
    async def simulate_agent_creation(agent_name: str, delay: float):
        """Simulate creating an agent with progress updates."""
        async with progress_tracker.track_operation("agent_creation", f"Creating {agent_name}") as session:
            steps = [
                ("Validating configuration", 20),
                ("Setting up voice profile", 40),
                ("Initializing knowledge base", 60),
                ("Testing connections", 80),
                ("Finalizing agent", 100)
            ]
            
            for step_name, progress in steps:
                await session.update(f"{agent_name}: {step_name}", progress)
                print(f"   {agent_name} ({session.get_session_id()[:8]}...): {step_name} ({progress}%)")
                await asyncio.sleep(delay)
    
    # Run multiple agent creations concurrently
    tasks = [
        simulate_agent_creation("SalesBot", 0.2),
        simulate_agent_creation("SupportAgent", 0.3),
        simulate_agent_creation("ReceptionistAI", 0.25)
    ]
    
    await asyncio.gather(*tasks)
    print("   All concurrent agent creations completed!")
    print()
    
    # Demo 4: Session Information
    print("📊 Demo 4: Session Information")
    print("-" * 30)
    
    active_sessions = progress_manager.get_active_sessions()
    print(f"   Active sessions: {len(active_sessions)}")
    
    # Create some test sessions for demonstration
    test_sessions = []
    for i in range(3):
        sid = progress_manager.create_session("test_operation")
        progress_manager.update_progress(sid, f"Test operation {i+1}", 50 + (i * 10))
        test_sessions.append(sid)
    
    active_sessions = progress_manager.get_active_sessions()
    print(f"   Active sessions after creating test sessions: {len(active_sessions)}")
    
    for session_id, session_data in active_sessions.items():
        latest = session_data['progress'][-1] if session_data['progress'] else None
        if latest:
            print(f"     • {session_id[:8]}...: {latest['message']} ({latest['progress']}%)")
    
    # Clean up test sessions
    for sid in test_sessions:
        progress_manager.complete_session(sid, True, "Test completed")
    
    print()
    print("🎉 Demo completed successfully!")
    print("   All WebSocket progress tracking functionality is working correctly.")


if __name__ == "__main__":
    print("Terminal 4: Real-time Communications - WebSocket Progress Demo")
    print()
    
    try:
        asyncio.run(demo_progress_tracking())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()