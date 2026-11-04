# LIFEGRID
LIFEGRID helps communities connect available resources with people who need them. For example, a restaurant can list surplus food for people and animal feeders that need them. A coordinator reviews requests and manually matches them with available resources.

Objective
Build a working application that allows users to register, publish available resources, submit requests and coordinate fulfilment.

For the first release, I am working on a pilot scenario: community resource sharing and volunteer coordination.

Functional requirements
User registration: Register, log in and manage basic profiles
User roles: Support requester, resource provider and administrator
Resource management: Create, view, edit and deactivate resources
Request management:	Submit, view, update and cancel resource requests
Resource categories: Categorise resources such as volunteers, equipment, transport and supplies
Availability:	Record resource availability and quantity
Manual matching: Allow administrators to match a resource to a request
Assignment tracking: Track requested, assigned, accepted, completed and cancelled states
Dashboard: Display active requests, available resources and pending assignments
Search and filters:	Search by category, location and availability

Basic user workflow
Resource provider -> Registers a resource: Two volunteers available on Saturday.
Requester -> Creates a request: Need two volunteers for a community activity.
Administrator -> Reviews the request and manually assigns the available volunteers.
Assignment completed -> Both parties can track the assignment and update its status.

Tech stack:
Frontend: React
Backend: Python, FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Authentication: JWT
API documentation: OpenAPI / Swagger
Deployment: Docker
Testing: Pytest

Architecture: modular monolith. 
