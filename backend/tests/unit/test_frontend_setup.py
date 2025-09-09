"""
Test for T007: Basic Frontend Setup
TDD: Write failing tests first for React components, routing, and API integration
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os


class TestFrontendConfiguration:
    """Test frontend configuration and environment setup"""
    
    def test_frontend_directory_structure(self):
        """Test that frontend directory structure exists"""
        # Expected frontend structure
        expected_dirs = [
            "../frontend",
            "../frontend/app",
            "../frontend/components", 
            "../frontend/lib",
            "../frontend/tests"
        ]
        
        for dir_path in expected_dirs:
            assert os.path.exists(dir_path), f"Directory {dir_path} should exist"
    
    def test_package_json_exists(self):
        """Test that package.json exists with required dependencies"""
        package_json_path = "../frontend/package.json"
        assert os.path.exists(package_json_path), "package.json should exist"
        
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        # Check required dependencies
        dependencies = package_data.get("dependencies", {})
        assert "react" in dependencies, "React should be installed"
        assert "react-dom" in dependencies, "React DOM should be installed"
        assert "axios" in dependencies, "Axios should be installed for API calls"
        assert "@types/react" in dependencies or "@types/react" in package_data.get("devDependencies", {}), "TypeScript React types should be installed"
    
    def test_typescript_config_exists(self):
        """Test that TypeScript configuration exists"""
        tsconfig_path = "../frontend/tsconfig.json"
        assert os.path.exists(tsconfig_path), "tsconfig.json should exist"
        
        with open(tsconfig_path, 'r') as f:
            tsconfig = json.load(f)
        
        assert "compilerOptions" in tsconfig, "TypeScript compiler options should be configured"
        # Next.js may not have tsconfig initially, that's okay
        if "compilerOptions" in tsconfig and "target" in tsconfig["compilerOptions"]:
            target = tsconfig["compilerOptions"]["target"]
            assert target in ["ES2015", "ES2020", "ES2022", "ESNext"], "TypeScript target should be modern"
    
    def test_tailwind_config_exists(self):
        """Test that Tailwind CSS is configured"""
        tailwind_config = "../frontend/tailwind.config.js"
        assert os.path.exists(tailwind_config), "Tailwind config should exist"
        
        # Check that Tailwind is properly configured
        with open(tailwind_config, 'r') as f:
            content = f.read()
            assert "content" in content, "Tailwind should have content paths configured"
            assert "./src/**/*.{js,ts,jsx,tsx}" in content, "Tailwind should scan src directory"


class TestReactComponents:
    """Test basic React components structure"""
    
    def test_app_component_exists(self):
        """Test that main App component exists (Next.js structure)"""
        # In Next.js, check for page.tsx in app directory or pages/index.tsx
        app_page = "../frontend/app/page.tsx"
        index_page = "../frontend/pages/index.tsx"
        
        page_exists = os.path.exists(app_page) or os.path.exists(index_page)
        assert page_exists, "Main page component should exist"
    
    def test_main_entry_point_exists(self):
        """Test that main entry point exists"""
        main_entry = "../frontend/src/main.tsx"
        index_entry = "../frontend/src/index.tsx"
        
        # Either main.tsx or index.tsx should exist
        assert os.path.exists(main_entry) or os.path.exists(index_entry), "Main entry point should exist"
        
        entry_file = main_entry if os.path.exists(main_entry) else index_entry
        with open(entry_file, 'r') as f:
            content = f.read()
            assert "ReactDOM" in content, "Entry point should import ReactDOM"
            assert "App" in content, "Entry point should import App component"
    
    def test_layout_component_exists(self):
        """Test that layout component exists"""
        layout_component = "../frontend/src/components/Layout.tsx"
        assert os.path.exists(layout_component), "Layout component should exist"
        
        with open(layout_component, 'r') as f:
            content = f.read()
            assert "interface" in content or "type" in content, "Layout should have TypeScript types"
            assert "children" in content, "Layout should accept children props"
    
    def test_header_component_exists(self):
        """Test that header component exists"""
        header_component = "../frontend/src/components/Header.tsx"
        assert os.path.exists(header_component), "Header component should exist"
        
        with open(header_component, 'r') as f:
            content = f.read()
            assert "function Header" in content or "const Header" in content, "Header component should be defined"
    
    def test_navigation_component_exists(self):
        """Test that navigation component exists"""
        nav_component = "../frontend/src/components/Navigation.tsx"
        assert os.path.exists(nav_component), "Navigation component should exist"
        
        with open(nav_component, 'r') as f:
            content = f.read()
            assert "Link" in content or "NavLink" in content, "Navigation should use routing links"


class TestRoutingSetup:
    """Test React Router configuration"""
    
    def test_router_config_exists(self):
        """Test that router configuration exists"""
        # Check for router setup in App.tsx or separate router file
        app_file = "../frontend/src/App.tsx"
        router_file = "../frontend/src/routes/index.tsx"
        
        router_configured = False
        
        if os.path.exists(app_file):
            with open(app_file, 'r') as f:
                content = f.read()
                if "BrowserRouter" in content or "createBrowserRouter" in content:
                    router_configured = True
        
        if os.path.exists(router_file):
            with open(router_file, 'r') as f:
                content = f.read()
                if "BrowserRouter" in content or "createBrowserRouter" in content:
                    router_configured = True
        
        assert router_configured, "React Router should be configured"
    
    def test_route_components_exist(self):
        """Test that page components for routes exist"""
        expected_pages = [
            "../frontend/src/pages/Dashboard.tsx",
            "../frontend/src/pages/Tenants.tsx", 
            "../frontend/src/pages/Settings.tsx"
        ]
        
        for page_path in expected_pages:
            assert os.path.exists(page_path), f"Page component {page_path} should exist"
    
    def test_dashboard_page_component(self):
        """Test dashboard page component"""
        dashboard_page = "../frontend/src/pages/Dashboard.tsx"
        assert os.path.exists(dashboard_page), "Dashboard page should exist"
        
        with open(dashboard_page, 'r') as f:
            content = f.read()
            assert "function Dashboard" in content or "const Dashboard" in content, "Dashboard component should be defined"
            assert "export default Dashboard" in content, "Dashboard should be exported"
    
    def test_tenants_page_component(self):
        """Test tenants page component"""
        tenants_page = "../frontend/src/pages/Tenants.tsx"
        assert os.path.exists(tenants_page), "Tenants page should exist"
        
        with open(tenants_page, 'r') as f:
            content = f.read()
            assert "function Tenants" in content or "const Tenants" in content, "Tenants component should be defined"


class TestAPIIntegration:
    """Test API integration setup"""
    
    def test_api_client_exists(self):
        """Test that API client utility exists"""
        api_client = "../frontend/src/services/api.ts"
        assert os.path.exists(api_client), "API client should exist"
        
        with open(api_client, 'r') as f:
            content = f.read()
            assert "axios" in content, "API client should use axios"
            assert "baseURL" in content, "API client should have base URL configured"
    
    def test_tenant_api_service_exists(self):
        """Test that tenant API service exists"""
        tenant_service = "../frontend/src/services/tenantService.ts"
        assert os.path.exists(tenant_service), "Tenant service should exist"
        
        with open(tenant_service, 'r') as f:
            content = f.read()
            assert "createTenant" in content, "Should have createTenant function"
            assert "getTenant" in content, "Should have getTenant function"
            assert "listTenants" in content, "Should have listTenants function"
    
    def test_api_types_exist(self):
        """Test that TypeScript types for API exist"""
        types_file = "../frontend/src/types/api.ts"
        assert os.path.exists(types_file), "API types should exist"
        
        with open(types_file, 'r') as f:
            content = f.read()
            assert "interface" in content or "type" in content, "Should have TypeScript type definitions"
            assert "Tenant" in content, "Should have Tenant interface"
    
    def test_api_constants_exist(self):
        """Test that API constants are configured"""
        constants_file = "../frontend/src/utils/constants.ts"
        config_file = "../frontend/src/config/api.ts"
        
        constants_exist = os.path.exists(constants_file) or os.path.exists(config_file)
        assert constants_exist, "API constants/config should exist"


class TestStylingSetup:
    """Test CSS and styling configuration"""
    
    def test_global_styles_exist(self):
        """Test that global styles are configured"""
        global_css = "../frontend/src/index.css"
        global_styles = "../frontend/src/styles/globals.css"
        
        styles_exist = os.path.exists(global_css) or os.path.exists(global_styles)
        assert styles_exist, "Global styles should exist"
    
    def test_tailwind_directives_exist(self):
        """Test that Tailwind directives are included"""
        style_files = ["../frontend/src/index.css", "../frontend/src/styles/globals.css"]
        
        tailwind_configured = False
        for style_file in style_files:
            if os.path.exists(style_file):
                with open(style_file, 'r') as f:
                    content = f.read()
                    if "@tailwind base" in content and "@tailwind components" in content:
                        tailwind_configured = True
                        break
        
        assert tailwind_configured, "Tailwind directives should be configured"
    
    def test_component_styles_directory(self):
        """Test that component styles directory exists"""
        styles_dir = "../frontend/src/styles"
        components_dir = "../frontend/src/styles/components"
        
        # Either styles directory should exist or components should have individual style files
        assert os.path.exists(styles_dir), "Styles directory should exist"


class TestBuildConfiguration:
    """Test build and development configuration"""
    
    def test_vite_config_exists(self):
        """Test that Vite configuration exists"""
        vite_config = "../frontend/vite.config.ts"
        assert os.path.exists(vite_config), "Vite config should exist"
        
        with open(vite_config, 'r') as f:
            content = f.read()
            assert "defineConfig" in content, "Vite config should use defineConfig"
            assert "react" in content, "Vite should be configured for React"
    
    def test_env_example_exists(self):
        """Test that environment example file exists"""
        env_example = "../frontend/.env.example"
        assert os.path.exists(env_example), ".env.example should exist"
        
        with open(env_example, 'r') as f:
            content = f.read()
            assert "VITE_API_BASE_URL" in content, "Should have API base URL environment variable"
    
    def test_package_scripts_configured(self):
        """Test that npm scripts are properly configured"""
        package_json_path = "../frontend/package.json"
        assert os.path.exists(package_json_path), "package.json should exist"
        
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get("scripts", {})
        assert "dev" in scripts, "Dev script should exist"
        assert "build" in scripts, "Build script should exist"
        assert "preview" in scripts, "Preview script should exist"


class TestComponentIntegration:
    """Test component integration and data flow"""
    
    def test_tenant_list_component_exists(self):
        """Test that tenant list component exists"""
        tenant_list = "../frontend/src/components/TenantList.tsx"
        assert os.path.exists(tenant_list), "TenantList component should exist"
    
    def test_tenant_form_component_exists(self):
        """Test that tenant form component exists"""
        tenant_form = "../frontend/src/components/TenantForm.tsx"
        assert os.path.exists(tenant_form), "TenantForm component should exist"
    
    def test_loading_component_exists(self):
        """Test that loading component exists"""
        loading_component = "../frontend/src/components/Loading.tsx"
        spinner_component = "../frontend/src/components/Spinner.tsx"
        
        loading_exists = os.path.exists(loading_component) or os.path.exists(spinner_component)
        assert loading_exists, "Loading component should exist"
    
    def test_error_boundary_exists(self):
        """Test that error boundary component exists"""
        error_boundary = "../frontend/src/components/ErrorBoundary.tsx"
        assert os.path.exists(error_boundary), "ErrorBoundary component should exist"


if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    pytest.main([__file__, "-v"])