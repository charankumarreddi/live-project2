"""
Test API endpoints with comprehensive coverage.
"""
import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient, test_user_data):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, client: AsyncClient, test_user_data):
        """Test duplicate user registration fails."""
        # Register user first time
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register again
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_login_user(self, client: AsyncClient, test_user_data):
        """Test user login."""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, test_user_data):
        """Test getting current user info."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]


class TestTaskAPI:
    """Test task management endpoints."""
    
    async def get_auth_headers(self, client: AsyncClient, test_user_data):
        """Helper to get authentication headers."""
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient, test_user_data, test_task_data):
        """Test task creation."""
        headers = await self.get_auth_headers(client, test_user_data)
        
        response = await client.post("/api/v1/tasks", json=test_task_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == test_task_data["title"]
        assert data["description"] == test_task_data["description"]
        assert data["priority"] == test_task_data["priority"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_tasks(self, client: AsyncClient, test_user_data, test_task_data):
        """Test getting user tasks."""
        headers = await self.get_auth_headers(client, test_user_data)
        
        # Create a task first
        await client.post("/api/v1/tasks", json=test_task_data, headers=headers)
        
        # Get tasks
        response = await client.get("/api/v1/tasks", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == test_task_data["title"]
    
    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, client: AsyncClient, test_task_data):
        """Test task creation without authentication."""
        response = await client.post("/api/v1/tasks", json=test_task_data)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_tasks_unauthorized(self, client: AsyncClient):
        """Test getting tasks without authentication."""
        response = await client.get("/api/v1/tasks")
        assert response.status_code == 403


class TestHealthAPI:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness probe."""
        response = await client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness probe."""
        response = await client.get("/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data