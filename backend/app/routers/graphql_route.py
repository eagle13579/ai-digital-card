"""GraphQL route — serves POST /graphql and GET /graphql (Banana Cake Pop IDE)."""

from fastapi import APIRouter

try:
    from strawberry.fastapi import GraphQLRouter
    from app.graphql.schema import schema
    HAS_STRAWBERRY = True
except ImportError:
    HAS_STRAWBERRY = False
    GraphQLRouter = None
    schema = None

graphql_router = APIRouter()

# Strawberry ASGI integration via GraphQLRouter
if HAS_STRAWBERRY:
    strawberry_app = GraphQLRouter(
        schema,
        graphql_ide="apollo-sandbox",
    )
else:
    strawberry_app = None

__all__ = ["graphql_router", "strawberry_app"]
