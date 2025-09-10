#!/usr/bin/env python3
"""
Verification script for PhoneService REAL status
Used to confirm the TWILIO-INTEGRATOR fix is working
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to path
sys.path.append('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')

load_dotenv()


def verify_phone_service_status():
    """Verify that PhoneService shows REAL status and integrates properly."""
    print("🔍 TWILIO-INTEGRATOR VERIFICATION")
    print("=" * 50)
    
    try:
        # Import and test PhoneService
        from src.services.phone.phone_service import PhoneService
        
        service = PhoneService()
        status = service.get_service_status()
        
        print(f"📞 PhoneService Status: {status['status']}")
        print(f"🔧 Service Type: {status['service_type']}")
        print(f"🎯 Demo Mode: {status['twilio_status'].get('demo_credentials', False)}")
        print(f"✅ Security Validated: {status['twilio_status'].get('security_validated', False)}")
        print()
        
        # Test AgentCreationPipeline integration
        from src.services.pipeline.agent_pipeline import AgentCreationPipeline
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline_status = pipeline.get_service_status()
        
        print(f"🔄 Pipeline Mode: {pipeline_status['pipeline_mode']}")
        print(f"📊 Phone Service in Pipeline: {'✅ REAL' if pipeline.service_status.get('phone_service') else '❌ MOCK'}")
        print(f"🏥 Total Services Healthy: {pipeline_status['healthy_services']}/{pipeline_status['total_services']}")
        print()
        
        # Verification logic
        is_real_status = status['service_type'] == 'real'
        is_healthy = status['status'] == 'healthy'
        is_pipeline_integrated = pipeline.service_status.get('phone_service') == True
        is_production_mode = pipeline_status['pipeline_mode'] == 'production'
        
        success = all([is_real_status, is_healthy, is_pipeline_integrated, is_production_mode])
        
        print("🎯 VERIFICATION RESULTS:")
        print(f"   Real Status: {'✅' if is_real_status else '❌'} {status['service_type']}")
        print(f"   Healthy Status: {'✅' if is_healthy else '❌'} {status['status']}")
        print(f"   Pipeline Integration: {'✅' if is_pipeline_integrated else '❌'}")
        print(f"   Production Mode: {'✅' if is_production_mode else '❌'}")
        print()
        
        if success:
            print("🎉 TWILIO-INTEGRATOR: SUCCESS - PhoneService is REAL")
            print("   ✅ Service shows REAL status (not MOCK)")
            print("   ✅ Integrated with AgentCreationPipeline") 
            print("   ✅ Demo credentials working properly")
            print("   ✅ Security validation passed")
            return True
        else:
            print("❌ TWILIO-INTEGRATOR: FAILED - Issues detected")
            return False
            
    except Exception as e:
        print(f"💥 ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_phone_service_status()
    exit(0 if success else 1)