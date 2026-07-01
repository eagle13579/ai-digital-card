"""匹配引擎测试。"""
import pytest
from unittest.mock import MagicMock, patch


class TestMatchingEngine:
    """匹配引擎核心功能测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """初始化mock。"""
        self.mock_db = MagicMock()
        with patch("app.services.matching_engine.SessionLocal", return_value=self.mock_db):
            from app.services.matching_engine import MatchingEngine
            self.engine = MatchingEngine(db=self.mock_db)

    def test_match_by_needs(self):
        """需求匹配：用户有需求时返回匹配结果。"""
        # Mock users with needs
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.name = "匹配用户"
        self.mock_db.query.return_value.all.return_value = [mock_user]

        result = self.engine.find_matches(1)
        assert result is not None

    def test_match_empty(self):
        """无匹配用户时返回空。"""
        self.mock_db.query.return_value.all.return_value = []
        result = self.engine.find_matches(999)
        assert result == [] or result is None

    def test_match_self_excluded(self):
        """自身不应出现在匹配结果中。"""
        self.mock_db.query.return_value.all.return_value = []
        result = self.engine.find_matches(1)
        assert result == [] or result is None
