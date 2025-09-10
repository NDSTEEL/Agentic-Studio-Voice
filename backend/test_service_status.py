#!/usr/bin/env python3
"""
TEST-FIXER-3: Service Status Audit
Check current status of all pipeline services
"""
import sys
import os
sys.path.append('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')

from src.services.pipeline.agent_pipeline import AgentCreationPipeline

def main():
    print("🔍 TEST-FIXER-3: Service Status Audit")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        print("Initializing Agent Creation Pipeline...")
        pipeline = AgentCreationPipeline(safe_mode=True)
        
        # Get service status
        status = pipeline.get_service_status()
        
        print("\n📊 SERVICE STATUS REPORT")
        print("-" * 30)
        print(f"Pipeline Mode: {status['pipeline_mode'].upper()}")
        print(f"Total Services: {status['total_services']}")
        print(f"Healthy Services: {status['healthy_services']}")
        print(f"Degraded Services: {status['degraded_services']}")
        
        print("\n📋 INDIVIDUAL SERVICE STATUS")
        print("-" * 30)
        for service, is_healthy in status['service_status'].items():
            icon = "✅" if is_healthy else "❌"
            status_text = "REAL" if is_healthy else "MOCK"
            print(f"{icon} {service}: {status_text}")
        
        # Determine what needs to be fixed
        degraded_services = [
            service for service, is_healthy in status['service_status'].items() 
            if not is_healthy
        ]
        
        if degraded_services:
            print(f"\n🚨 DEGRADED SERVICES REQUIRING CREDENTIALS:")
            for service in degraded_services:
                print(f"   - {service}")
        
        print(f"\n🎯 MISSION STATUS: {status['healthy_services']}/{status['total_services']} services operational")
        
        return status
        
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize pipeline: {e}")
        return None

if __name__ == "__main__":
    main()