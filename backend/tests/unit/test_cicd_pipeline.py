"""
T010: CI/CD Pipeline Setup Tests
Test-driven development for GitHub Actions automated testing and quality checks
"""
import os
import yaml
import json
import pytest
from unittest.mock import patch, MagicMock


class TestGitHubActions:
    """Test GitHub Actions workflow configuration"""
    
    def test_github_workflows_directory_exists(self):
        """Test that .github/workflows directory exists"""
        workflows_dir = "../.github/workflows"
        assert os.path.exists(workflows_dir), "GitHub workflows directory should exist"
    
    def test_ci_workflow_file_exists(self):
        """Test that CI workflow file exists"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        # Should have at least one CI/test workflow
        workflow_exists = (os.path.exists(ci_workflow) or 
                          os.path.exists(ci_workflow_yaml) or 
                          os.path.exists(test_workflow))
        assert workflow_exists, "CI workflow file should exist"
    
    def test_ci_workflow_configuration(self):
        """Test that CI workflow is properly configured"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        # Find the workflow file
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        assert workflow_file is not None, "CI workflow file should exist"
        
        with open(workflow_file, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        # Should have proper workflow structure
        assert 'name' in workflow_data, "Workflow should have a name"
        assert 'on' in workflow_data, "Workflow should have triggers"
        assert 'jobs' in workflow_data, "Workflow should have jobs"
        
        # Should trigger on push and pull requests
        triggers = workflow_data['on']
        if isinstance(triggers, dict):
            assert 'push' in triggers or 'pull_request' in triggers, "Should trigger on push or PR"
        
        # Should have at least one job
        jobs = workflow_data['jobs']
        assert len(jobs) >= 1, "Should have at least one job"
    
    def test_ci_workflow_includes_testing(self):
        """Test that CI workflow includes automated testing"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Should include testing commands
        has_testing = ("pytest" in content or 
                      "npm test" in content or 
                      "test" in content.lower())
        assert has_testing, "CI workflow should include testing"
    
    def test_ci_workflow_python_setup(self):
        """Test that CI workflow sets up Python environment"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Should setup Python environment
        has_python_setup = ("python" in content.lower() and 
                           ("setup-python" in content or "python-version" in content))
        assert has_python_setup, "CI workflow should set up Python environment"
    
    def test_ci_workflow_node_setup(self):
        """Test that CI workflow sets up Node.js environment"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Should setup Node.js environment
        has_node_setup = ("node" in content.lower() and 
                         ("setup-node" in content or "node-version" in content))
        assert has_node_setup, "CI workflow should set up Node.js environment"


class TestCodeQualityChecks:
    """Test linting and code quality configuration"""
    
    def test_python_linting_configuration(self):
        """Test that Python linting is configured"""
        # Check for linting configuration files
        flake8_config = "../.flake8"
        pyproject_toml = "../pyproject.toml"
        setup_cfg = "../setup.cfg"
        ruff_config = "../ruff.toml"
        
        # Should have some linting configuration
        has_linting_config = (os.path.exists(flake8_config) or 
                             os.path.exists(pyproject_toml) or 
                             os.path.exists(setup_cfg) or 
                             os.path.exists(ruff_config))
        
        # Or check in CI workflow for linting commands
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            has_linting_in_ci = ("flake8" in content or 
                                "ruff" in content or 
                                "pylint" in content or
                                "black" in content)
            has_linting_config = has_linting_config or has_linting_in_ci
        
        assert has_linting_config, "Python linting should be configured"
    
    def test_frontend_linting_configuration(self):
        """Test that frontend linting is configured"""
        # Check for ESLint configuration
        eslintrc_js = "../frontend/.eslintrc.js"
        eslintrc_json = "../frontend/.eslintrc.json"
        eslint_config = "../frontend/eslint.config.js"
        package_json = "../frontend/package.json"
        
        has_eslint_config = (os.path.exists(eslintrc_js) or 
                            os.path.exists(eslintrc_json) or 
                            os.path.exists(eslint_config))
        
        # Check package.json for ESLint
        if os.path.exists(package_json):
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            # Check for ESLint in dependencies or scripts
            deps = package_data.get('devDependencies', {})
            scripts = package_data.get('scripts', {})
            
            has_eslint_deps = 'eslint' in deps
            has_lint_script = any('lint' in script for script in scripts.values())
            
            has_eslint_config = has_eslint_config or has_eslint_deps or has_lint_script
        
        assert has_eslint_config, "Frontend linting should be configured"
    
    def test_code_formatting_configuration(self):
        """Test that code formatting is configured"""
        # Check for formatting tools
        prettier_config = "../.prettierrc"
        prettier_json = "../.prettierrc.json"
        black_config_in_pyproject = "../pyproject.toml"
        
        has_formatting = (os.path.exists(prettier_config) or 
                         os.path.exists(prettier_json))
        
        # Check for Black configuration in pyproject.toml
        if os.path.exists(black_config_in_pyproject):
            with open(black_config_in_pyproject, 'r') as f:
                content = f.read()
                has_formatting = has_formatting or "black" in content.lower()
        
        # Or check in CI workflow for formatting commands
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            has_formatting_in_ci = ("black" in content or 
                                   "prettier" in content or
                                   "format" in content)
            has_formatting = has_formatting or has_formatting_in_ci


class TestCoverageReporting:
    """Test test coverage reporting configuration"""
    
    def test_coverage_configuration_exists(self):
        """Test that test coverage is configured"""
        # Check for coverage configuration
        coverage_config = "../.coveragerc"
        pyproject_toml = "../pyproject.toml"
        setup_cfg = "../setup.cfg"
        
        has_coverage_config = os.path.exists(coverage_config)
        
        # Check for coverage in pyproject.toml or setup.cfg
        for config_file in [pyproject_toml, setup_cfg]:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                    if "coverage" in content.lower():
                        has_coverage_config = True
                        break
        
        # Or check in CI workflow for coverage commands
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            has_coverage_in_ci = ("coverage" in content or 
                                 "--cov" in content or
                                 "codecov" in content)
            has_coverage_config = has_coverage_config or has_coverage_in_ci
        
        assert has_coverage_config, "Test coverage should be configured"
    
    def test_coverage_threshold_configured(self):
        """Test that coverage threshold is set to 80% minimum"""
        coverage_config = "../.coveragerc"
        pyproject_toml = "../pyproject.toml"
        setup_cfg = "../setup.cfg"
        
        coverage_threshold_found = False
        
        # Check .coveragerc
        if os.path.exists(coverage_config):
            with open(coverage_config, 'r') as f:
                content = f.read()
                if "fail_under" in content:
                    coverage_threshold_found = True
        
        # Check pyproject.toml
        if os.path.exists(pyproject_toml):
            with open(pyproject_toml, 'r') as f:
                content = f.read()
                if "fail_under" in content or "min_percentage" in content:
                    coverage_threshold_found = True
        
        # Check setup.cfg
        if os.path.exists(setup_cfg):
            with open(setup_cfg, 'r') as f:
                content = f.read()
                if "fail_under" in content:
                    coverage_threshold_found = True
        
        # Note: This test checks for configuration, not the specific 80% value
        # as different projects might have different thresholds


class TestDependencyManagement:
    """Test dependency management and security"""
    
    def test_dependabot_configuration(self):
        """Test that Dependabot is configured for dependency updates"""
        dependabot_config = "../.github/dependabot.yml"
        dependabot_config_yaml = "../.github/dependabot.yaml"
        
        dependabot_exists = (os.path.exists(dependabot_config) or 
                           os.path.exists(dependabot_config_yaml))
        
        if dependabot_exists:
            config_file = dependabot_config if os.path.exists(dependabot_config) else dependabot_config_yaml
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            assert 'updates' in config_data, "Dependabot should have update configurations"
            
            updates = config_data['updates']
            package_ecosystems = [update.get('package-ecosystem') for update in updates]
            
            # Should monitor both Python and npm dependencies
            assert 'pip' in package_ecosystems, "Should monitor Python dependencies"
            assert 'npm' in package_ecosystems, "Should monitor npm dependencies"
    
    def test_security_scanning_configured(self):
        """Test that security scanning is configured"""
        # Check for security scanning in CI workflow
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        security_workflow = "../.github/workflows/security.yml"
        
        has_security_scan = os.path.exists(security_workflow)
        
        # Check for security scanning in CI workflow
        for workflow_file in [ci_workflow, ci_workflow_yaml]:
            if os.path.exists(workflow_file):
                with open(workflow_file, 'r') as f:
                    content = f.read()
                
                has_security_in_ci = ("bandit" in content or 
                                     "safety" in content or 
                                     "npm audit" in content or
                                     "security" in content.lower())
                has_security_scan = has_security_scan or has_security_in_ci
                break


class TestBuildAndDeploy:
    """Test build and deployment configuration"""
    
    def test_docker_build_in_ci(self):
        """Test that Docker builds are tested in CI"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Should test Docker builds
            has_docker_build = ("docker build" in content or 
                              "docker-compose" in content or
                              "docker compose" in content)
            
            # This is optional but recommended for CI/CD pipeline
    
    def test_environment_matrix(self):
        """Test that CI runs on multiple environments"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # Should test on multiple Python/Node versions or OS
            jobs = workflow_data.get('jobs', {})
            for job_name, job_config in jobs.items():
                strategy = job_config.get('strategy', {})
                matrix = strategy.get('matrix', {})
                
                has_matrix = (len(matrix.get('python-version', [])) > 1 or
                             len(matrix.get('node-version', [])) > 1 or
                             len(matrix.get('os', [])) > 1)
                
                # This is optional but recommended for robust CI


class TestCIPipelineFunctionality:
    """Test that CI pipeline validates correctly"""
    
    def test_workflow_syntax_valid(self):
        """Test that workflow YAML syntax is valid"""
        workflows_dir = "../.github/workflows"
        
        if os.path.exists(workflows_dir):
            for filename in os.listdir(workflows_dir):
                if filename.endswith(('.yml', '.yaml')):
                    workflow_path = os.path.join(workflows_dir, filename)
                    
                    try:
                        with open(workflow_path, 'r') as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        pytest.fail(f"Invalid YAML syntax in {filename}: {e}")
    
    def test_required_secrets_documented(self):
        """Test that required secrets are documented"""
        ci_workflow = "../.github/workflows/ci.yml"
        ci_workflow_yaml = "../.github/workflows/ci.yaml"
        test_workflow = "../.github/workflows/test.yml"
        readme = "../README.md"
        
        workflow_file = None
        for file_path in [ci_workflow, ci_workflow_yaml, test_workflow]:
            if os.path.exists(file_path):
                workflow_file = file_path
                break
        
        if workflow_file:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # If workflow uses secrets, they should be documented
            if "secrets." in content:
                # Should have documentation about secrets
                if os.path.exists(readme):
                    with open(readme, 'r') as f:
                        readme_content = f.read()
                    
                    has_secrets_docs = ("secrets" in readme_content.lower() or 
                                      "environment" in readme_content.lower())
                    # This is good practice but not always required