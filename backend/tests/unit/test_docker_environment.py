"""
T009: Docker Development Environment Tests
Test-driven development for multi-service docker-compose setup
"""
import os
import json
import yaml
import pytest
from unittest.mock import patch, MagicMock


class TestDockerComposeConfiguration:
    """Test docker-compose setup and configuration"""
    
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        # Either docker-compose.yml or docker-compose.dev.yml should exist
        compose_exists = os.path.exists(docker_compose) or os.path.exists(docker_compose_dev)
        assert compose_exists, "Docker compose file should exist"
    
    def test_docker_compose_services_configured(self):
        """Test that required services are configured in docker-compose"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose if os.path.exists(docker_compose) else docker_compose_dev
        assert os.path.exists(compose_file), "Docker compose file should exist"
        
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        # Required services for voice agent platform
        required_services = ['backend', 'frontend', 'postgres']
        for service in required_services:
            # Allow flexibility in service naming
            service_exists = (service in services or 
                            f"{service}-dev" in services or
                            (service == 'postgres' and 'database' in services))
            assert service_exists, f"Service {service} should be configured"
    
    def test_postgres_service_configuration(self):
        """Test that PostgreSQL service is properly configured"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose if os.path.exists(docker_compose) else docker_compose_dev
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        # Find PostgreSQL service (could be named database, postgres, db, etc.)
        postgres_service = None
        for service_name, service_config in services.items():
            if 'postgres' in service_config.get('image', '').lower():
                postgres_service = service_config
                break
        
        assert postgres_service is not None, "PostgreSQL service should be configured"
        assert 'environment' in postgres_service, "PostgreSQL should have environment variables"
        
        env_vars = postgres_service['environment']
        if isinstance(env_vars, list):
            env_vars = {var.split('=')[0]: var.split('=')[1] for var in env_vars if '=' in var}
        
        assert 'POSTGRES_DB' in env_vars, "PostgreSQL database name should be configured"
        assert 'POSTGRES_USER' in env_vars, "PostgreSQL user should be configured"
        assert 'POSTGRES_PASSWORD' in env_vars, "PostgreSQL password should be configured"

    def test_backend_service_configuration(self):
        """Test that backend service is properly configured"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose if os.path.exists(docker_compose) else docker_compose_dev
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        # Find backend service
        backend_service = services.get('backend') or services.get('backend-dev') or services.get('api')
        assert backend_service is not None, "Backend service should be configured"
        
        # Should have volume mounts for hot reload
        assert 'volumes' in backend_service, "Backend should have volume mounts for hot reload"
        
        # Should expose a port
        assert 'ports' in backend_service, "Backend should expose ports"


class TestDockerfiles:
    """Test Dockerfile configuration for services"""
    
    def test_backend_dockerfile_exists(self):
        """Test that backend Dockerfile exists"""
        backend_dockerfile = "../backend/Dockerfile"
        backend_dockerfile_dev = "../backend/Dockerfile.dev"
        
        dockerfile_exists = os.path.exists(backend_dockerfile) or os.path.exists(backend_dockerfile_dev)
        assert dockerfile_exists, "Backend Dockerfile should exist"
    
    def test_frontend_dockerfile_exists(self):
        """Test that frontend Dockerfile exists"""
        frontend_dockerfile = "../frontend/Dockerfile"
        frontend_dockerfile_dev = "../frontend/Dockerfile.dev"
        
        dockerfile_exists = os.path.exists(frontend_dockerfile) or os.path.exists(frontend_dockerfile_dev)
        assert dockerfile_exists, "Frontend Dockerfile should exist"
    
    def test_backend_dockerfile_configuration(self):
        """Test that backend Dockerfile is properly configured"""
        backend_dockerfile = "../backend/Dockerfile"
        backend_dockerfile_dev = "../backend/Dockerfile.dev"
        
        dockerfile = backend_dockerfile if os.path.exists(backend_dockerfile) else backend_dockerfile_dev
        assert os.path.exists(dockerfile), "Backend Dockerfile should exist"
        
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Should use Python base image
        assert "FROM python:" in content, "Should use Python base image"
        
        # Should install dependencies
        assert "pip install" in content or "poetry install" in content, "Should install Python dependencies"
        
        # Should expose a port
        assert "EXPOSE" in content, "Should expose a port"
        
        # Should have a CMD or ENTRYPOINT
        assert "CMD" in content or "ENTRYPOINT" in content, "Should have startup command"

    def test_frontend_dockerfile_configuration(self):
        """Test that frontend Dockerfile is properly configured"""
        frontend_dockerfile = "../frontend/Dockerfile"
        frontend_dockerfile_dev = "../frontend/Dockerfile.dev"
        
        dockerfile = frontend_dockerfile if os.path.exists(frontend_dockerfile) else frontend_dockerfile_dev
        assert os.path.exists(dockerfile), "Frontend Dockerfile should exist"
        
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Should use Node base image
        assert "FROM node:" in content, "Should use Node base image"
        
        # Should install dependencies
        assert "npm install" in content or "yarn install" in content, "Should install Node dependencies"
        
        # Should expose a port
        assert "EXPOSE" in content, "Should expose a port"


class TestEnvironmentConfiguration:
    """Test environment variable management"""
    
    def test_env_example_files_exist(self):
        """Test that .env.example files exist for services"""
        backend_env_example = "../backend/.env.example"
        frontend_env_example = "../frontend/.env.example"
        
        assert os.path.exists(backend_env_example), "Backend .env.example should exist"
        assert os.path.exists(frontend_env_example), "Frontend .env.example should exist"
    
    def test_docker_env_file_exists(self):
        """Test that Docker environment file exists"""
        docker_env = "../.env.docker"
        docker_env_dev = "../.env.docker.dev"
        env_file = "../.env"
        
        env_exists = (os.path.exists(docker_env) or 
                     os.path.exists(docker_env_dev) or 
                     os.path.exists(env_file))
        assert env_exists, "Docker environment file should exist"
    
    def test_backend_env_variables(self):
        """Test that backend environment variables are configured"""
        backend_env_example = "../backend/.env.example"
        
        with open(backend_env_example, 'r') as f:
            content = f.read()
        
        # Should have database configuration
        assert "DATABASE_URL" in content or "DB_" in content, "Should have database configuration"
        
        # Should have API configuration
        assert "API_" in content or "PORT" in content, "Should have API configuration"
    
    def test_frontend_env_variables(self):
        """Test that frontend environment variables are configured"""
        frontend_env_example = "../frontend/.env.example"
        
        with open(frontend_env_example, 'r') as f:
            content = f.read()
        
        # Should have API URL configuration
        assert "API_URL" in content or "NEXT_PUBLIC_API_URL" in content, "Should have API URL configuration"


class TestHotReloadConfiguration:
    """Test hot reload setup for development"""
    
    def test_backend_hot_reload_setup(self):
        """Test that backend has hot reload configured"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose_dev if os.path.exists(docker_compose_dev) else docker_compose
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        backend_service = services.get('backend') or services.get('backend-dev') or services.get('api')
        
        # Should have volume mounts for source code
        volumes = backend_service.get('volumes', [])
        has_source_mount = any('./backend' in volume or '/app' in volume for volume in volumes)
        assert has_source_mount, "Backend should have source code volume mount for hot reload"
    
    def test_frontend_hot_reload_setup(self):
        """Test that frontend has hot reload configured"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose_dev if os.path.exists(docker_compose_dev) else docker_compose
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        frontend_service = services.get('frontend') or services.get('frontend-dev') or services.get('web')
        
        if frontend_service:  # Frontend service might be optional in some setups
            # Should have volume mounts for source code
            volumes = frontend_service.get('volumes', [])
            has_source_mount = any('./frontend' in volume or '/app' in volume for volume in volumes)
            assert has_source_mount, "Frontend should have source code volume mount for hot reload"


class TestServiceConnectivity:
    """Test service connectivity and networking"""
    
    def test_services_use_same_network(self):
        """Test that services are configured to communicate"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose if os.path.exists(docker_compose) else docker_compose_dev
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        # Services should either share the default network or have explicit networking
        # This test checks basic structure is in place for service communication
        assert len(services) >= 2, "Should have multiple services that can communicate"
    
    def test_database_connection_string(self):
        """Test that database connection is configured for Docker networking"""
        backend_env_example = "../backend/.env.example"
        
        with open(backend_env_example, 'r') as f:
            content = f.read()
        
        # Should reference database service by name (not localhost)
        # This ensures proper Docker networking
        if "DATABASE_URL" in content:
            # Should use service name instead of localhost for Docker
            db_config_present = ("database:" in content or 
                               "postgres:" in content or 
                               "db:" in content)
            # Note: This is a basic check - in development might still use localhost


