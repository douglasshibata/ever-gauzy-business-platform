"""
Ever Gauzy Business Management Platform - Configuration & Infrastructure Test Suite
"""

import os
import re
import pytest
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_docker_compose_structure():
    """Verify docker-compose.yml exists, is valid YAML, and contains essential services."""
    compose_path = os.path.join(BASE_DIR, "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml does not exist"

    with open(compose_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config, "docker-compose.yml must define 'services'"
    services = config["services"]

    required_services = ["gauzy-server", "postgres", "redis", "nginx"]
    for service in required_services:
        assert service in services, f"Service '{service}' is missing from docker-compose.yml"

    # Check PostgreSQL healthcheck
    assert "healthcheck" in services["postgres"], "PostgreSQL service must configure a healthcheck"
    # Check Redis healthcheck
    assert "healthcheck" in services["redis"], "Redis service must configure a healthcheck"


def test_env_example_completeness():
    """Verify .env.example contains all required enterprise environment variables."""
    env_path = os.path.join(BASE_DIR, ".env.example")
    assert os.path.exists(env_path), ".env.example does not exist"

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_vars = [
        "NODE_ENV",
        "PORT",
        "CLIENT_BASE_URL",
        "API_BASE_URL",
        "DB_TYPE",
        "DB_HOST",
        "DB_PORT",
        "DB_USERNAME",
        "DB_PASSWORD",
        "DB_DATABASE",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD",
        "JWT_SECRET",
        "JWT_REFRESH_SECRET",
        "GOOGLE_CLIENT_ID",
        "GITHUB_CLIENT_ID",
        "JIRA_HOST",
        "STRIPE_SECRET_KEY",
        "SMTP_HOST",
    ]

    for var in required_vars:
        assert re.search(rf"^{var}=", content, re.MULTILINE), f"Variable '{var}' missing in .env.example"


def test_nginx_config_rules():
    """Verify Nginx reverse proxy configuration has required security & routing rules."""
    nginx_path = os.path.join(BASE_DIR, "nginx", "gauzy.conf")
    assert os.path.exists(nginx_path), "nginx/gauzy.conf does not exist"

    with open(nginx_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "upstream gauzy_backend" in content, "Nginx config missing gauzy_backend upstream"
    assert "upstream gauzy_frontend" in content, "Nginx config missing gauzy_frontend upstream"
    assert "location /api/" in content, "Nginx config missing /api/ proxy location"
    assert "location /socket.io/" in content, "Nginx config missing WebSockets /socket.io/ route"
    assert "limit_req_zone" in content, "Nginx config missing rate limiting directives"
    assert "add_header X-Frame-Options" in content, "Nginx config missing security headers"


def test_kubernetes_manifests():
    """Verify Kubernetes manifests exist and are valid YAML format."""
    k8s_dir = os.path.join(BASE_DIR, "k8s")
    assert os.path.exists(k8s_dir), "k8s directory does not exist"

    manifest_files = ["deployment.yaml", "service.yaml", "ingress.yaml", "configmap.yaml", "secret.yaml"]
    for filename in manifest_files:
        filepath = os.path.join(k8s_dir, filename)
        assert os.path.exists(filepath), f"Kubernetes manifest '{filename}' is missing"

        with open(filepath, "r", encoding="utf-8") as f:
            parsed = yaml.safe_load(f)
            assert parsed is not None, f"Manifest '{filename}' is empty or invalid YAML"
            assert "kind" in parsed, f"Manifest '{filename}' missing 'kind' field"
            assert "metadata" in parsed, f"Manifest '{filename}' missing 'metadata' field"


def test_backup_script_executable():
    """Verify database backup script exists and contains retention rules."""
    script_path = os.path.join(BASE_DIR, "scripts", "backup_gauzy_db.sh")
    assert os.path.exists(script_path), "backup_gauzy_db.sh does not exist"

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "pg_dump" in content, "Backup script must invoke pg_dump"
    assert "RETENTION_DAYS" in content, "Backup script must enforce a retention policy"
