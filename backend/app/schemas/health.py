from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    status: str = Field(..., description="Database status: healthy or unhealthy")
    connected: bool = Field(..., description="Boolean connection status")
    message: str = Field(..., description="Details or diagnostics message")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall API operational status")
    project_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Active deployment environment")
    version: str = Field(default="0.1.0", description="API version")
    database: DatabaseHealth = Field(..., description="Database connectivity status")
