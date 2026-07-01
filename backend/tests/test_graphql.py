"""Tests for GraphQL module — schema, queries, and resolver integration.

At least 8 tests covering:
  - Schema validity and introspection
  - Health query (no DB dependency)
  - Brochure queries (with optional status filter)
  - User / Team queries
  - Error handling for invalid fields
  - Pagination parameter forwarding
"""
from unittest.mock import AsyncMock, patch

import pytest
import strawberry

from app.graphql.schema import schema


class TestSchemaBasics:
    """Schema construction and introspection."""

    @pytest.mark.asyncio
    async def test_schema_is_valid_strawberry_instance(self):
        """Schema object is a valid Strawberry Schema with a Query root."""
        assert isinstance(schema, strawberry.Schema)
        assert schema.query is not None

    @pytest.mark.asyncio
    async def test_introspection_query_works(self):
        """Standard GraphQL introspection returns schema metadata."""
        result = await schema.execute(
            """{ __schema { queryType { name fields { name } } } }"""
        )
        assert result.errors is None
        assert result.data["__schema"]["queryType"]["name"] == "Query"
        field_names = {f["name"] for f in result.data["__schema"]["queryType"]["fields"]}
        assert "health" in field_names
        assert "brochures" in field_names
        assert "users" in field_names
        assert "teams" in field_names


class TestHealthQuery:
    """Health check — no DB dependency."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        """query { health } returns the string 'OK'."""
        result = await schema.execute("query { health }")
        assert result.errors is None
        assert result.data == {"health": "OK"}

    @pytest.mark.asyncio
    async def test_health_field_alias_works(self):
        """Field aliasing on health returns same value."""
        result = await schema.execute("query { h: health }")
        assert result.errors is None
        assert result.data == {"h": "OK"}


class TestBrochureQuery:
    """Brochure list query with optional filters."""

    @pytest.mark.asyncio
    async def test_brochures_returns_empty_list(self):
        """query { brochures { id title } } returns [] when no data."""
        with patch("app.graphql.schema.resolve_brochures", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await schema.execute("query { brochures { id title } }")
            assert result.errors is None
            assert result.data == {"brochures": []}

    @pytest.mark.asyncio
    async def test_brochures_with_status_filter_passed_to_resolver(self):
        """Status parameter is forwarded to the resolver."""
        with patch("app.graphql.schema.resolve_brochures", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await schema.execute(
                'query { brochures(status: "published") { id } }'
            )
            assert result.errors is None
            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs.get("status") == "published"

    @pytest.mark.asyncio
    async def test_brochures_pagination_parameters_forwarded(self):
        """offset and limit are passed to the resolver."""
        with patch("app.graphql.schema.resolve_brochures", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await schema.execute(
                "query { brochures(offset: 5, limit: 3) { id } }"
            )
            assert result.errors is None
            mock.assert_called_once_with(offset=5, limit=3, status=None)


class TestUserAndTeamQuery:
    """User and team list queries."""

    @pytest.mark.asyncio
    async def test_users_returns_empty_list(self):
        """query { users { id name } } returns [] when no data."""
        with patch("app.graphql.schema.resolve_users", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await schema.execute("query { users { id name } }")
            assert result.errors is None
            assert result.data == {"users": []}

    @pytest.mark.asyncio
    async def test_teams_returns_empty_list(self):
        """query { teams { id name } } returns [] when no data."""
        with patch("app.graphql.schema.resolve_teams", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await schema.execute("query { teams { id name slug } }")
            assert result.errors is None
            assert result.data == {"teams": []}


class TestErrorCases:
    """Invalid queries produce GraphQL errors."""

    @pytest.mark.asyncio
    async def test_unknown_field_returns_graphql_error(self):
        """Querying a non-existent field gives a GraphQL error."""
        result = await schema.execute("query { nonexistent }")
        assert result.errors is not None
        assert len(result.errors) > 0