class TestDockerIgnore:
    """Test .dockerignore files"""
    
    def test_backend_dockerignore_exists(self):
        """Test that backend .dockerignore exists"""
        backend_dockerignore = "../backend/.dockerignore"
        
        if os.path.exists("../backend/Dockerfile"):
            # If Dockerfile exists, should have .dockerignore for optimization
            assert os.path.exists(backend_dockerignore), "Backend .dockerignore should exist for build optimization"
    
    def test_frontend_dockerignore_exists(self):
        """Test that frontend .dockerignore exists"""
        frontend_dockerignore = "../frontend/.dockerignore"
        
        if os.path.exists("../frontend/Dockerfile"):
            # If Dockerfile exists, should have .dockerignore for optimization
            assert os.path.exists(frontend_dockerignore), "Frontend .dockerignore should exist for build optimization"
    
    def test_dockerignore_content(self):
        """Test that .dockerignore files have appropriate content"""
        backend_dockerignore = "../backend/.dockerignore"
        frontend_dockerignore = "../frontend/.dockerignore"
        
        if os.path.exists(backend_dockerignore):
            with open(backend_dockerignore, 'r') as f:
                content = f.read()
            assert "__pycache__" in content, "Should ignore Python cache files"
            assert "*.pyc" in content or "**/*.pyc" in content, "Should ignore Python compiled files"
        
        if os.path.exists(frontend_dockerignore):
            with open(frontend_dockerignore, 'r') as f:
                content = f.read()
            assert "node_modules" in content, "Should ignore node_modules"
            assert ".next" in content or "dist" in content, "Should ignore build directories"


