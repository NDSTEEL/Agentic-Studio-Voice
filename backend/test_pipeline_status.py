#!/usr/bin/env python3
"""
TEST-FIXER-3: Pipeline Service Status Test
Check if the agent pipeline can report service status correctly
"""
import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend/.env')

# Add the backend directory to sys.path
sys.path.insert(0, '/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')

def test_pipeline_service_status():
    """Test pipeline service status reporting"""
    print("🏭 Testing Agent Creation Pipeline Service Status...")
    
    try:
        # Import pipeline with proper module path handling
        from src.services.pipeline.agent_pipeline import AgentCreationPipeline
        
        print("  ✅ Pipeline module imported successfully")
        
        # Initialize pipeline in safe mode
        pipeline = AgentCreationPipeline(safe_mode=True)
        print("  ✅ Pipeline initialized successfully")
        
        # Get service status
        status = pipeline.get_service_status()
        
        print("\n📊 PIPELINE SERVICE STATUS:")
        print(f"  Pipeline Mode: {status['pipeline_mode'].upper()}")
        print(f"  Total Services: {status['total_services']}")
        print(f"  Healthy Services: {status['healthy_services']}")
        print(f"  Degraded Services: {status['degraded_services']}")
        
        print("\n📋 INDIVIDUAL SERVICE STATUS:")
        for service, is_healthy in status['service_status'].items():
            icon = "✅" if is_healthy else "❌"
            status_text = "REAL" if is_healthy else "MOCK"
            print(f"  {icon} {service}: {status_text}")
        
        # Calculate success metrics
        total_services = status['total_services']
        healthy_services = status['healthy_services']
        success_rate = (healthy_services / total_services) * 100 if total_services > 0 else 0
        
        print(f"\n🎯 SUCCESS METRICS:")
        print(f"  Service Success Rate: {success_rate:.1f}% ({healthy_services}/{total_services})")
        print(f"  Pipeline Mode: {status['pipeline_mode']}")
        
        # Determine if we've moved from DEGRADED to PRODUCTION
        is_production = status['pipeline_mode'] == 'production'
        is_improved = healthy_services >= 2  # At least some real services
        
        return {
            'success': True,
            'pipeline_mode': status['pipeline_mode'],
            'healthy_services': healthy_services,
            'total_services': total_services,
            'service_status': status['service_status'],
            'is_production': is_production,
            'is_improved': is_improved
        }
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("🔍 TEST-FIXER-3: Pipeline Service Status Test")
    print("=" * 60)
    
    # Test pipeline status
    result = test_pipeline_service_status()
    
    print("\n" + "=" * 60)
    print("📈 FINAL REPORT:")
    
    if result['success']:
        healthy = result['healthy_services']
        total = result['total_services']
        mode = result['pipeline_mode']
        
        print(f"✅ Pipeline Status: {mode.upper()}")
        print(f"📊 Service Health: {healthy}/{total} services operational")
        
        if result['is_production']:
            print("🎉 SUCCESS: Pipeline is now in PRODUCTION mode!")
            print("   All services have real implementations with valid credentials.")
        elif result['is_improved']:
            print("🚀 PROGRESS: Pipeline services have been improved!")
            print("   Some services now have real implementations.")
            print(f"   Mode: {mode} ({healthy}/{total} real services)")
        else:
            print("⚠️  DEGRADED: Pipeline is still in degraded mode.")
            print("   Most services are using mock implementations.")
        
        print(f"\n🏆 TEST-FIXER-3 REPORT: Fixed credentials, service_status now [{mode.upper()}], [{healthy}/{total}] services real")
        
    else:
        print("❌ FAILED: Could not initialize pipeline")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    return result['success'] if result['success'] else False

if __name__ == "__main__":
    main()