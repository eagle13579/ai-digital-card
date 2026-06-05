"""信任网络服务测试。"""
import pytest
from unittest.mock import MagicMock, patch


class TestTrustService:
    """信任网络服务核心功能测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前初始化。"""
        from app.services.trust_service import TrustService
        self.service = TrustService()

    def test_add_trust(self):
        """添加信任关系。"""
        result = self.service.add_trust("user_001", "user_002", "business_partner")
        assert result is True
        assert "user_002" in self.service.get_trust_network("user_001")

    def test_remove_trust(self):
        """移除信任关系。"""
        self.service.add_trust("user_001", "user_002")
        result = self.service.remove_trust("user_001", "user_002")
        assert result is True
        assert "user_002" not in self.service.get_trust_network("user_001")

    def test_trust_network_empty(self):
        """空信任网络。"""
        network = self.service.get_trust_network("nonexistent_user")
        assert network == []

    def test_duplicate_trust(self):
        """重复添加信任关系。"""
        self.service.add_trust("user_001", "user_002")
        result = self.service.add_trust("user_001", "user_002")
        assert result is False  # 应返回False表示已存在

    def test_self_trust_rejected(self):
        """自引用信任应被拒绝。"""
        with pytest.raises(ValueError):
            self.service.add_trust("user_001", "user_001")

    def test_bidirectional_trust(self):
        """双向信任链路。"""
        self.service.add_trust("user_a", "user_b", "partner")
        self.service.add_trust("user_b", "user_a", "partner")
        a_network = self.service.get_trust_network("user_a")
        b_network = self.service.get_trust_network("user_b")
        assert any(t["trusted_user"] == "user_b" for t in a_network)
        assert any(t["trusted_user"] == "user_a" for t in b_network)

    def test_trust_with_metadata(self):
        """带元数据的信任关系。"""
        metadata = {"relationship": "investor", "since": "2025", "level": "gold"}
        self.service.add_trust("user_001", "user_002", metadata=metadata)
        network = self.service.get_trust_network("user_001")
        entry = next(t for t in network if t["trusted_user"] == "user_002")
        assert entry["metadata"]["relationship"] == "investor"
        assert entry["metadata"]["level"] == "gold"

    def test_remove_nonexistent_trust(self):
        """移除不存在的信任关系。"""
        with pytest.raises(ValueError):
            self.service.remove_trust("user_001", "nonexistent")

    def test_trust_chain_depth(self):
        """信任链深度查询。"""
        self.service.add_trust("user_a", "user_b")
        self.service.add_trust("user_b", "user_c")
        self.service.add_trust("user_c", "user_d")
        chain = self.service.get_trust_chain("user_a", max_depth=2)
        assert len(chain) <= 2  # 只返回直接信任+一层间接

    def test_multiple_trust_sources(self):
        """多来源信任聚合。"""
        self.service.add_trust("user_x", "user_z", "colleague")
        self.service.add_trust("user_y", "user_z", "partner")
        x_network = self.service.get_trust_network("user_x")
        y_network = self.service.get_trust_network("user_y")
        assert any(t["trusted_user"] == "user_z" for t in x_network)
        assert any(t["trusted_user"] == "user_z" for t in y_network)
