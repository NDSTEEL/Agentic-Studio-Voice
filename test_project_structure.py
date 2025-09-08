"""
Test for T001: Project Structure Setup
TDD: Write failing test first, then implement structure
"""
import os
import json
from pathlib import Path

def test_backend_directory_structure():
    """Test that all required backend directories exist"""
    backend_dirs = [
        'backend',
        'backend/src',
        'backend/src/api',
        'backend/src/models', 
        'backend/src/services',
        'backend/src/auth',
        'backend/src/database',
        'backend/tests',
        'backend/tests/unit',
        'backend/tests/integration',
        'backend/tests/contract',
        'backend/tests/fixtures',
        'backend/docker'
    ]
    
    for directory in backend_dirs:
        assert os.path.exists(directory), f"Backend directory {directory} should exist"

def test_frontend_directory_structure():
    """Test that all required frontend directories exist"""
    frontend_dirs = [
        'frontend',
        'frontend/app',
        'frontend/app/(dashboard)',
        'frontend/app/api',
        'frontend/app/auth',
        'frontend/components',
        'frontend/components/ui',
        'frontend/lib',
        'frontend/tests',
        'frontend/tests/components'
    ]
    
    for directory in frontend_dirs:
        assert os.path.exists(directory), f"Frontend directory {directory} should exist"

def test_backend_requirements_file():
    """Test that backend requirements.txt exists and has basic dependencies"""
    requirements_file = 'backend/requirements.txt'
    assert os.path.exists(requirements_file), "backend/requirements.txt should exist"
    
    with open(requirements_file, 'r') as f:
        content = f.read()
        
    required_deps = ['fastapi', 'sqlalchemy', 'asyncpg', 'pydantic', 'pytest']
    for dep in required_deps:
        assert dep in content, f"Dependency {dep} should be in requirements.txt"

def test_frontend_package_json():
    """Test that frontend package.json exists with required dependencies"""
    package_json = 'frontend/package.json'
    assert os.path.exists(package_json), "frontend/package.json should exist"
    
    with open(package_json, 'r') as f:
        config = json.load(f)
    
    assert 'dependencies' in config, "package.json should have dependencies"
    assert 'next' in config['dependencies'], "Next.js should be in dependencies"
    assert 'typescript' in config['devDependencies'], "TypeScript should be in devDependencies"

def test_docker_compose_exists():
    """Test that docker-compose.yml exists for development"""
    assert os.path.exists('docker-compose.yml'), "docker-compose.yml should exist"
    
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    required_services = ['postgres', 'redis', 'backend', 'frontend']
    for service in required_services:
        assert service in content, f"Service {service} should be in docker-compose.yml"

if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    import pytest
    pytest.main([__file__, "-v"])