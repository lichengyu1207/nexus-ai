# API Layer

This directory contains the API layer of the application, responsible for handling HTTP requests and responses.

## Structure

- `endpoints/`: Contains route handlers for different resources:
  - `property.py`: Endpoints for property-related operations
  - `report.py`: Endpoints for report-related operations
  - `task.py`: Endpoints for task-related operations
  - `user.py`: Endpoints for user-related operations

## Key Responsibilities

- Define API routes and request handlers
- Validate incoming requests using Pydantic schemas
- Call appropriate services to process requests
- Return formatted responses to clients
- Handle authentication and authorization