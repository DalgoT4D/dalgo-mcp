"""Shared parameter definitions for dalgo-mcp tools.

Use these Annotated types as function parameter annotations to get
consistent descriptions across tools. FastMCP reads the Annotated
metadata to generate parameter descriptions in the tool schema.
"""
from typing import Annotated

from pydantic import Field

# Pipeline parameters
DeploymentId = Annotated[str, Field(description="The Prefect deployment ID.")]
FlowRunId = Annotated[str, Field(description="The Prefect flow run ID.")]

# Warehouse parameters
SchemaName = Annotated[str, Field(description="The warehouse schema name.")]
TableName = Annotated[str, Field(description="The warehouse table name.")]

# Chart / Dashboard parameters
ChartId = Annotated[str, Field(description="The chart ID.")]
DashboardId = Annotated[str, Field(description="The dashboard ID.")]

# Source / Connection parameters
SourceId = Annotated[str, Field(description="The Airbyte source ID.")]
ConnectionId = Annotated[str, Field(description="The Airbyte connection ID.")]

# Common pagination
Limit = Annotated[int, Field(default=10, description="Maximum number of items to return.", ge=1, le=500)]
Offset = Annotated[int, Field(default=0, description="Number of items to skip for pagination.", ge=0)]