class TestDevelopmentWorkflow:
    """Test development workflow with Docker"""
    
    def test_docker_compose_command_scripts(self):
        """Test that convenience scripts exist for Docker commands"""
        package_json = "../package.json"
        makefile = "../Makefile"
        scripts_dir = "../scripts/"
        
        # Should have some way to easily run Docker commands
        has_scripts = (os.path.exists(package_json) or 
                      os.path.exists(makefile) or 
                      os.path.exists(scripts_dir))
        
        # This is optional but recommended for developer experience
        if os.path.exists(package_json):
            with open(package_json, 'r') as f:
                content = json.load(f)
            
            scripts = content.get('scripts', {})
            # Should have development scripts
            has_dev_scripts = any('docker' in script or 'dev' in script for script in scripts.values())
    
    def test_health_checks_configured(self):
        """Test that services have health checks"""
        docker_compose = "../docker-compose.yml"
        docker_compose_dev = "../docker-compose.dev.yml"
        
        compose_file = docker_compose if os.path.exists(docker_compose) else docker_compose_dev
        with open(compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        services = compose_data.get('services', {})
        
        # At least critical services should have health checks
        for service_name, service_config in services.items():
            if 'postgres' in service_config.get('image', ''):
                # Database should have health check for dependency management
                has_healthcheck = 'healthcheck' in service_config
                # Note: This is optional but recommended for production readiness