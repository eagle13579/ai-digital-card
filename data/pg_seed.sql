-- AI数字名片 PostgreSQL 种子数据迁移脚本
-- 生成时间: 2026-07-08
-- 来源: SQLite → PostgreSQL


-- brochures: 49 rows (batch 1)
INSERT INTO "brochures" ("id", "user_id", "title", "cover", "purpose", "pages_count", "status", "share_token", "view_count", "album_meta", "created_at", "updated_at") VALUES
  (1, 51, 'roger的容蓝名片', '', 'partner', 3, 'draft', 'ead57c7f9b15489a', 1, NULL, '2026-07-05 14:36:46', '2026-07-06 01:07:27'),
  (2, 52, 'test', '', 'partner', 0, 'draft', 'd4336f5901b9424f', 0, NULL, '2026-07-05 14:45:36', '2026-07-05 14:45:36'),
  (3, 54, 'roger名片', '', 'partner', 0, 'draft', '02f06ce2e7a340f6', 0, NULL, '2026-07-05 14:48:01', '2026-07-05 14:48:01'),
  (4, 55, 'roger名片', '', 'partner', 0, 'draft', '5f8c1f6fbdf140ff', 0, NULL, '2026-07-05 14:49:11', '2026-07-05 14:49:11'),
  (5, 51, 'roger的容蓝名片', '', 'partner', 3, 'draft', 'c747f642d6f34e7c', 0, NULL, '2026-07-05 15:26:59', '2026-07-05 15:26:59'),
  (6, 56, '产品经理', '', '', 0, 'draft', 'a5535a0e96de474c', 0, NULL, '2026-07-06 00:14:06', '2026-07-06 00:14:06'),
  (7, 56, '产品经理', '', '', 0, 'draft', '57074561c68b4399', 0, NULL, '2026-07-06 00:14:32', '2026-07-06 00:14:32'),
  (8, 56, '测试公司产品画册', '', '', 2, 'draft', '5dfd5ce91aa74bfb', 0, NULL, '2026-07-06 00:14:36', '2026-07-06 00:14:36'),
  (9, 56, '产品经理', '', '', 0, 'draft', '3bf014875c0b4d18', 0, NULL, '2026-07-06 00:16:33', '2026-07-06 00:16:33'),
  (10, 56, '测试产品画册', '', '', 1, 'published', '2ce33d70ce7149cb', 0, NULL, '2026-07-06 00:16:37', '2026-07-06 00:16:39'),
  (11, 56, '测试用户名片', '', 'personal', 1, 'draft', '737441f1d07a441e', 0, NULL, '2026-07-06 00:24:47', '2026-07-06 00:24:47'),
  (12, 62, '测试名片', '', '', 1, 'draft', 'b80e0945053a43ac', 0, NULL, '2026-07-06 00:33:29', '2026-07-06 00:33:29'),
  (13, 56, '测试名片', '', 'personal', 1, 'draft', '9d497e4e76404737', 0, NULL, '2026-07-06 00:43:11', '2026-07-06 00:43:11'),
  (14, 56, '验证修复', '', 'personal', 1, 'draft', 'c845170eac254230', 0, NULL, '2026-07-06 00:55:37', '2026-07-06 00:55:37'),
  (15, 56, '验证修复', '', 'personal', 1, 'draft', '22717ed58acc4739', 0, NULL, '2026-07-06 01:00:10', '2026-07-06 01:00:10'),
  (16, 56, '验证修复', '', 'personal', 1, 'draft', '154328897e3c462d', 0, NULL, '2026-07-06 01:01:10', '2026-07-06 01:01:10'),
  (17, 56, 'test', '', 'personal', 1, 'draft', '1fba955df73e48d0', 0, NULL, '2026-07-06 01:02:24', '2026-07-06 01:02:24'),
  (18, 56, 'test', '', 'personal', 1, 'draft', 'ee1c28afb85b43a5', 0, NULL, '2026-07-06 01:05:15', '2026-07-06 01:05:15'),
  (19, 56, '修复验证', '', 'personal', 1, 'draft', '7d2a847e059d455d', 0, NULL, '2026-07-06 01:06:18', '2026-07-06 01:06:18'),
  (20, 56, 'test', '', 'personal', 1, 'draft', '0693ce1cfeef4f4f', 0, NULL, '2026-07-06 03:19:03', '2026-07-06 03:19:03'),
  (21, 56, '修复验证', '', 'personal', 1, 'draft', '040cf1e9fb8149d8', 0, NULL, '2026-07-06 03:19:29', '2026-07-06 03:19:29'),
  (22, 56, '产品经理', '', '', 0, 'draft', 'eac36502663649fd', 0, NULL, '2026-07-06 03:29:30', '2026-07-06 03:29:30'),
  (23, 56, '验证修复', '', 'personal', 1, 'draft', 'f433bd5c05bf499d', 0, NULL, '2026-07-06 03:29:40', '2026-07-06 03:29:40'),
  (24, 56, '验证修复', '', 'personal', 1, 'draft', '30393bb2f9ee42d9', 0, NULL, '2026-07-06 03:36:52', '2026-07-06 03:36:52'),
  (25, 64, '测试审计名片', '', '', 1, 'published', '12cbcedde1e3462d', 0, NULL, '2026-07-06 03:39:35', '2026-07-06 03:39:39'),
  (26, 66, '验证修复测试', '', '', 1, 'published', '519f237fd58d436d', 1, NULL, '2026-07-06 03:44:33', '2026-07-06 03:44:50'),
  (27, 64, '验证测试', '', '', 1, 'published', '4b0cd02c4b6948f2', 1, NULL, '2026-07-06 03:45:32', '2026-07-06 03:45:36'),
  (28, 51, '向海容的容蓝名片', '', 'partner', 3, 'draft', '1c65a04bb3a24677', 0, NULL, '2026-07-06 09:09:43', '2026-07-06 09:09:43'),
  (29, 56, '产品经理', '', '', 0, 'draft', 'c2664d0f533642f6', 0, NULL, '2026-07-06 23:57:51', '2026-07-06 23:57:51'),
  (30, 56, '测试产品画册', '', '', 1, 'published', 'd41a4373b1074ec5', 1, NULL, '2026-07-06 23:57:58', '2026-07-06 23:58:33'),
  (31, 70, '<script>alert(1)</script>', '', '', 1, 'draft', '90278578a12a4c47', 0, NULL, '2026-07-07 00:00:07', '2026-07-07 00:00:07'),
  (32, 73, '产品经理', '', '', 0, 'draft', '3f46a496397646f4', 0, NULL, '2026-07-07 00:02:45', '2026-07-07 00:02:45'),
  (33, 73, '测试产品画册', '', '', 1, 'published', '9f855ba1fe9045ab', 1, NULL, '2026-07-07 00:02:51', '2026-07-07 00:02:58'),
  (34, 78, '<script>alert(1)</script>', '', '', 0, 'draft', '41e039ec574f41bd', 0, NULL, '2026-07-07 00:32:57', '2026-07-07 00:32:57'),
  (35, 78, 'N', '', '', 0, 'draft', '8a9546638cbf4e64', 0, NULL, '2026-07-07 00:32:59', '2026-07-07 00:32:59'),
  (36, 51, 'roger的容蓝名片', '', 'partner', 3, 'draft', '8fa21658634745a2', 0, NULL, '2026-07-07 09:22:53', '2026-07-07 09:22:53'),
  (37, 51, 'roger的容蓝名片', '', 'partner', 3, 'draft', 'ffabd4ae8c384646', 0, NULL, '2026-07-07 09:44:10', '2026-07-07 09:44:10'),
  (38, 103, '测试画册_20260708000236', '', 'business', 3, 'draft', '04a48cbeeaf6419b', 0, NULL, '2026-07-07 16:02:36', '2026-07-07 16:02:36'),
  (39, 104, '测试画册_20260708000444', '', 'business', 3, 'draft', 'af866b155d524352', 0, NULL, '2026-07-07 16:04:44', '2026-07-07 16:04:44'),
  (40, 105, '测试画册_20260708000824', '', 'business', 3, 'draft', 'c97ba0217fae4332', 0, NULL, '2026-07-07 16:08:24', '2026-07-07 16:08:24'),
  (41, 106, '测试画册_20260708001012', '', 'business', 3, 'draft', 'fed1967f37d74734', 0, NULL, '2026-07-07 16:10:12', '2026-07-07 16:10:12'),
  (42, 107, '测试画册_20260708001138', '', 'business', 3, 'draft', '3271d6fc46b546b5', 0, NULL, '2026-07-07 16:11:38', '2026-07-07 16:11:38'),
  (43, 108, '测试画册_20260708001443', '', 'business', 3, 'draft', 'b3651ec137c04193', 0, NULL, '2026-07-07 16:14:43', '2026-07-07 16:14:43'),
  (44, 109, '测试画册_20260708001607', '', 'business', 3, 'draft', '5bd43b4fce35468f', 0, NULL, '2026-07-07 16:16:07', '2026-07-07 16:16:07'),
  (45, 110, '测试画册_20260708001816', '', 'business', 3, 'draft', '869eea4b58ed4ef7', 0, NULL, '2026-07-07 16:18:16', '2026-07-07 16:18:16'),
  (46, 111, '测试画册_20260708002440', '', 'business', 3, 'draft', 'ff8b4b18763d4f23', 0, NULL, '2026-07-07 16:24:40', '2026-07-07 16:24:40'),
  (47, 114, 'test', '', '', 0, 'draft', '519be2079b9f4d3f', 0, NULL, '2026-07-08 02:48:57', '2026-07-08 02:48:57'),
  (48, 120, '向海容 - AI数字名片', '', 'business', 3, 'published', '5b74081510214b63', 0, NULL, '2026-07-08 02:50:24', '2026-07-08 02:50:27'),
  (49, 121, '测试画册_20260708120426', '', 'business', 3, 'draft', 'f9b5e0c2ace44204', 0, NULL, '2026-07-08 04:04:26', '2026-07-08 04:04:26');

-- gaia_evolution_events: 71 rows (batch 1)
INSERT INTO "gaia_evolution_events" ("id", "event_type", "event_source", "description", "metadata", "reference_type", "reference_id", "created_at") VALUES
  (1, 'cycle_started', 'manual', '进化循环开始', NULL, NULL, NULL, '2026-07-01 11:39:21'),
  (2, 'cycle_completed', 'manual', '进化循环完成: 0 条知识, 0 个权重更新', NULL, 'training_run', 1, '2026-07-01 11:39:21'),
  (3, 'training_started', 'manual', '训练管线开始 (run_id=2)', NULL, 'training_run', 2, '2026-07-01 11:39:21'),
  (4, 'weights_updated', 'trainer', '训练管线部署权重: 7 个模块', NULL, 'training_run', 2, '2026-07-01 11:39:21'),
  (5, 'training_completed', 'manual', '训练管线完成: 0 条知识, 7 个权重更新 (15ms)', NULL, 'training_run', 2, '2026-07-01 11:39:21'),
  (6, 'cycle_started', 'manual', '进化循环开始', NULL, NULL, NULL, '2026-07-01 11:40:29'),
  (7, 'cycle_completed', 'manual', '进化循环完成: 0 条知识, 0 个权重更新', NULL, 'training_run', 3, '2026-07-01 11:40:29'),
  (8, 'training_started', 'manual', '训练管线开始 (run_id=4)', NULL, 'training_run', 4, '2026-07-01 11:40:29'),
  (9, 'training_completed', 'manual', '训练管线完成: 0 条知识, 0 个权重更新 (31ms)', NULL, 'training_run', 4, '2026-07-01 11:40:29'),
  (10, 'cycle_started', 'manual', '进化循环开始', NULL, NULL, NULL, '2026-07-01 11:40:42'),
  (11, 'cycle_completed', 'manual', '进化循环完成: 0 条知识, 0 个权重更新', NULL, 'training_run', 5, '2026-07-01 11:40:42'),
  (12, 'training_started', 'manual', '训练管线开始 (run_id=6)', NULL, 'training_run', 6, '2026-07-01 11:40:42'),
  (13, 'training_completed', 'manual', '训练管线完成: 0 条知识, 0 个权重更新 (15ms)', NULL, 'training_run', 6, '2026-07-01 11:40:42'),
  (14, 'knowledge_ingested', 'api', '知识已摄取: [pattern] 用户转化率提升策略', NULL, 'knowledge', 1, '2026-07-01 11:41:10'),
  (15, 'cycle_started', 'manual', '进化循环开始', NULL, NULL, NULL, '2026-07-01 11:41:10'),
  (16, 'weights_updated', 'system', '进化权重已更新: 7 个模块', NULL, NULL, NULL, '2026-07-01 11:42:18'),
  (17, 'cycle_completed', 'manual', '进化循环完成: 1 条知识, 7 个权重更新', NULL, 'training_run', 7, '2026-07-01 11:42:18'),
  (18, 'training_started', 'manual', '训练管线开始 (run_id=8)', NULL, 'training_run', 8, '2026-07-01 11:42:18'),
  (19, 'weights_updated', 'trainer', '训练管线部署权重: 7 个模块', NULL, 'training_run', 8, '2026-07-01 11:42:19'),
  (20, 'training_completed', 'manual', '训练管线完成: 1 条知识, 7 个权重更新 (47ms)', NULL, 'training_run', 8, '2026-07-01 11:42:19'),
  (21, 'knowledge_ingested', 'api', '知识已摄取: [pattern] F8复盘:转化率优化', NULL, 'knowledge', 2, '2026-07-01 14:16:06'),
  (22, 'knowledge_ingested', 'api', '知识已摄取: [preference] 用户1对42的好评反馈', NULL, 'knowledge', 3, '2026-07-01 14:16:06'),
  (23, 'cycle_started', 'manual', '进化循环开始', NULL, NULL, NULL, '2026-07-01 14:16:06'),
  (24, 'weights_updated', 'system', '进化权重已更新: 7 个模块', NULL, NULL, NULL, '2026-07-01 14:56:38'),
  (25, 'cycle_completed', 'manual', '进化循环完成: 2 条知识, 7 个权重更新', NULL, 'training_run', 9, '2026-07-01 14:56:38'),
  (26, 'training_started', 'manual', '训练管线开始 (run_id=10)', NULL, 'training_run', 10, '2026-07-01 14:56:38'),
  (27, 'weights_updated', 'trainer', '训练管线部署权重: 7 个模块', NULL, 'training_run', 10, '2026-07-01 14:56:38'),
  (28, 'training_completed', 'manual', '训练管线完成: 3 条知识, 7 个权重更新 (30ms)', NULL, 'training_run', 10, '2026-07-01 14:56:38'),
  (29, 'cycle_started', 'api', '进化循环开始', NULL, NULL, NULL, '2026-07-01 19:39:17'),
  (30, 'weights_updated', 'system', '进化权重已更新: 7 个模块', NULL, NULL, NULL, '2026-07-01 19:39:55'),
  (31, 'cycle_completed', 'api', '进化循环完成: 33 条知识, 7 个权重更新', NULL, 'training_run', 11, '2026-07-01 19:39:55'),
  (32, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — ai-shuzhi-juntuan — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 37, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 ai-shuzhi-juntuan", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 37, '2026-07-02 00:56:39'),
  (33, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — airbnb — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 38, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 airbnb", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 38, '2026-07-02 00:56:39'),
  (34, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — airtable — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 39, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 airtable", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 39, '2026-07-02 00:56:39'),
  (35, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — apple — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 40, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 apple", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 40, '2026-07-02 00:56:39'),
  (36, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — baize-console — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 41, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 baize-console", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 41, '2026-07-02 00:56:39'),
  (37, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — binance — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 42, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 binance", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 42, '2026-07-02 00:56:39'),
  (38, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bmw — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 43, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bmw", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 43, '2026-07-02 00:56:39'),
  (39, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bmw-m — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 44, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bmw-m", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 44, '2026-07-02 00:56:39'),
  (40, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bugatti — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 45, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bugatti", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 45, '2026-07-02 00:56:39'),
  (41, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cal — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 46, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cal", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 46, '2026-07-02 00:56:39'),
  (42, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — claude — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 47, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 claude", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 47, '2026-07-02 00:56:39'),
  (43, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — clay — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 48, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 clay", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 48, '2026-07-02 00:56:39'),
  (44, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — clickhouse — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 49, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 clickhouse", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 49, '2026-07-02 00:56:39'),
  (45, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cohere — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 50, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cohere", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 50, '2026-07-02 00:56:39'),
  (46, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — coinbase — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 51, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 coinbase", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 51, '2026-07-02 00:56:39'),
  (47, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — composio — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 52, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 composio", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 52, '2026-07-02 00:56:39'),
  (48, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — content-automation-factory — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 53, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 content-automation-factory", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 53, '2026-07-02 00:56:39'),
  (49, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cursor — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 54, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cursor", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 54, '2026-07-02 00:56:39'),
  (50, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — digital-employee-commander — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 55, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 digital-employee-commander", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 55, '2026-07-02 00:56:39'),
  (51, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — expo — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 57, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 expo", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 57, '2026-07-02 00:56:39'),
  (52, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — ai-shuzhi-juntuan — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 37, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 ai-shuzhi-juntuan", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 37, '2026-07-02 00:56:47'),
  (53, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — airbnb — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 38, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 airbnb", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 38, '2026-07-02 00:56:47'),
  (54, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — airtable — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 39, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 airtable", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 39, '2026-07-02 00:56:47'),
  (55, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — apple — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 40, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 apple", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 40, '2026-07-02 00:56:47'),
  (56, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — baize-console — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 41, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 baize-console", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 41, '2026-07-02 00:56:47'),
  (57, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — binance — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 42, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 binance", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 42, '2026-07-02 00:56:47'),
  (58, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bmw — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 43, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bmw", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 43, '2026-07-02 00:56:47'),
  (59, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bmw-m — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 44, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bmw-m", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 44, '2026-07-02 00:56:47'),
  (60, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — bugatti — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 45, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 bugatti", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 45, '2026-07-02 00:56:47'),
  (61, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cal — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 46, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cal", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 46, '2026-07-02 00:56:47'),
  (62, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — claude — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 47, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 claude", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 47, '2026-07-02 00:56:47'),
  (63, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — clay — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 48, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 clay", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 48, '2026-07-02 00:56:47'),
  (64, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — clickhouse — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 49, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 clickhouse", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 49, '2026-07-02 00:56:47'),
  (65, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cohere — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 50, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cohere", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 50, '2026-07-02 00:56:47'),
  (66, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — coinbase — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 51, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 coinbase", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 51, '2026-07-02 00:56:47'),
  (67, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — composio — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 52, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 composio", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 52, '2026-07-02 00:56:47'),
  (68, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — content-automation-factory — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 53, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 content-automation-factory", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 53, '2026-07-02 00:56:47'),
  (69, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — cursor — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 54, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 cursor", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 54, '2026-07-02 00:56:47'),
  (70, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — digital-employee-commander — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 55, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 digital-employee-commander", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 55, '2026-07-02 00:56:47'),
  (71, 'design_qa_audit_completed', 'cron_design_qa', 'DesignQA审核: 品牌设计规范 — expo — critique=65.0%, accessibility=16.7%, performance=62.5%, antipatterns=0.0%', '{"knowledge_id": 57, "target": "\u54c1\u724c\u8bbe\u8ba1\u89c4\u8303 \u2014 expo", "scores": {"critique": 65.0, "accessibility": 16.7, "performance": 62.5, "antipatterns": 0.0}, "total_findings": 91, "severity_counts": {"P0": 3, "P1": 23, "P2": 61, "P3": 4}}', 'knowledge', 57, '2026-07-02 00:56:47');

-- gaia_knowledge: 172 rows (batch 1)
INSERT INTO "gaia_knowledge" ("id", "source", "source_id", "knowledge_type", "title", "content", "tags", "confidence", "impact_score", "is_active", "vector_embedded", "created_at", "updated_at") VALUES
  (1, 'retrospective', 'retro_board:42', 'pattern', '用户转化率提升策略', '复盘发现：用户在首次看到匹配结果后的24小时内联系的概率提升60%。建议匹配引擎优先推荐最近活跃的用户，并缩短推荐结果的缓存时间。', '["matching", "conversion", "recency"]', 0.85, 0.85, 1, 1, '2026-07-01 11:41:10', '2026-07-01 11:42:18'),
  (2, 'retrospective', 'retro:42', 'pattern', 'F8复盘:转化率优化', '复盘发现:用户看到匹配结果后24h内联系概率+60%', '["matching", "conversion"]', 1.0, 1.0, 1, 1, '2026-07-01 14:16:06', '2026-07-01 14:56:38'),
  (3, 'feedback', 'feedback_1_42', 'preference', '用户1对42的好评反馈', '用户 1 对项目 42 的好评反馈, 评分: 5', '["feedback", "\u597d\u8bc4", "recommend"]', 1.0, 1.0, 1, 1, '2026-07-01 14:16:06', '2026-07-01 14:56:38'),
  (4, 'knowledge_model', 'FD-M01', 'pattern', 'Design Token 分层体系', '[design_system] Design Token 是设计系统中最小的可复用原子，分为三层：
1. 全局Token (Global Tokens) — 跨品牌的原始设计值，如 color-brand-500: #1677ff
2. 别名Token (Alias Tokens) — 语义化映射，如 color-primary: color-brand-500
3. 组件Token (Component Tokens) — 组件级特化，如 Button-background: color-primary

核心原则：
- Token命名规范: {category}-{type}-{property}-{subproperty}-{variant}
- 全局Token不可变，别名Token可随主题切换
- 组件Token应限定在组件边界内，不得跨组件引用

训练要点：Token化使主题切换、品牌定制、响应式适配的维护成本降低70%+。', '["design_token", "\u8bbe\u8ba1\u7cfb\u7edf", "\u4e3b\u9898\u5316", "\u539f\u5b50\u5316\u8bbe\u8ba1"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (5, 'knowledge_model', 'FD-M02', 'pattern', '色彩系统架构', '[design_system] 色彩系统应包含五层架构：
1. 品牌色 (Brand) — 主色+辅色，定义品牌识别
2. 语义色 (Semantic) — success/warning/error/info，功能导向
3. 中性色 (Neutral) — 文本/背景/边框/填充灰度阶梯
4. 数据色 (Data) — 图表/可视化配色序列
5. 覆盖色 (Overlay) — 遮罩/阴影/渐变

设计原则：
- 品牌色12阶阶梯: 50-900 (50最浅, 900最深), 每阶HSL亮度差≈7%
- 中性色需满足WCAG AA对比度: 正文≥4.5:1, 大文本≥3:1
- 语义色应与品牌色协调而非冲突，覆盖在品牌色上叠加透明度
- 高频使用色 (品牌色、中性色) 占设计表面积80%+，低频使用色占20%

训练要点：暗色主题的语义色需重新计算对比度而非简单反转。', '["\u8272\u5f69\u7cfb\u7edf", "\u54c1\u724c\u8272", "\u8bed\u4e49\u8272", "WCAG", "\u4e3b\u9898"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (6, 'knowledge_model', 'FD-M03', 'pattern', '字体层级调制 (Typography Scale)', '[design_system] 字体层级的数学模型 — 使用等比数列创建协调的字体大小系统：
1. 基准字号: 16px (1rem = 16px, 浏览器默认)
2. 调制比 (Modular Scale): 常用 1.25 (Major Third) 或 1.333 (Perfect Fourth)
3. 层级计算: 基准 × ratio^step, 如:
   - 正文: 16px (step=0)
   - H6: 16×1.25^1 = 20px
   - H5: 16×1.25^2 = 25px
   - H4: 16×1.25^3 = 31px
   - H3: 16×1.25^4 = 39px
   - H2: 16×1.25^5 = 49px
   - H1: 16×1.25^6 = 61px

行高规则: 正文1.5-1.6, 大标题1.1-1.2
字重分配: 正文Regular(400), 强调Medium(500), 标题Semibold(600)或Bold(700)

训练要点：每个设计系统应锁定一个调制比，避免随意选字号。', '["\u6392\u7248", "\u5b57\u4f53\u5c42\u7ea7", "typography", "modular_scale"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (7, 'knowledge_model', 'FD-M04', 'pattern', '间距网格系统 (Spacing & Grid)', '[design_system] 8px网格基准 — 以8为基本单位构建所有间距、内边距、外边距和尺寸：
1. 基础单位: 8px (4px用于微间距)
2. 间距尺: {0, 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 128}
3. 网格列系统: 12列弹性网格，间距(column-gap)为24px
4. 断点系统:
   - xs: <576px (手机)
   - sm: ≥576px (大屏手机)
   - md: ≥768px (平板)
   - lg: ≥992px (桌面)
   - xl: ≥1200px (宽屏)
   - xxl: ≥1600px (超大屏)

原则：
- 垂直韵律: 所有块级元素的下边距符合间距尺
- 一致性胜过完美: 宁可统一用24px也不混用23px和25px
- 响应式: 间距和网格列数在断点间可调整

训练要点：从ant-design和Stripe的设计中可见，严格的网格系统是专业感的基石。', '["\u95f4\u8ddd", "\u7f51\u683c", "8px\u7f51\u683c", "\u54cd\u5e94\u5f0f", "\u65ad\u70b9"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (8, 'knowledge_model', 'FD-M05', 'pattern', '原子化组件设计 (Atomic Design)', '[design_system] 由Brad Frost提出的设计方法论，将UI分解为五个层次：

1. 原子 (Atoms): 最小组件单元
   - Button, Input, Label, Icon, Color, Typography
   - 不可再分，只承载单一职责

2. 分子 (Molecules): 原子组合
   - SearchForm = Input + Button + Icon
   - Card = Image + Title + Description + Actions
   - 承担具体功能单元

3. 组织 (Organisms): 分子组合形成区块
   - Header = Logo(原子) + SearchForm(分子) + Nav(分子)
   - ProductGrid = 多个Card(分子) + Grid(原子)

4. 模板 (Templates): 组织的页面级布局
   - 关注结构而非内容
   - 定义内容区域的位置关系

5. 页面 (Pages): 模板 + 真实内容
   - 验证设计系统的实际效果
   - 发现边缘案例

核心收益: 跨项目复用率可达60-80%，修改一个原子影响所有上层组件。

训练要点：ant-design的83+组件、Stripe的模块化CSS都是原子化设计的实践典范。', '["atomic_design", "\u7ec4\u4ef6\u5316", "\u8bbe\u8ba1\u7cfb\u7edf", "\u65b9\u6cd5\u8bba"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (9, 'knowledge_model', 'FD-M06', 'pattern', '组件状态枚举设计', '[design_system] 每个UI组件必须明确定义所有可能的视觉状态：

通用状态集 (9种):
1. Default (默认) — 组件的静止状态
2. Hover (悬停) — 鼠标悬浮时的反馈
3. Active/Pressed (激活) — 点击或按压状态
4. Focus (聚焦) — 键盘/鼠标聚焦，用于可访问性
5. Disabled (禁用) — 不可交互状态
6. Loading (加载中) — 异步操作进行中
7. Error (错误) — 验证失败或异常
8. Empty (空状态) — 无数据时的展示
9. Selected/Checked (选中) — 被选择状态

进阶状态:
- 过渡状态: entering/entered/exiting/exited (动效状态机)
- 拖拽状态: drag-over/dragging/drag-end
- 响应式状态: mobile/tablet/desktop
- 主题状态: light/dark/high-contrast

设计规范: 每个状态应有明确的视觉差异(≥3个视觉属性变化)，且有平滑过渡。

训练要点：IMpeccable设计审核工具的23条审核命令专门检查状态完整性。', '["\u7ec4\u4ef6\u72b6\u6001", "\u4ea4\u4e92\u8bbe\u8ba1", "\u72b6\u6001\u7ba1\u7406", "impeccable"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:16', '2026-07-01 19:39:55'),
  (10, 'knowledge_model', 'FD-M07', 'pattern', '主题化引擎架构', '[design_system] 支持设计系统多主题切换的架构模式：

核心机制：
1. Token覆盖层: 主题 = 全局Token + 主题覆盖Token
   - Light模式: 覆盖阴影、背景、文字色
   - Dark模式: 反转亮度通道，重新计算对比度
   - 高对比度: 增强所有对比度到AAA级

2. CSS变量策略 (Runtime Theme):
   :root { --color-bg: #fff; }
   [data-theme="dark"] { --color-bg: #1a1a2e; }
   组件引用: background: var(--color-bg);

3. Token分类:
   - 浅色主题: 品牌色保持，背景减淡，阴影可见
   - 深色主题: 品牌色保持(必要时亮度+20%)，背景加深，阴影用发光替代
   - 所有主题必须通过色盲测试(Deuteranopia/Protanopia/Tritanopia)

4. 过渡策略:
   - Token切换应使用CSS transition: all 0.3s ease
   - 避免闪烁: 在DOM ready前注入主题变量

训练要点：taste-skill的"三旋钮"设计系统(视觉粒度/语言密度/工程纯度)可与主题联动。', '["\u4e3b\u9898\u5316", "\u6697\u8272\u6a21\u5f0f", "CSS\u53d8\u91cf", "design_token", "taste-skill"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (11, 'knowledge_model', 'FD-M08', 'pattern', '设计系统的版本化与发布管理', '[design_system] 设计系统应像软件一样进行版本化管理：

1. 语义化版本: MAJOR.MINOR.PATCH
   - MAJOR: 破坏性Token变更(品牌色更换、间距基准改4→8)
   - MINOR: 新增组件/Token(兼容)
   - PATCH: Bug修复(对比度调整、数值微调)

2. ChangeLog管理:
   - 每次发布记录 Token 变更差异
   - 标注 deprecation 计划(如: v2 token将在v4移除)
   - 迁移指南: 旧→新Token映射表

3. 分布式使用:
   - 发布npm包: @company/design-tokens
   - 同时发布CSS变量文件 + JS常量 + Figma Library
   - 消费者锁定版本，按节奏升级

4. 审核流程:
   - 设计审核(Design Review): 使用impeccable的23条审核命令
   - 代码审核(Code Review): 检查Token使用是否正确
   - 可访问性审核(A11Y Audit): 对比度/焦点/屏幕阅读器

训练要点：系统化版本管理使设计系统可持续演进10年+。', '["\u7248\u672c\u7ba1\u7406", "changelog", "\u8bbe\u8ba1\u7cfb\u7edf\u6cbb\u7406", "impeccable"]', 0.85, 0.765, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (12, 'knowledge_model', 'FD-M09', 'pattern', '视觉层级与信息架构', '[ui_principle] 通过视觉属性建立清晰的阅读/浏览优先级：

六大视觉权重控制手段:
1. 尺寸 (Size): 越大越重要。标题 > 副标题 > 正文 > 辅助文字
2. 色彩饱和度: 品牌色 > 中性色 > 灰色。重要信息用高饱和度
3. 对比度: 高对比度(Very important) → 中(Important) → 低(Secondary)
4. 位置: 左上→右下递减。F型扫描模式
5. 留白: 元素周围空间越大，越显得重要
6. 动效: 运动捕获注意力，但过度使用产生噪音

信息架构三原则:
- 分组 (Chunking): 7±2法则，信息块不超过9个
- 分层 (Layering): 全局导航→页面导航→内容→上下文
- 渐进呈现 (Progressive Disclosure): 先给核心，再给细节

训练要点：taste-skill的"反模板化"理念强调层次感而非模板堆砌。', '["\u89c6\u89c9\u5c42\u7ea7", "\u4fe1\u606f\u67b6\u6784", "taste-skill", "UI\u539f\u5219"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (13, 'knowledge_model', 'FD-M10', 'pattern', '格式塔原理 (Gestalt Principles) 的UI应用', '[ui_principle] 人类视觉系统自动将复杂图形组织为整体的心理法则：

1. 接近性 (Proximity): 距离近的元素被视为一组
   → UI应用: 表单标签贴近输入框，按钮组间距小于按钮间距

2. 相似性 (Similarity): 相似外观的元素被视为同一类
   → UI应用: 同层级标题用统一字号/色，所有按钮有统一样式

3. 连续性 (Continuity): 视觉沿平滑路径延伸
   → UI应用: 列表项对齐形成视觉流，分页器的箭头方向

4. 闭合性 (Closure): 大脑自动补全不完整图形
   → UI应用: 加载动画的旋转点阵，卡片缺口的隐式边界

5. 对称性 (Symmetry): 对称图形被视为整体
   → UI应用: 模态框居中设计，导航栏左右对称

6. 图底关系 (Figure-Ground): 自动区分前景和背景
   → UI应用: 卡片阴影分离前后景，模态遮罩区分层级

7. 共同命运 (Common Fate): 同方向运动的元素相关
   → UI应用: 展开/折叠动画的同步元素，滚动触发动效的关联性

训练要点：顶级设计系统(Stripe/Linear/Ant-design)处处体现格式塔原则。', '["\u683c\u5f0f\u5854", "gestalt", "\u611f\u77e5\u5fc3\u7406\u5b66", "UI\u539f\u5219"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (14, 'knowledge_model', 'FD-M11', 'pattern', '菲茨定律与交互可访问性 (Fitts''s Law)', '[ui_principle] 到达目标的时间 = a + b × log₂(距离/宽度 + 1)

核心推论:
1. 目标越大越好: 最小触控目标44×44px (iOS HIG) / 48×48px (Material)
2. 距离越近越好: 常用操作放在拇指可达区(手机下半部)
3. 屏幕边界是"无限大"目标: 菜单栏放顶部，Mac Dock放底部

UI设计应用:
- 操作按钮: 主要操作使用大按钮(≥44px高)，次要操作使用文本链接
- 表单: 提交按钮靠近最后一个输入项
- 导航: 常用项放在边缘或角落
- 右键菜单: 鼠标悬停展开，避免点击-移动-点击的两次操作

可访问性要求:
- 触控目标: 最小44×44px (iOS)/ 48×48px (Android)
- 功能等效: 触控、鼠标、键盘三种操作方式均支持
- 容错设计: 撤销操作比"确认"(confirm)弹窗更好

训练要点：stripe-clone和impeccable的设计审核都强调交互目标的尺寸合规。', '["\u83f2\u8328\u5b9a\u5f8b", "\u4ea4\u4e92\u8bbe\u8ba1", "\u53ef\u8bbf\u95ee\u6027", "\u89e6\u63a7\u76ee\u6807", "HCI"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (15, 'knowledge_model', 'FD-M12', 'pattern', 'Hick''s Law — 选择复杂度管理', '[ui_principle] 决策时间 = a + b × log₂(n)，其中n=选择数量

核心原则:
1. 选项越少越快: 导航项5-7个为佳(SaaS导航)，超过9个需分组
2. 分组减少选择: 设置用 tab/accordion 分组，每组≤7项
3. 默认值加速: 智能默认值减少思考负担
4. 渐进呈现: 先大类后小类，不一次性展示所有选项

UI设计应用:
- 下拉菜单: 超过15项需加搜索
- 多选表单: 用复选框组(≤7项)或级联选择
- 导航: 主导航≤7项，更多用"更多"折叠
- 定价页: 3个套餐为最佳 (免费/专业/企业)

反例: 过多的配置项导致用户放弃(paradox of choice)。

训练要点：Linear和Stripe的极简配置页是Hick''s Law的最佳实践。', '["Hick''s Law", "\u9009\u62e9\u590d\u6742\u5ea6", "UX\u539f\u5219", "\u8ba4\u77e5\u8d1f\u8377"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (16, 'knowledge_model', 'FD-M13', 'pattern', '留白与呼吸感设计 (White Space)', '[ui_principle] 空白(负空间)是UI设计中最重要的设计元素之一，不是浪费空间：

四大留白类型:
1. 微留白 (Micro White Space): 字符间距、行高、图标与文字间距
   → 设置: letter-spacing, line-height, gap
2. 宏留白 (Macro White Space): 区块间距、页面边距、卡片间距
   → 设置: padding, margin, 网格间距
3. 主动留白 (Active White Space): 有意识增加的呼吸区域
   → 用空白突出重要内容，创造视觉焦点
4. 被动留白 (Passive White Space): 布局未填满的自然空白
   → 响应式布局中的弹性空白

核心原则:
- 空白与信息密度成反比: 阅读型(多空白) > 工具型(少空白)
- 数据密集型设计(仪表盘/表格)可以更紧凑，但保持24px以上间距
- 空白具有重量感，设计时把它当"元素"而非"剩余"

训练要点：taste-skill提出"反模板化"风格 — 空白必须是设计意图的表达。', '["\u7559\u767d", "\u547c\u5438\u611f", "\u8d1f\u7a7a\u95f4", "taste-skill", "\u6392\u7248"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (17, 'knowledge_model', 'FD-M14', 'pattern', '一致性与标准化原则 (Consistency)', '[ui_principle] 一致性是设计系统最核心的价值主张：

四层一致性: 
1. 视觉一致性 (Visual): 色彩、间距、字体、圆角、阴影统一
   → 使用Token系统保证，禁止硬编码
2. 行为一致性 (Behavioral): 同类交互有相同行为
   → 所有弹窗按Esc关闭，所有表单Tab切换
3. 语义一致性 (Semantic): 颜色有固定语义
   → 红色=错误(非品牌色)，绿色=成功，蓝色=信息
4. 品牌一致性 (Brand): 跨触点品牌体验统一
   → 网站、App、邮件、打印物使用同一Token体系

检查清单:
- 所有按钮的圆角是否一致？
- 所有输入框的边框色在聚焦时是否一致？
- 所有空状态的插画风格是否一致？
- 所有加载态的骨架屏尺寸是否一致？

收益: 一致性每提升10%，用户完成任务的速度提升约5-7%。

训练要点：impeccable的23条审核命令设计就是为了发现不一致性。', '["\u4e00\u81f4\u6027", "\u6807\u51c6\u5316", "\u8bbe\u8ba1\u7cfb\u7edf", "impeccable", "\u54c1\u724c"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (18, 'knowledge_model', 'FD-M15', 'pattern', '渐进式呈现 (Progressive Disclosure)', '[ui_principle] 逐步展示信息，只有在用户需要时才显示更多细节：

核心策略:
1. 按角色呈现: 新手→高级→专家，控制面板逐步开放
2. 按任务呈现: 初始→进行中→完成，每个阶段展示当前所需
3. 按关注度呈现: 核心信息(始终可见)→辅助信息(可展开)→细节(深层)

常用UI模式:
- "了解更多"(Show more / Read more)展开
- 手风琴(Accordion)和折叠面板
- 步骤向导(Stepper / Wizard)
- 工具提示(Tooltip)悬停显示附加信息
- 滑动/拖拽揭示隐藏内容

适用场景:
- 复杂表单(注册/结账): 分步骤，每步聚焦一个任务
- 高级设置面板: 基础设置默认可见，高级设置折叠
- 数据详情页: 摘要卡片→弹出详情→完整报表钻取

反模式: 将关键功能藏在深层交互中导致用户找不到。

训练要点：Stripe和Linear的极简初始界面隐藏了80%的复杂性。', '["\u6e10\u8fdb\u5f0f\u5448\u73b0", "progressive_disclosure", "\u4fe1\u606f\u67b6\u6784", "UX"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (19, 'knowledge_model', 'FD-M16', 'pattern', '无障碍设计基础 (A11Y)', '[ui_principle] 让前端设计对所有人可用，包括残障用户：

WCAG 2.1 四原则 (POUR):
1. 可感知 (Perceivable): 信息必须能以多种方式呈现
   - 所有图片有alt文本
   - 视频有字幕
   - 颜色不唯一传达信息(需搭配图标/文字)
   
2. 可操作 (Operable): 交互组件必须可键盘操作
   - 所有功能可通过键盘完成
   - 焦点顺序符合视觉顺序
   - 触控目标≥44×44px

3. 可理解 (Understandable): 信息和操作必须可理解
   - 表单有明确的Label
   - 错误信息描述清晰
   - 保持一致的导航模式

4. 健壮性 (Robust): 内容能被辅助技术可靠解析
   - 使用语义化HTML (nav, main, article, aside)
   - ARIA属性正确使用
   - 自定义组件有完整的role/state/label

关键指标:
- 对比度: 正文≥4.5:1 (AA) / ≥7:1 (AAA)
- 焦点可见: 焦点环≥2px, 与背景对比≥3:1
- 屏幕阅读器: 所有关键信息可通过语音朗读获取

训练要点：impeccable有专门的a11y审核命令检测这些标准。', '["\u65e0\u969c\u788d", "A11Y", "WCAG", "\u53ef\u8bbf\u95ee\u6027", "\u5305\u5bb9\u6027\u8bbe\u8ba1"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (20, 'knowledge_model', 'FD-M17', 'pattern', '用户心智模型对齐', '[ux_interaction] 用户在使用产品前已存在的心理模型决定了他们如何理解和使用UI：

核心概念:
1. 系统模型 (System Model): 产品实际如何工作
2. 用户模型 (User''s Mental Model): 用户认为产品如何工作
3. 设计模型 (Designer''s Conceptual Model): 设计师想让用户如何理解

对齐策略:
- 隐喻 (Metaphor): 用现实世界概念降低学习成本 (桌面/文件夹/购物车)
- 模式匹配: 复用用户已熟悉的交互模式
  - 点击Logo回到首页 (所有人都会)
  - 三横线=菜单 (移动端标准)
  - 购物车图标=查看已选商品
- 心理预期管理: 
  - 链接用蓝色+下划线表示可点击
  - 按钮有悬停/按下状态表示交互
  - 加载动画意味着"正在处理，请等待"

测试方法: 
- 首次点击测试 (First Click Test)
- 卡片分类法 (Card Sorting) 验证信息架构
- 五点测试 (5-Second Test) 验证第一印象

训练要点：anti-design的反模式库可帮助理解用户错误预期。', '["\u5fc3\u667a\u6a21\u578b", "\u7528\u6237\u6a21\u578b", "\u9690\u55bb", "UX\u7814\u7a76", "\u4ea4\u4e92\u8bbe\u8ba1"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (21, 'knowledge_model', 'FD-M18', 'pattern', '反馈循环与微交互设计', '[ux_interaction] 每次用户操作都应有即时、恰当、有意义的反馈：

反馈的时间层级:
1. 即时反馈 (0-0.1s): 按钮悬停/按下、键盘按键
2. 延迟反馈 (0.1-1s): 加载动画、表单验证
3. 操作结果 (1-5s): Toast提示、成功/失败通知
4. 长期反馈 (小时-天): 邮件通知、推送消息

微交互四要素 (Dan Saffer):
1. 触发器 (Trigger): 用户操作或系统条件
2. 规则 (Rules): 如何响应的逻辑
3. 反馈 (Feedback): 用户感知到的变化
4. 循环/模式 (Loops/Modes): 重复或例外

UI模式:
- 按钮反馈: 悬停变色→按下内陷→加载旋转→完成打勾
- 表单反馈: 实时验证(失焦触发)→内联错误→提交成功轻提示
- 页面过渡: 路由切换滑入动画→内容淡入
- 数据更新: 新数据高亮闪烁→旧数据淡出

训练要点：react-bits的110+动画组件展示了微交互的丰富可能性。', '["\u5fae\u4ea4\u4e92", "\u53cd\u9988\u5faa\u73af", "\u52a8\u6548", "react-bits", "UX"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (22, 'knowledge_model', 'FD-M19', 'pattern', '状态设计四元组 (Empty/Loading/Error/Edge)', '[ux_interaction] 产品设计中常被忽视的四种关键状态，决定用户体验质量：

1. 空状态 (Empty State):
   - 首次使用: "尚无数据，开始创建第一个..."
   - 搜索无结果: "未找到相关内容，试试其他关键词"
   - 已完成: "所有任务已完成 🎉"
   - 设计原则: 给用户明确的下一步操作

2. 加载状态 (Loading State):
   - Skeleton屏: 与最终结构一致的骨架占位
   - Spinner: 短时等待(<3s)
   - 进度条: 长时等待(>3s)，有明确进度
   - 设计原则: 永远不要让用户面对白屏

3. 错误状态 (Error State):
   - 网络错误: "连接中断，请检查网络"
   - 服务器错误: "服务器繁忙，请稍后重试"
   - 权限错误: "无访问权限"
   - 设计原则: 错误信息要可理解、可操作、有人情味

4. 边缘状态 (Edge Cases):
   - 超长文本截断
   - 特殊字符处理
   - 极端屏幕尺寸
   - 设计原则: QA测试时必须覆盖

训练要点：impeccable的审核检查要求每个组件都定义这四种状态。', '["\u72b6\u6001\u8bbe\u8ba1", "\u7a7a\u72b6\u6001", "\u52a0\u8f7d\u72b6\u6001", "\u9519\u8bef\u5904\u7406", "impeccable"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (23, 'knowledge_model', 'FD-M20', 'pattern', '导航与寻路设计 (Wayfinding)', '[ux_interaction] 帮助用户理解当前位置、去向何方、如何返回的寻路系统：

六大导航模式:
1. 全局导航 (Global Navigation) — 始终可见的顶层导航
   - Top Nav: SaaS标准，7±2项
   - Sidebar: 深度导航，支持分组折叠
   
2. 局部导航 (Local Navigation) — 当前区域的次级导航
   - Tabs: 同一页面的不同视图
   - Sub-nav: 选中全局导航项后的展开

3. 面包屑 (Breadcrumb) — 层级位置指示
   - 位置型: 首页 > 产品 > 详情
   - 路径型: 用户从哪里来
   - 属性型: 当前筛选条件

4. 导航辅助元素:
   - 搜索: 最重要的导航工具
   - 站点地图: 全站内容索引
   - 最近访问: 用户自己的历史路径

5. 寻路信号:
   - "你在这里"指示器 (当前导航项高亮)
   - 页面Title与导航项匹配
   - URL与导航层级对应

6. 移动端适配: 
   - 汉堡菜单(Hamburger Menu)
   - 底部Tab导航 (iOS标准)
   - 手势导航: 滑动返回

训练要点：13个品牌参考(awwwards/siteinspire等)的获奖设计都有出色的寻路设计。', '["\u5bfc\u822a", "\u5bfb\u8def", "\u4fe1\u606f\u67b6\u6784", "wayfinding", "UX"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (24, 'knowledge_model', 'FD-M21', 'pattern', '动效设计原则与性能平衡', '[ux_interaction] 动效应服务于功能而非装饰：

12条动效原则 (UI改编版):
1. 缓动 (Easing): 自然运动用 ease-in-out，非 linear
   - 进入: ease-out (快速开始，慢速结束)
   - 退出: ease-in (慢速开始，快速结束)
2. 时间感: 0.2-0.5s，大于0.5s感觉卡顿，小于0.1s感觉不到
3. 层次感: 元素按重要性错开进入 (stagger)
4. 关联性: 相关元素同方向/同速度运动
5. 空间连贯: 元素动效前后位置合理
6. 反馈: 操作后50ms内给出视觉反馈

性能要求:
- 优先用 transform 和 opacity (GPU加速)
- 避免: height/width/top/left 的动画 (触发Layout)
- 60fps 是目标，掉帧到30fps以下需简化
- will-change 属性谨慎使用

常用UI动效:
- 页面过渡: 滑入/淡入/缩放
- 列表动效: stagger载入、拖拽重排
- 模态框: 缩放入场 + 遮罩淡入
- Hover: 微妙的上移+阴影加深

训练要点：react-bits提供了110+可直接使用的动效组件示例。', '["\u52a8\u6548", "\u52a8\u753b", "\u6027\u80fd", "react-bits", "CSS\u52a8\u753b"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (25, 'knowledge_model', 'FD-M22', 'pattern', '表单设计最佳实践', '[ux_interaction] 表单是用户与产品交互的最核心模式:

表单设计九原则:
1. 标签位置: 顶部标签(最快完成) > 左对齐标签(扫描最优) > 右对齐(最慢)
2. 字段分组: 相关字段分组，每步≤7个字段
3. 单列布局: 单列表单完成率比多列高40%
4. 即时验证: 失焦(onBlur)即时校验，不等到提交
5. 智能默认: 预填已知信息(地区、语言、日期格式)
6. 清晰错误: 内联错误(Inline Error) > 顶部错误汇总
7. 进度指示: 多步表单显示当前步骤/总步骤、已完成
8. 键盘优化: Tab顺序=视觉顺序，Enter提交
9. 输入类型: 使用正确的 input type (tel/number/email/date)

移动端特化:
- 使用系统原生键盘类型(数字键盘用于电话号码)
- 大触控目标(≥44px)
- 自动聚焦第一个字段

数据验证层级:
- 格式验证: 邮箱格式、电话号码
- 业务验证: 是否存在、是否可用
- 安全验证: XSS过滤、CSRF防护

训练要点：Ant Design的Form组件是表单设计系统的工业级实现。', '["\u8868\u5355\u8bbe\u8ba1", "UX", "ant-design", "\u6570\u636e\u8f93\u5165", "\u9a8c\u8bc1"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (26, 'knowledge_model', 'FD-M23', 'pattern', '移动端优先设计思维 (Mobile First)', '[ux_interaction] 从最小的屏幕开始设计，渐进增强到更大的屏幕：

核心方法论:
1. 内容优先级: 最小屏幕上只展示核心内容
2. 渐进增强: 屏幕越大→展示越多、越详细
3. 触控优先: 所有交互为手指设计，而非鼠标

移动端设计约束:
- 单手持握: 拇指覆盖区=手机屏幕下半部40%
- 最小触控: 44×44px (Apple HIG) / 48×48px (Material)
- 网络环境: 假设3G网络(200KB/s)，懒加载优化

响应式断点决策:
1. 不是"适配移动"，而是"从小到大"
2. 每个断点重新审视布局，不只缩放
3. 导航模式切换: 底部Tab(移动)→顶部导航(桌面)
4. 表格响应: 卡片化(移动) → 表格(桌面)

常见反模式:
- 桌面端塞满功能再移到移动端(裁剪很难)
- 隐藏重要功能在汉堡菜单后
- 桌面端hover态交互在触控上不起作用

训练要点：Awwwards获奖移动端设计是移动优先的最佳参考。', '["\u79fb\u52a8\u4f18\u5148", "\u54cd\u5e94\u5f0f\u8bbe\u8ba1", "\u89e6\u63a7", "mobile-first", "UX"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (27, 'knowledge_model', 'FD-M24', 'pattern', '转化率优化设计 (CRO Design)', '[ux_interaction] 通过设计手段提升用户完成目标转化的比率：

CRO设计七原则:
1. 清晰的价值主张 (Value Proposition):
   - 首屏5秒内回答: "这是什么? 对我有什么用?"
   - 使用具体数字而非模糊描述

2. 减少摩擦 (Friction Reduction):
   - 减少表单字段 (每少1个字段提升转化5-10%)
   - 社交登录一键注册
   - 无需注册即可预览产品

3. 信任信号 (Trust Signals):
   - 安全认证标识 (SSL/PCI)
   - 客户Logo墙
   - 真实评价/案例
   - 退款保证

4. 紧迫感 (Urgency & Scarcity):
   - 限时优惠倒计时
   - 库存显示 ("仅剩3件")
   - 合理使用，过度使用降低信任

5. 清晰的CTA (Call to Action):
   - 按钮文案: "开始免费试用" > "提交"
   - 对比色CTA按钮
   - 唯一主要操作

6. 社会证明 (Social Proof):
   - 用户数/下载量展示
   - 实时购买通知
   - 第三方背书

7. 消除焦虑 (Anxiety Reduction):
   - 明确的定价
   - 取消订阅的便捷性
   - 隐私保护说明

训练要点：Stripe-clone是CRO设计的教科书级案例。', '["CRO", "\u8f6c\u5316\u7387", "\u589e\u957f\u8bbe\u8ba1", "Stripe", "UX"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (28, 'knowledge_model', 'FD-M25', 'pattern', '对比度与可读性设计', '[visual_design] 对比度是阅读体验的基础，直接影响信息传达效率:

对比度层级设计:
1. 极重要信息: 品牌色背景+白色文字，或黑字白底
2. 正文: #1a1a1a 背景#fff (对比度15:1) 
3. 次级信息: #666 背景#fff (对比度5.5:1)
4. 辅助信息: #999 背景#fff (对比度2.8:1, 仅用于装饰)
5. 禁用状态: #ccc 背景#fff (对比度1.6:1)

可访问性对比度标准 (WCAG 2.1):
- AA级: 正文4.5:1, 大文本(≥18pt bold/≥24pt)3:1
- AAA级: 正文7:1, 大文本4.5:1

颜色组合考虑:
- 色盲类型: Deuteranopia(红绿色盲6%)、Protanopia、Tritanopia
- 信息不应仅靠颜色区分: 搭配图标、文字、形状
- 使用亮度对比而非色相对比: 黑白模式下也应可读

工具链:
- 设计时: 对比度检查插件 (Stark, Axe)
- 构建时: CI流水线自动检查Token对比度
- 运行时: 高对比度模式检测 (prefers-contrast: more)

训练要点：awesome-design-md中Apple/特斯拉的设计以高对比度著称。', '["\u5bf9\u6bd4\u5ea6", "\u53ef\u8bfb\u6027", "WCAG", "\u8272\u76f2", "A11Y"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (29, 'knowledge_model', 'FD-M26', 'pattern', '视觉节奏与重复设计模式', '[visual_design] 通过有规律的视觉重复创造和谐、可预测的用户体验:

视觉节奏的四种类型:
1. 规律节奏 (Regular Rhythm): 等间距重复
   - 卡片网格、列表项、时间轴
   - 稳定、可靠、可预测

2. 流动节奏 (Flowing Rhythm): 有机重复
   - 曲线排列的插图、手绘风格
   - 动态、自然、亲切

3. 渐进节奏 (Progressive Rhythm): 递进变化
   - 字体层级、色彩阶梯、尺寸递增
   - 引导视线向特定方向

4. 交替节奏 (Alternating Rhythm): 模式交替
   - 斑马纹表格、交替卡片排列
   - 减少视觉疲劳

设计应用:
- 重复: 组件复用 (相同卡片样式), 间距模式 (8px系统)
- 渐变: 颜色从主→辅渐变, 尺寸从大到小
- 强调: 打破节奏吸引注意力 (特殊颜色卡片)

训练要点：taste-skill强调"节奏感"是区分专业和业余设计的标志。', '["\u89c6\u89c9\u8282\u594f", "\u91cd\u590d", "\u8bbe\u8ba1\u6a21\u5f0f", "taste-skill", "\u6392\u7248"]', 0.85, 0.765, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (30, 'knowledge_model', 'FD-M27', 'pattern', '品牌视觉语言一致性', '[visual_design] 品牌的视觉语言必须在所有触点上保持一致:

品牌视觉系统的八大要素:
1. Logo系统: 标准/简化/图标/ Favicon版本
2. 色彩系统: 品牌色+辅助色+中性色+语义色
3. 字体系统: 品牌字体+ Web后备字体
4. 插画风格: 统一线条粗细/着色方式/角色风格
5. 摄影风格: 光线/色调/构图/后期统一
6. 图标系统: 线型/面型统一，圆角/端点统一
7. 空间规则: 留白比例、元素间距标准
8. 动效语言: 缓动函数/时长/运动方向统一

品牌落地检查清单:
- 是否有品牌规范文档 (Brand Guidelines)?
- Token是否跨项目一致 (Web/App/打印)？
- 第三方生态(合作伙伴)是否获得品牌资源？
- 品牌色在不同屏幕(OLED/LCD)是否表现一致？

品牌演进:
- 小步更新: 渐进式优化，避免突变
- 保留核心: Logo/品牌色/字体需高度稳定
- 记录变迁: 每次变更记录原因和时间

训练要点：awesome-design-md收录的73+品牌规范是学习的宝库。', '["\u54c1\u724c\u8bbe\u8ba1", "\u89c6\u89c9\u8bed\u8a00", "brand", "\u8bbe\u8ba1\u89c4\u8303"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (31, 'knowledge_model', 'FD-M28', 'pattern', '数据可视化设计原则', '[visual_design] 将数据转化为易于理解的可视化形式：

图表选择决策树:
- 比较: 柱状图 (数量比较) / 雷达图 (多维比较)
- 趋势: 折线图 (时间序列) / 面积图 (趋势+量级)
- 组成: 饼图 (占比, ≤5项) / 堆叠柱状图 (组成变化)
- 分布: 散点图 (相关性) / 直方图 (数值分布)
- 流程: 漏斗图 (转化路径) / 桑基图 (流量分配)
- 关系: 网络图 (节点关系) / 树图 (层次结构)

设计原则:
1. 数据-墨水比 (Data-Ink Ratio): 去除不必要的装饰
2. 零基线: 柱状图从0开始，避免误导
3. 排序: 默认按数值降序排列
4. 标签清晰: 轴线标签、数据标签、图例完整
5. 无障碍: 图表有文字描述、支持键盘导航
6. 交互: 悬停显示详情、点击下钻、缩放

色彩规范:
- 数据色板: 8-12种可区分的颜色
- 色盲友好: 避免红绿同时使用
- 语义色: 好(绿)、坏(红)、中性(蓝/灰)

训练要点：ant-design的图表组件和Stripe的Dashboard是数据可视化典范。', '["\u6570\u636e\u53ef\u89c6\u5316", "\u56fe\u8868", "dashboard", "ant-design", "\u4fe1\u606f\u8bbe\u8ba1"]', 0.85, 0.765, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (32, 'knowledge_model', 'FD-M29', 'pattern', '排版与文字层次设计', '[visual_design] 文字是产品与用户沟通的核心媒介:

排版六维控制:
1. 字号 (Font Size): modular scale等比，确保层级分明
2. 字重 (Font Weight): 400/500/600/700，每跳一级需视觉可见差异
3. 颜色 (Color): 正文近黑、辅助浅灰，颜色=层级
4. 间距 (Spacing): 字距(letter-spacing)、词距(word-spacing)
5. 行高 (Line Height): 正文1.5-1.6、标题1.1-1.2
6. 大小写 (Case): 标题Title Case、正文Sentence case、标签UPPER

文字层级参考 (16px基准, 1.25 scale):
- Display (特大标题): 48/40/32px — 1-2次/页
- H1: 28px — 页面标题，每页1个
- H2: 22px — 区块标题
- H3: 18px — 小组件标题
- Body: 16px — 正文
- Small: 14px — 辅助信息
- Caption: 12px — 标注/注释

响应式排版:
- 移动端: 基准15px, H1=24px
- 桌面端: 基准16px, H1=32px
- 使用 clamp() 实现流畅排版: font-size: clamp(1rem, 1rem + 0.5vw, 1.5rem)

训练要点：taste-skill中"反模板化"的排版策略追求可读性>装饰性。', '["\u6392\u7248", "\u5b57\u4f53\u5c42\u6b21", "typography", "taste-skill", "\u54cd\u5e94\u5f0f"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (33, 'knowledge_model', 'FD-M30', 'pattern', '设计中的阴影与深度系统', '[visual_design] 通过阴影和层级创造视觉深度的系统化方法:

阴影层级设计 (Z-Space):
- Level 0 (Base): 无阴影，平面元素
- Level 1 (Raised): 小偏移+小模糊，卡片默认态
  box-shadow: 0 1px 3px rgba(0,0,0,0.08)
- Level 2 (Elevated): 中偏移+中模糊，悬停卡片
  box-shadow: 0 4px 12px rgba(0,0,0,0.12)
- Level 3 (Overlay): 大偏移+大模糊，下拉菜单/弹出层
  box-shadow: 0 8px 24px rgba(0,0,0,0.16)
- Level 4 (Modal): 最大偏移+最大模糊，模态框
  box-shadow: 0 16px 48px rgba(0,0,0,0.24)

阴影的三个维度:
1. 偏移 (Offset): X/Y方向，决定光源方向（统一从上方）
2. 模糊 (Blur): 决定柔和度
3. 扩散 (Spread): 决定生长感

暗色模式适配:
- 阴影透明度降低 (深色背景上看不清阴影)
- 使用发光代替阴影: box-shadow: 0 0 20px rgba(0,0,0,0.3)
- 通过背景色层次区分深度 (surface 1/2/3)

训练要点：Apple的设计强调无阴影的平面层级，Material Design强调阴影的层次。', '["\u9634\u5f71", "\u6df1\u5ea6", "\u5c42\u7ea7", "Material Design", "\u6697\u8272\u6a21\u5f0f"]', 0.85, 0.765, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (34, 'knowledge_model', 'FD-M31', 'pattern', '设计冲刺与迭代设计思维', '[process_methodology] 加速设计决策、减少猜测的迭代方法论:

设计冲刺五步 (Google Ventures改编):
1. 理解 (Understand): 用户研究、竞品分析、定义问题
2. 发散 (Diverge): Brainstorming、草稿、概念探索
3. 决策 (Decide): 投票、聚焦、确定方案
4. 原型 (Prototype): 快速原型(低保真→高保真)
5. 验证 (Validate): 用户测试、A/B测试、反馈收集

迭代频率建议:
- 探索阶段: 每2-3天一个迭代循环
- 开发阶段: 每1-2周一个设计验收
- 优化阶段: 每月一次设计审核 (Design Audit)

设计评审四维度:
1. 功能完整性: 是否覆盖所有用户场景
2. 视觉质量: 是否符合设计系统标准
3. 交互合理性: 用户是否能自然完成任务
4. 实现可行性: 技术约束下的可落地性

最佳实践:
- 使用darwin-skill的设计进化工具追踪设计版本
- taste-skill的"三旋钮"(视觉粒度/语言密度/工程纯度)做质量评估
- 每周设计复盘：什么有效/什么无效/下次改进

训练要点：darwin-skill是专门用于设计进化和迭代的工具。', '["\u8bbe\u8ba1\u51b2\u523a", "\u8fed\u4ee3", "\u8bbe\u8ba1\u601d\u7ef4", "darwin-skill", "\u65b9\u6cd5\u8bba"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (35, 'knowledge_model', 'FD-M32', 'pattern', '设计审核与质量评估体系', '[process_methodology] 系统化评估设计质量的标准化流程:

impeccable 23条设计审核命令 (按维度分组):

A. 布局 (Layout):
1. 网格一致性检查
2. 间距合规性
3. 对齐完整性
4. 响应式断点覆盖

B. 视觉 (Visual):
5. Color Token使用检查
6. Typography层级规范
7. Shadow层级检查
8. BorderRadius一致性

C. 状态 (States):
9. Hover状态完整性
10. Focus状态可见性
11. Active状态反馈
12. Disabled状态表现
13. Loading状态存在
14. Empty状态处理
15. Error状态处理

D. 交互 (Interaction):
16. 触控目标尺寸(≥44px)
17. 键盘可操作性
18. 焦点顺序(Tab Order)
19. 页面过渡动效

E. 内容 (Content):
20. 文本截断处理
21. 空状态文案
22. 错误信息质量
23. 多语言适配

评分体系:
- Pass (通过): 完全符合标准
- Warning (警告): 轻微偏差，可接受
- Fail (不通过): 需要修复

训练要点：impeccable旨在实现设计审核自动化，可直接集成到CI/CD。', '["\u8bbe\u8ba1\u5ba1\u6838", "\u8d28\u91cf\u8bc4\u4f30", "impeccable", "\u8bbe\u8ba1QA"]', 0.95, 0.855, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (36, 'knowledge_model', 'FD-M33', 'pattern', '设计与开发的协同工作流 (Design-Dev Handoff)', '[process_methodology] 设计到开发的交接流程是产品交付效率的关键瓶颈:

设计交付物规范:
1. 设计稿 → 开发
   - 明确标注: 间距、字号、颜色值(使用Token而非绝对数值)
   - 组件状态覆盖: 每个组件的所有状态截图
   - 响应式说明: 每个断点的布局变化
   - 动效规范: 时长、缓动函数、触发条件

2. Figma→代码工作流:
   - Tokens: 通过 design_tokens.json 直接导出
   - 组件: Figma组件的属性对应到组件Props
   - 样式: 自动生成CSS变量

3. 开发实现阶段:
   - 使用ant-design等组件库保证80%的界面一致
   - 自定义组件严格遵循设计系统Token
   - Storybook作为组件文档和测试平台

4. 设计验收 (Design QA):
   - 开发完成后的像素级对比验收
   - 使用impeccable的自动化审核
   - 回归检查清单

5. 持续同步:
   - 设计师可直接修改CSS变量文件(无需开发介入)
   - Token变更自动生成Changelog
   - 每周设计-开发同步会议

训练要点：Token化是设计与开发同步的关键基础设施。', '["\u8bbe\u8ba1\u4ea4\u4ed8", "\u5f00\u53d1\u534f\u540c", "handoff", "\u6d41\u7a0b", "Token"]', 0.9, 0.81, 1, 1, '2026-07-01 19:39:17', '2026-07-01 19:39:55'),
  (37, 'design_brand', 'ai-shuzhi-juntuan', 'design_system', '品牌设计规范 — ai-shuzhi-juntuan', '# 品牌设计规范: AI数智军团 (AI Digital Legion)

A dark cyber-recruitment dashboard for AI digital employees. The system anchors on a deep navy canvas (#0a0e1a) with cyan (#22d3ee) as the single chromatic accent — the signal color across CTAs, hover borders, skill tags, and active indicators. Cards render as gradient-dark panels (#111827 → #0f172a) with 1px hairline borders in gray-800 (#1f2937). The atmosphere is command-center technical: dense information density, glowing status dots, and a recruitment-market-style employee directory. Gold (#f59e0b) appears sparingly for rank insignia and special badges. Type runs Inter/system-ui at 400–700 weight with tight line-heights for data density.

## 颜色体系 (Colors)

- **primary**: #22d3ee
- **primary-hover**: #67e8f9
- **primary-active**: #06b6d4
- **ink**: #f1f5f9
- **ink-secondary**: #94a3b8
- **ink-muted**: #6b7280
- **canvas**: #0a0e1a
- **canvas-elevated**: #111827
- **canvas-gradient**: #0f172a
- **surface-card**: #111827
- **surface-card-hover**: #1e293b
- **surface-dark-soft**: #1f2937
- **hairline**: #1f2937
- **hairline-strong**: #334155
- **gold**: #f59e0b
- **gold-soft**: #fbbf24
- **green**: #22c55e
- **green-glow**: rgba(34, 197, 94, 0.5)
- **red**: #ef4444
- **purple**: #a78bfa
- **pink**: #f472b6
- **on-primary**: #0a0e1a
- **on-dark**: #f1f5f9
- **on-card**: #e2e8f0

## 排版体系 (Typography)

- **display-xl**: font: Inter, system-ui, -apple-system, sans-serif | size: 36px | weight: 700 | lh: 1.15 | ls: -0.5px
- **display-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 28px | weight: 700 | lh: 1.2 | ls: -0.3px
- **display-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 24px | weight: 700 | lh: 1.25 | ls: -0.2px
- **headline**: font: Inter, system-ui, -apple-system, sans-serif | size: 20px | weight: 600 | lh: 1.3 | ls: 0
- **title-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 18px | weight: 600 | lh: 1.35 | ls: 0
- **title-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 15px | weight: 400 | lh: 1.55 | ls: 0
- **body-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 400 | lh: 1.45 | ls: 0
- **button**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 500 | lh: 1.0 | ls: 0
- **caption**: font: Inter, system-ui, -apple-system, sans-serif | size: 12px | weight: 500 | lh: 1.4 | ls: 0.3px
- **micro**: font: Inter, system-ui, -apple-system, sans-serif | size: 11px | weight: 400 | lh: 1.3 | ls: 0
- **code**: font: JetBrains Mono, ui-monospace, monospace | size: 13px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **xxxl**: 32px
- **section**: 48px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 16px, height: 34px

### button-primary-hover
backgroundColor: {colors.primary-hover}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 16px, height: 34px, border: 1px solid {colors.hairline}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink-secondary}, typography: {typography.button}, rounded: {rounded.md}, padding: 6px 12px

### status-dot
width: 10px, height: 10px, rounded: {rounded.full}

### emp-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 20px, border: 1px solid {colors.hairline}

### emp-card-hover
backgroundColor: {colors.surface-card-hover}, borderColor: {colors.primary}, shadow: 0 0 25px rgba(34, 211, 238, 0.12)

### metric-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 16px

### skill-tag
backgroundColor: rgba(34, 211, 238, 0.1), textColor: {colors.primary-hover}, typography: {typography.caption}, rounded: {rounded.sm}, padding: 2px 8px, border: 1px solid rgba(34, 211, 238, 0.2)

### badge-rank
backgroundColor: {colors.gold}, textColor: {colors.on-primary}, typography: {typography.micro}, rounded: {rounded.sm}, padding: 1px 6px

### search-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 14px, height: 36px, border: 1px solid {colors.hairline}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, height: 56px, borderBottom: 1px solid {colors.hairline}

### table-row
backgroundColor: {colors.canvas}, textColor: {colors.ink-secondary}, typography: {typography.body-sm}, hoverBg: {colors.surface-card-hover}
', '["design-brand", "ai-shuzhi-juntuan", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (38, 'design_brand', 'airbnb', 'design_system', '品牌设计规范 — airbnb', '# 品牌设计规范: Airbnb

A warm, generous consumer marketplace anchored on a clean white canvas and Airbnb Rausch (#ff385c), the single brand voltage that carries every primary CTA, search-button orb, and rating dot. Type runs Airbnb Cereal VF at modest weights — display sits at 22–28px in weight 500/600 rather than the heavy 700+ that fintech and enterprise systems use; the brand trusts photography and generous whitespace over typographic muscle. Three product entries (Homes, Experiences, Services) sit in the top nav with hand-illustrated 32-icon glyphs and "NEW" badges, signaling a marketplace expansion rather than a feature dump. Pill-shaped search bars (`{rounded.full}`), softly rounded property cards (`{rounded.lg}` ~14px), and 32px button radii read as friendly and human — there is no hard corner anywhere except the body grid.

## 颜色体系 (Colors)

- **primary**: #ff385c
- **primary-active**: #e00b41
- **primary-disabled**: #ffd1da
- **primary-error-text**: #c13515
- **primary-error-text-hover**: #b32505
- **luxe**: #460479
- **plus**: #92174d
- **ink**: #222222
- **body**: #3f3f3f
- **muted**: #6a6a6a
- **muted-soft**: #929292
- **hairline**: #dddddd
- **hairline-soft**: #ebebeb
- **border-strong**: #c1c1c1
- **canvas**: #ffffff
- **surface-soft**: #f7f7f7
- **surface-card**: #ffffff
- **surface-strong**: #f2f2f2
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **legal-link**: #428bff
- **star-rating**: #222222
- **scrim**: #000000

## 排版体系 (Typography)

- **display-xl**: font: ''Airbnb Cereal VF'', Circular, -apple-system, system-ui, Roboto, ''Helvetica Neue'', sans-serif | size: 28px | weight: 700 | lh: 1.43 | ls: 0
- **display-lg**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 22px | weight: 500 | lh: 1.18 | ls: -0.44px
- **display-md**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 21px | weight: 700 | lh: 1.43 | ls: 0
- **display-sm**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 20px | weight: 600 | lh: 1.2 | ls: -0.18px
- **title-md**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 16px | weight: 600 | lh: 1.25 | ls: 0
- **title-sm**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 16px | weight: 500 | lh: 1.25 | ls: 0
- **rating-display**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 64px | weight: 700 | lh: 1.1 | ls: -1px
- **body-md**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **caption**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 14px | weight: 500 | lh: 1.29 | ls: 0
- **caption-sm**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 13px | weight: 400 | lh: 1.23 | ls: 0
- **badge**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 11px | weight: 600 | lh: 1.18 | ls: 0
- **micro-label**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 12px | weight: 700 | lh: 1.33 | ls: 0
- **uppercase-tag**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 8px | weight: 700 | lh: 1.25 | ls: 0.32px | transform: uppercase
- **button-md**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 16px | weight: 500 | lh: 1.25 | ls: 0
- **button-sm**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 14px | weight: 500 | lh: 1.29 | ls: 0
- **link**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **nav-link**: font: ''Airbnb Cereal VF'', Circular, sans-serif | size: 16px | weight: 600 | lh: 1.25 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **base**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 64px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 8px
- **md**: 14px
- **lg**: 20px
- **xl**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 14px 24px, height: 48px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.sm}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.on-primary}, rounded: {rounded.sm}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 13px 23px, height: 48px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}

### button-pill-rausch
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 10px 20px

### search-orb
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.full}, height: 48px

### icon-button-circle
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, rounded: {rounded.full}, height: 32px

### icon-button-outline
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, height: 40px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 80px

### product-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.nav-link}, rounded: {rounded.none}

### product-tab-inactive
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.nav-link}

### search-bar-pill
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.full}, padding: 14px 24px, height: 64px

### search-field-segment
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.caption}, padding: 8px 24px

### category-strip
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.button-sm}

### category-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.none}

### property-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}

### property-card-photo
rounded: {rounded.md}

### experience-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.md}

### city-link-block
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.title-sm}

### rating-display-card
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.rating-display}

### guest-favorite-badge
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.badge}, rounded: {rounded.full}, padding: 4px 10px

### new-tag
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.uppercase-tag}, rounded: {rounded.full}, padding: 2px 6px

### amenity-row
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}, padding: 12px 0

### reviews-card
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm}

### host-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 24px

### reservation-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### date-picker-day
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.full}

### date-picker-day-selected
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, rounded: {rounded.full}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 14px 12px, height: 56px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, padding: 48px 80px

### footer-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm}

### legal-band
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.caption-sm}
', '["design-brand", "airbnb", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (39, 'design_brand', 'airtable', 'design_system', '品牌设计规范 — airtable', '# 品牌设计规范: Airtable

A sober, editorial workflow-software interface anchored on white canvas and dark-ink type, where brand voltage comes from full-bleed signature cards in coral, dark green, peach, and dark navy that punctuate long-scroll explainer pages. Primary actions use a near-black pill CTA; secondary actions sit in a white outlined button. Type runs Haas Grotesk in modest weights — never bold for its own sake.

## 颜色体系 (Colors)

- **primary**: #181d26
- **primary-active**: #0d1218
- **ink**: #181d26
- **body**: #333840
- **muted**: #41454d
- **hairline**: #dddddd
- **border-strong**: #9297a0
- **canvas**: #ffffff
- **surface-soft**: #f8fafc
- **surface-strong**: #e0e2e6
- **surface-dark**: #181d26
- **surface-dark-elevated**: #1d1f25
- **signature-coral**: #aa2d00
- **signature-forest**: #0a2e0e
- **signature-cream**: #f5e9d4
- **signature-peach**: #fcab79
- **signature-mint**: #a8d8c4
- **signature-yellow**: #f4d35e
- **signature-mustard**: #d9a441
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **link**: #1b61c9
- **link-active**: #1a3866
- **info**: #254fad
- **info-border**: #458fff
- **success**: #006400
- **success-border**: #39bf45
- **pricing-ink**: #1d1f25

## 排版体系 (Typography)

- **display-xl**: font: Haas Groot Disp, Haas, sans-serif | size: 48px | weight: 500 | lh: 1.1 | ls: 0
- **display-lg**: font: Haas Groot Disp, Haas, sans-serif | size: 40px | weight: 400 | lh: 1.2 | ls: 0
- **display-md**: font: Haas Groot Disp, Haas, sans-serif | size: 32px | weight: 400 | lh: 1.2 | ls: 0
- **title-lg**: font: Haas, sans-serif | size: 24px | weight: 400 | lh: 1.35 | ls: 0.12px
- **title-md**: font: Haas Groot Disp, Haas, sans-serif | size: 20px | weight: 400 | lh: 1.5 | ls: 0
- **title-sm**: font: Haas, sans-serif | size: 18px | weight: 500 | lh: 1.4 | ls: 0
- **label-md**: font: Haas, sans-serif | size: 16px | weight: 500 | lh: 1.4 | ls: 0
- **button**: font: Haas, sans-serif | size: 16px | weight: 500 | lh: 1.4 | ls: 0
- **body-md**: font: Haas, sans-serif | size: 14px | weight: 400 | lh: 1.25 | ls: 0
- **caption**: font: Haas, sans-serif | size: 14px | weight: 500 | lh: 1.35 | ls: 0.16px
- **legal**: font: Haas, sans-serif | size: 13.12px | weight: 600 | lh: 1.2 | ls: 0
- **pricing-display**: font: Inter Display, system-ui, sans-serif | size: 44.8px | weight: 475 | lh: 1.1 | ls: 0
- **pricing-section**: font: Inter Display, system-ui, sans-serif | size: 28px | weight: 475 | lh: 1.2 | ls: 0
- **pricing-card-title**: font: Inter Display, system-ui, sans-serif | size: 20px | weight: 475 | lh: 1.3 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 2px
- **sm**: 6px
- **md**: 10px
- **lg**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.lg}, padding: 16px 24px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.lg}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.lg}, padding: 16px 24px

### button-secondary-on-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.lg}, padding: 16px 24px

### button-legal
backgroundColor: {colors.link}, textColor: {colors.on-primary}, typography: {typography.legal}, rounded: {rounded.xs}, padding: 12px 10px

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 40px

### button-pricing-pill
backgroundColor: {colors.canvas}, textColor: {colors.pricing-ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 12px 24px

### text-link
backgroundColor: transparent, textColor: {colors.link}, typography: {typography.body-md}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, height: 64px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### signature-coral-card
backgroundColor: {colors.signature-coral}, textColor: {colors.on-primary}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 48px

### signature-forest-card
backgroundColor: {colors.signature-forest}, textColor: {colors.on-primary}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 48px

### hero-card-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 48px

### feature-card-tabbed
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### cream-callout-card
backgroundColor: {colors.signature-cream}, textColor: {colors.ink}, typography: {typography.title-lg}, rounded: {rounded.md}, padding: 24px

### demo-grid-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.label-md}, rounded: {rounded.md}, padding: 16px

### logo-strip
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.body-md}, padding: 32px

### article-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-sm}, rounded: {rounded.md}, padding: 16px

### topic-filter-rail
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-md}, width: 240px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 12px 16px, height: 44px

### text-input-focus
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.sm}

### pricing-tier-card
backgroundColor: {colors.canvas}, textColor: {colors.pricing-ink}, typography: {typography.pricing-card-title}, rounded: {rounded.md}, padding: 32px

### pricing-tier-card-featured
backgroundColor: {colors.surface-soft}, textColor: {colors.pricing-ink}, typography: {typography.pricing-card-title}, rounded: {rounded.md}, padding: 32px

### pricing-comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-md}, padding: 12px

### cta-band-light
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 48px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-md}, padding: 64px
', '["design-brand", "airtable", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (40, 'design_brand', 'apple', 'design_system', '品牌设计规范 — apple', '# 品牌设计规范: Apple

A photography-first interface that turns marketing into a museum gallery. Edge-to-edge product tiles alternate light and dark canvases, framed by SF Pro Display headlines with negative letter-spacing and a single Action Blue (#0066cc) interactive color. UI chrome recedes so the product can speak — no decorative gradients, no shadows on chrome, only the one signature drop-shadow under product imagery resting on a surface.

## 颜色体系 (Colors)

- **primary**: #0066cc
- **primary-focus**: #0071e3
- **primary-on-dark**: #2997ff
- **ink**: #1d1d1f
- **body**: #1d1d1f
- **body-on-dark**: #ffffff
- **body-muted**: #cccccc
- **ink-muted-80**: #333333
- **ink-muted-48**: #7a7a7a
- **divider-soft**: #f0f0f0
- **hairline**: #e0e0e0
- **canvas**: #ffffff
- **canvas-parchment**: #f5f5f7
- **surface-pearl**: #fafafc
- **surface-tile-1**: #272729
- **surface-tile-2**: #2a2a2c
- **surface-tile-3**: #252527
- **surface-black**: #000000
- **surface-chip-translucent**: #d2d2d7
- **on-primary**: #ffffff
- **on-dark**: #ffffff

## 排版体系 (Typography)

- **hero-display**: font: SF Pro Display, system-ui, -apple-system, sans-serif | size: 56px | weight: 600 | lh: 1.07 | ls: -0.28px
- **display-lg**: font: SF Pro Display, system-ui, -apple-system, sans-serif | size: 40px | weight: 600 | lh: 1.1 | ls: 0
- **display-md**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 34px | weight: 600 | lh: 1.47 | ls: -0.374px
- **lead**: font: SF Pro Display, system-ui, -apple-system, sans-serif | size: 28px | weight: 400 | lh: 1.14 | ls: 0.196px
- **lead-airy**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 24px | weight: 300 | lh: 1.5 | ls: 0
- **tagline**: font: SF Pro Display, system-ui, -apple-system, sans-serif | size: 21px | weight: 600 | lh: 1.19 | ls: 0.231px
- **body-strong**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 17px | weight: 600 | lh: 1.24 | ls: -0.374px
- **body**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 17px | weight: 400 | lh: 1.47 | ls: -0.374px
- **dense-link**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 17px | weight: 400 | lh: 2.41 | ls: 0
- **caption**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: -0.224px
- **caption-strong**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 14px | weight: 600 | lh: 1.29 | ls: -0.224px
- **button-large**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 18px | weight: 300 | lh: 1.0 | ls: 0
- **button-utility**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.29 | ls: -0.224px
- **fine-print**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 12px | weight: 400 | lh: 1.0 | ls: -0.12px
- **micro-legal**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 10px | weight: 400 | lh: 1.3 | ls: -0.08px
- **nav-link**: font: SF Pro Text, system-ui, -apple-system, sans-serif | size: 12px | weight: 400 | lh: 1.0 | ls: -0.12px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 17px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 80px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 5px
- **sm**: 8px
- **md**: 11px
- **lg**: 18px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body}, rounded: {rounded.pill}, padding: 11px 22px

### button-primary-focus
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.pill}

### button-primary-active
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.pill}

### button-secondary-pill
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.body}, rounded: {rounded.pill}, padding: 11px 22px

### button-dark-utility
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.button-utility}, rounded: {rounded.sm}, padding: 8px 15px

### button-pearl-capsule
backgroundColor: {colors.surface-pearl}, textColor: {colors.ink-muted-80}, typography: {typography.caption}, rounded: {rounded.md}, padding: 8px 14px

### button-store-hero
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-large}, rounded: {rounded.pill}, padding: 14px 28px

### button-icon-circular
backgroundColor: {colors.surface-chip-translucent}, textColor: {colors.ink}, rounded: {rounded.full}, size: 44px

### text-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body}

### text-link-on-dark
backgroundColor: transparent, textColor: {colors.primary-on-dark}, typography: {typography.body}

### global-nav
backgroundColor: {colors.surface-black}, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 44px

### sub-nav-frosted
backgroundColor: {colors.canvas-parchment}, textColor: {colors.ink}, typography: {typography.tagline}, height: 52px

### product-tile-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, rounded: {rounded.none}, padding: 80px

### product-tile-parchment
backgroundColor: {colors.canvas-parchment}, textColor: {colors.ink}, typography: {typography.display-lg}, rounded: {rounded.none}, padding: 80px

### product-tile-dark
backgroundColor: {colors.surface-tile-1}, textColor: {colors.on-dark}, typography: {typography.display-lg}, rounded: {rounded.none}, padding: 80px

### product-tile-dark-2
backgroundColor: {colors.surface-tile-2}, textColor: {colors.on-dark}, rounded: {rounded.none}

### product-tile-dark-3
backgroundColor: {colors.surface-tile-3}, textColor: {colors.on-dark}, rounded: {rounded.none}

### store-utility-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.lg}, padding: 24px

### configurator-option-chip
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 12px 16px

### configurator-option-chip-selected
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.pill}

### search-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.pill}, padding: 12px 20px, height: 44px

### floating-sticky-bar
backgroundColor: {colors.canvas-parchment}, textColor: {colors.ink}, typography: {typography.body}, height: 64px, padding: 12px 32px

### environment-quote-card
backgroundColor: {colors.surface-tile-1}, textColor: {colors.on-dark}, typography: {typography.display-lg}, rounded: {rounded.none}, padding: 80px

### footer
backgroundColor: {colors.canvas-parchment}, textColor: {colors.ink-muted-80}, typography: {typography.fine-print}, padding: 64px
', '["design-brand", "apple", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (41, 'design_brand', 'baize-console', 'design_system', '品牌设计规范 — baize-console', '# 品牌设计规范: 白泽控制台 (Baize Console)

A warm-dark CEO command center with a golden-yellow brand accent (#f59e0b) on a deep slate canvas (#0f172a). The system''s personality is ''warm authority'' — the gold primary evokes the Baize mythical beast (白泽神兽, a golden-furred creature of wisdom), used on CTAs, highlight accents, and status indicators. Cards sit on slate-800 (#1e293b) with gradient backgrounds and sky-blue (#38bdf8) as a secondary accent for informational chrome. The atmosphere is less cold-technical and more regal-command: gold outlines, warm highlights, and metric cards with glowing accents. Typography runs Inter/system-ui with generous letter-spacing on labels and uppercase badge text.

## 颜色体系 (Colors)

- **primary**: #f59e0b
- **primary-hover**: #fbbf24
- **primary-active**: #d97706
- **accent-blue**: #38bdf8
- **accent-blue-hover**: #7dd3fc
- **accent-blue-active**: #0ea5e9
- **ink**: #f1f5f9
- **ink-secondary**: #94a3b8
- **ink-muted**: #64748b
- **canvas**: #0f172a
- **surface-card**: #1e293b
- **surface-elevated**: #334155
- **surface-soft**: #1e293b
- **hairline**: #334155
- **gold**: #f59e0b
- **gold-soft**: #fef3c7
- **gold-glow**: rgba(245, 158, 11, 0.15)
- **green**: #22c55e
- **red**: #ef4444
- **on-primary**: #0f172a
- **on-dark**: #f1f5f9
- **on-card**: #cbd5e1

## 排版体系 (Typography)

- **display-xl**: font: Inter, system-ui, -apple-system, sans-serif | size: 32px | weight: 700 | lh: 1.15 | ls: -0.5px
- **display-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 26px | weight: 700 | lh: 1.2 | ls: -0.3px
- **display-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 22px | weight: 600 | lh: 1.3 | ls: -0.2px
- **headline**: font: Inter, system-ui, -apple-system, sans-serif | size: 18px | weight: 600 | lh: 1.35 | ls: 0
- **title-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 15px | weight: 600 | lh: 1.4 | ls: 0
- **body-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 15px | weight: 400 | lh: 1.6 | ls: 0
- **body-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **body-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 500 | lh: 1.0 | ls: 0
- **button-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **caption**: font: Inter, system-ui, -apple-system, sans-serif | size: 12px | weight: 500 | lh: 1.4 | ls: 0.5px
- **caption-uppercase**: font: Inter, system-ui, -apple-system, sans-serif | size: 11px | weight: 600 | lh: 1.3 | ls: 1px
- **micro**: font: Inter, system-ui, -apple-system, sans-serif | size: 10px | weight: 500 | lh: 1.3 | ls: 0
- **code**: font: JetBrains Mono, ui-monospace, monospace | size: 13px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **xxxl**: 32px
- **section**: 48px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 18px, height: 36px

### button-primary-hover
backgroundColor: {colors.primary-hover}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 18px, height: 36px, border: 1px solid {colors.hairline}

### button-primary-lg
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-lg}, rounded: {rounded.md}, padding: 10px 24px, height: 42px

### hex-space
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 20px, border: 1px solid {colors.hairline}

### hex-space-hover
borderColor: {colors.accent-blue}, shadow: 0 0 15px rgba(56, 189, 248, 0.1)

### hex-space-title
textColor: {colors.accent-blue}, typography: {typography.caption-uppercase}, borderBottom: 1px solid {colors.hairline}, marginBottom: 12px, paddingBottom: 8px

### metric-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.headline}, rounded: {rounded.lg}, padding: 20px

### metric-card-hover
borderColor: {colors.accent-blue}, transform: translateY(-2px), shadow: 0 4px 20px rgba(56, 189, 248, 0.15)

### status-online
textColor: {colors.green}, textShadow: 0 0 8px rgba(34, 197, 94, 0.3)

### status-offline
textColor: {colors.ink-muted}

### event-dot
width: 8px, height: 8px, rounded: {rounded.full}, backgroundColor: {colors.accent-blue}, animation: pulse 2s infinite

### badge-cost
backgroundColor: {colors.gold-soft}, textColor: {colors.primary-active}, typography: {typography.micro}, rounded: {rounded.sm}, padding: 1px 6px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 12px, border: 1px solid {colors.hairline}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, height: 56px, borderBottom: 1px solid {colors.hairline}

### tab-active
textColor: {colors.accent-blue}, borderBottom: 2px solid {colors.accent-blue}

### tab-default
textColor: {colors.ink-muted}
', '["design-brand", "baize-console", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (42, 'design_brand', 'binance', 'design_system', '品牌设计规范 — binance', '# 品牌设计规范: Binance

A confident financial-platform interface anchored on a deep near-black canvas, where Binance''s iconic yellow (#FCD535) carries every primary CTA, brand accent, and value-claim moment. Type runs Binance''s custom BinanceNova / BinancePlex stack at modest weights — the system trusts size and yellow voltage over bold weight. Marketing and product surfaces default to the dark theme; transactional surfaces (buy crypto, deposit, exchange) flip to a light theme that shares the same yellow CTAs and gray-blue hairlines. Trading green (up) and red (down) accents thread through both modes for price-direction signals.

## 颜色体系 (Colors)

- **primary**: #fcd535
- **primary-active**: #f0b90b
- **primary-disabled**: #3a3a1f
- **ink**: #181a20
- **body**: #eaecef
- **body-on-light**: #181a20
- **muted**: #707a8a
- **muted-strong**: #929aa5
- **hairline-on-light**: #eaecef
- **hairline-on-dark**: #2b3139
- **border-strong**: #cdd1d6
- **canvas-light**: #ffffff
- **canvas-dark**: #0b0e11
- **surface-card-dark**: #1e2329
- **surface-elevated-dark**: #2b3139
- **surface-soft-light**: #fafafa
- **surface-strong-light**: #f5f5f5
- **on-primary**: #181a20
- **on-dark**: #ffffff
- **trading-up**: #0ecb81
- **trading-down**: #f6465d
- **accent-turquoise**: #2dbdb6
- **info**: #3b82f6
- **info-ring**: #3b82f6

## 排版体系 (Typography)

- **hero-display**: font: BinanceNova, -apple-system, BlinkMacSystemFont, sans-serif | size: 64px | weight: 700 | lh: 1.1 | ls: -1px
- **display-lg**: font: BinanceNova, sans-serif | size: 48px | weight: 700 | lh: 1.1 | ls: -0.5px
- **display-md**: font: BinanceNova, sans-serif | size: 40px | weight: 600 | lh: 1.15 | ls: -0.3px
- **display-sm**: font: BinanceNova, sans-serif | size: 32px | weight: 600 | lh: 1.2 | ls: 0
- **title-lg**: font: BinanceNova, sans-serif | size: 24px | weight: 600 | lh: 1.3 | ls: 0
- **title-md**: font: BinanceNova, sans-serif | size: 20px | weight: 600 | lh: 1.35 | ls: 0
- **title-sm**: font: BinanceNova, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **number-display**: font: BinancePlex, BinanceNova, sans-serif | size: 40px | weight: 700 | lh: 1.1 | ls: -0.3px
- **number-md**: font: BinancePlex, BinanceNova, sans-serif | size: 16px | weight: 500 | lh: 1.4 | ls: 0
- **number-sm**: font: BinancePlex, BinanceNova, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0
- **body-md**: font: BinanceNova, sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: BinanceNova, sans-serif | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: BinanceNova, sans-serif | size: 12px | weight: 500 | lh: 1.4 | ls: 0
- **button**: font: BinanceNova, sans-serif | size: 14px | weight: 600 | lh: 1 | ls: 0
- **nav-link**: font: BinanceNova, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 80px

## 圆角体系 (Border Radius)

- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **lg**: 8px
- **xl**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 24px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.md}

### button-primary-pill
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 14px 32px

### button-secondary-on-dark
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 24px

### button-secondary-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 24px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.button}

### button-trading-up
backgroundColor: {colors.trading-up}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.sm}, padding: 8px 20px

### button-trading-down
backgroundColor: {colors.trading-down}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.sm}, padding: 8px 20px

### button-subscribe
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.sm}, padding: 6px 16px, height: 28px

### text-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-md}

### top-nav-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 64px

### top-nav-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### hero-band-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.hero-display}, padding: 80px

### stat-callout-card
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.number-display}

### trust-badge
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.title-sm}, rounded: {rounded.lg}, padding: 16px 20px

### markets-table-card
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 24px

### markets-row
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.number-md}, padding: 12px 0

### price-up-cell
backgroundColor: transparent, textColor: {colors.trading-up}, typography: {typography.number-md}

### price-down-cell
backgroundColor: transparent, textColor: {colors.trading-down}, typography: {typography.number-md}

### search-input-on-dark
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 10px 16px, height: 40px

### text-input-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 16px, height: 40px

### funds-safu-band
backgroundColor: {colors.canvas-dark}, textColor: {colors.primary}, typography: {typography.display-lg}, padding: 80px

### feature-photo-card
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, rounded: {rounded.xl}

### qr-promo-card
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### faq-row
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.title-sm}, rounded: {rounded.md}, padding: 20px 0

### cta-band-dark
backgroundColor: {colors.surface-card-dark}, textColor: {colors.on-dark}, typography: {typography.display-sm}, rounded: {rounded.xl}, padding: 48px

### arena-hero-gradient
backgroundColor: {colors.canvas-dark}, textColor: {colors.primary}, typography: {typography.display-lg}, padding: 80px

### cookie-consent-card
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 16px

### buy-crypto-amount-card
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.number-display}, rounded: {rounded.lg}, padding: 24px

### steps-card
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.title-sm}, rounded: {rounded.lg}, padding: 24px

### price-chart-card
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### conversion-cell
backgroundColor: transparent, textColor: {colors.body-on-light}, typography: {typography.body-md}

### trader-row
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.body-md}, padding: 12px 0

### footer-light
backgroundColor: {colors.surface-soft-light}, textColor: {colors.body-on-light}, typography: {typography.body-md}, padding: 64px
', '["design-brand", "binance", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (43, 'design_brand', 'bmw', 'design_system', '品牌设计规范 — bmw', '# 品牌设计规范: BMW

BMW''s corporate site — distinct from BMW M''s motorsport-bombastic variant, this is a measured and settled corporate-automotive interface. On a light (cream-tinted white) canvas, BMW corporate blue (#1c69d4) carries every primary CTA; dark navy hero bands frame model photography. BMW Type Next Latin sets the entire hierarchy on two weights — heavy 700 display and Light 300 body. Configuration and reservation flows ride a card-based 4-up grid, where each card holds a model render, a name, and a "Learn More" link.

## 颜色体系 (Colors)

- **primary**: #1c69d4
- **primary-active**: #0653b6
- **primary-disabled**: #d6d6d6
- **ink**: #262626
- **body**: #3c3c3c
- **body-strong**: #1a1a1a
- **muted**: #6b6b6b
- **muted-soft**: #9a9a9a
- **hairline**: #e6e6e6
- **hairline-strong**: #cccccc
- **canvas**: #ffffff
- **surface-soft**: #f7f7f7
- **surface-card**: #fafafa
- **surface-strong**: #ebebeb
- **surface-dark**: #1a2129
- **surface-dark-elevated**: #262e38
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #bbbbbb
- **m-blue-light**: #0066b1
- **m-blue-dark**: #1c69d4
- **m-red**: #e22718
- **success**: #22c55e
- **warning**: #f59e0b
- **error**: #dc2626

## 排版体系 (Typography)

- **display-xl**: font: ''BMW Type Next Latin'', system-ui, -apple-system, BlinkMacSystemFont, ''Segoe UI'', Roboto, sans-serif | size: 64px | weight: 700 | lh: 1.05 | ls: 0
- **display-lg**: font: ''BMW Type Next Latin'', sans-serif | size: 48px | weight: 700 | lh: 1.1 | ls: 0
- **display-md**: font: ''BMW Type Next Latin'', sans-serif | size: 32px | weight: 700 | lh: 1.15 | ls: 0
- **display-sm**: font: ''BMW Type Next Latin'', sans-serif | size: 24px | weight: 700 | lh: 1.25 | ls: 0
- **title-lg**: font: ''BMW Type Next Latin'', sans-serif | size: 20px | weight: 700 | lh: 1.3 | ls: 0
- **title-md**: font: ''BMW Type Next Latin'', sans-serif | size: 18px | weight: 700 | lh: 1.4 | ls: 0
- **title-sm**: font: ''BMW Type Next Latin'', sans-serif | size: 16px | weight: 700 | lh: 1.4 | ls: 0
- **body-md**: font: ''BMW Type Next Latin'', sans-serif | size: 16px | weight: 300 | lh: 1.55 | ls: 0
- **body-sm**: font: ''BMW Type Next Latin'', sans-serif | size: 14px | weight: 300 | lh: 1.55 | ls: 0
- **caption**: font: ''BMW Type Next Latin'', sans-serif | size: 12px | weight: 400 | lh: 1.4 | ls: 0.5px
- **label-uppercase**: font: ''BMW Type Next Latin'', sans-serif | size: 13px | weight: 700 | lh: 1.3 | ls: 1.5px | transform: uppercase
- **button**: font: ''BMW Type Next Latin'', sans-serif | size: 14px | weight: 700 | lh: 1.0 | ls: 0.5px
- **nav-link**: font: ''BMW Type Next Latin'', sans-serif | size: 14px | weight: 400 | lh: 1.4 | ls: 0.3px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 80px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 4px
- **md**: 8px
- **lg**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 14px 32px, height: 48px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.none}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.none}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.none}, padding: 13px 31px, height: 48px

### button-secondary-on-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.none}, padding: 13px 31px

### button-text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.label-uppercase}

### text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}

### hero-band-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-xl}, padding: 80px

### hero-photo-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 80px

### model-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### model-card-photo
backgroundColor: {colors.surface-card}, rounded: {rounded.none}

### feature-photo-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### spec-cell
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.display-sm}, rounded: {rounded.none}, padding: 24px

### inventory-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-sm}, rounded: {rounded.none}, padding: 16px

### filter-chip
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.none}, padding: 8px 14px

### filter-chip-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, rounded: {rounded.none}

### configurator-option-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 16px 24px

### configurator-option-tile-selected
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.none}, padding: 15px 23px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 14px 16px, height: 48px

### cookie-consent-card
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 24px

### category-tab
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.label-uppercase}, rounded: {rounded.none}

### category-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.label-uppercase}, rounded: {rounded.none}

### m-stripe-divider
backgroundColor: transparent, rounded: {rounded.none}

### cta-band-photo
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-md}, padding: 80px

### footer
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "bmw", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (44, 'design_brand', 'bmw-m', 'design_system', '品牌设计规范 — bmw-m', '# 品牌设计规范: BMW M

A motorsport-engineering interface anchored on a near-black canvas with white BMW Type Next Latin display headlines in confident UPPERCASE. The brand carries no decorative voltage — its energy comes from full-bleed automotive photography (cars on tracks, driver-cockpit shots, carbon-fiber detail) and the iconic M tricolor stripe (light blue → dark blue → red) used sparingly as a brand signature on logos, dividers, and motorsport chrome. Type stays light to medium weight to feel European-engineered, never American-bombastic.

## 颜色体系 (Colors)

- **primary**: #ffffff
- **ink**: #ffffff
- **body**: #bbbbbb
- **body-strong**: #e6e6e6
- **muted**: #7e7e7e
- **hairline**: #3c3c3c
- **hairline-strong**: #262626
- **canvas**: #000000
- **surface-card**: #1a1a1a
- **surface-elevated**: #262626
- **surface-soft**: #0d0d0d
- **on-primary**: #000000
- **on-dark**: #ffffff
- **m-blue-light**: #0066b1
- **m-blue-dark**: #1c69d4
- **m-red**: #e22718
- **bmw-blue**: #1c69d4
- **electric-blue**: #0653b6
- **carbon-gray**: #2b2b2b
- **warning**: #f4b400
- **success**: #0fa336

## 排版体系 (Typography)

- **display-xl**: font: BMWTypeNextLatin, sans-serif | size: 80px | weight: 700 | lh: 1 | ls: 0
- **display-lg**: font: BMWTypeNextLatin, sans-serif | size: 56px | weight: 700 | lh: 1.05 | ls: 0
- **display-md**: font: BMWTypeNextLatin, sans-serif | size: 40px | weight: 700 | lh: 1.1 | ls: 0
- **display-sm**: font: BMWTypeNextLatin, sans-serif | size: 32px | weight: 700 | lh: 1.15 | ls: 0
- **title-lg**: font: BMWTypeNextLatin, sans-serif | size: 24px | weight: 700 | lh: 1.3 | ls: 0
- **title-md**: font: BMWTypeNextLatin, sans-serif | size: 20px | weight: 400 | lh: 1.4 | ls: 0
- **title-sm**: font: BMWTypeNextLatin, sans-serif | size: 18px | weight: 400 | lh: 1.4 | ls: 0
- **label-uppercase**: font: BMWTypeNextLatin, sans-serif | size: 14px | weight: 700 | lh: 1.3 | ls: 1.5px
- **body-md**: font: BMWTypeNextLatin Light, BMWTypeNextLatin, sans-serif | size: 16px | weight: 300 | lh: 1.5 | ls: 0
- **body-sm**: font: BMWTypeNextLatin Light, sans-serif | size: 14px | weight: 300 | lh: 1.5 | ls: 0
- **caption**: font: BMWTypeNextLatin, sans-serif | size: 12px | weight: 400 | lh: 1.4 | ls: 0.5px
- **button**: font: BMWTypeNextLatin, sans-serif | size: 14px | weight: 700 | lh: 1 | ls: 1.5px
- **nav-link**: font: BMWTypeNextLatin, sans-serif | size: 14px | weight: 400 | lh: 1.4 | ls: 0.5px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 40px
- **xxl**: 64px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.none}, padding: 16px 32px, height: 48px

### button-primary-outline
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.none}, padding: 16px 32px, height: 48px

### button-on-light
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.none}, padding: 16px 32px

### button-icon
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, rounded: {rounded.full}, size: 48px

### text-link
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.label-uppercase}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 64px

### hero-photo-band
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-xl}, padding: 96px

### m-stripe-divider
backgroundColor: transparent, textColor: {colors.on-dark}, height: 4px

### feature-photo-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### model-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.title-lg}, rounded: {rounded.none}, padding: 24px

### magazine-article-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### spec-cell
backgroundColor: {colors.surface-soft}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 24px

### cookie-consent-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 24px

### category-tab
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.label-uppercase}, padding: 12px 0

### category-tab-active
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.label-uppercase}, padding: 12px 0

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 12px 16px, height: 48px

### chatbot-launcher
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### cta-band-photo
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-md}, padding: 80px

### motorsport-photo-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.none}

### carousel-arrow
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, rounded: {rounded.full}, size: 48px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "bmw-m", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (45, 'design_brand', 'bugatti', 'design_system', '品牌设计规范 — bugatti', '# 品牌设计规范: Bugatti

An austere luxury-automotive interface that uses near-pure black canvas, white uppercase letterspaced display, and full-bleed automotive photography as the only voltage. The system runs three custom Bugatti typefaces — Bugatti Display, Bugatti Text Regular, and Bugatti Monospace — and combines them at modest weights with wide tracking to feel European-engineered, hyper-minimal, and quietly expensive. There is no accent color, no decorative element, no chrome — only photography, typography, and the brand wordmark.

## 颜色体系 (Colors)

- **primary**: #ffffff
- **ink**: #ffffff
- **body**: #cccccc
- **body-strong**: #e6e6e6
- **muted**: #999999
- **muted-soft**: #666666
- **hairline**: #262626
- **hairline-strong**: #3a3a3a
- **canvas**: #000000
- **surface-soft**: #0d0d0d
- **surface-card**: #141414
- **surface-elevated**: #1f1f1f
- **on-primary**: #000000
- **on-dark**: #ffffff
- **on-photo**: #ffffff
- **link**: #c3d9f3
- **warning**: #d4a017
- **success**: #5fa657

## 排版体系 (Typography)

- **display-xl**: font: Bugatti Display, sans-serif | size: 64px | weight: 400 | lh: 1.1 | ls: 4px
- **display-lg**: font: Bugatti Display, sans-serif | size: 48px | weight: 400 | lh: 1.15 | ls: 3px
- **display-md**: font: Bugatti Display, sans-serif | size: 32px | weight: 400 | lh: 1.2 | ls: 2px
- **display-sm**: font: Bugatti Display, sans-serif | size: 24px | weight: 400 | lh: 1.3 | ls: 1.5px
- **wordmark**: font: Bugatti Display, serif | size: 14px | weight: 400 | lh: 1 | ls: 6px
- **title-md**: font: Bugatti Display, sans-serif | size: 20px | weight: 400 | lh: 1.3 | ls: 1px
- **title-sm**: font: Bugatti Display, sans-serif | size: 16px | weight: 400 | lh: 1.3 | ls: 1.5px
- **caption-uppercase**: font: Bugatti Monospace, ui-monospace, monospace | size: 11px | weight: 400 | lh: 1.4 | ls: 2px
- **body-md**: font: Bugatti Text Regular, serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: Bugatti Text Regular, serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: Bugatti Monospace, ui-monospace, monospace | size: 14px | weight: 400 | lh: 1 | ls: 2.5px
- **nav-link**: font: Bugatti Monospace, ui-monospace, monospace | size: 12px | weight: 400 | lh: 1.4 | ls: 2px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 40px
- **xxl**: 64px
- **section**: 120px

## 圆角体系 (Border Radius)

- **none**: 0px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.pill}, padding: 14px 32px, height: 44px

### button-icon
backgroundColor: transparent, textColor: {colors.on-dark}, rounded: {rounded.full}, size: 40px

### text-link
backgroundColor: transparent, textColor: {colors.link}, typography: {typography.button}

### top-nav
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 56px

### wordmark-display
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.wordmark}

### hero-photo-band
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-xl}, padding: 96px

### caption-overlay
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.caption-uppercase}

### career-callout-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 16px, width: 320px

### model-photo-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-md}, rounded: {rounded.none}

### newsroom-article-card
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### career-listing-row
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.title-md}, padding: 24px 0

### text-input
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 12px 0, height: 44px

### spec-cell
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.title-md}, padding: 24px 0

### date-pill
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.caption-uppercase}

### category-tag
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.caption-uppercase}

### cta-band-photo
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-md}, padding: 80px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "bugatti", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (46, 'design_brand', 'cal', 'design_system', '品牌设计规范 — cal', '# 品牌设计规范: Cal.com

A clean, calendar-software-first interface anchored on white canvas with black primary CTAs and custom Cal Sans display typography. The system reads as friendly modern SaaS — generous whitespace, soft-rounded cards (~12px), product UI fragments shown directly inside cards, and a dark navy footer that visually closes long-scroll pages. Brand voltage comes from the Cal Sans display headline (a custom geometric face) and from product UI artifacts shown in-card rather than from accent colors.

## 颜色体系 (Colors)

- **primary**: #111111
- **primary-active**: #242424
- **primary-disabled**: #e5e7eb
- **ink**: #111111
- **body**: #374151
- **muted**: #6b7280
- **muted-soft**: #898989
- **hairline**: #e5e7eb
- **hairline-soft**: #f3f4f6
- **canvas**: #ffffff
- **surface-soft**: #f8f9fa
- **surface-card**: #f5f5f5
- **surface-strong**: #e5e7eb
- **surface-dark**: #101010
- **surface-dark-elevated**: #1a1a1a
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #a1a1aa
- **brand-accent**: #3b82f6
- **success**: #10b981
- **warning**: #f59e0b
- **error**: #ef4444
- **badge-orange**: #fb923c
- **badge-pink**: #ec4899
- **badge-violet**: #8b5cf6
- **badge-emerald**: #34d399

## 排版体系 (Typography)

- **display-xl**: font: Cal Sans, Inter, sans-serif | size: 64px | weight: 600 | lh: 1.05 | ls: -2px
- **display-lg**: font: Cal Sans, Inter, sans-serif | size: 48px | weight: 600 | lh: 1.1 | ls: -1.5px
- **display-md**: font: Cal Sans, Inter, sans-serif | size: 36px | weight: 600 | lh: 1.15 | ls: -1px
- **display-sm**: font: Cal Sans, Inter, sans-serif | size: 28px | weight: 600 | lh: 1.2 | ls: -0.5px
- **title-lg**: font: Inter, sans-serif | size: 22px | weight: 600 | lh: 1.3 | ls: -0.3px
- **title-md**: font: Inter, sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: Inter, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: Inter, sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: Inter, sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: Inter, sans-serif | size: 13px | weight: 500 | lh: 1.4 | ls: 0
- **code**: font: JetBrains Mono, ui-monospace, monospace | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: Inter, sans-serif | size: 14px | weight: 600 | lh: 1 | ls: 0
- **nav-link**: font: Inter, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px

### button-text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### nav-pill-group
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.nav-link}, rounded: {rounded.pill}, padding: 6px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-xl}, padding: 96px

### hero-app-mockup-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.xl}

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### feature-icon-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-sm}, rounded: {rounded.lg}, padding: 24px

### product-mockup-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: 24px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### pricing-tier-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-card-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 14px, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.md}

### category-tab
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.nav-link}, padding: 8px 14px, rounded: {rounded.md}

### category-tab-active
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, rounded: {rounded.md}

### avatar-circle
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px

### badge-pill
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 4px 12px

### rating-stars
backgroundColor: transparent, textColor: {colors.badge-orange}, typography: {typography.caption}

### cta-band-light
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.display-sm}, rounded: {rounded.lg}, padding: 48px

### footer
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark-soft}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "cal", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (47, 'design_brand', 'claude', 'design_system', '品牌设计规范 — claude', '# 品牌设计规范: Claude

A warm-canvas editorial interface for Anthropic''s Claude product. The system anchors on a tinted cream canvas with serif display headlines, warm coral CTAs, and dark navy product surfaces (code editor mockups, model showcase cards). Brand voltage comes from the cream/coral pairing — deliberately warm and humanist where most AI brands use cool blue + slate. Type voice runs a slab-serif display ("Copernicus" / Tiempos Headline) for h1/h2 and a humanist sans for body. The signature Anthropic black-radial-spike mark anchors the wordmark.

## 颜色体系 (Colors)

- **primary**: #cc785c
- **primary-active**: #a9583e
- **primary-disabled**: #e6dfd8
- **ink**: #141413
- **body**: #3d3d3a
- **body-strong**: #252523
- **muted**: #6c6a64
- **muted-soft**: #8e8b82
- **hairline**: #e6dfd8
- **hairline-soft**: #ebe6df
- **canvas**: #faf9f5
- **surface-soft**: #f5f0e8
- **surface-card**: #efe9de
- **surface-cream-strong**: #e8e0d2
- **surface-dark**: #181715
- **surface-dark-elevated**: #252320
- **surface-dark-soft**: #1f1e1b
- **on-primary**: #ffffff
- **on-dark**: #faf9f5
- **on-dark-soft**: #a09d96
- **accent-teal**: #5db8a6
- **accent-amber**: #e8a55a
- **success**: #5db872
- **warning**: #d4a017
- **error**: #c64545

## 排版体系 (Typography)

- **display-xl**: font: Copernicus, Tiempos Headline, serif | size: 64px | weight: 400 | lh: 1.05 | ls: -1.5px
- **display-lg**: font: Copernicus, Tiempos Headline, serif | size: 48px | weight: 400 | lh: 1.1 | ls: -1px
- **display-md**: font: Copernicus, Tiempos Headline, serif | size: 36px | weight: 400 | lh: 1.15 | ls: -0.5px
- **display-sm**: font: Copernicus, Tiempos Headline, serif | size: 28px | weight: 400 | lh: 1.2 | ls: -0.3px
- **title-lg**: font: StyreneB, Inter, sans-serif | size: 22px | weight: 500 | lh: 1.3 | ls: 0
- **title-md**: font: StyreneB, Inter, sans-serif | size: 18px | weight: 500 | lh: 1.4 | ls: 0
- **title-sm**: font: StyreneB, Inter, sans-serif | size: 16px | weight: 500 | lh: 1.4 | ls: 0
- **body-md**: font: StyreneB, Inter, sans-serif | size: 16px | weight: 400 | lh: 1.55 | ls: 0
- **body-sm**: font: StyreneB, Inter, sans-serif | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **caption**: font: StyreneB, Inter, sans-serif | size: 13px | weight: 500 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: StyreneB, Inter, sans-serif | size: 12px | weight: 500 | lh: 1.4 | ls: 1.5px
- **code**: font: JetBrains Mono, ui-monospace, monospace | size: 14px | weight: 400 | lh: 1.6 | ls: 0
- **button**: font: StyreneB, Inter, sans-serif | size: 14px | weight: 500 | lh: 1 | ls: 0
- **nav-link**: font: StyreneB, Inter, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-secondary-on-dark
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px

### button-text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px

### text-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-md}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-xl}, padding: 96px

### hero-illustration-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.xl}

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### product-mockup-card-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### code-window-card
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.code}, rounded: {rounded.lg}, padding: 24px

### model-comparison-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-card-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### callout-card-coral
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### connector-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-sm}, rounded: {rounded.lg}, padding: 20px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 14px, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.md}

### cookie-consent-card
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 24px

### category-tab
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.nav-link}, padding: 8px 14px, rounded: {rounded.md}

### category-tab-active
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.nav-link}, rounded: {rounded.md}

### badge-pill
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 4px 12px

### badge-coral
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 12px

### cta-band-coral
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.display-sm}, rounded: {rounded.lg}, padding: 64px

### cta-band-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-sm}, rounded: {rounded.lg}, padding: 64px

### footer
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark-soft}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "claude", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (48, 'design_brand', 'clay', 'design_system', '品牌设计规范 — clay', '# 品牌设计规范: Clay

A vibrant claymation-meets-data interface for Clay.com (GTM data-orchestration platform). Anchors on white canvas with dark-navy primary CTAs, custom rounded display type, and saturated single-color feature cards — hot pink, deep teal, lavender, peach, ochre — that punctuate long-scroll explainer pages. Brand voltage comes from 3D-rendered claymation illustrations (mountains, characters, mascots) used as full-bleed hero artifacts and the bright multi-color card surfaces showing product UI fragments.

## 颜色体系 (Colors)

- **primary**: #0a0a0a
- **primary-active**: #1f1f1f
- **primary-disabled**: #e5e5e5
- **ink**: #0a0a0a
- **body**: #3a3a3a
- **body-strong**: #1a1a1a
- **muted**: #6a6a6a
- **muted-soft**: #9a9a9a
- **hairline**: #e5e5e5
- **hairline-soft**: #f0f0f0
- **canvas**: #fffaf0
- **surface-soft**: #faf5e8
- **surface-card**: #f5f0e0
- **surface-strong**: #ebe6d6
- **surface-dark**: #0a1a1a
- **surface-dark-elevated**: #1a2a2a
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #a0a0a0
- **brand-pink**: #ff4d8b
- **brand-teal**: #1a3a3a
- **brand-lavender**: #b8a4ed
- **brand-peach**: #ffb084
- **brand-ochre**: #e8b94a
- **brand-mint**: #a4d4c5
- **brand-coral**: #ff6b5a
- **success**: #22c55e
- **warning**: #f59e0b
- **error**: #ef4444

## 排版体系 (Typography)

- **display-xl**: font: Plain Black, Inter, sans-serif | size: 72px | weight: 500 | lh: 1 | ls: -2.5px
- **display-lg**: font: Plain Black, Inter, sans-serif | size: 56px | weight: 500 | lh: 1.05 | ls: -2px
- **display-md**: font: Plain Black, Inter, sans-serif | size: 40px | weight: 500 | lh: 1.1 | ls: -1px
- **display-sm**: font: Plain Black, Inter, sans-serif | size: 32px | weight: 500 | lh: 1.15 | ls: -0.5px
- **title-lg**: font: Inter, sans-serif | size: 24px | weight: 600 | lh: 1.3 | ls: -0.3px
- **title-md**: font: Inter, sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: Inter, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: Inter, sans-serif | size: 16px | weight: 400 | lh: 1.55 | ls: 0
- **body-sm**: font: Inter, sans-serif | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **caption**: font: Inter, sans-serif | size: 13px | weight: 500 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: Inter, sans-serif | size: 12px | weight: 600 | lh: 1.4 | ls: 1.5px
- **button**: font: Inter, sans-serif | size: 14px | weight: 600 | lh: 1 | ls: 0
- **nav-link**: font: Inter, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 6px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 44px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 44px

### button-on-color
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 44px

### button-text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### text-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-xl}, padding: 96px

### hero-illustration-card
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, rounded: {rounded.xl}

### feature-card-pink
backgroundColor: {colors.brand-pink}, textColor: {colors.on-primary}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### feature-card-teal
backgroundColor: {colors.brand-teal}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### feature-card-lavender
backgroundColor: {colors.brand-lavender}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### feature-card-peach
backgroundColor: {colors.brand-peach}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### feature-card-ochre
backgroundColor: {colors.brand-ochre}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### feature-card-cream
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### product-mockup-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### pricing-tier-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-card-featured
backgroundColor: {colors.brand-teal}, textColor: {colors.on-dark}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 12px 16px, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.md}

### category-tab
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.nav-link}, rounded: {rounded.pill}, padding: 8px 16px

### category-tab-active
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.nav-link}, rounded: {rounded.pill}

### badge-pill
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 4px 12px

### expert-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### cta-band-illustrated
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.display-md}, rounded: {rounded.xl}, padding: 80px

### footer
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 80px
', '["design-brand", "clay", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (49, 'design_brand', 'clickhouse', 'design_system', '品牌设计规范 — clickhouse', '# 品牌设计规范: ClickHouse

A high-performance database interface anchored on near-pure black canvas with electric yellow as the brand voltage. White typography in confident sans, yellow CTAs, and yellow-text stat numbers carry the brand voice across every page. Code blocks and product UI fragments embed directly in dark cards. The yellow + black pairing (and yellow used scarcely as accent) is the system''s signature — brand identity without atmospheric decoration.

## 颜色体系 (Colors)

- **primary**: #faff69
- **primary-active**: #e6eb52
- **primary-disabled**: #3a3a1f
- **ink**: #ffffff
- **body**: #cccccc
- **body-strong**: #e6e6e6
- **muted**: #888888
- **muted-soft**: #5a5a5a
- **hairline**: #2a2a2a
- **hairline-strong**: #3a3a3a
- **canvas**: #0a0a0a
- **surface-soft**: #121212
- **surface-card**: #1a1a1a
- **surface-elevated**: #242424
- **surface-yellow-band**: #faff69
- **on-primary**: #0a0a0a
- **on-dark**: #ffffff
- **on-yellow**: #0a0a0a
- **accent-emerald**: #22c55e
- **accent-rose**: #ef4444
- **accent-blue**: #3b82f6
- **success**: #22c55e
- **warning**: #f59e0b
- **error**: #ef4444

## 排版体系 (Typography)

- **display-xl**: font: Inter, sans-serif | size: 72px | weight: 700 | lh: 1.05 | ls: -2.5px
- **display-lg**: font: Inter, sans-serif | size: 56px | weight: 700 | lh: 1.1 | ls: -2px
- **display-md**: font: Inter, sans-serif | size: 40px | weight: 700 | lh: 1.15 | ls: -1.5px
- **display-sm**: font: Inter, sans-serif | size: 32px | weight: 700 | lh: 1.2 | ls: -1px
- **title-lg**: font: Inter, sans-serif | size: 24px | weight: 700 | lh: 1.3 | ls: -0.3px
- **title-md**: font: Inter, sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: Inter, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **stat-display**: font: Inter, sans-serif | size: 56px | weight: 700 | lh: 1.0 | ls: -1.5px
- **body-md**: font: Inter, sans-serif | size: 16px | weight: 400 | lh: 1.55 | ls: 0
- **body-sm**: font: Inter, sans-serif | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **caption**: font: Inter, sans-serif | size: 13px | weight: 500 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: Inter, sans-serif | size: 12px | weight: 600 | lh: 1.4 | ls: 1.5px
- **code**: font: JetBrains Mono, ui-monospace, monospace | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **button**: font: Inter, sans-serif | size: 14px | weight: 600 | lh: 1 | ls: 0
- **nav-link**: font: Inter, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.muted}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 40px

### button-text-link
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button}

### button-icon-circular
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, rounded: {rounded.full}, size: 36px

### text-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-md}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 64px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-xl}, padding: 96px

### hero-stat-card
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.stat-display}

### feature-card-yellow
backgroundColor: {colors.surface-yellow-band}, textColor: {colors.on-yellow}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### feature-card-dark
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 32px

### code-window-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.code}, rounded: {rounded.lg}, padding: 24px

### product-mockup-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### pricing-tier-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-card-featured
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.title-lg}, rounded: {rounded.lg}, padding: 32px

### stat-callout
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.stat-display}

### cta-band-yellow
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 64px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 14px, height: 40px

### text-input-focused
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, rounded: {rounded.md}

### category-tab
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.nav-link}, rounded: {rounded.md}, padding: 8px 14px

### category-tab-active
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.nav-link}, rounded: {rounded.md}

### badge-pill
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 4px 12px

### badge-yellow
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 12px

### events-card
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### customer-logo-strip
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.body-md}, padding: 32px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.body-sm}, padding: 64px
', '["design-brand", "clickhouse", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (50, 'design_brand', 'cohere', 'design_system', '品牌设计规范 — cohere', '# 品牌设计规范: Cohere

Cohere''s 2026 web system is a controlled enterprise AI interface built from stark white editorial space, deep green-black product bands, soft mineral surfaces, rounded media cards, and a distinctive type split between monospaced-feeling display headlines and precise Unica77 UI text.

## 颜色体系 (Colors)

- **primary**: #17171c
- **cohere-black**: #000000
- **ink**: #212121
- **deep-green**: #003c33
- **dark-navy**: #071829
- **canvas**: #ffffff
- **soft-stone**: #eeece7
- **pale-green**: #edfce9
- **pale-blue**: #f1f5ff
- **hairline**: #d9d9dd
- **border-light**: #e5e7eb
- **card-border**: #f2f2f2
- **muted**: #93939f
- **slate**: #75758a
- **body-muted**: #616161
- **action-blue**: #1863dc
- **focus-blue**: #4c6ee6
- **coral**: #ff7759
- **coral-soft**: #ffad9b
- **form-focus**: #9b60aa
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **error**: #b30000

## 排版体系 (Typography)

- **hero-display**: font: CohereText | size: 96px | weight: 400 | lh: 1 | ls: -1.92px
- **product-display**: font: CohereText | size: 72px | weight: 400 | lh: 1 | ls: -1.44px
- **section-display**: font: Unica77 Cohere Web | size: 60px | weight: 400 | lh: 1 | ls: -1.2px
- **section-heading**: font: Unica77 Cohere Web | size: 48px | weight: 400 | lh: 1.2 | ls: -0.48px
- **card-heading**: font: Unica77 Cohere Web | size: 32px | weight: 400 | lh: 1.2 | ls: -0.32px
- **feature-heading**: font: Unica77 Cohere Web | size: 24px | weight: 400 | lh: 1.3 | ls: 0
- **body-large**: font: Unica77 Cohere Web | size: 18px | weight: 400 | lh: 1.4 | ls: 0
- **body**: font: Unica77 Cohere Web | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: Unica77 Cohere Web | size: 14px | weight: 500 | lh: 1.71 | ls: 0
- **caption**: font: Unica77 Cohere Web | size: 14px | weight: 400 | lh: 1.4 | ls: 0
- **mono-label**: font: CohereMono | size: 14px | weight: 400 | lh: 1.4 | ls: 0.28px
- **micro**: font: Unica77 Cohere Web | size: 12px | weight: 400 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 6px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 80px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 22px
- **xl**: 30px
- **pill**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 12px 24px

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xs}, padding: 8px 0

### button-pill-outline
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.button}, rounded: {rounded.xl}, padding: 6px 12px

### announcement-bar
backgroundColor: {colors.cohere-black}, textColor: {colors.on-dark}, typography: {typography.micro}, height: 36px

### hero-photo-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}

### agent-console-card
backgroundColor: {colors.primary}, textColor: {colors.on-dark}, rounded: {rounded.sm}, padding: 24px

### trust-logo-strip
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}

### capability-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xs}, padding: 24px

### dark-feature-band
backgroundColor: {colors.deep-green}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: 80px

### product-card
backgroundColor: {colors.soft-stone}, textColor: {colors.ink}, rounded: {rounded.sm}, padding: 32px

### blog-filter-chip
backgroundColor: transparent, textColor: {colors.coral}, typography: {typography.card-heading}, rounded: {rounded.sm}, padding: 8px 14px

### research-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-large}

### contact-form-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: 32px

### footer-newsletter
backgroundColor: {colors.primary}, textColor: {colors.on-dark}, typography: {typography.micro}
', '["design-brand", "cohere", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (51, 'design_brand', 'coinbase', 'design_system', '品牌设计规范 — coinbase', '# 品牌设计规范: Coinbase

An institutional-grade crypto exchange whose marketing surfaces read like a quietly-confident financial-services brand. The base canvas is pure white; Coinbase Blue (`#0052ff`) is the single brand voltage, used scarcely on primary CTAs, signature glyphs, and inline accent moments. Type runs Coinbase''s licensed CoinbaseDisplay (display) and CoinbaseSans (body) at modest weights — display sits at weight 400 not 700, signaling editorial calm rather than fintech-bombastic. Page rhythm rotates between bright white sections, soft gray elevation bands, and full-bleed dark editorial heroes (`#0a0b0d`) carrying product-ui mockup cards. Iconography is geometric and minimal; depth comes from card-on-card layering, never decorative shadows.

## 颜色体系 (Colors)

- **primary**: #0052ff
- **primary-active**: #003ecc
- **primary-disabled**: #a8b8cc
- **ink**: #0a0b0d
- **body**: #5b616e
- **body-strong**: #0a0b0d
- **muted**: #7c828a
- **muted-soft**: #a8acb3
- **hairline**: #dee1e6
- **hairline-soft**: #eef0f3
- **canvas**: #ffffff
- **surface-soft**: #f7f7f7
- **surface-card**: #ffffff
- **surface-strong**: #eef0f3
- **surface-dark**: #0a0b0d
- **surface-dark-elevated**: #16181c
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #a8acb3
- **semantic-up**: #05b169
- **semantic-down**: #cf202f
- **accent-yellow**: #f4b000

## 排版体系 (Typography)

- **display-mega**: font: ''Coinbase Display'', -apple-system, system-ui, ''Segoe UI'', Roboto, Helvetica, Arial, sans-serif | size: 80px | weight: 400 | lh: 1.0 | ls: -2px
- **display-xl**: font: ''Coinbase Display'', sans-serif | size: 64px | weight: 400 | lh: 1.0 | ls: -1.6px
- **display-lg**: font: ''Coinbase Display'', sans-serif | size: 52px | weight: 400 | lh: 1.0 | ls: -1.3px
- **display-md**: font: ''Coinbase Display'', sans-serif | size: 44px | weight: 400 | lh: 1.09 | ls: -1px
- **display-sm**: font: ''Coinbase Sans'', sans-serif | size: 36px | weight: 400 | lh: 1.11 | ls: -0.5px
- **title-lg**: font: ''Coinbase Sans'', sans-serif | size: 32px | weight: 400 | lh: 1.13 | ls: -0.4px
- **title-md**: font: ''Coinbase Sans'', sans-serif | size: 18px | weight: 600 | lh: 1.33 | ls: 0
- **title-sm**: font: ''Coinbase Sans'', sans-serif | size: 16px | weight: 600 | lh: 1.25 | ls: 0
- **body-md**: font: ''Coinbase Sans'', sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: ''Coinbase Sans'', sans-serif | size: 16px | weight: 700 | lh: 1.5 | ls: 0
- **body-sm**: font: ''Coinbase Sans'', sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: ''Coinbase Sans'', sans-serif | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **caption-strong**: font: ''Coinbase Sans'', sans-serif | size: 12px | weight: 600 | lh: 1.5 | ls: 0
- **number-display**: font: ''Coinbase Mono'', ''Coinbase Sans'', monospace | size: 18px | weight: 500 | lh: 1.4 | ls: 0
- **button**: font: ''Coinbase Sans'', sans-serif | size: 16px | weight: 600 | lh: 1.15 | ls: 0
- **nav-link**: font: ''Coinbase Sans'', sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **base**: 16px
- **md**: 20px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **pill**: 100px
- **full**: 9999px

## 组件定义 (Components)

### top-nav-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### top-nav-on-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 12px 20px, height: 44px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.pill}

### button-primary-disabled
backgroundColor: {colors.primary-disabled}, textColor: {colors.on-primary}, rounded: {rounded.pill}

### button-secondary-light
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 12px 20px, height: 44px

### button-secondary-dark
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.pill}, padding: 12px 20px, height: 44px

### button-outline-on-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button}, rounded: {rounded.pill}, padding: 11px 19px, height: 44px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.button}

### button-pill-cta
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 16px 32px, height: 56px

### hero-band-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-mega}, padding: 96px

### hero-band-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-mega}, padding: 96px

### product-ui-card-dark
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, rounded: {rounded.xl}, padding: 32px

### product-ui-card-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.xl}, padding: 32px

### feature-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 32px

### asset-row
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}, padding: 16px 0

### price-up-cell
backgroundColor: transparent, textColor: {colors.semantic-up}, typography: {typography.number-display}

### price-down-cell
backgroundColor: transparent, textColor: {colors.semantic-down}, typography: {typography.number-display}

### pricing-tier-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### cta-band-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-lg}, padding: 96px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 14px 16px, height: 48px

### search-input-pill
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 20px, height: 44px

### badge-pill
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.caption-strong}, rounded: {rounded.pill}, padding: 4px 12px

### asset-icon-circular
backgroundColor: {colors.surface-strong}, rounded: {rounded.full}, size: 32px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}

### legal-band
backgroundColor: {colors.canvas}, textColor: {colors.muted}, typography: {typography.caption}
', '["design-brand", "coinbase", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (52, 'design_brand', 'composio', 'design_system', '品牌设计规范 — composio', '# 品牌设计规范: Composio

A developer-tools brand for AI-agent tool integration whose marketing surfaces lean into a dark, technical aesthetic with a single deep-electric-blue voltage (`#0007cd`). The page floor is near-black (`#0f0f0f`); cards float above on subtle gray-tinted surfaces. abcDiatype carries display and body in a single sans family with weights 400-600. The brand''s strongest visual signature is a four-pane terminal-style mockup (a 2×2 grid of dark code/output panels) with a central blue spotlight glow — used as the homepage hero anchor.

## 颜色体系 (Colors)

- **primary**: #0007cd
- **primary-active**: #0005a3
- **primary-glow**: #1a26ff
- **ink**: #ffffff
- **body**: #a8a8a8
- **body-strong**: #ffffff
- **muted**: #888888
- **muted-soft**: #666666
- **hairline**: #222222
- **hairline-soft**: #1a1a1a
- **hairline-strong**: #333333
- **canvas**: #0f0f0f
- **canvas-deep**: #000000
- **surface-card**: #181818
- **surface-card-elevated**: #222222
- **surface-strong**: #2a2a2a
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **accent-cyan**: #00d4ff
- **accent-violet**: #7b3aed
- **semantic-error**: #ff4d4d
- **semantic-success**: #33d17a

## 排版体系 (Typography)

- **display-mega**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 72px | weight: 500 | lh: 1.05 | ls: -2.16px
- **display-xl**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 56px | weight: 500 | lh: 1.05 | ls: -1.68px
- **display-lg**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 44px | weight: 500 | lh: 1.1 | ls: -1.32px
- **display-md**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 32px | weight: 500 | lh: 1.15 | ls: -0.96px
- **display-sm**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 24px | weight: 500 | lh: 1.25 | ls: -0.5px
- **title-md**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 13px | weight: 400 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 11px | weight: 600 | lh: 1.4 | ls: 0.88px | transform: uppercase
- **code**: font: ''JetBrains Mono'', ''Fira Code'', monospace | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **nav-link**: font: ''abcDiatype'', ui-sans-serif, system-ui, sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **base**: 16px
- **md**: 20px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### top-nav-dark
backgroundColor: {colors.canvas}, textColor: {colors.body-strong}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-secondary-dark
backgroundColor: {colors.surface-card-elevated}, textColor: {colors.body-strong}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px, height: 40px

### button-outline
backgroundColor: transparent, textColor: {colors.body-strong}, typography: {typography.button}, rounded: {rounded.md}, padding: 9px 17px, height: 40px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.button}

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.body-strong}, typography: {typography.display-mega}, padding: 96px

### terminal-mockup-grid
backgroundColor: {colors.canvas-deep}, textColor: {colors.body-strong}, typography: {typography.code}, rounded: {rounded.xl}, padding: 32px

### terminal-pane
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.code}, rounded: {rounded.lg}, padding: 20px

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 28px

### toolkit-card
backgroundColor: {colors.surface-card}, textColor: {colors.body-strong}, typography: {typography.title-sm}, rounded: {rounded.lg}, padding: 20px

### toolkit-icon
backgroundColor: {colors.surface-card-elevated}, rounded: {rounded.md}, size: 40px

### spotlight-glow-card
backgroundColor: {colors.surface-card}, textColor: {colors.body-strong}, typography: {typography.display-md}, rounded: {rounded.xl}, padding: 48px

### code-block
backgroundColor: {colors.canvas-deep}, textColor: {colors.body}, typography: {typography.code}, rounded: {rounded.lg}, padding: 20px

### badge-pill
backgroundColor: {colors.surface-card-elevated}, textColor: {colors.body-strong}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.body-strong}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 12px 16px, height: 44px

### search-input
backgroundColor: {colors.surface-card}, textColor: {colors.body-strong}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 16px, height: 40px

### cta-band-spotlight
backgroundColor: {colors.canvas}, textColor: {colors.body-strong}, typography: {typography.display-lg}, padding: 96px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### footer-dark
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}
', '["design-brand", "composio", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (53, 'design_brand', 'content-automation-factory', 'design_system', '品牌设计规范 — content-automation-factory', '# 品牌设计规范: 内容自动化工厂 (Content Automation Factory)

A light-themed content management portal on a warm gray canvas (#f0f2f5) with deep navy ink (#1a1a2e) and a clean white card system. The atmosphere is editorial-operational: white cards (#ffffff) with subtle box-shadows (0 1px 3px rgba(0,0,0,.08)) sit on the warm gray floor, creating a content-dashboard that feels like a newsroom CMS crossed with a factory conveyor belt. The primary accent is deep navy (#1a1a2e) — used on primary CTAs and page title. The system uses status badges (blue/yellow/green/red/purple) for content pipeline states, and chart.js-powered analytics panels for publishing trends. This is a light, information-dense interface designed for content operators — it prioritizes readability and scanability over atmosphere.

## 颜色体系 (Colors)

- **primary**: #1a1a2e
- **primary-hover**: #2d2d5e
- **primary-active**: #0f0f1e
- **ink**: #1a1a2e
- **ink-secondary**: #374151
- **ink-muted**: #666666
- **ink-soft**: #888888
- **canvas**: #f0f2f5
- **canvas-warm**: #f5f5f0
- **surface-card**: #ffffff
- **surface-soft**: #f3f4f6
- **hairline**: #d1d5db
- **hairline-soft**: #f0f0f0
- **accent-blue**: #1d4ed8
- **accent-yellow**: #92400e
- **accent-green**: #065f46
- **accent-red**: #991b1b
- **accent-purple**: #6b21a8
- **badge-blue**: #dbeafe
- **badge-yellow**: #fef3c7
- **badge-green**: #d1fae5
- **badge-red**: #fee2e2
- **badge-purple**: #f3e8ff
- **badge-gray**: #f3f4f6
- **success**: #22c55e
- **error**: #ef4444
- **on-primary**: #ffffff
- **on-dark**: #ffffff

## 排版体系 (Typography)

- **display-xl**: font: Inter, system-ui, -apple-system, sans-serif | size: 28px | weight: 700 | lh: 1.2 | ls: -0.3px
- **display-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 24px | weight: 700 | lh: 1.25 | ls: -0.2px
- **display-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 20px | weight: 600 | lh: 1.3 | ls: 0
- **headline**: font: Inter, system-ui, -apple-system, sans-serif | size: 18px | weight: 600 | lh: 1.35 | ls: 0
- **title-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 15px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 600 | lh: 1.4 | ls: 0
- **body-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 16px | weight: 400 | lh: 1.6 | ls: 0
- **body-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.55 | ls: 0
- **body-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **button-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 12px | weight: 500 | lh: 1.0 | ls: 0
- **caption**: font: Inter, system-ui, -apple-system, sans-serif | size: 12px | weight: 500 | lh: 1.4 | ls: 0.3px
- **micro**: font: Inter, system-ui, -apple-system, sans-serif | size: 11px | weight: 500 | lh: 1.3 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **xxxl**: 32px
- **section**: 40px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 10px
- **xl**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 16px, height: 38px

### button-primary-hover
backgroundColor: {colors.primary-hover}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-success
backgroundColor: {colors.success}, textColor: {colors.on-primary}, typography: {typography.button-sm}, rounded: {rounded.md}, padding: 6px 14px, height: 32px

### button-danger
backgroundColor: {colors.error}, textColor: {colors.on-primary}, typography: {typography.button-sm}, rounded: {rounded.md}, padding: 6px 14px, height: 32px

### button-outline
backgroundColor: transparent, textColor: {colors.ink-secondary}, typography: {typography.button-sm}, rounded: {rounded.md}, padding: 6px 14px, border: 1px solid {colors.hairline}

### stat-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.display-md}, rounded: {rounded.lg}, padding: 12px 8px, shadow: 0 1px 3px rgba(0,0,0,.08)

### stat-card-value
typography: {typography.display-lg}, fontWeight: 700

### stat-card-label
typography: {typography.caption}, textColor: {colors.ink-muted}

### chart-box
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.lg}, padding: 12px, shadow: 0 1px 3px rgba(0,0,0,.08)

### section-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 14px, shadow: 0 1px 3px rgba(0,0,0,.08)

### item-row
backgroundColor: transparent, textColor: {colors.ink-secondary}, typography: {typography.body-md}, borderBottom: 1px solid {colors.hairline-soft}, padding: 8px 0

### badge-status
typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### badge-blue
backgroundColor: {colors.badge-blue}, textColor: {colors.accent-blue}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### badge-yellow
backgroundColor: {colors.badge-yellow}, textColor: {colors.accent-yellow}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### badge-green
backgroundColor: {colors.badge-green}, textColor: {colors.accent-green}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### badge-red
backgroundColor: {colors.badge-red}, textColor: {colors.accent-red}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### badge-purple
backgroundColor: {colors.badge-purple}, textColor: {colors.accent-purple}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 7px 10px, border: 1px solid {colors.hairline}

### textarea
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 7px 10px, border: 1px solid {colors.hairline}, minHeight: 60px

### select-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 7px 10px, border: 1px solid {colors.hairline}

### top-nav
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-sm}, height: 48px, shadow: 0 1px 3px rgba(0,0,0,.08)

### status-dot
width: 8px, height: 8px, rounded: {rounded.full}

### dot-green
backgroundColor: {colors.success}

### dot-gray
backgroundColor: {colors.ink-soft}
', '["design-brand", "content-automation-factory", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (54, 'design_brand', 'cursor', 'design_system', '品牌设计规范 — cursor', '# 品牌设计规范: Cursor

An AI-first code editor whose marketing site reads like a quietly-confident developer-tools brand with a warm-cream editorial canvas (`#f7f7f4`) instead of the typical dark IDE atmosphere. Near-black warm ink (`#26251e`) carries body and display alike — display sits at weight 400 with negative letter-spacing for a magazine feel rather than a bold tech voice. The single brand voltage is **Cursor Orange** (`#f54e00`) reserved for primary CTAs and the wordmark. A signature pastel timeline palette (peach, mint, blue, lavender, gold) marks AI-action stages (Thinking / Reading / Editing / Grepping / Done) — only inside in-product timeline visualizations. Cards use minimal hairlines, no shadows, generous 80px section rhythm. CursorGothic for display/body, JetBrains Mono on every code surface (which is roughly half the page).

## 颜色体系 (Colors)

- **primary**: #f54e00
- **primary-active**: #d04200
- **ink**: #26251e
- **body**: #5a5852
- **body-strong**: #26251e
- **muted**: #807d72
- **muted-soft**: #a09c92
- **hairline**: #e6e5e0
- **hairline-soft**: #efeee8
- **hairline-strong**: #cfcdc4
- **canvas**: #f7f7f4
- **canvas-soft**: #fafaf7
- **surface-card**: #ffffff
- **surface-strong**: #e6e5e0
- **on-primary**: #ffffff
- **timeline-thinking**: #dfa88f
- **timeline-grep**: #9fc9a2
- **timeline-read**: #9fbbe0
- **timeline-edit**: #c0a8dd
- **timeline-done**: #c08532
- **semantic-error**: #cf2d56
- **semantic-success**: #1f8a65

## 排版体系 (Typography)

- **display-mega**: font: ''CursorGothic'', system-ui, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 72px | weight: 400 | lh: 1.1 | ls: -2.16px
- **display-lg**: font: ''CursorGothic'', sans-serif | size: 36px | weight: 400 | lh: 1.2 | ls: -0.72px
- **display-md**: font: ''CursorGothic'', sans-serif | size: 26px | weight: 400 | lh: 1.25 | ls: -0.325px
- **display-sm**: font: ''CursorGothic'', sans-serif | size: 22px | weight: 400 | lh: 1.3 | ls: -0.11px
- **title-md**: font: ''CursorGothic'', sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: ''CursorGothic'', sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: ''CursorGothic'', sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-tracked**: font: ''CursorGothic'', sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0.08px
- **body-sm**: font: ''CursorGothic'', sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: ''CursorGothic'', sans-serif | size: 13px | weight: 400 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: ''CursorGothic'', sans-serif | size: 11px | weight: 600 | lh: 1.4 | ls: 0.88px | transform: uppercase
- **code**: font: ''JetBrains Mono'', ''Fira Code'', monospace | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: ''CursorGothic'', sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **nav-link**: font: ''CursorGothic'', sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **base**: 16px
- **md**: 20px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 80px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 9px 17px, height: 40px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### button-download
backgroundColor: {colors.ink}, textColor: {colors.canvas}, typography: {typography.button}, rounded: {rounded.md}, padding: 12px 20px, height: 44px

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-mega}, padding: 80px

### ide-mockup-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: 0

### ide-pane
backgroundColor: {colors.canvas-soft}, textColor: {colors.body}, typography: {typography.code}, rounded: {rounded.md}, padding: 16px

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### comparison-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### timeline-pill-thinking
backgroundColor: {colors.timeline-thinking}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### timeline-pill-grep
backgroundColor: {colors.timeline-grep}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### timeline-pill-read
backgroundColor: {colors.timeline-read}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### timeline-pill-edit
backgroundColor: {colors.timeline-edit}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### timeline-pill-done
backgroundColor: {colors.timeline-done}, textColor: {colors.on-primary}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### code-block
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.code}, rounded: {rounded.lg}, padding: 20px

### pricing-tier-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.ink}, textColor: {colors.canvas}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 12px 16px, height: 44px

### badge-pill
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### cta-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}
', '["design-brand", "cursor", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (55, 'design_brand', 'digital-employee-commander', 'design_system', '品牌设计规范 — digital-employee-commander', '# 品牌设计规范: 数字员工指挥官 (Digital Employee Commander)

A deep charcoal management dashboard built on a gray-900 canvas (#111827) with blue-violet command accents (#60a5fa for primary, #818cf8 for purple-variant). The system is designed for ''legion command'' — organizing digital employees into tactical legions, issuing commands, running hive-mind sessions, and monitoring compliance. The atmosphere is military-ops-meets-software: dark charcoal surfaces, blue command accents, and dense tabular data displays. Cards use gray-800 (#1f2937) backgrounds with hairline borders in gray-700 (#374151). The blue primary acts as ''command signal'' — used for CTAs, active tabs, and focus rings. A purple variant (#818cf8) serves as secondary accent for legion/team indicators. The type runs Inter/system-ui at compact sizes optimized for data-dense management views.

## 颜色体系 (Colors)

- **primary**: #60a5fa
- **primary-hover**: #93bbfd
- **primary-active**: #3b82f6
- **accent-purple**: #818cf8
- **accent-purple-hover**: #a5b4fc
- **accent-purple-active**: #6366f1
- **ink**: #f1f5f9
- **ink-secondary**: #9ca3af
- **ink-muted**: #6b7280
- **ink-tertiary**: #4b5563
- **canvas**: #111827
- **canvas-soft**: #1a202c
- **surface-card**: #1f2937
- **surface-elevated**: #2d3748
- **surface-modal**: #1f2937
- **hairline**: #374151
- **hairline-soft**: #4b5563
- **green**: #34d399
- **green-bg**: rgba(5, 150, 105, 0.5)
- **red**: #f87171
- **red-bg**: rgba(220, 38, 38, 0.5)
- **yellow**: #fbbf24
- **yellow-bg**: rgba(217, 119, 6, 0.5)
- **on-primary**: #ffffff
- **on-dark**: #f1f5f9

## 排版体系 (Typography)

- **display-xl**: font: Inter, system-ui, -apple-system, sans-serif | size: 30px | weight: 700 | lh: 1.15 | ls: -0.5px
- **display-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 24px | weight: 700 | lh: 1.2 | ls: -0.3px
- **display-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 20px | weight: 600 | lh: 1.25 | ls: -0.2px
- **headline**: font: Inter, system-ui, -apple-system, sans-serif | size: 18px | weight: 600 | lh: 1.3 | ls: 0
- **title-lg**: font: Inter, system-ui, -apple-system, sans-serif | size: 16px | weight: 600 | lh: 1.35 | ls: 0
- **title-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: Inter, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 400 | lh: 1.45 | ls: 0
- **body-xs**: font: Inter, system-ui, -apple-system, sans-serif | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **button**: font: Inter, system-ui, -apple-system, sans-serif | size: 13px | weight: 500 | lh: 1.0 | ls: 0
- **caption**: font: Inter, system-ui, -apple-system, sans-serif | size: 11px | weight: 500 | lh: 1.3 | ls: 0.5px
- **caption-uppercase**: font: Inter, system-ui, -apple-system, sans-serif | size: 11px | weight: 600 | lh: 1.3 | ls: 0.8px
- **mono**: font: JetBrains Mono, ui-monospace, monospace | size: 12px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **xxxl**: 32px
- **section**: 40px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 10px
- **xl**: 12px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 6px 14px, height: 32px

### button-primary-hover
backgroundColor: {colors.primary-hover}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 6px 14px, height: 32px, border: 1px solid {colors.hairline}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink-secondary}, typography: {typography.button}, rounded: {rounded.md}, padding: 6px 10px

### tab-default
backgroundColor: transparent, textColor: {colors.ink-secondary}, typography: {typography.caption-uppercase}, padding: 6px 12px, rounded: {rounded.md}

### tab-active
backgroundColor: {colors.surface-elevated}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, padding: 6px 12px, rounded: {rounded.md}, borderBottom: 2px solid {colors.primary}

### metric-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.display-lg}, rounded: {rounded.lg}, padding: 16px

### metric-card-label
textColor: {colors.ink-secondary}, typography: {typography.caption-uppercase}

### legion-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 16px, border: 1px solid {colors.hairline}

### legion-card-hover
backgroundColor: {colors.surface-elevated}, borderColor: {colors.primary}

### table-header
textColor: {colors.ink-secondary}, typography: {typography.caption-uppercase}, borderBottom: 1px solid {colors.hairline}, padding: 8px 12px

### table-row
textColor: {colors.ink}, typography: {typography.body-sm}, borderBottom: 1px solid {colors.hairline}, padding: 8px 12px

### table-row-hover
backgroundColor: rgba(96, 165, 250, 0.05)

### status-pill
typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### status-active
backgroundColor: {colors.green-bg}, textColor: {colors.green}

### status-inactive
backgroundColor: {colors.red-bg}, textColor: {colors.red}

### status-pending
backgroundColor: {colors.yellow-bg}, textColor: {colors.yellow}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 6px 10px, height: 32px, border: 1px solid {colors.hairline}

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 6px 10px, ring: 2px solid {colors.primary}

### modal
backgroundColor: {colors.surface-modal}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px, maxWidth: 560px

### modal-scrim
backgroundColor: rgba(0, 0, 0, 0.6)

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, height: 56px, borderBottom: 1px solid {colors.hairline}

### command-msg
backgroundColor: {colors.green-bg}, textColor: {colors.green}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 8px 16px
', '["design-brand", "digital-employee-commander", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (57, 'design_brand', 'expo', 'design_system', '品牌设计规范 — expo', '# 品牌设计规范: Expo

A React Native developer-platform whose marketing site reads like a quietly-confident infrastructure brand. The base canvas is pure white with a soft sky-blue gradient atmospheric wash behind the hero; near-black ink (`#171717`) carries body and display alike. The single brand voltage is **pure black** (`#000000`) for primary CTAs — minimal and editorial-feeling, paired with a small blue text-link accent (`#0d74ce`) reserved for inline body links. Type pairs Inter at modest weights (display 600, body 400) with JetBrains Mono on every code surface. The brand''s strongest visual signature is the **device-mockup hero** — a centered MacBook + iPhone composite showing real Expo dev surfaces — over the gradient sky wash.

## 颜色体系 (Colors)

- **primary**: #000000
- **primary-active**: #1a1a1a
- **text-link**: #0d74ce
- **text-link-secondary**: #476cff
- **ink**: #171717
- **body**: #60646c
- **body-strong**: #171717
- **muted**: #999999
- **muted-soft**: #cccccc
- **hairline**: #f0f0f3
- **hairline-soft**: #f5f5f7
- **hairline-strong**: #dcdee0
- **canvas**: #ffffff
- **canvas-soft**: #fafafa
- **surface-card**: #ffffff
- **surface-strong**: #f0f0f3
- **surface-dark**: #171717
- **surface-dark-elevated**: #1a1a1a
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #b0b4ba
- **gradient-sky-light**: #cfe7ff
- **gradient-sky-mid**: #a8c8e8
- **accent-warning**: #ab6400
- **accent-preview**: #8145b5
- **accent-link-bright**: #47c2ff
- **semantic-error**: #eb8e90
- **semantic-success**: #16a34a

## 排版体系 (Typography)

- **display-mega**: font: ''Inter'', -apple-system, system-ui, sans-serif | size: 64px | weight: 600 | lh: 1.05 | ls: -1.92px
- **display-xl**: font: ''Inter'', sans-serif | size: 48px | weight: 600 | lh: 1.1 | ls: -1.44px
- **display-lg**: font: ''Inter'', sans-serif | size: 36px | weight: 600 | lh: 1.15 | ls: -1.08px
- **display-md**: font: ''Inter'', sans-serif | size: 28px | weight: 600 | lh: 1.2 | ls: -0.84px
- **display-sm**: font: ''Inter'', sans-serif | size: 22px | weight: 600 | lh: 1.25 | ls: -0.5px
- **title-md**: font: ''Inter'', sans-serif | size: 18px | weight: 600 | lh: 1.4 | ls: 0
- **title-sm**: font: ''Inter'', sans-serif | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-md**: font: ''Inter'', sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: ''Inter'', sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: ''Inter'', sans-serif | size: 13px | weight: 400 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: ''Inter'', sans-serif | size: 11px | weight: 600 | lh: 1.4 | ls: 0.88px | transform: uppercase
- **code**: font: ''JetBrains Mono'', ''Fira Code'', monospace | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **button**: font: ''Inter'', sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **nav-link**: font: ''Inter'', sans-serif | size: 14px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **base**: 16px
- **md**: 20px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 9px 17px, height: 40px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.text-link}, typography: {typography.button}

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-mega}, padding: 96px

### device-mockup-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.xl}, padding: 0

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### feature-card-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.title-md}, rounded: {rounded.lg}, padding: 24px

### workflow-step-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 20px

### workflow-step-icon
backgroundColor: {colors.surface-strong}, rounded: {rounded.md}, size: 32px

### code-block
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.code}, rounded: {rounded.lg}, padding: 20px

### ide-mockup-card
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: 0

### pricing-tier-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 12px 16px, height: 44px

### badge-pill
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### ecosystem-tile
backgroundColor: {colors.surface-card}, rounded: {rounded.md}, size: 64px

### cta-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}
', '["design-brand", "expo", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (58, 'design_brand', 'ferrari', 'design_system', '品牌设计规范 — ferrari', '# 品牌设计规范: Ferrari

A luxury-automotive brand whose marketing surfaces read as cinematic editorial. The base canvas is **near-black** (`#181818`) holding pure white display type; white-canvas bands appear only inside specific editorial contexts (preowned listings, pricing tables). The single brand voltage is **Rosso Corsa** (`#da291c`) — the iconic Ferrari racing red — used scarcely on primary CTAs, the Cavallino mark, and Formula 1 race-position highlights. Type runs **FerrariSans** at modest weights (display 500, body 400) — never bombastic. Spacing follows an explicit 8px token ladder (`xxxs` 4px through `super` 128px); generous editorial pacing throughout. The brand''s strongest visual signature is the **full-bleed cinematic hero photograph** that fills the viewport top with car photography, model details, or trackside livery — followed by a tighter editorial body layout below.

## 颜色体系 (Colors)

- **primary**: #da291c
- **primary-active**: #b01e0a
- **primary-hover**: #9d2211
- **ink**: #ffffff
- **body**: #969696
- **body-strong**: #ffffff
- **body-on-light**: #181818
- **muted**: #666666
- **muted-soft**: #8f8f8f
- **hairline**: #303030
- **hairline-on-light**: #d2d2d2
- **hairline-soft**: #ebebeb
- **canvas**: #181818
- **canvas-elevated**: #303030
- **canvas-light**: #ffffff
- **surface-card**: #303030
- **surface-soft-light**: #f7f7f7
- **surface-strong-light**: #ebebeb
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-light**: #181818
- **accent-yellow-hypersail**: #fff200
- **accent-yellow**: #f6e500
- **semantic-info**: #4c98b9
- **semantic-success**: #03904a
- **semantic-warning**: #f13a2c

## 排版体系 (Typography)

- **display-mega**: font: ''FerrariSans'', -apple-system, system-ui, sans-serif | size: 80px | weight: 500 | lh: 1.05 | ls: -1.6px
- **display-xl**: font: ''FerrariSans'', sans-serif | size: 56px | weight: 500 | lh: 1.1 | ls: -1.12px
- **display-lg**: font: ''FerrariSans'', sans-serif | size: 36px | weight: 500 | lh: 1.2 | ls: -0.36px
- **display-md**: font: ''FerrariSans'', sans-serif | size: 26px | weight: 500 | lh: 1.5 | ls: 0.195px
- **title-md**: font: ''FerrariSans'', sans-serif | size: 18px | weight: 700 | lh: 1.2 | ls: 0
- **title-sm**: font: ''FerrariSans'', sans-serif | size: 16px | weight: 500 | lh: 1.4 | ls: 0.08px
- **body-md**: font: ''FerrariSans'', sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: ''FerrariSans'', sans-serif | size: 13px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: ''FerrariSans'', sans-serif | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **caption-uppercase**: font: ''FerrariSans'', sans-serif | size: 11px | weight: 600 | lh: 1.4 | ls: 1.1px | transform: uppercase
- **button**: font: ''FerrariSans'', sans-serif | size: 14px | weight: 700 | lh: 1.0 | ls: 1.4px | transform: uppercase
- **nav-link**: font: ''FerrariSans'', sans-serif | size: 13px | weight: 600 | lh: 1.4 | ls: 0.65px | transform: uppercase
- **number-display**: font: ''FerrariSans'', sans-serif | size: 80px | weight: 700 | lh: 1.0 | ls: -1.6px

## 间距体系 (Spacing)

- **xxxs**: 4px
- **xxs**: 8px
- **xs**: 16px
- **sm**: 24px
- **md**: 32px
- **lg**: 48px
- **xl**: 64px
- **xxl**: 96px
- **super**: 128px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **lg**: 8px
- **xl**: 12px
- **full**: 9999px

## 组件定义 (Components)

### top-nav-on-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### top-nav-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.body-on-light}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 14px 32px, height: 48px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.none}

### button-outline-on-dark
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.none}, padding: 13px 31px, height: 48px

### button-outline-on-light
backgroundColor: transparent, textColor: {colors.body-on-light}, typography: {typography.button}, rounded: {rounded.none}, padding: 13px 31px, height: 48px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### hero-band-cinema
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-mega}, padding: 0

### hero-band-light
backgroundColor: {colors.canvas-light}, textColor: {colors.body-on-light}, typography: {typography.display-xl}, padding: 96px

### feature-card-photo
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 0

### feature-card-light
backgroundColor: {colors.canvas-light}, textColor: {colors.body-on-light}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 32px

### livery-band
backgroundColor: {colors.primary}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### preowned-listing-card
backgroundColor: {colors.canvas-light}, textColor: {colors.body-on-light}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 24px

### spec-cell
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.number-display}, padding: 24px 0

### race-position-cell
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.number-display}

### race-calendar-row
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}, padding: 16px 0

### driver-card
backgroundColor: {colors.canvas-elevated}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.none}, padding: 24px

### text-input-on-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 14px 16px, height: 48px

### text-input-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.body-on-light}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 14px 16px, height: 48px

### badge-pill
backgroundColor: {colors.canvas-elevated}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.full}, padding: 4px 12px

### cta-band-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### newsletter-input-band
backgroundColor: {colors.canvas-elevated}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 32px

### footer-dark
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}
', '["design-brand", "ferrari", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (59, 'design_brand', 'figma', 'design_system', '品牌设计规范 — figma', '# 品牌设计规范: Figma

A confident black-and-white editorial frame interrupted by oversized, hand-cut pastel color blocks. The marketing canvas is rigorously monochrome — figmaSans variable type, pure white surfaces, pure black ink, pill-shaped CTAs — while each story section drops the page into a saturated lime, lavender, cream, mint, or pink panel that reads like a sticky note placed on a clean desk. The result is a design system that feels both technical and joyful — a tool for serious work, made by people who like color.

## 颜色体系 (Colors)

- **primary**: #000000
- **on-primary**: #ffffff
- **ink**: #000000
- **canvas**: #ffffff
- **inverse-canvas**: #000000
- **inverse-ink**: #ffffff
- **on-inverse-soft**: #ffffff
- **hairline**: #e6e6e6
- **hairline-soft**: #f1f1f1
- **surface-soft**: #f7f7f5
- **block-lime**: #dceeb1
- **block-lilac**: #c5b0f4
- **block-cream**: #f4ecd6
- **block-pink**: #efd4d4
- **block-mint**: #c8e6cd
- **block-coral**: #f3c9b6
- **block-navy**: #1f1d3d
- **accent-magenta**: #ff3d8b
- **semantic-success**: #1ea64a
- **overlay-scrim**: #000000

## 排版体系 (Typography)

- **display-xl**: font: figmaSans | size: 86px | weight: 340 | lh: 1.0 | ls: -1.72px
- **display-lg**: font: figmaSans | size: 64px | weight: 340 | lh: 1.1 | ls: -0.96px
- **headline**: font: figmaSans | size: 26px | weight: 540 | lh: 1.35 | ls: -0.26px
- **subhead**: font: figmaSans | size: 26px | weight: 340 | lh: 1.35 | ls: -0.26px
- **card-title**: font: figmaSans | size: 24px | weight: 700 | lh: 1.45 | ls: 0
- **body-lg**: font: figmaSans | size: 20px | weight: 330 | lh: 1.4 | ls: -0.14px
- **body**: font: figmaSans | size: 18px | weight: 320 | lh: 1.45 | ls: -0.26px
- **body-sm**: font: figmaSans | size: 16px | weight: 330 | lh: 1.45 | ls: -0.14px
- **link**: font: figmaSans | size: 20px | weight: 480 | lh: 1.4 | ls: -0.10px
- **button**: font: figmaSans | size: 20px | weight: 480 | lh: 1.4 | ls: -0.10px
- **eyebrow**: font: figmaMono | size: 18px | weight: 400 | lh: 1.3 | ls: 0.54px
- **caption**: font: figmaMono | size: 12px | weight: 400 | lh: 1.0 | ls: 0.60px

## 间距体系 (Spacing)

- **hair**: 1px
- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 2px
- **sm**: 6px
- **md**: 8px
- **lg**: 24px
- **xl**: 32px
- **pill**: 50px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 10px 20px

### button-primary-pressed
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 18px 10px

### button-tertiary-text
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.link}, rounded: {rounded.full}, padding: 8px 12px

### button-icon-circular
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.full}, size: 40px

### button-icon-circular-inverse
backgroundColor: {colors.on-inverse-soft}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.full}, size: 40px

### button-magenta-promo
backgroundColor: {colors.accent-magenta}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 10px 18px

### pricing-tab-default
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 18px

### pricing-tab-selected
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 18px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 12px 14px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 12px 14px

### pricing-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### pricing-card-feature-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}

### color-block-section
backgroundColor: {colors.block-lime}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.lg}, padding: 48px

### color-block-section-lilac
backgroundColor: {colors.block-lilac}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.lg}, padding: 48px

### color-block-section-navy
backgroundColor: {colors.block-navy}, textColor: {colors.inverse-ink}, typography: {typography.subhead}, rounded: {rounded.lg}, padding: 48px

### promo-banner-lilac
backgroundColor: {colors.block-lilac}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 16px 24px

### template-card
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 16px

### feature-illustration-tile
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.eyebrow}, rounded: {rounded.md}, padding: 24px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 56px

### marquee-strip
backgroundColor: {colors.inverse-canvas}, textColor: {colors.inverse-ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 36px

### comparison-checkmark
backgroundColor: {colors.canvas}, textColor: {colors.semantic-success}, typography: {typography.body-sm}, rounded: {rounded.full}, size: 16px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 32px
', '["design-brand", "figma", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (60, 'design_brand', 'framer', 'design_system', '品牌设计规范 — framer', '# 品牌设计规范: Framer

A confident dark-canvas builder marketing site that treats the page like a working artboard — pure black surfaces, white display type set in GT Walsheim Medium with aggressive negative tracking, and a single confident blue (#0099ff) reserved for hyperlinks and selection states. The page rhythm is broken by oversized vibrant gradient atmosphere panels — magenta, violet, orange spotlights — that act as living showcase tiles, not decoration. Every CTA is a white pill on dark; every card is a translucent or charcoal surface; every section title pulls letter-spacing tight enough to feel like a poster.

## 颜色体系 (Colors)

- **primary**: #ffffff
- **on-primary**: #000000
- **accent-blue**: #0099ff
- **ink**: #ffffff
- **ink-muted**: #999999
- **canvas**: #090909
- **surface-1**: #141414
- **surface-2**: #1c1c1c
- **hairline**: #262626
- **hairline-soft**: #1a1a1a
- **inverse-canvas**: #ffffff
- **inverse-ink**: #000000
- **gradient-magenta**: #d44df0
- **gradient-violet**: #6a4cf5
- **gradient-orange**: #ff7a3d
- **gradient-coral**: #ff5577
- **semantic-success**: #22c55e

## 排版体系 (Typography)

- **display-xxl**: font: GT Walsheim Framer Medium | size: 110px | weight: 500 | lh: 0.85 | ls: -5.5px
- **display-xl**: font: GT Walsheim Medium | size: 85px | weight: 500 | lh: 0.95 | ls: -4.25px
- **display-lg**: font: GT Walsheim Medium | size: 62px | weight: 500 | lh: 1.0 | ls: -3.1px
- **display-md**: font: GT Walsheim Medium | size: 32px | weight: 500 | lh: 1.13 | ls: -1.0px
- **headline**: font: Inter | size: 22px | weight: 700 | lh: 1.2 | ls: -0.8px
- **subhead**: font: Inter Variable | size: 24px | weight: 400 | lh: 1.3 | ls: -0.01px
- **body-lg**: font: Inter Variable | size: 18px | weight: 400 | lh: 1.3 | ls: -0.18px
- **body**: font: Inter Variable | size: 15px | weight: 400 | lh: 1.3 | ls: -0.15px
- **body-sm**: font: Inter Variable | size: 14px | weight: 500 | lh: 1.4 | ls: -0.14px
- **caption**: font: Inter Variable | size: 13px | weight: 500 | lh: 1.2 | ls: -0.13px
- **micro**: font: Inter Variable | size: 12px | weight: 400 | lh: 1.2 | ls: -0.12px
- **button**: font: Inter Variable | size: 14px | weight: 500 | lh: 1.0 | ls: -0.14px

## 间距体系 (Spacing)

- **hair**: 1px
- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 15px
- **lg**: 20px
- **xl**: 30px
- **xxl**: 40px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 10px
- **lg**: 15px
- **xl**: 20px
- **xxl**: 30px
- **pill**: 100px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 10px 15px

### button-primary-pressed
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}

### button-secondary
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 10px 15px

### button-translucent
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.xxl}, padding: 8px 14px

### button-icon-circular
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.full}, size: 40px

### pricing-tab-default
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 14px

### pricing-tab-selected
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 14px

### text-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### text-input-focused
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### pricing-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xl}, padding: 24px

### pricing-card-featured
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xl}, padding: 24px

### template-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 12px

### gradient-spotlight-card
backgroundColor: {colors.gradient-violet}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.xl}, padding: 32px

### gradient-spotlight-card-magenta
backgroundColor: {colors.gradient-magenta}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.xl}, padding: 32px

### gradient-spotlight-card-orange
backgroundColor: {colors.gradient-orange}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.xl}, padding: 32px

### product-mockup-tile
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xl}, padding: 16px

### feature-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xs}

### comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.body-sm}, rounded: {rounded.xs}

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 56px

### faq-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 24px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 32px
', '["design-brand", "framer", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (61, 'design_brand', 'hashicorp', 'design_system', '品牌设计规范 — hashicorp', '# 品牌设计规范: HashiCorp

An enterprise-infrastructure marketing canvas built around a near-black ground (#000000) and a system of per-product accent colors — Terraform purple, Vault yellow, Consul pink, Waypoint cyan, Vagrant blue — that act as identity tokens rather than decorative palette. Display type is hashicorpSans set in 600/700 with tight 1.17–1.21 line-heights; body type runs the same family at 500 weight with relaxed 1.50–1.71 line-heights. Cards live as charcoal surfaces with 1px translucent gray borders; product showcase cards lift into per-product chromatic gradients. The system reads as confident, technical, and intentionally multi-product — every section quietly signals which HashiCorp tool it represents.

## 颜色体系 (Colors)

- **primary**: #000000
- **on-primary**: #ffffff
- **accent-blue**: #2b89ff
- **ink**: #ffffff
- **ink-muted**: #b2b6bd
- **ink-subtle**: #656a76
- **canvas**: #000000
- **surface-1**: #15181e
- **surface-2**: #1f232b
- **surface-3**: #3b3d45
- **hairline**: #3b3d45
- **hairline-soft**: #252830
- **inverse-canvas**: #ffffff
- **inverse-ink**: #000000
- **product-terraform**: #7b42bc
- **product-terraform-bright**: #911ced
- **product-vault**: #ffcf25
- **product-consul**: #e62b1e
- **product-waypoint**: #14c6cb
- **product-waypoint-deep**: #12b6bb
- **product-vagrant**: #1868f2
- **product-nomad**: #00ca8e
- **product-boundary**: #f24c53
- **amber-100**: #fbeabf
- **amber-200**: #bb5a00
- **blue-7**: #101a59
- **semantic-success**: #00ca8e
- **semantic-warning**: #ffcf25
- **semantic-error**: #e62b1e
- **semantic-visited**: #a737ff

## 排版体系 (Typography)

- **display-xl**: font: hashicorpSans | size: 80px | weight: 700 | lh: 1.17 | ls: -2.5px
- **display-lg**: font: hashicorpSans | size: 56px | weight: 700 | lh: 1.18 | ls: -1.6px
- **display-md**: font: hashicorpSans | size: 40px | weight: 600 | lh: 1.19 | ls: -1.0px
- **headline**: font: hashicorpSans | size: 28px | weight: 600 | lh: 1.21 | ls: -0.6px
- **card-title**: font: hashicorpSans | size: 22px | weight: 600 | lh: 1.18 | ls: -0.4px
- **subhead**: font: hashicorpSans | size: 20px | weight: 600 | lh: 1.35 | ls: -0.2px
- **body-lg**: font: hashicorpSans | size: 18px | weight: 500 | lh: 1.69 | ls: 0
- **body**: font: hashicorpSans | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **body-sm**: font: hashicorpSans | size: 14px | weight: 500 | lh: 1.71 | ls: 0
- **caption**: font: hashicorpSans | size: 13px | weight: 500 | lh: 1.38 | ls: 0.2px
- **button**: font: hashicorpSans | size: 14px | weight: 600 | lh: 1.29 | ls: 0
- **eyebrow**: font: hashicorpSans | size: 12px | weight: 600 | lh: 1.23 | ls: 0.6px

## 间距体系 (Spacing)

- **hair**: 1px
- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.inverse-canvas}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-primary-pressed
backgroundColor: {colors.inverse-canvas}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-tertiary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-product-terraform
backgroundColor: {colors.product-terraform}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-product-vault
backgroundColor: {colors.product-vault}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-product-waypoint
backgroundColor: {colors.product-waypoint}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### product-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### product-card-terraform
backgroundColor: {colors.product-terraform}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### product-card-vault
backgroundColor: {colors.product-vault}, textColor: {colors.inverse-ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### product-card-waypoint
backgroundColor: {colors.product-waypoint}, textColor: {colors.inverse-ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### feature-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### pricing-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 32px

### pricing-card-featured
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 32px

### resource-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: 16px

### text-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### text-input-focused
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### product-pill
backgroundColor: {colors.surface-1}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 4px 10px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 64px

### comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.body-sm}, rounded: {rounded.xs}

### cta-banner
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.subhead}, rounded: {rounded.xxl}, padding: 48px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 32px
', '["design-brand", "hashicorp", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (62, 'design_brand', 'ibm', 'design_system', '品牌设计规范 — ibm', '# 品牌设计规范: IBM

An enterprise-marketing canvas faithful to Carbon Design System: white surfaces, charcoal type, IBM Blue (#0f62fe) as the single confident accent, and a deliberately flat-square aesthetic where corners stay at 0–4px. Type runs IBM Plex Sans at light weight 300 for display sizes (a brand signature) and 400/600 for body and emphasis. Cards live as thin-bordered tiles with no shadow; sections separate via subtle gray rows. The chrome is square, the typography is light, and the only color in the system is one assertive blue — the result reads as old-world enterprise gravitas reframed for the cloud era.

## 颜色体系 (Colors)

- **primary**: #0f62fe
- **on-primary**: #ffffff
- **ink**: #161616
- **ink-muted**: #525252
- **ink-subtle**: #8c8c8c
- **canvas**: #ffffff
- **surface-1**: #f4f4f4
- **surface-2**: #e0e0e0
- **inverse-canvas**: #161616
- **inverse-surface-1**: #262626
- **inverse-ink**: #ffffff
- **inverse-ink-muted**: #c6c6c6
- **hairline**: #e0e0e0
- **hairline-strong**: #161616
- **blue-60**: #0043ce
- **blue-80**: #002d9c
- **blue-hover**: #0050e6
- **semantic-success**: #24a148
- **semantic-warning**: #f1c21b
- **semantic-error**: #da1e28
- **semantic-info**: #0f62fe

## 排版体系 (Typography)

- **display-xl**: font: IBM Plex Sans | size: 76px | weight: 300 | lh: 1.17 | ls: -0.5px
- **display-lg**: font: IBM Plex Sans | size: 60px | weight: 300 | lh: 1.17 | ls: -0.4px
- **display-md**: font: IBM Plex Sans | size: 42px | weight: 300 | lh: 1.2 | ls: 0
- **headline**: font: IBM Plex Sans | size: 32px | weight: 400 | lh: 1.25 | ls: 0
- **card-title**: font: IBM Plex Sans | size: 24px | weight: 400 | lh: 1.33 | ls: 0
- **subhead**: font: IBM Plex Sans | size: 20px | weight: 400 | lh: 1.4 | ls: 0
- **body-lg**: font: IBM Plex Sans | size: 18px | weight: 400 | lh: 1.5 | ls: 0
- **body**: font: IBM Plex Sans | size: 16px | weight: 400 | lh: 1.5 | ls: 0.16px
- **body-sm**: font: IBM Plex Sans | size: 14px | weight: 400 | lh: 1.29 | ls: 0.16px
- **body-emphasis**: font: IBM Plex Sans | size: 14px | weight: 600 | lh: 1.29 | ls: 0.16px
- **caption**: font: IBM Plex Sans | size: 12px | weight: 400 | lh: 1.33 | ls: 0.32px
- **button**: font: IBM Plex Sans | size: 14px | weight: 400 | lh: 1.29 | ls: 0.16px
- **eyebrow**: font: IBM Plex Sans | size: 14px | weight: 400 | lh: 1.29 | ls: 0.16px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **lg**: 8px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 12px 16px

### button-primary-pressed
backgroundColor: {colors.blue-80}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.none}

### button-secondary
backgroundColor: {colors.ink}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.none}, padding: 12px 16px

### button-tertiary
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 12px 16px

### button-ghost
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 12px 16px

### button-danger
backgroundColor: {colors.semantic-error}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.none}, padding: 12px 16px

### feature-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 24px

### feature-card-elevated
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 24px

### product-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 32px

### hero-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-md}, rounded: {rounded.none}, padding: 48px

### cta-banner
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.headline}, rounded: {rounded.none}, padding: 48px

### text-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 11px 16px

### text-input-focused
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 11px 16px

### text-input-error
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 11px 16px

### newsletter-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.none}, padding: 11px 16px

### product-tab
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 16px 20px

### product-tab-selected
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-emphasis}, rounded: {rounded.none}, padding: 16px 20px

### resource-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 16px

### customer-logo-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.none}, padding: 24px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.none}, height: 48px

### utility-bar
backgroundColor: {colors.surface-1}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.none}, height: 32px

### footer
backgroundColor: {colors.inverse-canvas}, textColor: {colors.inverse-ink-muted}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 32px
', '["design-brand", "ibm", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (63, 'design_brand', 'intercom', 'design_system', '品牌设计规范 — intercom', '# 品牌设计规范: Intercom

An editorial customer-service marketing canvas built around a soft cream-white ground, charcoal type set in Saans (Intercom''s proprietary geometric sans), and a single confident Fin Orange (#ff5600) reserved for the Fin AI brand. Cards live as floating white tiles with thin hairline borders and minimal radii (8–16px). Display headlines run Saans at weight 500 with measured negative tracking. The system reads as a careful, product-led publication: product screenshots dominate, ornament is rare, and the only place chromatic energy enters is the Fin Orange CTA.

## 颜色体系 (Colors)

- **primary**: #111111
- **on-primary**: #ffffff
- **ink**: #111111
- **ink-muted**: #626260
- **ink-subtle**: #7b7b78
- **ink-tertiary**: #9c9fa5
- **canvas**: #f5f1ec
- **surface-1**: #ffffff
- **surface-2**: #ebe7e1
- **inverse-canvas**: #000000
- **inverse-surface-1**: #313130
- **inverse-ink**: #ffffff
- **inverse-ink-muted**: #9c9fa5
- **hairline**: #d3cec6
- **hairline-soft**: #ebe7e1
- **fin-orange**: #ff5600
- **report-orange**: #fe4c02
- **report-blue**: #65b5ff
- **report-green**: #0bdf50
- **report-pink**: #ff2067
- **report-lime**: #b3e01c
- **report-cyan**: #03b2cb
- **brand-blue**: #0007cb
- **semantic-error**: #c41c1c
- **semantic-success**: #0bdf50

## 排版体系 (Typography)

- **display-xl**: font: Saans | size: 72px | weight: 500 | lh: 1.05 | ls: -2.0px
- **display-lg**: font: Saans | size: 56px | weight: 500 | lh: 1.1 | ls: -1.4px
- **display-md**: font: Saans | size: 40px | weight: 500 | lh: 1.15 | ls: -0.8px
- **headline**: font: Saans | size: 28px | weight: 500 | lh: 1.2 | ls: -0.5px
- **card-title**: font: Saans | size: 22px | weight: 500 | lh: 1.25 | ls: -0.3px
- **subhead**: font: Saans | size: 20px | weight: 400 | lh: 1.4 | ls: -0.2px
- **body-lg**: font: Saans | size: 18px | weight: 400 | lh: 1.5 | ls: -0.1px
- **body**: font: Saans | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: Saans | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: Saans | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **button**: font: Saans | size: 15px | weight: 500 | lh: 1.2 | ls: 0
- **eyebrow**: font: Saans | size: 14px | weight: 500 | lh: 1.3 | ls: 0
- **mono**: font: SaansMono | size: 13px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-primary-pressed
backgroundColor: {colors.inverse-canvas}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-tertiary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### button-fin
backgroundColor: {colors.fin-orange}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 10px 18px

### pricing-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### pricing-card-featured
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### feature-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### product-mockup-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xl}, padding: 24px

### testimonial-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body-lg}, rounded: {rounded.lg}, padding: 32px

### customer-logo-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 16px

### text-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### text-input-focused
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 10px 14px

### pricing-tab-default
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 16px

### pricing-tab-selected
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 8px 16px

### faq-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 24px

### cta-banner
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.headline}, rounded: {rounded.lg}, padding: 48px

### startup-discount-card
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 32px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 56px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 32px
', '["design-brand", "intercom", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (64, 'design_brand', 'kraken', 'design_system', '品牌设计规范 — kraken', '# Design System Inspired by Kraken

## 1. Visual Theme & Atmosphere

Kraken''s website is a clean, trustworthy crypto exchange that uses purple as its commanding brand color. The design operates on white backgrounds with Kraken Purple (`#7132f5`, `#5741d8`, `#5b1ecf`) creating a distinctive, professional crypto identity. The proprietary Kraken-Brand font handles display headings with bold (700) weight and negative tracking, while Kraken-Product (with IBM Plex Sans fallback) serves as the UI workhorse.

**Key Characteristics:**
- Kraken Purple (`#7132f5`) as primary brand with darker variants (`#5741d8`, `#5b1ecf`)
- Kraken-Brand (display) + Kraken-Product (UI) dual font system
- Near-black (`#101114`) text with cool blue-gray neutral scale
- 12px radius buttons (rounded but not pill)
- Subtle shadows (`rgba(0,0,0,0.03) 0px 4px 24px`) — whisper-level
- Green accent (`#149e61`) for positive/success states

## 2. Color Palette & Roles

### Primary
- **Kraken Purple** (`#7132f5`): Primary CTA, brand accent, links
- **Purple Dark** (`#5741d8`): Button borders, outlined variants
- **Purple Deep** (`#5b1ecf`): Deepest purple
- **Purple Subtle** (`rgba(133,91,251,0.16)`): Purple at 16% — subtle button backgrounds
- **Near Black** (`#101114`): Primary text

### Neutral
- **Cool Gray** (`#686b82`): Primary neutral, borders at 24% opacity
- **Silver Blue** (`#9497a9`): Secondary text, muted elements
- **White** (`#ffffff`): Primary surface
- **Border Gray** (`#dedee5`): Divider borders

### Semantic
- **Green** (`#149e61`): Success/positive at 16% opacity for badges
- **Green Dark** (`#026b3f`): Badge text

## 3. Typography Rules

### Font Families
- **Display**: `Kraken-Brand`, fallbacks: `IBM Plex Sans, Helvetica, Arial`
- **UI / Body**: `Kraken-Product`, fallbacks: `Helvetica Neue, Helvetica, Arial`

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Display Hero | Kraken-Brand | 48px', '["design-brand", "kraken"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (65, 'design_brand', 'lamborghini', 'design_system', '品牌设计规范 — lamborghini', '# Design System Inspired by Lamborghini

## 1. Visual Theme & Atmosphere

Lamborghini''s website is a cathedral of darkness — a digital stage where jet-black surfaces stretch infinitely and every element emerges from the void like a machine under a spotlight. The page is almost entirely black. Not dark gray, not near-black — true, uncompromising black (`#000000`) that saturates the viewport and refuses to yield. Into this abyss, white type and Lamborghini Gold (`#FFC000`) are deployed with surgical precision, creating a visual language that feels like walking through a nighttime motorsport event where every surface absorbs light except the things that matter.

The hero is a full-viewport video — dark, cinematic, immersive — showing event footage or vehicle reveals with the Lamborghini bull logo floating ethereally above. The navigation is minimal: a centered bull logo, a "MENU" hamburger on the left, and search/bookmark icons on the right, all rendered in white against the black canvas. There are no borders, no visible nav containers, no background color on the header — just white marks floating in darkness. The overall mood is nocturnal luxury: exclusive, theatrical, and deliberately intimidating. Each section transition is a scroll through darkness into the next revelation.

Typography is the voice of this darkness. LamboType — a custom Neo-Grotesk typeface created by Character Type and design agency Strichpunkt — is used for everything from 120px uppercase display headlines to 10px micro labels. Its distinctive 12° angled terminals are inspired by the aerodynamic lines of Lamborghini''s super sports cars, and its proportions range from Normal to Ultracompressed width. Headlines SHOUT in uppercase at enormous scales with tight line-heights (0.92 at 120px), creating dense blocks of text that feel stamped from steel. The typeface carries hexagonal geometric DNA — constructed from hexagons, three-armed stars, and circles — that echoes throughout the interface in the he', '["design-brand", "lamborghini"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (66, 'design_brand', 'linear-app', 'design_system', '品牌设计规范 — linear.app', '# 品牌设计规范: Linear

A near-black product-focused marketing canvas built around #010102 (the deepest dark surface of any tool in this collection), light gray text (#f7f8f8), and the signature Linear lavender-blue (#5e6ad2) used as the single chromatic accent. The system reads as software-craft documentation: dense, technical, and quietly luxurious. Display type is set in the Linear custom sans (SF Pro Display fallback) at 500–700 with measured negative tracking. Cards live as charcoal panels (#0f1011) with hairline borders. The accent lavender appears on the brand mark, focus rings, and a few intentional CTAs — never decoratively. Page rhythm leans on product UI screenshots framed in dark panels rather than atmospheric color.

## 颜色体系 (Colors)

- **primary**: #5e6ad2
- **on-primary**: #ffffff
- **primary-hover**: #828fff
- **primary-focus**: #5e69d1
- **ink**: #f7f8f8
- **ink-muted**: #d0d6e0
- **ink-subtle**: #8a8f98
- **ink-tertiary**: #62666d
- **canvas**: #010102
- **surface-1**: #0f1011
- **surface-2**: #141516
- **surface-3**: #18191a
- **surface-4**: #191a1b
- **hairline**: #23252a
- **hairline-strong**: #34343a
- **hairline-tertiary**: #3e3e44
- **inverse-canvas**: #ffffff
- **inverse-surface-1**: #f5f6f6
- **inverse-surface-2**: #f6f7f7
- **inverse-ink**: #000000
- **brand-secure**: #7a7fad
- **semantic-success**: #27a644
- **semantic-overlay**: #000000

## 排版体系 (Typography)

- **display-xl**: font: Linear Display | size: 80px | weight: 600 | lh: 1.05 | ls: -3.0px
- **display-lg**: font: Linear Display | size: 56px | weight: 600 | lh: 1.1 | ls: -1.8px
- **display-md**: font: Linear Display | size: 40px | weight: 600 | lh: 1.15 | ls: -1.0px
- **headline**: font: Linear Display | size: 28px | weight: 600 | lh: 1.2 | ls: -0.6px
- **card-title**: font: Linear Display | size: 22px | weight: 500 | lh: 1.25 | ls: -0.4px
- **subhead**: font: Linear Display | size: 20px | weight: 400 | lh: 1.4 | ls: -0.2px
- **body-lg**: font: Linear Text | size: 18px | weight: 400 | lh: 1.5 | ls: -0.1px
- **body**: font: Linear Text | size: 16px | weight: 400 | lh: 1.5 | ls: -0.05px
- **body-sm**: font: Linear Text | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption**: font: Linear Text | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **button**: font: Linear Text | size: 14px | weight: 500 | lh: 1.2 | ls: 0
- **eyebrow**: font: Linear Text | size: 13px | weight: 500 | lh: 1.3 | ls: 0.4px
- **mono**: font: Linear Mono | size: 13px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 14px

### button-primary-pressed
backgroundColor: {colors.primary-focus}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-primary-hover
backgroundColor: {colors.primary-hover}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 14px

### button-tertiary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 14px

### button-inverse
backgroundColor: {colors.inverse-canvas}, textColor: {colors.inverse-ink}, typography: {typography.button}, rounded: {rounded.md}, padding: 8px 14px

### pricing-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### pricing-card-featured
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### feature-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.lg}, padding: 24px

### product-screenshot-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xl}, padding: 24px

### testimonial-card
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body-lg}, rounded: {rounded.lg}, padding: 32px

### customer-logo-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink-subtle}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 16px

### text-input
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 8px 12px

### text-input-focused
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.md}, padding: 8px 12px

### pricing-tab-default
backgroundColor: {colors.canvas}, textColor: {colors.ink-subtle}, typography: {typography.button}, rounded: {rounded.pill}, padding: 6px 14px

### pricing-tab-selected
backgroundColor: {colors.surface-2}, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 6px 14px

### cta-banner
backgroundColor: {colors.surface-1}, textColor: {colors.ink}, typography: {typography.headline}, rounded: {rounded.lg}, padding: 48px

### changelog-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body}, rounded: {rounded.xs}, padding: 24px 0

### status-badge
backgroundColor: {colors.surface-2}, textColor: {colors.ink-muted}, typography: {typography.caption}, rounded: {rounded.pill}, padding: 2px 8px

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.xs}, height: 56px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.ink-subtle}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 32px
', '["design-brand", "linear.app", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (67, 'design_brand', 'lovable', 'design_system', '品牌设计规范 — lovable', '# Design System Inspired by Lovable

## 1. Visual Theme & Atmosphere

Lovable''s website radiates warmth through restraint. The entire page sits on a creamy, parchment-toned background (`#f7f4ed`) that immediately separates it from the cold-white conventions of most developer tool sites. This isn''t minimalism for minimalism''s sake — it''s a deliberate choice to feel approachable, almost analog, like a well-crafted notebook. The near-black text (`#1c1c1c`) against this warm cream creates a contrast ratio that''s easy on the eyes while maintaining sharp readability.

The custom Camera Plain Variable typeface is the system''s secret weapon. Unlike geometric sans-serifs that signal "tech company," Camera Plain has a humanist warmth — slightly rounded terminals, organic curves, and a comfortable reading rhythm. At display sizes (48px–60px), weight 600 with aggressive negative letter-spacing (-0.9px to -1.5px) compresses headlines into confident, editorial statements. The font uses `ui-sans-serif, system-ui` as fallbacks, acknowledging that the custom typeface carries the brand personality.

What makes Lovable''s visual system distinctive is its opacity-driven depth model. Rather than using a traditional gray scale, the system modulates `#1c1c1c` at varying opacities (0.03, 0.04, 0.4, 0.82–0.83) to create a unified tonal range. Every shade of gray on the page is technically the same hue — just more or less transparent. This creates a visual coherence that''s nearly impossible to achieve with arbitrary hex values. The border system follows suit: `1px solid #eceae4` for light divisions and `1px solid rgba(28, 28, 28, 0.4)` for stronger interactive boundaries.

**Key Characteristics:**
- Warm parchment background (`#f7f4ed`) — not white, not beige, a deliberate cream that feels hand-selected
- Camera Plain Variable typeface with humanist warmth and editorial letter-spacing at display sizes
- Opacity-driven color system: all grays derived from `#1c1c1c` at varying transparency leve', '["design-brand", "lovable"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (68, 'design_brand', 'mastercard', 'design_system', '品牌设计规范 — mastercard', '# Design System Inspired by Mastercard

## 1. Visual Theme & Atmosphere

Mastercard''s experience reads like a warm, editorial magazine built from soft stone and signal orange. The canvas is a muted putty-cream (`#F3F0EE`) — not white, not gray, but a color that feels like the paper of a premium annual report. On top of that canvas, everything that matters is shaped like a stadium, a pill, or a perfect circle. The dominant visual gesture is the **oversized radius**: heroes carry 40-point corners, cards go fully pill-shaped, service images are cropped into circular orbits, and buttons either complete the pill or fit snugly at 20 points. There are almost no sharp corners anywhere on the page.

The second gesture is **orbit and trajectory**. Circular image masks don''t sit still — they''re connected by thin, hand-drawn-feeling orange arcs that span entire viewport widths, implying a constellation of services rather than a list. Each circle has a small attached "satellite" — a white micro-CTA holding an arrow icon — docked onto its perimeter like a moon. This is the most distinctive thing about Mastercard''s current design language: the circles feel like they''re in motion even though the page is still.

Typography is rendered entirely in **MarkForMC**, Mastercard''s proprietary geometric sans. Headlines are set at a medium weight (500) with tight negative letter-spacing (-2%), giving them confidence without shouting. Body copy runs at the same family in a slightly lighter weight (450) — a weight you rarely see on the web, chosen because it reads softer than regular 400 without feeling thin. The whole system — warm cream surfaces, pill shapes, circular portraits, traced-orange orbits, black CTAs — feels simultaneously institutional (a 60-year-old payments network) and editorial (a modern brand magazine), which is exactly the tension Mastercard wants to hold.

**Key Characteristics:**
- Warm cream canvas (`#F3F0EE`) replaces traditional white — every surface is tinted, never s', '["design-brand", "mastercard"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (69, 'design_brand', 'meta', 'design_system', '品牌设计规范 — meta', '# 品牌设计规范: Meta

Meta''s design system spans hardware commerce (Quest VR, Ray-Ban Meta AI glasses) and brand surfaces with a confident product-merchandising voice. The system pairs a stark white canvas with full-bleed photographic product cards, a confident Optimistic VF wordmark/headline face, dual-CTA hero patterns (black primary + outlined secondary), and a saturated cobalt blue (#0064E0) for in-product purchase actions. Pill-shaped 100px-radius buttons, generous 24-32px card rounding, and tight three-tier text hierarchy carry across homepage, product detail (PDP), buy-now configurator, and accessory subpages.

## 颜色体系 (Colors)

- **primary**: #0064e0
- **primary-deep**: #0457cb
- **primary-soft**: #0091ff
- **on-primary**: #ffffff
- **ink-button**: #000000
- **on-ink-button**: #ffffff
- **fb-blue**: #1876f2
- **meta-link**: #385898
- **oculus-purple**: #a121ce
- **success**: #31a24c
- **success-bg**: #24e400
- **attention**: #f2a918
- **warning**: #f7b928
- **warning-bg**: #ffe200
- **critical**: #e41e3f
- **critical-strong**: #f0284a
- **canvas**: #ffffff
- **surface-soft**: #f1f4f7
- **ink-deep**: #0a1317
- **ink**: #1c1e21
- **charcoal**: #444950
- **slate**: #4b4c4f
- **steel**: #5d6c7b
- **stone**: #8595a4
- **hairline**: #ced0d4
- **hairline-soft**: #dee3e9
- **disabled-text**: #bcc0c4

## 排版体系 (Typography)

- **hero-display**: font: Optimistic VF | size: 64px | weight: 500 | lh: 1.16
- **display-lg**: font: Optimistic VF | size: 48px | weight: 500 | lh: 1.17
- **heading-lg**: font: Optimistic VF | size: 36px | weight: 500 | lh: 1.28
- **heading-md**: font: Optimistic VF | size: 28px | weight: 300 | lh: 1.21
- **heading-sm**: font: Optimistic VF | size: 24px | weight: 500 | lh: 1.25
- **subtitle-lg**: font: Optimistic VF | size: 18px | weight: 700 | lh: 1.44
- **subtitle-md**: font: Optimistic VF | size: 18px | weight: 400 | lh: 1.44
- **body-md-bold**: font: Optimistic VF | size: 16px | weight: 700 | lh: 1.5 | ls: -0.16px
- **body-md**: font: Optimistic VF | size: 16px | weight: 400 | lh: 1.5 | ls: -0.16px
- **body-sm-bold**: font: Optimistic VF | size: 14px | weight: 700 | lh: 1.43 | ls: -0.14px
- **body-sm**: font: Optimistic VF | size: 14px | weight: 400 | lh: 1.43 | ls: -0.14px
- **caption-bold**: font: Optimistic VF | size: 12px | weight: 700 | lh: 1.33
- **caption**: font: Optimistic VF | size: 12px | weight: 400 | lh: 1.33
- **button-md**: font: Optimistic VF | size: 14px | weight: 700 | lh: 1.43 | ls: -0.14px
- **link-md**: font: Optimistic VF | size: 16px | weight: 700 | lh: 1.5 | ls: -0.16px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 10px
- **md**: 12px
- **base**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 80px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **lg**: 8px
- **xl**: 16px
- **xxl**: 24px
- **xxxl**: 32px
- **feature**: 40px
- **full**: 100px
- **circle**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.ink-button}, textColor: {colors.on-ink-button}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 14px 30px

### button-primary-pressed
backgroundColor: {colors.charcoal}, textColor: {colors.on-ink-button}

### button-primary-disabled
backgroundColor: {colors.disabled-text}, textColor: {colors.canvas}

### button-buy-cta
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 14px 30px

### button-buy-cta-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}

### button-secondary
backgroundColor: transparent, textColor: {colors.ink-deep}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 28px, border: 2px solid {colors.ink-deep}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink-deep}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 22px, border: 2px solid rgba(10, 19, 23, 0.12)

### button-pill-tab
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm-bold}, rounded: {rounded.full}, padding: 8px 16px, border: 1px solid {colors.hairline}

### button-pill-tab-active
backgroundColor: {colors.ink-deep}, textColor: {colors.canvas}

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.circle}, size: 40px

### card-product-feature
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### card-feature-photo
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: 0, border: none

### card-promo-strip
backgroundColor: {colors.ink-deep}, textColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.section}

### card-icon-feature
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}

### card-checkout-summary
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}, shadow: rgba(20, 22, 26, 0.3) 0px 1px 4px 0px

### product-thumbnail
backgroundColor: {colors.surface-soft}, rounded: {rounded.xl}, padding: {spacing.base}, aspect-ratio: 1 / 1

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: {spacing.md}, border: 1px solid {colors.hairline}, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.fb-blue}

### text-input-error
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 1px solid {colors.critical-strong}

### search-pill
backgroundColor: {colors.surface-soft}, textColor: {colors.steel}, typography: {typography.body-sm}, rounded: {rounded.full}, padding: {spacing.md} {spacing.lg}, height: 40px

### radio-option
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.lg}, border: 1px solid rgba(10, 19, 23, 0.12)

### radio-option-selected
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, border: 2px solid #0143b5

### color-swatch-circle
rounded: {rounded.circle}, size: 32px, border: 2px solid {colors.canvas}

### badge-promo-yellow
backgroundColor: {colors.warning}, textColor: {colors.ink-deep}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-attention
backgroundColor: {colors.attention}, textColor: {colors.canvas}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-success
backgroundColor: {colors.success}, textColor: {colors.canvas}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-critical
backgroundColor: {colors.critical}, textColor: {colors.canvas}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### promo-banner
backgroundColor: {colors.ink-deep}, textColor: {colors.canvas}, typography: {typography.body-sm-bold}, padding: {spacing.md} {spacing.xl}

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### why-buy-tile
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xxl} {spacing.xl}, border: 1px solid {colors.hairline-soft}

### warranty-card
backgroundColor: {colors.surface-soft}, rounded: {rounded.xxl}, padding: {spacing.xxl}

### footer-region
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### hero-band-marketing
backgroundColor: {colors.canvas}, textColor: {colors.canvas}, typography: {typography.hero-display}, rounded: {rounded.xxxl}, padding: {spacing.section-lg}

### product-gallery-pdp
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.base}

### color-sku-picker-row
backgroundColor: {colors.surface-soft}, rounded: {rounded.lg}, padding: {spacing.base}

### feature-icon-row
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### tech-specs-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.lg}, padding: {spacing.lg}, border: 1px solid {colors.hairline-soft}

### testimonial-customer-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}
', '["design-brand", "meta", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (70, 'design_brand', 'minimax', 'design_system', '品牌设计规范 — minimax', '# 品牌设计规范: MiniMax

MiniMax presents itself as a premium AI infrastructure brand through a striking duality — bold black-pill CTAs and stark white canvas for marketing, paired with vibrant gradient product cards (orange-red, magenta-pink, purple, blue) that turn each model release into a distinctive visual identity. The system uses DM Sans across all surfaces, employs an oversized 80px hero display, anchors major actions in deep near-black pills, and layers content density via a 3-column documentation grid with sidebar nav, prose body, and TOC. Coverage spans the marketing homepage, model showcase pages, developer documentation, and platform pricing surfaces.

## 颜色体系 (Colors)

- **primary**: #0a0a0a
- **on-primary**: #ffffff
- **primary-soft**: #181e25
- **brand-coral**: #ff5530
- **brand-magenta**: #ea5ec1
- **brand-blue**: #1456f0
- **brand-blue-mid**: #3b82f6
- **brand-blue-deep**: #1d4ed8
- **brand-blue-700**: #17437d
- **brand-cyan**: #3daeff
- **brand-blue-200**: #bfdbfe
- **brand-purple**: #a855f7
- **canvas**: #ffffff
- **surface**: #f7f8fa
- **surface-soft**: #f2f3f5
- **hairline**: #e5e7eb
- **hairline-soft**: #eaecf0
- **ink**: #0a0a0a
- **ink-strong**: #000000
- **charcoal**: #222222
- **slate**: #45515e
- **steel**: #5f5f5f
- **stone**: #8e8e93
- **muted**: #a8aab2
- **success-bg**: #e8ffea
- **success-text**: #1ba673
- **on-dark**: #ffffff
- **footer-bg**: #0a0a0a

## 排版体系 (Typography)

- **hero-display**: font: DM Sans | size: 80px | weight: 600 | lh: 1.1 | ls: -2px
- **display-lg**: font: DM Sans | size: 56px | weight: 600 | lh: 1.1 | ls: -1.5px
- **heading-lg**: font: DM Sans | size: 40px | weight: 600 | lh: 1.2 | ls: -1px
- **heading-md**: font: DM Sans | size: 32px | weight: 600 | lh: 1.25 | ls: -0.5px
- **heading-sm**: font: DM Sans | size: 24px | weight: 600 | lh: 1.3
- **card-title**: font: DM Sans | size: 20px | weight: 600 | lh: 1.4
- **subtitle**: font: DM Sans | size: 18px | weight: 500 | lh: 1.5
- **body-md**: font: DM Sans | size: 16px | weight: 400 | lh: 1.5
- **body-md-bold**: font: DM Sans | size: 16px | weight: 700 | lh: 1.5
- **body-sm**: font: DM Sans | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: DM Sans | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: DM Sans | size: 13px | weight: 400 | lh: 1.7
- **caption-bold**: font: DM Sans | size: 13px | weight: 600 | lh: 1.5
- **micro**: font: DM Sans | size: 12px | weight: 400 | lh: 1.5
- **button-md**: font: DM Sans | size: 14px | weight: 600 | lh: 1.4

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 80px
- **hero**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 20px
- **xxxl**: 24px
- **hero**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 11px 24px

### button-primary-pressed
backgroundColor: {colors.charcoal}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 11px 24px, border: 1px solid {colors.ink}

### button-tertiary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 11px 24px, border: 1px solid {colors.hairline}

### button-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm-medium}, padding: 8px 0

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px, border: 1px solid {colors.hairline}

### product-card-coral
backgroundColor: {colors.brand-coral}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.xxl}

### product-card-magenta
backgroundColor: {colors.brand-magenta}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.xxl}

### product-card-blue
backgroundColor: {colors.brand-blue}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.xxl}

### product-card-purple
backgroundColor: {colors.brand-purple}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.xxl}

### product-card-photo
backgroundColor: {colors.primary}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.xxl}

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-feature
backgroundColor: {colors.surface}, rounded: {rounded.xl}, padding: {spacing.xxl}

### card-recommendation
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.lg}, border: 1px solid {colors.hairline}

### promo-cta-card
backgroundColor: {colors.brand-coral}, textColor: {colors.on-dark}, rounded: {rounded.hero}, padding: {spacing.section}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline}, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.brand-blue-deep}

### text-input-error
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 1px solid #d45656

### search-pill
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: {spacing.xs} {spacing.md}, height: 36px, border: 1px solid {colors.hairline}

### segmented-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.button-md}, rounded: 0, padding: {spacing.md} {spacing.lg}, border: 0 0 2px transparent solid

### segmented-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, border: 0 0 2px {colors.ink} solid

### pill-tab
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.full}, border: 1px solid {colors.primary}

### badge-success
backgroundColor: {colors.success-bg}, textColor: {colors.success-text}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-new
backgroundColor: {colors.brand-coral}, textColor: {colors.on-dark}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-beta
backgroundColor: {colors.brand-blue-200}, textColor: {colors.brand-blue-deep}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-code
backgroundColor: {colors.brand-blue-200}, textColor: {colors.brand-blue-deep}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 6px

### promo-banner
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.lg}

### data-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### data-table-header
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.caption-bold}, padding: {spacing.sm} {spacing.md}

### data-table-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, padding: {spacing.md}, border: 0 0 1px {colors.hairline-soft} solid

### sidebar-nav-item
backgroundColor: transparent, textColor: {colors.charcoal}, typography: {typography.body-sm}, rounded: {rounded.sm}, padding: {spacing.xs} {spacing.md}

### sidebar-nav-item-active
backgroundColor: {colors.surface}, textColor: {colors.ink}, typography: {typography.body-sm-medium}

### doc-toc-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.xs} 0

### ai-product-tile
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### footer-region
backgroundColor: {colors.footer-bg}, textColor: {colors.on-dark}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}

### footer-link
backgroundColor: transparent, textColor: {colors.muted}, typography: {typography.body-sm}, padding: {spacing.xxs} 0

### hero-band-marketing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.hero-display}, rounded: {rounded.lg}, padding: {spacing.hero}

### product-matrix-grid
backgroundColor: {colors.canvas}, rounded: {rounded.hero}, padding: {spacing.xxl}

### ai-product-matrix
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### docs-prose-block
backgroundColor: {colors.canvas}, textColor: {colors.charcoal}, typography: {typography.body-md}, padding: {spacing.xxl}

### models-comparison-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### testimonial-stat-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.heading-lg}, padding: {spacing.xl}
', '["design-brand", "minimax", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (71, 'design_brand', 'mintlify', 'design_system', '品牌设计规范 — mintlify', '# 品牌设计规范: Mintlify

Mintlify presents documentation infrastructure with a dual-mode aesthetic — atmospheric sky-gradient marketing heroes (cloud illustration backdrops, soft cream-to-blue washes) paired with dense developer-grade documentation surfaces. The system uses Inter for UI prose, Geist Mono for code, and a signature Mintlify green ({colors.brand-green}) reserved for accent CTAs and active states. Black-pill primary buttons dominate marketing, white-on-dark inversions appear on dark hero bands, and a 3-column documentation layout (sidebar / prose / TOC) anchors the developer experience. Coverage spans homepage, startups program, pricing comparison, and the live tabs documentation page.

## 颜色体系 (Colors)

- **primary**: #0a0a0a
- **on-primary**: #ffffff
- **brand-green**: #00d4a4
- **brand-green-deep**: #00b48a
- **brand-green-soft**: #7cebcb
- **brand-tag**: #3772cf
- **brand-warn**: #c37d0d
- **brand-annotate**: #1ba673
- **brand-error**: #d45656
- **brand-cursor**: #888888
- **hero-sky-from**: #87a8c8
- **hero-sky-to**: #f5e9d8
- **hero-dark-from**: #1a3d4a
- **hero-dark-to**: #2d5a4f
- **testimonial-orange**: #f55a3c
- **testimonial-orange-deep**: #cc3a1f
- **canvas**: #ffffff
- **canvas-dark**: #0a0a0a
- **surface**: #f7f7f7
- **surface-soft**: #fafafa
- **surface-code**: #1c1c1e
- **hairline**: #e5e5e5
- **hairline-soft**: #ededed
- **hairline-dark**: #1f1f1f
- **ink**: #0a0a0a
- **charcoal**: #1c1c1e
- **slate**: #3a3a3c
- **steel**: #5a5a5c
- **stone**: #888888
- **muted**: #a8a8aa
- **on-dark**: #ffffff
- **on-dark-muted**: #b3b3b3

## 排版体系 (Typography)

- **hero-display**: font: Inter | size: 72px | weight: 600 | lh: 1.05 | ls: -2px
- **display-lg**: font: Inter | size: 56px | weight: 600 | lh: 1.1 | ls: -1.5px
- **heading-1**: font: Inter | size: 48px | weight: 600 | lh: 1.1 | ls: -1px
- **heading-2**: font: Inter | size: 36px | weight: 600 | lh: 1.2 | ls: -0.5px
- **heading-3**: font: Inter | size: 28px | weight: 600 | lh: 1.25
- **heading-4**: font: Inter | size: 22px | weight: 600 | lh: 1.3
- **heading-5**: font: Inter | size: 18px | weight: 600 | lh: 1.4
- **subtitle**: font: Inter | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: Inter | size: 16px | weight: 400 | lh: 1.5
- **body-md-medium**: font: Inter | size: 16px | weight: 500 | lh: 1.5
- **body-sm**: font: Inter | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: Inter | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: Inter | size: 13px | weight: 400 | lh: 1.4
- **caption-bold**: font: Inter | size: 13px | weight: 600 | lh: 1.4
- **micro**: font: Inter | size: 12px | weight: 500 | lh: 1.4
- **micro-uppercase**: font: Inter | size: 11px | weight: 600 | lh: 1.4 | ls: 0.5px
- **button-md**: font: Inter | size: 14px | weight: 500 | lh: 1.3
- **code-md**: font: Geist Mono | size: 14px | weight: 400 | lh: 1.5
- **code-sm**: font: Geist Mono | size: 13px | weight: 400 | lh: 1.4
- **code-inline**: font: Geist Mono | size: 13px | weight: 500 | lh: 1.3

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 96px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 20px

### button-primary-pressed
backgroundColor: {colors.charcoal}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-accent-green
backgroundColor: {colors.brand-green}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 20px

### button-on-dark
backgroundColor: {colors.on-dark}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 20px

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 20px, border: 1px solid {colors.hairline}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 12px

### button-link
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm-medium}, padding: 0

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 32px, border: 1px solid {colors.hairline}

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-feature
backgroundColor: {colors.surface}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-help
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-startup-perk
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### pricing-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### pricing-card-featured
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 2px solid {colors.brand-green}, shadow: rgba(0, 212, 164, 0.08) 0px 8px 24px

### testimonial-card-feature
backgroundColor: {colors.testimonial-orange}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: {spacing.section}

### testimonial-card-quote
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline}, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.brand-green}

### search-pill
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: {spacing.xs} {spacing.md}, height: 36px, border: 1px solid {colors.hairline}

### segmented-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}, border: 0 0 2px transparent solid

### segmented-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm-medium}, border: 0 0 2px {colors.ink} solid

### pill-tab
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: 8px 16px, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.full}, border: 1px solid {colors.primary}

### toggle-monthly-yearly
backgroundColor: {colors.surface}, textColor: {colors.ink}, rounded: {rounded.full}, padding: 4px

### badge-discount
backgroundColor: {colors.brand-green}, textColor: {colors.primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 2px 8px

### badge-required
backgroundColor: {colors.brand-error}, textColor: {colors.on-dark}, typography: {typography.micro-uppercase}, rounded: {rounded.sm}, padding: 2px 6px

### badge-type
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.code-sm}, rounded: {rounded.sm}, padding: 2px 6px

### badge-tag
backgroundColor: rgba(55, 114, 207, 0.15), textColor: {colors.brand-tag}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### promo-banner
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}

### code-block
backgroundColor: {colors.surface-code}, textColor: {colors.on-dark}, typography: {typography.code-md}, rounded: {rounded.md}, padding: {spacing.md}

### code-block-header
backgroundColor: {colors.surface-code}, textColor: {colors.on-dark-muted}, typography: {typography.caption}, padding: {spacing.xs} {spacing.md}, border: 0 0 1px {colors.hairline-dark} solid

### code-inline
backgroundColor: {colors.surface}, textColor: {colors.charcoal}, typography: {typography.code-inline}, rounded: {rounded.xs}, padding: 2px 6px, border: 1px solid {colors.hairline}

### property-row
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm}, padding: {spacing.md} 0, border: 0 0 1px {colors.hairline-soft} solid

### feature-comparison-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### feature-comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, padding: {spacing.md} {spacing.lg}, border: 0 0 1px {colors.hairline-soft} solid

### sidebar-nav-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm}, rounded: {rounded.sm}, padding: {spacing.xs} {spacing.md}

### sidebar-nav-item-active
backgroundColor: {colors.surface}, textColor: {colors.ink}, typography: {typography.body-sm-medium}

### sidebar-section-header
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.micro-uppercase}, padding: {spacing.md} {spacing.md} {spacing.xs}

### doc-toc-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.xxs} 0

### doc-toc-item-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm-medium}

### copy-code-button
backgroundColor: transparent, textColor: {colors.on-dark-muted}, typography: {typography.caption}, rounded: {rounded.sm}, padding: {spacing.xxs} {spacing.xs}, border: 1px solid {colors.hairline-dark}

### hero-band-sky
backgroundColor: {colors.hero-sky-from}, textColor: {colors.on-dark}, rounded: 0, padding: {spacing.hero}

### hero-band-dark
backgroundColor: {colors.hero-dark-from}, textColor: {colors.on-dark}, rounded: 0, padding: {spacing.hero}

### hero-product-mockup
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: 0, border: 1px solid {colors.hairline-soft}, shadow: rgba(0, 0, 0, 0.12) 0px 24px 48px -8px

### logo-wall-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-md-medium}, padding: {spacing.lg}

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.md}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### footer-region
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}, border: 1px solid {colors.hairline}

### footer-link
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.xxs} 0

### startup-program-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### founder-quote-card
backgroundColor: {colors.testimonial-orange}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: {spacing.xxl}
', '["design-brand", "mintlify", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (72, 'design_brand', 'miro', 'design_system', '品牌设计规范 — miro', '# 品牌设计规范: Miro

Miro presents itself as the AI-powered visual workspace through a confident, almost playful brand voice — anchored by its signature canary yellow ({colors.brand-yellow}) wordmark over white canvas, broken open by colorful pastel feature tints (rose, teal, coral, orange, mint) that echo the actual sticky-note color palette used on the live whiteboard. Black-pill primary buttons dominate marketing, real Miro-board mockups serve as feature illustrations, and a 4-tier pricing grid leads into a dense comparison table. Roobert PRO carries display headlines; the system supports homepage, pricing, AI Workflows product page, agile vertical, and customer stories surfaces.

## 颜色体系 (Colors)

- **primary**: #1c1c1e
- **on-primary**: #ffffff
- **brand-yellow**: #ffd02f
- **brand-yellow-deep**: #fcb900
- **yellow-light**: #fff4c4
- **yellow-dark**: #746019
- **brand-blue**: #4262ff
- **blue-450**: #5b76fe
- **blue-pressed**: #2a41b6
- **brand-coral**: #ff9999
- **coral-light**: #ffc6c6
- **coral-dark**: #600000
- **brand-rose**: #ffd8f4
- **rose-light**: #fde0f0
- **brand-pink**: #fde0f0
- **brand-teal**: #0fbcb0
- **teal-light**: #c3faf5
- **moss-dark**: #187574
- **brand-orange-light**: #ffe6cd
- **brand-red**: #fbd4d4
- **brand-red-dark**: #e3c5c5
- **success-accent**: #00b473
- **canvas**: #ffffff
- **surface**: #f7f8fa
- **surface-soft**: #fafbfc
- **surface-yellow**: #fff8e0
- **surface-pricing-featured**: #f5f3ff
- **hairline**: #e0e2e8
- **hairline-soft**: #eef0f3
- **hairline-strong**: #c7cad5
- **ink-deep**: #050038
- **ink**: #1c1c1e
- **charcoal**: #2c2c34
- **slate**: #555a6a
- **steel**: #6b6f7e
- **stone**: #8e91a0
- **muted**: #a5a8b5
- **on-dark**: #ffffff
- **on-dark-muted**: #a5a8b5
- **footer-bg**: #1c1c1e

## 排版体系 (Typography)

- **hero-display**: font: Roobert PRO | size: 80px | weight: 500 | lh: 1.05 | ls: -2px
- **display-lg**: font: Roobert PRO | size: 60px | weight: 500 | lh: 1.1 | ls: -1.5px
- **heading-1**: font: Roobert PRO | size: 48px | weight: 500 | lh: 1.15 | ls: -1px
- **heading-2**: font: Roobert PRO | size: 36px | weight: 500 | lh: 1.2 | ls: -0.5px
- **heading-3**: font: Roobert PRO | size: 28px | weight: 500 | lh: 1.25
- **heading-4**: font: Roobert PRO | size: 22px | weight: 500 | lh: 1.3
- **heading-5**: font: Roobert PRO | size: 18px | weight: 500 | lh: 1.4
- **subtitle**: font: Roobert PRO | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: Roobert PRO | size: 16px | weight: 400 | lh: 1.5
- **body-md-medium**: font: Roobert PRO | size: 16px | weight: 500 | lh: 1.5
- **body-sm**: font: Roobert PRO | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: Roobert PRO | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: Roobert PRO | size: 13px | weight: 400 | lh: 1.4
- **caption-bold**: font: Roobert PRO | size: 13px | weight: 600 | lh: 1.4
- **micro**: font: Roobert PRO | size: 12px | weight: 500 | lh: 1.4
- **micro-uppercase**: font: Roobert PRO | size: 11px | weight: 600 | lh: 1.4 | ls: 0.5px
- **button-md**: font: Roobert PRO | size: 14px | weight: 500 | lh: 1.3
- **stat-display**: font: Roobert PRO | size: 64px | weight: 500 | lh: 1.1 | ls: -1.5px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 96px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 20px
- **xxxl**: 28px
- **feature**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px

### button-primary-pressed
backgroundColor: {colors.charcoal}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-yellow
backgroundColor: {colors.brand-yellow}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px

### button-blue
backgroundColor: {colors.brand-blue}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px, border: 1px solid {colors.hairline-strong}

### button-on-dark
backgroundColor: {colors.on-dark}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px

### button-ghost
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 12px

### button-link
backgroundColor: transparent, textColor: {colors.brand-blue}, typography: {typography.body-sm-medium}, padding: 0

### button-icon-circular
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px, border: 1px solid {colors.hairline}

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### card-feature
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### card-feature-yellow
backgroundColor: {colors.brand-yellow}, textColor: {colors.primary}, rounded: {rounded.xxxl}, padding: {spacing.xxl}

### card-feature-coral
backgroundColor: {colors.coral-light}, textColor: {colors.primary}, rounded: {rounded.xxxl}, padding: {spacing.xxl}

### card-feature-teal
backgroundColor: {colors.teal-light}, textColor: {colors.primary}, rounded: {rounded.xxxl}, padding: {spacing.xxl}

### card-feature-rose
backgroundColor: {colors.rose-light}, textColor: {colors.primary}, rounded: {rounded.xxxl}, padding: {spacing.xxl}

### card-customer-story
backgroundColor: {colors.canvas}, rounded: {rounded.xxxl}, padding: 0, border: 1px solid {colors.hairline-soft}

### card-stat
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.stat-display}, padding: {spacing.lg}

### pricing-card
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### pricing-card-featured
backgroundColor: {colors.surface-pricing-featured}, rounded: {rounded.xl}, padding: {spacing.xxl}, border: 2px solid {colors.brand-blue}

### pricing-card-enterprise
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.xl}, padding: {spacing.xxl}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline-strong}, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.brand-blue}

### search-pill
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: {spacing.xs} {spacing.md}, height: 40px, border: 1px solid {colors.hairline}

### filter-dropdown
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline-strong}

### pill-tab
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.full}, border: 1px solid {colors.primary}

### toggle-monthly-yearly
backgroundColor: {colors.surface}, textColor: {colors.ink}, rounded: {rounded.full}, padding: 4px

### badge-promo
backgroundColor: {colors.brand-yellow}, textColor: {colors.primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-tag-yellow
backgroundColor: {colors.surface-yellow}, textColor: {colors.yellow-dark}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-tag-purple
backgroundColor: {colors.surface-pricing-featured}, textColor: {colors.brand-blue}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-tag-coral
backgroundColor: {colors.coral-light}, textColor: {colors.coral-dark}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-success
backgroundColor: {colors.success-accent}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-discount
backgroundColor: {colors.brand-yellow}, textColor: {colors.primary}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 6px

### promo-banner
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}

### comparison-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, padding: {spacing.md} {spacing.lg}, border: 0 0 1px {colors.hairline-soft} solid

### template-card
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.md}, border: 1px solid {colors.hairline}

### whiteboard-mockup
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: 0, border: 1px solid {colors.hairline-soft}, shadow: rgba(5, 0, 56, 0.08) 0px 12px 32px -4px

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.md}, padding: {spacing.xl}, border: 0 0 1px {colors.hairline} solid

### logo-wall-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-md-medium}, padding: {spacing.lg}

### hero-band-marketing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.hero-display}, rounded: 0, padding: {spacing.hero}

### cta-banner-dark
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: {rounded.feature}, padding: {spacing.section}

### industry-tile
backgroundColor: {colors.canvas}, rounded: {rounded.xl}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### capterra-badge
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline}

### footer-region
backgroundColor: {colors.footer-bg}, textColor: {colors.on-dark}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}

### footer-link
backgroundColor: transparent, textColor: {colors.on-dark-muted}, typography: {typography.body-sm}, padding: {spacing.xxs} 0

### app-store-badge
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.caption-bold}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}
', '["design-brand", "miro", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:27', '2026-07-02 00:11:27'),
  (73, 'design_brand', 'mistral-ai', 'design_system', '品牌设计规范 — mistral.ai', '# 品牌设计规范: Mistral AI

Mistral AI brands itself with a singular signature — atmospheric sunset gradients (mustard, orange, deep red) layered over photography of mountains, plus a horizontal "sunset stripe" bar that closes every page. The system pairs warm cream-yellow surfaces ({colors.cream}) with a saturated orange primary CTA ({colors.primary}) and uses an elegant near-serif voice for hero displays. Coverage spans homepage (Frontier AI hero), Le Studio product page, Coding solutions, news article surfaces, contact form, and services tier page — all anchored by the signature gradient closing band.

## 颜色体系 (Colors)

- **primary**: #fa520f
- **primary-deep**: #cc3a05
- **on-primary**: #ffffff
- **sunshine-300**: #ffd06a
- **sunshine-500**: #ffb83e
- **sunshine-700**: #ffa110
- **sunshine-800**: #ff8105
- **sunshine-900**: #ff8a00
- **yellow-saturated**: #ffd900
- **cream**: #fff8e0
- **cream-light**: #fffaeb
- **cream-deeper**: #fff0c2
- **beige-deep**: #e6d5a8
- **block-5**: #ffe295
- **block-6**: #ffd900
- **block-7**: #ff8105
- **ink**: #1f1f1f
- **ink-tint**: #3d3d3d
- **charcoal**: #2c2c2c
- **slate**: #4a4a4a
- **steel**: #6a6a6a
- **stone**: #8a8a8a
- **muted**: #a8a8a8
- **hairline**: #e5e5e5
- **hairline-soft**: #ededed
- **hairline-strong**: #c7c7c7
- **canvas**: #ffffff
- **surface**: #fafafa
- **surface-cream**: #fff8e0
- **surface-cream-soft**: #fffaeb
- **surface-code**: #1c1c1e
- **on-dark**: #ffffff
- **on-dark-muted**: #a8a8a8
- **on-cream**: #1f1f1f
- **footer-cream**: #fff8e0
- **link**: #fa520f

## 排版体系 (Typography)

- **hero-display**: font: PP Editorial Old | size: 84px | weight: 400 | lh: 1.05 | ls: -1.5px
- **display-lg**: font: PP Editorial Old | size: 64px | weight: 400 | lh: 1.1 | ls: -1px
- **heading-1**: font: PP Editorial Old | size: 52px | weight: 400 | lh: 1.15 | ls: -0.5px
- **heading-2**: font: Inter | size: 36px | weight: 500 | lh: 1.2 | ls: -0.5px
- **heading-3**: font: Inter | size: 28px | weight: 500 | lh: 1.25
- **heading-4**: font: Inter | size: 22px | weight: 500 | lh: 1.3
- **heading-5**: font: Inter | size: 18px | weight: 500 | lh: 1.4
- **subtitle**: font: Inter | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: Inter | size: 16px | weight: 400 | lh: 1.55
- **body-md-medium**: font: Inter | size: 16px | weight: 500 | lh: 1.55
- **body-sm**: font: Inter | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: Inter | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: Inter | size: 13px | weight: 400 | lh: 1.4
- **caption-bold**: font: Inter | size: 13px | weight: 600 | lh: 1.4
- **micro**: font: Inter | size: 12px | weight: 500 | lh: 1.4
- **micro-uppercase**: font: Inter | size: 11px | weight: 600 | lh: 1.4 | ls: 1px
- **button-md**: font: Inter | size: 14px | weight: 500 | lh: 1.3
- **stat-display**: font: PP Editorial Old | size: 56px | weight: 400 | lh: 1.1 | ls: -1px
- **code-md**: font: JetBrains Mono | size: 14px | weight: 400 | lh: 1.5

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 96px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 20px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 20px

### button-primary-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-cream
backgroundColor: {colors.cream}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 20px, border: 1px solid {colors.beige-deep}

### button-dark
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 20px

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 20px, border: 1px solid {colors.hairline-strong}

### button-on-cream
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 20px, border: 1px solid {colors.beige-deep}

### button-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-sm-medium}, padding: 0

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### card-feature
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### card-cream
backgroundColor: {colors.cream}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.beige-deep}

### card-cream-soft
backgroundColor: {colors.surface-cream-soft}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-product
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}, shadow: rgba(0, 0, 0, 0.04) 0px 4px 12px

### card-photographic
backgroundColor: {colors.surface-code}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: 0

### pricing-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### pricing-card-featured
backgroundColor: {colors.cream}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 2px solid {colors.primary}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline-strong}, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.primary}

### text-area
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.md}, border: 1px solid {colors.hairline-strong}

### contact-form-panel
backgroundColor: {colors.cream}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.beige-deep}

### pill-tab
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, rounded: {rounded.full}, border: 1px solid {colors.ink}

### segmented-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}, border: 0 0 2px transparent solid

### segmented-tab-active
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-sm-medium}, border: 0 0 2px {colors.primary} solid

### badge-orange
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-cream
backgroundColor: {colors.cream-deeper}, textColor: {colors.ink}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-dark
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### promo-banner
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}

### hero-band-sunset
backgroundColor: {colors.sunshine-700}, textColor: {colors.ink}, rounded: 0, padding: {spacing.hero}

### sunset-stripe-band
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, rounded: 0, padding: {spacing.lg} 0

### cta-banner-cream
backgroundColor: {colors.cream}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.section}

### code-block
backgroundColor: {colors.surface-code}, textColor: {colors.on-dark}, typography: {typography.code-md}, rounded: {rounded.md}, padding: {spacing.md}

### code-block-header
backgroundColor: {colors.surface-code}, textColor: {colors.on-dark-muted}, typography: {typography.caption}, padding: {spacing.xs} {spacing.md}, border: 0 0 1px rgba(255,255,255,0.08) solid

### feature-icon-tile
backgroundColor: {colors.cream}, rounded: {rounded.md}, padding: {spacing.md}, border: 1px solid {colors.beige-deep}

### industry-tile
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline-soft}

### stat-cell
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.stat-display}, padding: {spacing.lg}

### customer-testimonial-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline-soft}

### logo-wall-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-md-medium}, padding: {spacing.lg}

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.md}, padding: {spacing.xl}, border: 0 0 1px {colors.hairline} solid

### footer-region
backgroundColor: {colors.footer-cream}, textColor: {colors.ink}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}

### footer-link
backgroundColor: transparent, textColor: {colors.primary}, typography: {typography.body-sm}, padding: {spacing.xxs} 0

### app-store-badge
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.caption-bold}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}
', '["design-brand", "mistral.ai", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (74, 'design_brand', 'mongodb', 'design_system', '品牌设计规范 — mongodb', '# 品牌设计规范: MongoDB

MongoDB carries a strong dual-mode visual identity — dark deep-teal hero bands with bright MongoDB green ({colors.brand-green}) CTAs paired with stark white documentation surfaces. The signature green pill button is unmistakable across product, pricing, learning, and AI use-case surfaces. The system uses Euclid Circular A as its display face, anchors a 3-tier pricing comparison (Free / Flex / Dedicated), and presents extensive course catalogs in card grids with colored category tags. Coverage spans homepage, Atlas product page, Community Edition, MongoDB University, AI use cases, and pricing.

## 颜色体系 (Colors)

- **primary**: #00ed64
- **primary-deep**: #00b545
- **primary-pressed**: #008c34
- **on-primary**: #001e2b
- **brand-green**: #00ed64
- **brand-green-dark**: #00684a
- **brand-green-mid**: #00a35c
- **brand-green-soft**: #c3f0d2
- **brand-teal-deep**: #001e2b
- **brand-teal**: #003d4f
- **brand-teal-mid**: #00684a
- **accent-purple**: #7b3ff2
- **accent-orange**: #fa6e39
- **accent-pink**: #f06bb8
- **accent-blue**: #3d4f9f
- **semantic-warning-bg**: #fff8e0
- **semantic-warning-text**: #946f3f
- **canvas**: #ffffff
- **canvas-dark**: #001e2b
- **surface**: #f9fbfa
- **surface-soft**: #f4f7f6
- **surface-feature**: #e3fcef
- **hairline**: #e1e5e8
- **hairline-soft**: #eceff1
- **hairline-strong**: #c1ccd6
- **hairline-dark**: #1c2d38
- **ink**: #001e2b
- **charcoal**: #1c2d38
- **slate**: #3d4f5b
- **steel**: #5c6c7a
- **stone**: #7c8c9a
- **muted**: #a8b3bc
- **on-dark**: #ffffff
- **on-dark-muted**: #a8b3bc

## 排版体系 (Typography)

- **hero-display**: font: Euclid Circular A | size: 72px | weight: 500 | lh: 1.1 | ls: -1.5px
- **display-lg**: font: Euclid Circular A | size: 56px | weight: 500 | lh: 1.15 | ls: -1px
- **heading-1**: font: Euclid Circular A | size: 48px | weight: 500 | lh: 1.2 | ls: -0.5px
- **heading-2**: font: Euclid Circular A | size: 36px | weight: 500 | lh: 1.25 | ls: -0.5px
- **heading-3**: font: Euclid Circular A | size: 28px | weight: 500 | lh: 1.3
- **heading-4**: font: Euclid Circular A | size: 22px | weight: 500 | lh: 1.35
- **heading-5**: font: Euclid Circular A | size: 18px | weight: 600 | lh: 1.4
- **subtitle**: font: Euclid Circular A | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: Euclid Circular A | size: 16px | weight: 400 | lh: 1.55
- **body-md-medium**: font: Euclid Circular A | size: 16px | weight: 500 | lh: 1.55
- **body-sm**: font: Euclid Circular A | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: Euclid Circular A | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: Euclid Circular A | size: 13px | weight: 400 | lh: 1.4
- **caption-bold**: font: Euclid Circular A | size: 13px | weight: 600 | lh: 1.4
- **micro**: font: Euclid Circular A | size: 12px | weight: 500 | lh: 1.4
- **micro-uppercase**: font: Euclid Circular A | size: 11px | weight: 600 | lh: 1.4 | ls: 1px
- **button-md**: font: Euclid Circular A | size: 14px | weight: 600 | lh: 1.3
- **code-md**: font: Source Code Pro | size: 14px | weight: 400 | lh: 1.55

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 96px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.brand-green}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 22px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 22px, border: 1px solid {colors.hairline-strong}

### button-on-dark
backgroundColor: {colors.brand-green}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 22px

### button-secondary-on-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 10px 22px, border: 1px solid {colors.hairline-dark}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 12px

### button-link
backgroundColor: transparent, textColor: {colors.brand-green-dark}, typography: {typography.body-sm-medium}, padding: 0

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-feature
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### card-product-deploy
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### card-feature-dark
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-course
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-cert
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### pricing-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### pricing-card-featured
backgroundColor: {colors.surface-feature}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 2px solid {colors.brand-green}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline-strong}, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.brand-green-dark}

### search-pill
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, height: 44px, border: 1px solid {colors.hairline-strong}

### search-pill-large
backgroundColor: {colors.canvas}, textColor: {colors.steel}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.md}, height: 56px, border: 1px solid {colors.hairline-strong}

### pill-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, rounded: {rounded.full}, border: 1px solid {colors.ink}

### segmented-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}, border: 0 0 2px transparent solid

### segmented-tab-active
backgroundColor: transparent, textColor: {colors.brand-green-dark}, typography: {typography.body-sm-medium}, border: 0 0 2px {colors.brand-green-dark} solid

### badge-green
backgroundColor: {colors.brand-green}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-green-soft
backgroundColor: {colors.brand-green-soft}, textColor: {colors.brand-green-dark}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-purple
backgroundColor: {colors.accent-purple}, textColor: {colors.on-dark}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-orange
backgroundColor: {colors.accent-orange}, textColor: {colors.on-dark}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-popular
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.brand-green}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### promo-banner
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.on-dark}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}

### hero-band-dark
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.on-dark}, rounded: 0, padding: {spacing.hero}

### hero-platform-card
backgroundColor: {colors.brand-teal-mid}, textColor: {colors.on-dark}, rounded: {rounded.xl}, padding: {spacing.xxl}

### cta-banner-dark
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: {spacing.section}

### code-block
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.code-md}, rounded: {rounded.md}, padding: {spacing.md}

### code-mockup-card
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, rounded: {rounded.lg}, padding: {spacing.lg}

### comparison-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, padding: {spacing.md} {spacing.lg}, border: 0 0 1px {colors.hairline-soft} solid

### service-tile
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### why-card
backgroundColor: {colors.surface}, rounded: {rounded.lg}, padding: {spacing.xl}

### customer-testimonial-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### logo-wall-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-md-medium}, padding: {spacing.lg}

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.md}, padding: {spacing.xl}, border: 0 0 1px {colors.hairline} solid

### footer-region
backgroundColor: {colors.brand-teal-deep}, textColor: {colors.on-dark}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}

### footer-link
backgroundColor: transparent, textColor: {colors.on-dark-muted}, typography: {typography.body-sm}, padding: {spacing.xxs} 0
', '["design-brand", "mongodb", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (75, 'design_brand', 'nike', 'design_system', '品牌设计规范 — nike', '# 品牌设计规范: Nike

A photography-first commerce system built on extreme typographic contrast — towering uppercase Futura display lockups burned into editorial campaign imagery, sitting above a dense, neutral, near-monochrome retail chrome of pill-shaped black CTAs, gray search and tag pills, and tight 8px-grid product cards. The brand''s voice is athletic, kinetic, and absolute: pure black, pure white, a single soft surface gray, and a deliberately small set of semantic accents (sale red, success green, restrained category tints) — every chromatic moment is reserved for editorial photography or pricing signal, never decorative chrome.


## 颜色体系 (Colors)

- **primary**: #111111
- **on-primary**: #ffffff
- **canvas**: #ffffff
- **soft-cloud**: #f5f5f5
- **ink**: #111111
- **charcoal**: #39393b
- **ash**: #4b4b4d
- **mute**: #707072
- **stone**: #9e9ea0
- **hairline**: #cacacb
- **hairline-soft**: #e5e5e5
- **sale**: #d30005
- **sale-deep**: #780700
- **success**: #007d48
- **success-bright**: #1eaa52
- **info**: #1151ff
- **info-deep**: #0034e3
- **accent-pink**: #ed1aa0
- **accent-pink-soft**: #ffb0dd
- **accent-purple-soft**: #beaffd
- **accent-purple-pale**: #d6d1ff
- **accent-teal**: #0a7281
- **accent-pink-deep**: #4c012d

## 排版体系 (Typography)

- **display-campaign**: font: Nike Futura ND | size: 96px | weight: 500 | lh: 0.9 | ls: 0 | transform: uppercase
- **heading-xl**: font: Helvetica Now Display Medium | size: 32px | weight: 500 | lh: 1.2 | ls: 0
- **heading-lg**: font: Helvetica Now Display Medium | size: 24px | weight: 500 | lh: 1.2 | ls: 0
- **heading-md**: font: Helvetica Now Display Medium | size: 16px | weight: 500 | lh: 1.75 | ls: 0
- **body-md**: font: Helvetica Now Text | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: Helvetica Now Text Medium | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **button-lg**: font: Helvetica Now Display Medium | size: 24px | weight: 500 | lh: 1.2 | ls: 0
- **button-md**: font: Helvetica Now Text Medium | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **button-sm**: font: Helvetica Now Text Medium | size: 14px | weight: 500 | lh: 1.5 | ls: 0
- **link-md**: font: Helvetica Now Text | size: 16px | weight: 500 | lh: 1.75 | ls: 0
- **caption-md**: font: Helvetica Now Text Medium | size: 14px | weight: 500 | lh: 1.5 | ls: 0
- **caption-sm**: font: Helvetica Now Text Medium | size: 12px | weight: 500 | lh: 1.5 | ls: 0
- **utility-xs**: font: Helvetica Neue | size: 9px | weight: 500 | lh: 1.75 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 18px
- **xl**: 24px
- **xxl**: 30px
- **section**: 48px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 18px
- **md**: 24px
- **lg**: 30px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 16px 32px, height: 48px

### button-primary-active
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}

### button-secondary
backgroundColor: {colors.soft-cloud}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 16px 32px, height: 48px

### button-outline-on-image
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px

### button-icon-circular
backgroundColor: {colors.soft-cloud}, textColor: {colors.ink}, rounded: {rounded.full}, size: 40px

### search-pill
backgroundColor: {colors.soft-cloud}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 16px, height: 40px

### search-pill-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.md}

### filter-chip
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 16px

### filter-chip-active
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}

### badge-promo
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption-sm}, rounded: {rounded.full}, padding: 4px 12px

### badge-sale-text
textColor: {colors.sale}, typography: {typography.caption-md}

### product-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, padding: 0px

### product-card-image
backgroundColor: {colors.soft-cloud}, rounded: {rounded.none}

### swatch-dot
backgroundColor: {colors.ink}, rounded: {rounded.full}, size: 12px

### swatch-dot-active
backgroundColor: {colors.ink}, rounded: {rounded.full}, size: 12px

### campaign-tile
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.display-campaign}, rounded: {rounded.none}

### category-icon-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption-md}, rounded: {rounded.none}

### member-benefit-card
backgroundColor: {colors.ink}, textColor: {colors.on-primary}, typography: {typography.heading-lg}, rounded: {rounded.none}

### faq-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.heading-md}, rounded: {rounded.none}, padding: 24px 0px

### pdp-disclosure-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, padding: 24px 0px

### utility-bar
backgroundColor: {colors.soft-cloud}, textColor: {colors.ink}, typography: {typography.caption-sm}, rounded: {rounded.none}, height: 36px

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 56px

### filter-sidebar
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}

### footer
backgroundColor: {colors.canvas}, textColor: {colors.mute}, typography: {typography.caption-md}, rounded: {rounded.none}
', '["design-brand", "nike", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (76, 'design_brand', 'notion', 'design_system', '品牌设计规范 — notion', '# 品牌设计规范: Notion

Notion presents itself as the all-in-one workspace through a confident, illustration-rich brand voice — anchored by a deep navy hero band ({colors.brand-navy}) decorated with brand-colored sticky-note dots and mesh wire illustrations, a signature purple pill primary CTA ({colors.primary}), and a rich palette of pastel-tinted feature cards that echo the colorful database properties of the live product. The system uses a Notion-Sans (Inter-based) typeface across every UI surface, anchors a 4-tier pricing comparison (Free / Plus / Business / Enterprise), and presents the live workspace UI mockup directly inside the hero band. Coverage spans homepage, Enterprise, Product AI, Product Agents, Startups, and Pricing surfaces.

## 颜色体系 (Colors)

- **primary**: #5645d4
- **primary-pressed**: #4534b3
- **primary-deep**: #3a2a99
- **on-primary**: #ffffff
- **brand-navy**: #0a1530
- **brand-navy-deep**: #070f24
- **brand-navy-mid**: #1a2a52
- **link-blue**: #0075de
- **link-blue-pressed**: #005bab
- **brand-orange**: #dd5b00
- **brand-orange-deep**: #793400
- **brand-pink**: #ff64c8
- **brand-pink-deep**: #a02e6d
- **brand-purple**: #7b3ff2
- **brand-purple-300**: #d6b6f6
- **brand-purple-800**: #391c57
- **brand-teal**: #2a9d99
- **brand-green**: #1aae39
- **brand-yellow**: #f5d75e
- **brand-brown**: #523410
- **card-tint-peach**: #ffe8d4
- **card-tint-rose**: #fde0ec
- **card-tint-mint**: #d9f3e1
- **card-tint-lavender**: #e6e0f5
- **card-tint-sky**: #dcecfa
- **card-tint-yellow**: #fef7d6
- **card-tint-yellow-bold**: #f9e79f
- **card-tint-cream**: #f8f5e8
- **card-tint-gray**: #f0eeec
- **canvas**: #ffffff
- **surface**: #f6f5f4
- **surface-soft**: #fafaf9
- **hairline**: #e5e3df
- **hairline-soft**: #ede9e4
- **hairline-strong**: #c8c4be
- **ink-deep**: #000000
- **ink**: #1a1a1a
- **charcoal**: #37352f
- **slate**: #5d5b54
- **steel**: #787671
- **stone**: #a4a097
- **muted**: #bbb8b1
- **on-dark**: #ffffff
- **on-dark-muted**: #a4a097
- **semantic-success**: #1aae39
- **semantic-warning**: #dd5b00
- **semantic-error**: #e03131

## 排版体系 (Typography)

- **hero-display**: font: Notion Sans | size: 80px | weight: 600 | lh: 1.05 | ls: -2px
- **display-lg**: font: Notion Sans | size: 56px | weight: 600 | lh: 1.1 | ls: -1px
- **heading-1**: font: Notion Sans | size: 48px | weight: 600 | lh: 1.15 | ls: -0.5px
- **heading-2**: font: Notion Sans | size: 36px | weight: 600 | lh: 1.2 | ls: -0.5px
- **heading-3**: font: Notion Sans | size: 28px | weight: 600 | lh: 1.25
- **heading-4**: font: Notion Sans | size: 22px | weight: 600 | lh: 1.3
- **heading-5**: font: Notion Sans | size: 18px | weight: 600 | lh: 1.4
- **subtitle**: font: Notion Sans | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: Notion Sans | size: 16px | weight: 400 | lh: 1.55
- **body-md-medium**: font: Notion Sans | size: 16px | weight: 500 | lh: 1.55
- **body-sm**: font: Notion Sans | size: 14px | weight: 400 | lh: 1.5
- **body-sm-medium**: font: Notion Sans | size: 14px | weight: 500 | lh: 1.5
- **caption**: font: Notion Sans | size: 13px | weight: 400 | lh: 1.4
- **caption-bold**: font: Notion Sans | size: 13px | weight: 600 | lh: 1.4
- **micro**: font: Notion Sans | size: 12px | weight: 500 | lh: 1.4
- **micro-uppercase**: font: Notion Sans | size: 11px | weight: 600 | lh: 1.4 | ls: 1px
- **button-md**: font: Notion Sans | size: 14px | weight: 500 | lh: 1.3

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section-sm**: 48px
- **section**: 64px
- **section-lg**: 96px
- **hero**: 120px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 20px
- **xxxl**: 24px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 18px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}

### button-primary-disabled
backgroundColor: {colors.hairline}, textColor: {colors.muted}

### button-dark
backgroundColor: {colors.ink-deep}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 18px

### button-secondary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 18px, border: 1px solid {colors.hairline-strong}

### button-on-dark
backgroundColor: {colors.on-dark}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 18px

### button-secondary-on-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 10px 18px, border: 1px solid {colors.on-dark-muted}

### button-ghost
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 8px 12px

### button-link
backgroundColor: transparent, textColor: {colors.link-blue}, typography: {typography.body-sm-medium}, padding: 0

### card-base
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-feature
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### card-feature-yellow-bold
backgroundColor: {colors.card-tint-yellow-bold}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-peach
backgroundColor: {colors.card-tint-peach}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-rose
backgroundColor: {colors.card-tint-rose}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-mint
backgroundColor: {colors.card-tint-mint}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-sky
backgroundColor: {colors.card-tint-sky}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-lavender
backgroundColor: {colors.card-tint-lavender}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-yellow
backgroundColor: {colors.card-tint-yellow}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-feature-cream
backgroundColor: {colors.card-tint-cream}, textColor: {colors.charcoal}, rounded: {rounded.lg}, padding: {spacing.xxl}

### card-agent-tile
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### card-template
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.lg}, border: 1px solid {colors.hairline}

### card-startup-perk
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xl}, border: 1px solid {colors.hairline}

### pricing-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### pricing-card-featured
backgroundColor: {colors.surface}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 2px solid {colors.primary}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, border: 1px solid {colors.hairline-strong}, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, border: 2px solid {colors.primary}

### search-pill
backgroundColor: {colors.surface}, textColor: {colors.steel}, typography: {typography.body-md}, rounded: {rounded.md}, padding: {spacing.sm} {spacing.md}, height: 44px, border: 1px solid {colors.hairline}

### pill-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, rounded: {rounded.full}, padding: {spacing.xs} {spacing.md}, border: 1px solid {colors.hairline}

### pill-tab-active
backgroundColor: {colors.ink-deep}, textColor: {colors.on-dark}, rounded: {rounded.full}, border: 1px solid {colors.ink-deep}

### segmented-tab
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}, border: 0 0 2px transparent solid

### segmented-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-sm-medium}, border: 0 0 2px {colors.ink} solid

### badge-purple
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-pink
backgroundColor: {colors.brand-pink}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-orange
backgroundColor: {colors.brand-orange}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### badge-tag-purple
backgroundColor: {colors.card-tint-lavender}, textColor: {colors.brand-purple-800}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-tag-orange
backgroundColor: {colors.card-tint-peach}, textColor: {colors.brand-orange-deep}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-tag-green
backgroundColor: {colors.card-tint-mint}, textColor: {colors.brand-green}, typography: {typography.caption-bold}, rounded: {rounded.sm}, padding: 2px 8px

### badge-popular
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-bold}, rounded: {rounded.full}, padding: 4px 10px

### promo-banner
backgroundColor: {colors.surface}, textColor: {colors.ink}, typography: {typography.body-sm-medium}, padding: {spacing.sm} {spacing.md}

### hero-band-dark
backgroundColor: {colors.brand-navy}, textColor: {colors.on-dark}, rounded: 0, padding: {spacing.hero}

### workspace-mockup-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: 0, border: 1px solid {colors.hairline}, shadow: rgba(15, 15, 15, 0.2) 0px 24px 48px -8px

### cta-banner-light
backgroundColor: {colors.surface}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.section}

### comparison-table
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, border: 1px solid {colors.hairline}

### comparison-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, padding: {spacing.md} {spacing.lg}, border: 0 0 1px {colors.hairline-soft} solid

### testimonial-card
backgroundColor: {colors.canvas}, rounded: {rounded.lg}, padding: {spacing.xxl}, border: 1px solid {colors.hairline}

### logo-wall-item
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-md-medium}, padding: {spacing.lg}

### faq-accordion-item
backgroundColor: {colors.canvas}, rounded: {rounded.md}, padding: {spacing.xl}, border: 0 0 1px {colors.hairline} solid

### stat-row
backgroundColor: {colors.surface}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: {spacing.section-sm}

### footer-region
backgroundColor: {colors.canvas}, textColor: {colors.charcoal}, typography: {typography.body-sm}, padding: {spacing.section} {spacing.xxl}, border: 1px solid {colors.hairline}

### footer-link
backgroundColor: transparent, textColor: {colors.steel}, typography: {typography.body-sm}, padding: {spacing.xxs} 0
', '["design-brand", "notion", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (77, 'design_brand', 'nvidia', 'design_system', '品牌设计规范 — nvidia', '# 品牌设计规范: NVIDIA

An engineering-grade marketing system organized around two surface modes — a deep black canvas for hero and footer chapters and a flat paper-white canvas for body content — connected by a single, almost violently saturated NVIDIA Green accent that carries every CTA, every active tab, and the small decorative corner squares that mark out cards. The system is unapologetically angular: 2px radius across every surface, tight bold sans-serif typography in NVIDIA''s proprietary EMEA cut, and a hairline gray rule that separates dense multi-column technical content. There is no decorative gradient, no atmospheric mesh, no soft drop shadow — just black, white, gray, and green stacked into a structured editorial grid that scales from product cards to massive industry landing pages without bending its rules.


## 颜色体系 (Colors)

- **primary**: #76b900
- **on-primary**: #000000
- **primary-dark**: #5a8d00
- **ink**: #000000
- **canvas**: #ffffff
- **surface-dark**: #000000
- **surface-soft**: #f7f7f7
- **surface-elevated**: #1a1a1a
- **hairline**: #cccccc
- **hairline-strong**: #5e5e5e
- **body**: #1a1a1a
- **mute**: #757575
- **stone**: #898989
- **ash**: #a7a7a7
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.7)
- **link-blue**: #0046a4
- **blue-700**: #0046a4
- **error**: #e52020
- **error-deep**: #650b0b
- **warning**: #df6500
- **warning-bright**: #ef9100
- **success-deep**: #3f8500
- **accent-yellow-pale**: #feeeb2
- **accent-purple**: #952fc6
- **accent-purple-deep**: #4d1368
- **accent-purple-pale**: #f9d4ff
- **accent-green-pale**: #bff230

## 排版体系 (Typography)

- **display-xl**: font: NVIDIA-EMEA | size: 48px | weight: 700 | lh: 1.25 | ls: 0
- **display-lg**: font: NVIDIA-EMEA | size: 36px | weight: 700 | lh: 1.25 | ls: 0
- **heading-xl**: font: NVIDIA-EMEA | size: 24px | weight: 700 | lh: 1.25 | ls: 0
- **heading-lg**: font: NVIDIA-EMEA | size: 22px | weight: 400 | lh: 1.75 | ls: 0
- **heading-md**: font: NVIDIA-EMEA | size: 20px | weight: 700 | lh: 1.25 | ls: 0
- **heading-sm**: font: NVIDIA-EMEA | size: 18px | weight: 700 | lh: 1.4 | ls: 0
- **card-title**: font: NVIDIA-EMEA | size: 17px | weight: 700 | lh: 1.47 | ls: 0
- **body-md**: font: NVIDIA-EMEA | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: NVIDIA-EMEA | size: 16px | weight: 700 | lh: 1.5 | ls: 0
- **body-sm**: font: NVIDIA-EMEA | size: 15px | weight: 400 | lh: 1.67 | ls: 0
- **button-lg**: font: NVIDIA-EMEA | size: 18px | weight: 700 | lh: 1.25 | ls: 0
- **button-md**: font: NVIDIA-EMEA | size: 16px | weight: 700 | lh: 1.25 | ls: 0
- **button-sm**: font: NVIDIA-EMEA | size: 14.4px | weight: 700 | lh: 1 | ls: 0.144px
- **link-md**: font: NVIDIA-EMEA | size: 15px | weight: 400 | lh: 1.5 | ls: 0
- **caption-md**: font: NVIDIA-EMEA | size: 14px | weight: 700 | lh: 1.43 | ls: 0 | transform: uppercase
- **caption-sm**: font: NVIDIA-EMEA | size: 12px | weight: 400 | lh: 1.25 | ls: 0
- **caption-xs**: font: NVIDIA-EMEA | size: 11px | weight: 700 | lh: 1 | ls: 0
- **utility-xs**: font: NVIDIA-EMEA | size: 10px | weight: 700 | lh: 1.5 | ls: 0 | transform: uppercase

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 64px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 1px
- **sm**: 2px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 11px 24px, height: 44px

### button-primary-active
backgroundColor: {colors.primary-dark}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}

### button-outline
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 11px 13px

### button-outline-on-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.sm}

### button-ghost-link
textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.none}

### button-disabled
backgroundColor: {colors.surface-soft}, textColor: {colors.ash}, rounded: {rounded.sm}

### pill-tab
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.sm}, padding: 10px 18px

### pill-tab-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.button-sm}, rounded: {rounded.sm}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 12px 16px, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.sm}

### search-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 10px 16px, height: 40px

### product-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.card-title}, rounded: {rounded.sm}, padding: 24px

### feature-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 32px

### resource-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.card-title}, rounded: {rounded.sm}, padding: 24px

### hero-card-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 80px 48px

### cta-strip-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.heading-xl}, rounded: {rounded.none}, padding: 64px 48px

### callout-stat
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, rounded: {rounded.sm}, padding: 32px

### corner-square
backgroundColor: {colors.primary}, rounded: {rounded.none}, size: 12px

### utility-bar
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.caption-sm}, rounded: {rounded.none}, height: 32px

### primary-nav
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 64px

### breadcrumb-bar
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.caption-md}, rounded: {rounded.none}, height: 48px

### sub-nav-strip
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.none}, height: 56px

### footer-section
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark-mute}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 48px

### link-inline
textColor: {colors.link-blue}, typography: {typography.link-md}

### badge-tag
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.caption-md}, rounded: {rounded.sm}, padding: 4px 10px
', '["design-brand", "nvidia", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (78, 'design_brand', 'ollama', 'design_system', '品牌设计规范 — ollama', '# 品牌设计规范: Ollama

An almost defiantly minimal documentation-first system that treats the home page like a Markdown README — paper-white canvas, 36px center-aligned heading, a single black pill CTA, an inline terminal install snippet, and a hand-drawn llama mascot as the only ornamental element. No gradient, no hero photography, no marketing pyrotechnics. The chrome is a tiny utility palette of pure black, pure white, and three neutral grays; every interactive element is fully rounded into a pill (`{rounded.full}`); typography is SF Pro Rounded for headings paired with system sans for body and ui-monospace for code. Pricing tiers, FAQs, and "your data stays yours" guarantees all sit on the same flat canvas inside thin-border cards — the system is the documentation, and the documentation is the system.


## 颜色体系 (Colors)

- **primary**: #000000
- **on-primary**: #ffffff
- **ink**: #000000
- **ink-deep**: #090909
- **charcoal**: #525252
- **body**: #737373
- **mute**: #a3a3a3
- **canvas**: #ffffff
- **surface-soft**: #fafafa
- **surface-card**: #ffffff
- **hairline**: #e5e5e5
- **hairline-strong**: #d4d4d4
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.7)
- **surface-dark**: #171717
- **focus-ring**: rgba(59,130,246,0.5)
- **link**: #000000
- **link-mute**: #737373
- **terminal-red**: #ff5f56
- **terminal-yellow**: #ffbd2e
- **terminal-green**: #27c93f

## 排版体系 (Typography)

- **display-xl**: font: SF Pro Rounded | size: 36px | weight: 500 | lh: 1.11 | ls: 0
- **display-lg**: font: SF Pro Rounded | size: 30px | weight: 500 | lh: 1.2 | ls: 0
- **heading-lg**: font: SF Pro Rounded | size: 24px | weight: 600 | lh: 1.33 | ls: 0
- **heading-md**: font: ui-sans-serif | size: 20px | weight: 500 | lh: 1.4 | ls: 0
- **heading-sm**: font: ui-sans-serif | size: 18px | weight: 500 | lh: 1.56 | ls: 0
- **body-md**: font: ui-sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: ui-sans-serif | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **body-sm**: font: ui-sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **body-sm-strong**: font: ui-sans-serif | size: 14px | weight: 500 | lh: 1.43 | ls: 0
- **caption-sm**: font: ui-sans-serif | size: 12px | weight: 400 | lh: 1.33 | ls: 0
- **code-md**: font: ui-monospace | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **code-sm**: font: ui-monospace | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **button-md**: font: ui-sans-serif | size: 14px | weight: 500 | lh: 1 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 88px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 20px, height: 36px

### button-primary-active
backgroundColor: {colors.ink-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 20px, height: 36px

### button-pill-on-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 20px

### button-disabled
backgroundColor: {colors.surface-soft}, textColor: {colors.mute}, rounded: {rounded.full}

### search-pill
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.full}, padding: 8px 16px, height: 36px

### search-pill-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.full}, padding: 8px 16px, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}

### install-snippet
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.code-md}, rounded: {rounded.full}, padding: 12px 20px, height: 48px

### command-tag
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.code-sm}, rounded: {rounded.full}, padding: 6px 12px

### terminal-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.code-sm}, rounded: {rounded.lg}, padding: 16px

### terminal-traffic-lights
rounded: {rounded.full}, size: 12px

### pricing-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-card-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### feature-bullet
textColor: {colors.charcoal}, typography: {typography.body-sm}

### faq-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 16px 0px

### link-inline
textColor: {colors.ink}, typography: {typography.body-md}

### link-mute
textColor: {colors.body}, typography: {typography.body-sm}

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-sm-strong}, rounded: {rounded.none}, height: 56px

### footer-section
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.caption-sm}, rounded: {rounded.none}, padding: 32px 24px

### cta-strip-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.heading-lg}, rounded: {rounded.lg}, padding: 24px 32px
', '["design-brand", "ollama", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (79, 'design_brand', 'opencode-ai', 'design_system', '品牌设计规范 — opencode.ai', '# 品牌设计规范: OpenCode

A terminal-native marketing system rendered entirely in Berkeley Mono — every word on the page, from the hero headline down to the footer fine print, is monospaced. The page itself reads like a manpage or a static-site README: warm cream canvas (`#fdfcfc`), nearly-black ink (`#201d1d`), 4px-radius rectangles for the few interactive elements, and bracketed `[+]`/`[-]` ASCII markers used as bullets. The brand''s only "visual moment" is a single dark hero card that mocks up the OpenCode TUI itself — black background, monospaced terminal output, ASCII pipe characters, and a wordmark rendered as block-pixel ASCII. Every section sits as a hairline-bordered text block on the cream canvas with no shadows, no gradients, no decorative imagery, and no non-monospaced character anywhere in the system.


## 颜色体系 (Colors)

- **primary**: #201d1d
- **on-primary**: #fdfcfc
- **ink**: #201d1d
- **ink-deep**: #0f0000
- **charcoal**: #302c2c
- **body**: #424245
- **mute**: #646262
- **stone**: #6e6e73
- **ash**: #9a9898
- **canvas**: #fdfcfc
- **surface-soft**: #f8f7f7
- **surface-card**: #f1eeee
- **surface-dark**: #201d1d
- **surface-dark-elevated**: #302c2c
- **hairline**: rgba(15,0,0,0.12)
- **hairline-strong**: #646262
- **on-dark**: #fdfcfc
- **on-dark-mute**: #9a9898
- **accent**: #007aff
- **accent-hover**: #0056b3
- **accent-active**: #004085
- **warning**: #ff9f0a
- **warning-hover**: #cc7f08
- **warning-active**: #995f06
- **danger**: #ff3b30
- **danger-hover**: #d70015
- **danger-active**: #a50011
- **success**: #30d158

## 排版体系 (Typography)

- **display-xl**: font: Berkeley Mono | size: 38px | weight: 700 | lh: 1.5 | ls: 0
- **heading-md**: font: Berkeley Mono | size: 16px | weight: 700 | lh: 1.5 | ls: 0
- **body-md**: font: Berkeley Mono | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: Berkeley Mono | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **body-tight**: font: Berkeley Mono | size: 16px | weight: 500 | lh: 1 | ls: 0
- **link-md**: font: Berkeley Mono | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **button-md**: font: Berkeley Mono | size: 16px | weight: 500 | lh: 2 | ls: 0
- **caption-md**: font: Berkeley Mono | size: 14px | weight: 400 | lh: 2 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 1px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 4px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 4px 20px, height: 36px

### button-primary-active
backgroundColor: {colors.ink-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 4px 20px

### button-tab
backgroundColor: transparent, textColor: {colors.mute}, typography: {typography.button-md}, rounded: {rounded.none}, padding: 8px 16px

### button-tab-active
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.none}

### button-disabled
backgroundColor: {colors.surface-card}, textColor: {colors.ash}, rounded: {rounded.sm}

### badge-news
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.caption-md}, rounded: {rounded.sm}, padding: 2px 8px

### text-input
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px, height: 40px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.sm}

### textarea
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 12px

### install-snippet
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 12px 16px

### hero-tui-mockup
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 64px 32px

### tui-prompt-row
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### list-row
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 8px 0px

### faq-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 12px 0px

### testimonial-row
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 16px 20px

### chart-tile
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.caption-md}, rounded: {rounded.none}, padding: 16px

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 56px

### footer-section
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.caption-md}, rounded: {rounded.none}, padding: 32px 0px

### link-inline
textColor: {colors.ink}, typography: {typography.link-md}

### badge-section-label
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.heading-md}, rounded: {rounded.none}
', '["design-brand", "opencode.ai", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (80, 'design_brand', 'pinterest', 'design_system', '品牌设计规范 — pinterest', '# 品牌设计规范: Pinterest

A photography-first discovery system organized around the Pinterest Red CTA, the masonry pin grid, and a soft warm-cream chrome that gets out of the imagery''s way. The home page is a content-discovery tool wearing the chrome of a magazine publisher: 70px display headlines, friendly Pin Sans typography, fully-rounded pill buttons (16px) on a cream-tinted neutral palette, and a sticky red "Sign up" CTA that anchors every viewport. Pin imagery is the system''s load-bearing visual element — square, portrait, and landscape pins tile in a column-based masonry grid where each tile is a fully-rounded 16px-radius card, separated by tight 8px gutters. The chrome is otherwise quiet: warm grays, true whites, and a single saturated red — no decorative gradients, no atmospheric backgrounds, no shadows beyond a soft modal scrim.


## 颜色体系 (Colors)

- **primary**: #e60023
- **on-primary**: #ffffff
- **primary-pressed**: #cc001f
- **ink**: #000000
- **ink-soft**: #211922
- **body**: #33332e
- **charcoal**: #262622
- **mute**: #62625b
- **ash**: #91918c
- **stone**: #c8c8c1
- **hairline**: #dadad3
- **hairline-soft**: #e5e5e0
- **on-secondary**: #000000
- **secondary-bg**: #e5e5e0
- **secondary-pressed**: #c8c8c1
- **canvas**: #ffffff
- **surface-soft**: #fbfbf9
- **surface-card**: #f6f6f3
- **surface-elevated**: #ffffff
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.7)
- **surface-dark**: #262622
- **focus-outer**: #435ee5
- **focus-inner**: #ffffff
- **accent-pressed-blue**: #617bff
- **accent-purple**: #7e238b
- **accent-purple-deep**: #6845ab
- **success-deep**: #103c25
- **success-pale**: #c7f0da
- **error**: #9e0a0a
- **error-deep**: #cc001f

## 排版体系 (Typography)

- **display-xl**: font: Pin Sans | size: 70px | weight: 600 | lh: 1.1 | ls: -1.2px
- **display-lg**: font: Pin Sans | size: 44px | weight: 700 | lh: 1.15 | ls: -0.8px
- **heading-xl**: font: Pin Sans | size: 28px | weight: 700 | lh: 1.2 | ls: -1.2px
- **heading-lg**: font: Pin Sans | size: 22px | weight: 600 | lh: 1.25 | ls: 0
- **heading-md**: font: Pin Sans | size: 18px | weight: 600 | lh: 1.3 | ls: 0
- **body-md**: font: Pin Sans | size: 16px | weight: 400 | lh: 1.4 | ls: 0
- **body-strong**: font: Pin Sans | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **body-sm**: font: Pin Sans | size: 14px | weight: 400 | lh: 1.4 | ls: 0
- **body-sm-strong**: font: Pin Sans | size: 14px | weight: 700 | lh: 1.4 | ls: 0
- **caption-md**: font: Pin Sans | size: 12px | weight: 500 | lh: 1.5 | ls: 0
- **caption-sm**: font: Pin Sans | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **link-md**: font: Pin Sans | size: 16px | weight: 600 | lh: 1.4 | ls: 0
- **button-md**: font: Pin Sans | size: 14px | weight: 700 | lh: 1 | ls: 0
- **button-sm**: font: Pin Sans | size: 12px | weight: 700 | lh: 1 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 6px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 64px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 8px
- **md**: 16px
- **lg**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 6px 14px, height: 40px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.secondary-bg}, textColor: {colors.on-secondary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 6px 14px, height: 40px

### button-secondary-pressed
backgroundColor: {colors.secondary-pressed}, textColor: {colors.on-secondary}, typography: {typography.button-md}, rounded: {rounded.md}

### button-tertiary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}

### button-icon-circular
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.full}, size: 40px

### button-pill-on-image
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 14px

### button-disabled
backgroundColor: {colors.surface-card}, textColor: {colors.ash}, rounded: {rounded.md}

### search-bar
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.full}, padding: 11px 15px, height: 48px

### search-bar-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.full}

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 11px 15px, height: 44px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.md}

### pin-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.md}, padding: 0px

### pin-card-large
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.lg}, padding: 0px

### pin-overlay-pill
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 6px 12px

### filter-chip
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 16px

### filter-chip-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.full}

### category-tile
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.md}, padding: 16px

### feature-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.heading-xl}, rounded: {rounded.md}, padding: 32px

### feature-card-soft
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.heading-xl}, rounded: {rounded.md}, padding: 32px

### modal-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### hero-cta-strip
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.heading-xl}, rounded: {rounded.none}, padding: 48px 32px

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 64px

### footer-section
backgroundColor: {colors.canvas}, textColor: {colors.mute}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 32px 24px

### link-inline
textColor: {colors.ink-soft}, typography: {typography.link-md}
', '["design-brand", "pinterest", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (81, 'design_brand', 'playstation', 'design_system', '品牌设计规范 — playstation', '# 品牌设计规范: PlayStation

A three-surface marketing system organized around alternating black, white, and PlayStation Blue chapters that scroll past the viewer like a console launch trailer. Each section has a single editorial purpose — hero photography, console product render, PS Plus tier callout, news strip — and each owns one of three full-bleed canvas modes. The chrome is unusually quiet for a gaming brand: bright PlayStation Blue (`#0070d1`) carries every primary CTA as a fully-rounded pill, the proprietary SST face renders display copy at a signature weight 300 (light) for an airy, premium feel, and a crisp 8px-radius secondary card system carries product info on either canvas mode. The system never decorates — no gradient backgrounds on chrome, no atmospheric mesh, no drop shadows beyond a faint section-divide. Imagery does all the heavy lifting: console glamour shots, game key art, and PS Plus tier illustrations occupy 60-90% of every section, with copy compressed into a small editorial slot.


## 颜色体系 (Colors)

- **primary**: #0070d1
- **primary-pressed**: #0064b7
- **primary-active**: #004d8d
- **on-primary**: #ffffff
- **link-light**: #0064b7
- **link-dark**: #53b1ff
- **commerce**: #d53b00
- **commerce-pressed**: #aa2f00
- **commerce-link-base**: #d63d00
- **on-commerce**: #ffffff
- **ink**: #000000
- **ink-deep**: #121314
- **ink-elevated**: #181818
- **charcoal**: #1f2024
- **body-light**: rgba(0,0,0,0.6)
- **mute-light**: #6b6b6b
- **ash-light**: #cccccc
- **body-dark**: rgba(255,255,255,0.7)
- **mute-dark**: rgba(229,229,229,0.55)
- **ash-dark**: rgba(229,229,229,0.2)
- **canvas-light**: #ffffff
- **surface-soft**: #f3f3f3
- **surface-card**: #f5f7fa
- **surface-filter**: rgba(245,247,250,0.3)
- **canvas-dark**: #000000
- **surface-dark-elevated**: #121314
- **surface-dark-card**: #181818
- **hairline-light**: #f3f3f3
- **hairline-dark**: rgba(229,229,229,0.2)
- **on-dark**: #ffffff
- **on-dark-mute**: #cccccc
- **warning**: #c81b3a
- **ps-plus-gold-start**: #ffce21
- **ps-plus-gold-mid**: #f5a623
- **ps-plus-gold-end**: #ee8e00
- **marathon-yellow**: #deff20

## 排版体系 (Typography)

- **display-xl**: font: PlayStation SST | size: 54px | weight: 300 | lh: 1.25 | ls: -0.1px
- **display-lg**: font: PlayStation SST | size: 44px | weight: 300 | lh: 1.25 | ls: 0.1px
- **display-md**: font: PlayStation SST | size: 35px | weight: 300 | lh: 1.25 | ls: 0
- **heading-xl**: font: PlayStation SST | size: 28px | weight: 300 | lh: 1.25 | ls: 0.1px
- **heading-lg**: font: PlayStation SST | size: 22px | weight: 300 | lh: 1.25 | ls: 0.1px
- **heading-md**: font: PlayStation SST | size: 18px | weight: 600 | lh: 1 | ls: 0
- **body-md**: font: PlayStation SST | size: 18px | weight: 400 | lh: 1.5 | ls: 0.1px
- **body-strong**: font: PlayStation SST | size: 18px | weight: 500 | lh: 1.25 | ls: 0.4px
- **body-sm**: font: PlayStation SST | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **caption-md**: font: PlayStation SST | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption-sm**: font: PlayStation SST | size: 12px | weight: 500 | lh: 1.5 | ls: 0
- **link-md**: font: PlayStation SST | size: 18px | weight: 400 | lh: 1.5 | ls: 0
- **button-lg**: font: PlayStation SST | size: 18px | weight: 700 | lh: 1.25 | ls: 0.45px
- **button-md**: font: PlayStation SST | size: 14px | weight: 700 | lh: 1.25 | ls: 0.324px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 4px
- **md**: 8px
- **lg**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-lg}, rounded: {rounded.full}, padding: 12px 28px, height: 48px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}, typography: {typography.button-lg}, rounded: {rounded.full}

### button-commerce
backgroundColor: {colors.commerce}, textColor: {colors.on-commerce}, typography: {typography.button-lg}, rounded: {rounded.full}, padding: 12px 28px, height: 48px

### button-commerce-pressed
backgroundColor: {colors.commerce-pressed}, textColor: {colors.on-commerce}, typography: {typography.button-lg}, rounded: {rounded.full}

### button-secondary-light
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-lg}, rounded: {rounded.full}, padding: 12px 28px, height: 48px

### button-secondary-dark
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-lg}, rounded: {rounded.full}, padding: 12px 28px, height: 48px

### button-disabled
backgroundColor: {colors.surface-soft}, textColor: {colors.ash-light}, rounded: {rounded.full}

### text-input
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 12px 16px, height: 48px

### text-input-focused
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, rounded: {rounded.sm}

### filter-pill
backgroundColor: {colors.surface-filter}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 16px

### filter-pill-active
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}

### product-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### product-card-dark
backgroundColor: {colors.surface-dark-card}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### game-tile
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 0px

### feature-card
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 32px

### hero-band-blue
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.display-md}, rounded: {rounded.none}, padding: 96px 48px

### hero-band-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 96px 48px

### hero-band-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 96px 48px

### ps-plus-banner
backgroundColor: {colors.surface-dark-elevated}, textColor: {colors.on-dark}, typography: {typography.heading-xl}, rounded: {rounded.md}, padding: 48px 32px

### carousel-paddle
backgroundColor: rgba(255,255,255,0.16), textColor: {colors.on-dark}, rounded: {rounded.full}, size: 48px

### pagination-dot
backgroundColor: {colors.ash-dark}, rounded: {rounded.full}, size: 8px

### pagination-dot-active
backgroundColor: {colors.on-dark}, rounded: {rounded.full}, size: 8px

### badge-info
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-sm}, rounded: {rounded.full}, padding: 4px 10px

### primary-nav
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 48px

### sub-nav
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.caption-md}, rounded: {rounded.none}, height: 40px

### footer-section
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption-md}, rounded: {rounded.none}, padding: 48px 32px

### support-search-bar
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.full}, padding: 12px 24px, height: 56px

### support-row
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 16px 0px

### link-inline
textColor: {colors.link-light}, typography: {typography.link-md}
', '["design-brand", "playstation", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (82, 'design_brand', 'posthog', 'design_system', '品牌设计规范 — posthog', '# 品牌设计规范: PostHog

A playful developer-tools system rendered on a warm cream canvas with hand-drawn hedgehog mascots dotted across every page like marginalia in a sketchbook. The chrome reads like a friendly engineering blog: olive-gray ink (#4d4f46) for body, deep olive-charcoal (#23251d) for headlines, IBM Plex Sans Variable typography in tight 1.43-line-height paragraphs, and a single saturated yellow-orange CTA pill (#f7a501) carrying every primary action. The system actively rejects the genre''s typical somber dark-tech aesthetic in favor of a creamy, textbook-illustration sensibility — bordered cards stack on the cream canvas with 4–6px radii, doc sidebars use rounded outline-icon mini-illustrations, and the home page leans on cartoon characters (hedgehogs in lab coats, hedgehogs at terminals, hedgehogs in lounge chairs) as its signature decoration. Code samples and product analytics charts live inside white-on-cream cards with thin olive borders; the contrast between the playful illustration and the data-dense product imagery is the brand''s signature voice.


## 颜色体系 (Colors)

- **primary**: #f7a501
- **primary-pressed**: #dd9001
- **primary-active**: #b17816
- **on-primary**: #23251d
- **ink**: #23251d
- **body**: #4d4f46
- **charcoal**: #33342d
- **mute**: #6c6e63
- **ash**: #9b9c92
- **stone**: #b6b7af
- **hairline**: #bfc1b7
- **hairline-soft**: #dcdfd2
- **on-dark**: #ffffff
- **canvas**: #eeefe9
- **surface-soft**: #e5e7e0
- **surface-card**: #ffffff
- **surface-doc**: #fcfcfa
- **surface-dark**: #23251d
- **link-blue**: #1d4ed8
- **link-teal**: #1078a3
- **accent-blue**: #2c84e0
- **accent-blue-soft**: #dceaf6
- **accent-red**: #cd4239
- **accent-red-soft**: #f7d6d3
- **accent-green**: #2c8c66
- **accent-green-soft**: #d9eddf
- **accent-purple**: #7c44a6
- **accent-purple-soft**: #e7d8ee
- **focus-ring**: rgba(59,130,246,0.5)

## 排版体系 (Typography)

- **display-xl**: font: IBM Plex Sans Variable | size: 36px | weight: 700 | lh: 1.5 | ls: 0
- **display-lg**: font: IBM Plex Sans Variable | size: 24px | weight: 800 | lh: 1.33 | ls: -0.6px
- **heading-lg**: font: IBM Plex Sans Variable | size: 21px | weight: 700 | lh: 1.4 | ls: -0.5px
- **heading-md**: font: IBM Plex Sans Variable | size: 20px | weight: 700 | lh: 1.4 | ls: 0
- **heading-sm**: font: IBM Plex Sans Variable | size: 18px | weight: 700 | lh: 1.5 | ls: 0 | transform: uppercase
- **heading-sm-mixed**: font: IBM Plex Sans Variable | size: 18px | weight: 600 | lh: 1.56 | ls: 0
- **body-md**: font: IBM Plex Sans Variable | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-strong**: font: IBM Plex Sans Variable | size: 16px | weight: 600 | lh: 1.5 | ls: 0
- **body-sm**: font: IBM Plex Sans Variable | size: 15px | weight: 400 | lh: 1.71 | ls: 0
- **body-sm-strong**: font: IBM Plex Sans Variable | size: 15px | weight: 600 | lh: 1.71 | ls: 0
- **body-xs**: font: IBM Plex Sans Variable | size: 14px | weight: 500 | lh: 1.43 | ls: 0
- **caption-md**: font: IBM Plex Sans Variable | size: 14px | weight: 700 | lh: 1.71 | ls: 0
- **caption-sm**: font: IBM Plex Sans Variable | size: 13px | weight: 500 | lh: 1.5 | ls: 0
- **caption-xs**: font: IBM Plex Sans Variable | size: 12px | weight: 600 | lh: 1.33 | ls: 0 | transform: uppercase
- **utility-xs**: font: IBM Plex Sans Variable | size: 12px | weight: 700 | lh: 1.33 | ls: 0 | transform: uppercase
- **link-md**: font: IBM Plex Sans Variable | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **button-md**: font: IBM Plex Sans Variable | size: 14px | weight: 700 | lh: 1.5 | ls: 0
- **button-sm**: font: IBM Plex Sans Variable | size: 13px | weight: 500 | lh: 1 | ls: 0
- **code-sm**: font: ui-monospace | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **code-xs**: font: Source Code Pro | size: 14px | weight: 500 | lh: 1.43 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 80px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 4px
- **md**: 6px
- **lg**: 8px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 40px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}

### button-secondary
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 40px

### button-tertiary
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 12px

### button-disabled
backgroundColor: {colors.surface-soft}, textColor: {colors.ash}, rounded: {rounded.md}

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 12px, height: 36px

### text-input-focused
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.md}

### search-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 12px, height: 36px

### product-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### doc-card
backgroundColor: {colors.surface-doc}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### feature-tile
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.heading-sm-mixed}, rounded: {rounded.md}, padding: 20px

### pricing-tier-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 32px

### hedgehog-mascot-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### product-tab
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-strong}, rounded: {rounded.md}, padding: 8px 12px

### product-tab-active
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.md}

### pill-tab
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 6px 14px

### pill-tab-active
backgroundColor: {colors.ink}, textColor: {colors.on-dark}, typography: {typography.button-sm}, rounded: {rounded.full}

### badge-uppercase
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.utility-xs}, rounded: {rounded.none}

### badge-promo
backgroundColor: {colors.accent-blue-soft}, textColor: {colors.link-blue}, typography: {typography.caption-xs}, rounded: {rounded.full}, padding: 2px 8px

### banner-tip-blue
backgroundColor: {colors.accent-blue-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px 20px

### banner-tip-green
backgroundColor: {colors.accent-green-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px 20px

### banner-tip-red
backgroundColor: {colors.accent-red-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px 20px

### banner-tip-purple
backgroundColor: {colors.accent-purple-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px 20px

### code-block
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.code-sm}, rounded: {rounded.md}, padding: 16px 20px

### inline-code
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.code-xs}, rounded: {rounded.xs}, padding: 2px 6px

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-strong}, rounded: {rounded.none}, height: 56px

### sub-nav-strip
backgroundColor: {colors.surface-soft}, textColor: {colors.body}, typography: {typography.body-xs}, rounded: {rounded.none}, height: 40px

### doc-sidebar
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-xs}, rounded: {rounded.none}, width: 240px

### footer-section
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-xs}, rounded: {rounded.none}, padding: 32px 24px

### link-inline
textColor: {colors.link-teal}, typography: {typography.link-md}
', '["design-brand", "posthog", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (84, 'design_brand', 'renault', 'design_system', '品牌设计规范 — renault', '# 品牌设计规范: Renault

Renault''s web presence pairs the freshly-modernised Renault diamond
(the 2021 flat-line rhombus mark) with a stark black-and-white canvas, a
signature Sunlight Yellow accent, and the proprietary NouvelR display
typeface. The system reads as confident, photography-first automotive — large
hero cars on neutral or atmospheric backdrops, square-edged or barely-rounded
containers, and a small disciplined palette where every coloured element is
intentional. Tile grids, full-bleed banners, and a recurring "configurator"
surface (white card, yellow accent dots, neutral product chrome) carry the
mass-market dealership tone without crossing into luxury.


## 颜色体系 (Colors)

- **primary**: #ffed00
- **primary-deep**: #e6d200
- **on-primary**: #000000
- **ink**: #000000
- **body**: #222222
- **charcoal**: #333333
- **mute**: #666666
- **ash**: #8a8a8a
- **stone**: #c4c4c4
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.72)
- **canvas**: #ffffff
- **surface-soft**: #f7f7f7
- **surface-card**: #ffffff
- **surface-dark**: #000000
- **surface-deep**: #111111
- **hairline**: #f2f2f2
- **hairline-strong**: #000000
- **divider-dark**: rgba(255,255,255,0.16)
- **badge-new**: #ffed00
- **link**: #0000ee
- **error**: #be6464
- **warning**: #f0ad4e
- **success**: #8dc572
- **info**: #337ab7

## 排版体系 (Typography)

- **display-xl**: font: NouvelR | size: 56px | weight: 700 | lh: 0.95 | ls: 0
- **display-lg**: font: NouvelR | size: 40px | weight: 700 | lh: 0.95 | ls: 0
- **display-md**: font: NouvelR | size: 32px | weight: 700 | lh: 0.95 | ls: 0
- **heading-lg**: font: NouvelR | size: 24px | weight: 700 | lh: 0.95 | ls: 0
- **heading-md**: font: NouvelR | size: 20px | weight: 700 | lh: 0.95 | ls: 0
- **heading-sm**: font: NouvelR | size: 18px | weight: 700 | lh: 1.0 | ls: 0
- **subtitle**: font: NouvelR | size: 19.2px | weight: 600 | lh: 1.3 | ls: 0
- **body-lg**: font: NouvelR | size: 18px | weight: 400 | lh: 1.5 | ls: 0
- **body-md**: font: NouvelR | size: 16px | weight: 400 | lh: 1.4 | ls: 0
- **body-sm**: font: NouvelR | size: 14px | weight: 400 | lh: 1.57 | ls: 0
- **button-lg**: font: NouvelR | size: 16px | weight: 700 | lh: 1.0 | ls: 0
- **button-md**: font: NouvelR | size: 14.4px | weight: 700 | lh: 1.0 | ls: 0.144px
- **button-sm**: font: NouvelR | size: 13px | weight: 600 | lh: 1.2 | ls: 0.13px
- **caption**: font: NouvelR | size: 12px | weight: 400 | lh: 1.4 | ls: 0
- **overline**: font: NouvelR | size: 10px | weight: 700 | lh: 1.45 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 20px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 40px
- **section**: 80px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 2px
- **sm**: 3px
- **md**: 4px
- **pill**: 46px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.xs}, padding: 14px 24px, height: 48px

### button-primary-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.xs}

### button-secondary-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.xs}, padding: 14px 24px

### button-outline-dark
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.xs}, padding: 13px 23px

### button-outline-light
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.xs}, padding: 13px 23px

### button-pill
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.pill}, padding: 8px 16px, height: 36px

### button-icon-square
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.xs}, size: 40px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 12px 16px, height: 48px

### hero-banner
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, rounded: {rounded.none}, padding: 0

### promo-tile-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.heading-lg}, rounded: {rounded.none}, padding: 32px

### promo-tile-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.heading-lg}, rounded: {rounded.none}, padding: 32px

### promo-tile-yellow
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.heading-lg}, rounded: {rounded.none}, padding: 32px

### vehicle-card
backgroundColor: {colors.canvas}, textColor: {colors.ink}, rounded: {rounded.none}, padding: 0

### configurator-row
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.none}, padding: 24px 0

### configurator-swatch
backgroundColor: {colors.surface-soft}, rounded: {rounded.full}, size: 56px

### badge-new
backgroundColor: {colors.badge-new}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 6px 14px

### nav-bar
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.none}, height: 60px

### sub-nav-pill
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.pill}, padding: 8px 16px

### footer
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 24px
', '["design-brand", "renault", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (85, 'design_brand', 'replicate', 'design_system', '品牌设计规范 — replicate', '# 品牌设计规范: Replicate

Replicate''s marketing surfaces pair the warm-cream developer-tools aesthetic
of an indie ML playground with a confident hot-orange brand accent and a
signature display typeface (rb-freigeist-neue) sized aggressively large at
72px+. The system reads as "AI lab notebook crossed with print magazine":
cream and bone surfaces, dark ink type, monospace code wells, irregular
hand-drawn-feeling diagrams, and a rich orange used scarcely on the most
consequential CTA. Photography of contributors and example outputs is
square-ish with mid-radius corners; everything else is borderless or hairline.


## 颜色体系 (Colors)

- **primary**: #ea2804
- **primary-deep**: #c01f00
- **on-primary**: #ffffff
- **ink**: #202020
- **body**: #3a3a3a
- **charcoal**: #575757
- **mute**: #646464
- **ash**: #8d8d8d
- **stone**: #bbbbbb
- **on-dark**: #fcfcfc
- **on-dark-mute**: rgba(252,252,252,0.72)
- **canvas**: #f9f7f3
- **surface-bone**: #f3f0e8
- **surface-card**: #ffffff
- **surface-dark**: #202020
- **surface-deep**: #000000
- **hairline**: rgba(32,32,32,0.12)
- **hairline-strong**: #202020
- **divider-dark**: rgba(255,255,255,0.2)
- **hero-warm**: #ea2804
- **hero-glow**: #ff6a3d
- **hero-pink**: #f4a8a0
- **badge-success**: #2b9a66
- **link**: #ea2804
- **ring-focus**: rgba(59,130,246,0.5)
- **github-dark**: #24292e

## 排版体系 (Typography)

- **display-xxl**: font: rb-freigeist-neue | size: 128px | weight: 700 | lh: 1.0 | ls: -3px
- **display-xl**: font: rb-freigeist-neue | size: 72px | weight: 700 | lh: 1.0 | ls: -1.8px
- **display-lg**: font: rb-freigeist-neue | size: 48px | weight: 700 | lh: 1.0 | ls: -1px
- **display-md**: font: rb-freigeist-neue | size: 30px | weight: 600 | lh: 1.2 | ls: -0.5px
- **heading-lg**: font: basier-square | size: 38.4px | weight: 600 | lh: 0.83 | ls: -0.5px
- **heading-md**: font: basier-square | size: 24px | weight: 600 | lh: 1.33 | ls: -0.35px
- **heading-sm**: font: basier-square | size: 20px | weight: 600 | lh: 1.4 | ls: -0.3px
- **subtitle**: font: rb-freigeist-neue | size: 18px | weight: 600 | lh: 1.56 | ls: 0
- **body-lg**: font: basier-square | size: 18px | weight: 400 | lh: 1.56 | ls: 0
- **body-md**: font: basier-square | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **body-sm**: font: basier-square | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **button-md**: font: basier-square | size: 16px | weight: 600 | lh: 1.0 | ls: 0
- **button-sm**: font: basier-square | size: 14px | weight: 600 | lh: 1.0 | ls: 0
- **caption**: font: basier-square | size: 12px | weight: 400 | lh: 1.33 | ls: 0
- **caption-tight**: font: basier-square | size: 14px | weight: 600 | lh: 1.43 | ls: -0.35px
- **code-md**: font: jetbrains-mono | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **code-sm**: font: jetbrains-mono | size: 11px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 48px
- **section**: 96px
- **band**: 160px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 10px
- **lg**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px, height: 44px

### button-primary-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.full}

### button-dark
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 24px, height: 44px

### button-outline
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 11px 23px, height: 44px

### button-ghost
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 8px 16px, height: 36px

### button-icon
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.full}, size: 36px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.full}, padding: 12px 20px, height: 44px

### hero-band
backgroundColor: {colors.hero-warm}, textColor: {colors.on-dark}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 96px 32px

### model-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px

### collection-tile
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.heading-md}, rounded: {rounded.md}, padding: 24px

### pricing-tier
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### code-block
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.code-md}, rounded: {rounded.md}, padding: 24px

### code-tab
backgroundColor: {colors.surface-deep}, textColor: {colors.on-dark-mute}, typography: {typography.code-sm}, rounded: {rounded.xs}, padding: 6px 12px

### badge-status
backgroundColor: {colors.badge-success}, textColor: {colors.on-dark}, typography: {typography.caption}, rounded: {rounded.full}, padding: 4px 10px

### badge-tag
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.full}, padding: 4px 10px

### nav-bar
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.none}, height: 60px

### sub-nav-pill
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 6px 14px

### contributor-avatar
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.full}, size: 40px

### footer
backgroundColor: {colors.surface-deep}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 32px
', '["design-brand", "replicate", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (86, 'design_brand', 'resend', 'design_system', '品牌设计规范 — resend', '# 品牌设计规范: Resend

Resend''s marketing surfaces sit on a near-pure black canvas with off-white
text and a single signature color — the deep editorial-serif Domaine
Display headline mark — that gives an otherwise utilitarian developer-tool
brand its print-magazine confidence. The system pairs Domaine Display
(oversized 76px–96px serif, ss01/ss04/ss11 features on) with ABC Favorit
for body and Inter for UI. Surfaces rely on subtle 6–9% opacity gradient
glows, hairline 1px borders made from translucent white, and a strict
rounded-12px container vocabulary. There is no decorative chrome — just
type, code, and atmospheric depth.


## 颜色体系 (Colors)

- **primary**: #fcfdff
- **primary-on**: #000000
- **ink**: #fcfdff
- **body**: rgba(252,253,255,0.86)
- **charcoal**: rgba(252,253,255,0.7)
- **mute**: #a1a4a5
- **ash**: #888e90
- **stone**: #464a4d
- **on-light**: #000000
- **on-light-mute**: rgba(0,0,51,0.7)
- **canvas**: #000000
- **surface-card**: #0a0a0c
- **surface-elevated**: #101012
- **surface-deep**: #06060a
- **hairline**: rgba(255,255,255,0.06)
- **hairline-strong**: rgba(255,255,255,0.14)
- **divider-soft**: rgba(255,255,255,0.04)
- **accent-orange**: #ff801f
- **accent-orange-glow**: rgba(255,89,0,0.22)
- **accent-yellow**: #ffc53d
- **accent-blue**: #3b9eff
- **accent-blue-glow**: rgba(0,117,255,0.34)
- **accent-green**: #11ff99
- **accent-green-glow**: rgba(34,255,153,0.18)
- **accent-red**: #ff2047
- **accent-red-glow**: rgba(255,32,71,0.34)
- **link**: #3b9eff
- **surface-light**: #f1f7fe

## 排版体系 (Typography)

- **display-xxl**: font: Domaine Display | size: 96px | weight: 400 | lh: 1.0 | ls: -0.96px
- **display-xl**: font: Domaine Display | size: 76.8px | weight: 400 | lh: 1.0 | ls: -0.768px
- **display-lg**: font: ABC Favorit | size: 56px | weight: 400 | lh: 1.2 | ls: -2.8px
- **heading-md**: font: Inter | size: 24px | weight: 500 | lh: 1.5 | ls: -0.4px
- **heading-sm**: font: Inter | size: 20px | weight: 500 | lh: 1.3 | ls: -0.3px
- **subtitle**: font: ABC Favorit | size: 20px | weight: 400 | lh: 1.3
- **body-lg**: font: Inter | size: 18px | weight: 400 | lh: 1.5
- **body-md**: font: ABC Favorit | size: 16px | weight: 400 | lh: 1.5 | ls: -0.8px
- **body-sm**: font: Inter | size: 14px | weight: 400 | lh: 1.43
- **button-md**: font: Inter | size: 14px | weight: 500 | lh: 1.43
- **button-sm**: font: ABC Favorit | size: 14px | weight: 500 | lh: 1.43 | ls: 0.35px
- **caption**: font: Inter | size: 12px | weight: 400 | lh: 1.5
- **caption-emph**: font: Helvetica | size: 14px | weight: 600 | lh: 1.0
- **code-md**: font: Geist Mono | size: 13px | weight: 400 | lh: 1.6

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 48px
- **section**: 96px
- **band**: 128px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.primary-on}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 36px

### button-primary-pressed
backgroundColor: {colors.surface-light}, textColor: {colors.primary-on}, typography: {typography.button-md}, rounded: {rounded.md}

### button-ghost
backgroundColor: {colors.surface-elevated}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 36px

### button-outline
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 7px 15px, height: 36px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 10px 14px, height: 40px

### hero-stripe
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-xxl}, rounded: {rounded.none}, padding: 96px 32px

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### feature-card-bordered
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.surface-elevated}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### code-window
backgroundColor: {colors.surface-deep}, textColor: {colors.body}, typography: {typography.code-md}, rounded: {rounded.lg}, padding: 24px

### code-tab
backgroundColor: {colors.surface-card}, textColor: {colors.charcoal}, typography: {typography.code-md}, rounded: {rounded.sm}, padding: 6px 12px

### email-mockup
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 0

### badge-pill
backgroundColor: {colors.surface-elevated}, textColor: {colors.body}, typography: {typography.caption}, rounded: {rounded.full}, padding: 4px 10px

### status-dot
backgroundColor: {colors.accent-green}, rounded: {rounded.full}, size: 8px

### nav-bar
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.button-sm}, rounded: {rounded.none}, height: 64px

### sub-nav-pill
backgroundColor: {colors.surface-elevated}, textColor: {colors.body}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 6px 14px

### contributor-avatar
backgroundColor: {colors.surface-card}, rounded: {rounded.full}, size: 32px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.charcoal}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 32px
', '["design-brand", "resend", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (87, 'design_brand', 'revolut', 'design_system', '品牌设计规范 — revolut', '# 品牌设计规范: Revolut

Revolut''s marketing surfaces pair a stark black canvas with the brand''s
cobalt-violet (`#494fdf`) and a wide accent palette of deep, fully-saturated
product colours — teal, light-blue, deep pink, light-green, warning orange.
The system reads as fintech-meets-product-brochure: oversized 80px–136px
Aeonik Pro display headlines, generous whitespace, photography-led hero
bands, and full-width product mockups (cards, phones, terminals) shown as
hero objects inside near-black sections. Most surfaces are either black or
off-white; pill-shaped buttons and rounded-12/20px content cards carry the
consumer-financial-app feel without crossing into playful territory.


## 颜色体系 (Colors)

- **primary**: #494fdf
- **primary-bright**: #4f55f1
- **primary-deep**: #3a40c4
- **on-primary**: #ffffff
- **ink**: #191c1f
- **body**: #1f2226
- **charcoal**: #3a3d40
- **mute**: #505a63
- **ash**: #5c5e60
- **stone**: #8d969e
- **faint**: #c9c9cd
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.72)
- **canvas-light**: #ffffff
- **canvas-dark**: #000000
- **surface-soft**: #f4f4f4
- **surface-card**: #ffffff
- **surface-deep**: #0a0a0a
- **surface-elevated**: #16181a
- **hairline-light**: #e2e2e7
- **hairline-dark**: rgba(255,255,255,0.12)
- **hairline-strong**: #191c1f
- **divider-soft**: rgba(255,255,255,0.06)
- **accent-teal**: #00a87e
- **accent-blue-link**: #376cd5
- **accent-light-blue**: #007bc2
- **accent-light-green**: #428619
- **accent-green-text**: #006400
- **accent-yellow**: #b09000
- **accent-warning**: #ec7e00
- **accent-pink**: #e61e49
- **accent-danger**: #e23b4a
- **accent-deep-red**: #8b0000
- **accent-brown**: #936d62
- **link**: #376cd5

## 排版体系 (Typography)

- **display-xxl**: font: Aeonik Pro | size: 136px | weight: 500 | lh: 1.0 | ls: -2.72px
- **display-xl**: font: Aeonik Pro | size: 80px | weight: 500 | lh: 1.0 | ls: -0.8px
- **display-lg**: font: Aeonik Pro | size: 48px | weight: 500 | lh: 1.21 | ls: -0.48px
- **display-md**: font: Aeonik Pro | size: 40px | weight: 500 | lh: 1.2 | ls: -0.4px
- **heading-lg**: font: Aeonik Pro | size: 32px | weight: 500 | lh: 1.19 | ls: -0.32px
- **heading-md**: font: Aeonik Pro | size: 24px | weight: 500 | lh: 1.33 | ls: 0
- **heading-sm**: font: Aeonik Pro | size: 20px | weight: 500 | lh: 1.4 | ls: 0
- **body-lg**: font: Inter | size: 18px | weight: 400 | lh: 1.56 | ls: -0.09px
- **body-md**: font: Inter | size: 16px | weight: 400 | lh: 1.5 | ls: 0.24px
- **body-md-bold**: font: Inter | size: 16px | weight: 600 | lh: 1.5 | ls: 0.16px
- **body-sm**: font: Inter | size: 14px | weight: 400 | lh: 1.43
- **button-lg**: font: Aeonik Pro | size: 20px | weight: 500 | lh: 1.4
- **button-md**: font: Inter | size: 16px | weight: 600 | lh: 1.5 | ls: 0.24px
- **button-sm**: font: Inter | size: 14px | weight: 600 | lh: 1.43
- **caption**: font: Inter | size: 13px | weight: 400 | lh: 1.4
- **link-emph**: font: Inter | size: 16px | weight: 700 | lh: 1.5 | ls: 0.24px

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 6px
- **sm**: 8px
- **md**: 14px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **xxxl**: 48px
- **block**: 80px
- **section**: 88px
- **band**: 120px

## 圆角体系 (Border Radius)

- **none**: 0px
- **sm**: 8px
- **md**: 12px
- **lg**: 20px
- **xl**: 28px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.canvas-light}, textColor: {colors.canvas-dark}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 14px 28px, height: 48px

### button-primary-pressed
backgroundColor: {colors.faint}, textColor: {colors.canvas-dark}, typography: {typography.button-md}, rounded: {rounded.full}

### button-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 14px 28px, height: 48px

### button-soft
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 14px 28px, height: 48px

### button-outline-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 13px 27px, height: 48px

### button-outline-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 13px 27px, height: 48px

### button-pill-sm
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 8px 16px, height: 36px

### text-input
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 14px 16px, height: 56px

### hero-band-dark
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.display-xxl}, rounded: {rounded.none}, padding: 88px 24px

### hero-band-photo
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 0

### feature-card-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### feature-card-dark
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### plan-card
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### plan-card-featured
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### product-mockup
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, rounded: {rounded.xl}, padding: 48px

### download-tile
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.body-sm}, rounded: {rounded.md}, padding: 12px 20px, height: 56px

### badge-tag
backgroundColor: {colors.surface-soft}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.full}, padding: 4px 12px

### badge-feature
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.caption}, rounded: {rounded.full}, padding: 4px 12px

### nav-bar
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.none}, height: 64px

### sub-nav-pill
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.button-sm}, rounded: {rounded.full}, padding: 8px 16px

### footer
backgroundColor: {colors.canvas-dark}, textColor: {colors.on-dark-mute}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 80px 24px
', '["design-brand", "revolut", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (88, 'design_brand', 'runwayml', 'design_system', '品牌设计规范 — runwayml', '# Design System Inspired by Runway

## 1. Visual Theme & Atmosphere

Runway''s interface is a cinematic reel brought to life as a website — a dark, editorial, film-production-grade design where full-bleed photography and video ARE the primary UI elements. This is not a typical tech product page; it''s a visual manifesto for AI-powered creativity. Every section feels like a frame from a film: dramatic lighting, sweeping landscapes, and intimate human moments captured in high-quality imagery that dominates the viewport.

The design language is built on a single typeface — abcNormal — a clean, geometric sans-serif that handles everything from 48px display headlines to 11px uppercase labels. This single-font commitment creates an extreme typographic uniformity that lets the visual content speak louder than the text. Headlines use tight line-heights (1.0) with negative letter-spacing (-0.9px to -1.2px), creating compressed text blocks that feel like film titles rather than marketing copy.

What makes Runway distinctive is its complete commitment to visual content as design. Rather than illustrating features with icons or diagrams, Runway shows actual AI-generated and AI-enhanced imagery — cars driving through cinematic landscapes, artistic portraits, architectural renders. The interface itself retreats into near-invisibility: minimal borders, zero shadows, subtle cool-gray text, and a dark palette that puts maximum focus on the photography.

**Key Characteristics:**
- Cinematic full-bleed photography and video as primary UI elements
- Single typeface system: abcNormal for everything from display to micro labels
- Dark-dominant palette with cool-toned neutrals (#767d88, #7d848e)
- Zero shadows, minimal borders — the interface is intentionally invisible
- Tight display typography (line-height 1.0) with negative tracking (-0.9px to -1.2px)
- Uppercase labels with positive letter-spacing for navigational structure
- Weight 450 (unusual intermediate) for small uppercase text —', '["design-brand", "runwayml"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (89, 'design_brand', 'sanity', 'design_system', '品牌设计规范 — sanity', '# Design System Inspired by Sanity

## 1. Visual Theme & Atmosphere

Sanity''s website is a developer-content platform rendered as a nocturnal command center -- dark, precise, and deeply structured. The entire experience sits on a near-black canvas (`#0b0b0b`) that reads less like a "dark mode toggle" and more like the natural state of a tool built for people who live in terminals. Where most CMS marketing pages reach for friendly pastels and soft illustration, Sanity leans into the gravity of its own product: structured content deserves a structured stage.

The signature typographic voice is waldenburgNormal -- a distinctive, slightly geometric sans-serif with tight negative letter-spacing (-0.32px to -4.48px at display sizes) that gives headlines a compressed, engineered quality. At 112px hero scale with -4.48px tracking, the type feels almost machined -- like precision-cut steel letterforms. This is paired with IBM Plex Mono for code and technical labels, creating a dual-register voice: editorial authority meets developer credibility.

What makes Sanity distinctive is the interplay between its monochromatic dark palette and vivid, saturated accent punctuation. The neutral scale runs from pure black through a tightly controlled gray ramp (`#0b0b0b` -> `#212121` -> `#353535` -> `#797979` -> `#b9b9b9` -> `#ededed` -> `#ffffff`) with no warm or cool bias -- just pure, achromatic precision. Against this disciplined backdrop, a neon green accent (display-p3 green) and electric blue (`#0052ef`) land with the impact of signal lights in a dark control room. The orange-red CTA (`#f36458`) provides the only warm touch in an otherwise cool system.

**Key Characteristics:**
- Near-black canvas (`#0b0b0b`) as the default, natural environment -- not a dark "mode" but the primary identity
- waldenburgNormal with extreme negative tracking at display sizes, creating a precision-engineered typographic voice
- Pure achromatic gray scale -- no warm or cool undertones, pure neutral dis', '["design-brand", "sanity"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (90, 'design_brand', 'sentry', 'design_system', '品牌设计规范 — sentry', '# 品牌设计规范: Sentri Inspired

An inspired interpretation of Sentri''s design language — a developer-tools brand built on a deep purple-violet midnight canvas, electric lime accents, and a slightly subversive illustrated personality. The system pairs a custom display sans (chunky, playful, near-condensed) with the open Rubik family for UI copy and Monaco for code, then leans on dark-on-light pricing surfaces, sticker-style mascots, and a single-color CTA hierarchy where black-violet buttons read as the primary action against either polarity.

## 颜色体系 (Colors)

- **primary**: #150f23
- **ink-deep**: #1f1633
- **on-primary**: #ffffff
- **accent-lime**: #c2ef4e
- **accent-pink**: #fa7faa
- **accent-violet**: #6a5fc1
- **accent-violet-deep**: #422082
- **accent-violet-mid**: #79628c
- **surface-canvas-dark**: #1f1633
- **surface-canvas-light**: #ffffff
- **surface-night**: #150f23
- **surface-press-light**: #f0f0f0
- **surface-press-stronger**: #efefef
- **hairline-violet**: #362d59
- **hairline-cool**: #cfcfdb
- **hairline-cloud**: #e5e7eb
- **ink**: #1f1633
- **ink-press**: #1a1a1a
- **on-dark-muted**: #bdb8c0
- **on-dark-faint**: #3f3849
- **ring-focus**: #9dc1f5

## 排版体系 (Typography)

- **display-hero**: font: Sentri Display, Rubik, system-ui, sans-serif | size: 88px | weight: 700 | lh: 1.2 | ls: 0
- **display-large**: font: Sentri Display, Rubik, system-ui, sans-serif | size: 60px | weight: 500 | lh: 1.1 | ls: 0
- **heading-xl**: font: Rubik, -apple-system, system-ui, Segoe UI, Helvetica, Arial, sans-serif | size: 30px | weight: 500 | lh: 1.2 | ls: 0
- **heading-lg**: font: Rubik, -apple-system, system-ui, sans-serif | size: 27px | weight: 500 | lh: 1.25 | ls: 0
- **heading-md**: font: Rubik, -apple-system, system-ui, sans-serif | size: 24px | weight: 500 | lh: 1.25 | ls: 0
- **heading-sm**: font: Rubik, -apple-system, system-ui, sans-serif | size: 20px | weight: 600 | lh: 1.25 | ls: 0
- **body-lg**: font: Rubik, -apple-system, system-ui, sans-serif | size: 16px | weight: 400 | lh: 2.0 | ls: 0
- **body-strong**: font: Rubik, -apple-system, system-ui, sans-serif | size: 16px | weight: 600 | lh: 1.5 | ls: 0
- **body-md**: font: Rubik, -apple-system, system-ui, sans-serif | size: 16px | weight: 500 | lh: 1.5 | ls: 0
- **eyebrow**: font: Rubik, -apple-system, system-ui, sans-serif | size: 15px | weight: 500 | lh: 1.4 | ls: 0
- **button-cap**: font: Rubik, -apple-system, system-ui, sans-serif | size: 14px | weight: 700 | lh: 1.14 | ls: 0.2px
- **button-cap-light**: font: Rubik, -apple-system, system-ui, sans-serif | size: 14px | weight: 500 | lh: 1.29 | ls: 0.2px
- **caption**: font: Rubik, -apple-system, system-ui, sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: 0
- **micro-cap**: font: Rubik, -apple-system, system-ui, sans-serif | size: 10px | weight: 600 | lh: 1.8 | ls: 0.25px
- **code**: font: Monaco, Menlo, Ubuntu Mono, monospace | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **code-strong**: font: Monaco, Menlo, Ubuntu Mono, monospace | size: 16px | weight: 700 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 96px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 10px
- **xl**: 12px
- **xxl**: 18px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-cap}, rounded: {rounded.md}, padding: 12px 16px

### button-primary-pressed
backgroundColor: {colors.surface-press-stronger}, textColor: {colors.ink-press}, typography: {typography.button-cap}, rounded: {rounded.md}, padding: 12px 16px

### button-inverted
backgroundColor: {colors.on-primary}, textColor: {colors.ink-deep}, typography: {typography.button-cap}, rounded: {rounded.md}, padding: 12px 16px

### button-inverted-pressed
backgroundColor: {colors.surface-press-light}, textColor: {colors.ink-press}, typography: {typography.button-cap}, rounded: {rounded.md}, padding: 12px 16px

### button-ghost-on-dark
backgroundColor: {colors.on-dark-faint}, textColor: {colors.on-primary}, typography: {typography.button-cap}, rounded: {rounded.xl}, padding: 8px

### button-violet-token
backgroundColor: {colors.accent-violet-mid}, textColor: {colors.on-primary}, typography: {typography.button-cap-light}, rounded: {rounded.xl}, padding: 8px 16px

### button-disabled
backgroundColor: {colors.hairline-cloud}, textColor: {colors.on-dark-muted}, typography: {typography.button-cap}, rounded: {rounded.md}, padding: 12px 16px

### pill-neutral-dark
backgroundColor: {colors.surface-night}, textColor: {colors.on-primary}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 4px 8px

### chip-lime-keyword
backgroundColor: {colors.accent-lime}, textColor: {colors.ink-deep}, typography: {typography.display-hero}, rounded: {rounded.xs}, padding: 0 12px

### text-input
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### text-input-focused
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### select-violet
backgroundColor: {colors.accent-violet-deep}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 16px

### card-pricing
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.surface-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### card-feature-dark
backgroundColor: {colors.ink-deep}, textColor: {colors.on-primary}, typography: {typography.body-lg}, rounded: {rounded.xxl}, padding: 32px

### card-spotlight-violet
backgroundColor: {colors.accent-violet-deep}, textColor: {colors.on-primary}, typography: {typography.body-lg}, rounded: {rounded.xxl}, padding: 32px

### code-block
backgroundColor: {colors.surface-night}, textColor: {colors.on-primary}, typography: {typography.code}, rounded: {rounded.md}, padding: 16px

### link-on-dark
backgroundColor: {colors.surface-canvas-dark}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### link-on-light
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### nav-bar-light
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### footer-light
backgroundColor: {colors.surface-canvas-light}, textColor: {colors.ink-deep}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 32px 24px
', '["design-brand", "sentry", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (91, 'design_brand', 'shopify', 'design_system', '品牌设计规范 — shopify', '# 品牌设计规范: Shopifi Inspired

An inspired interpretation of Shopifi''s design language — a cinematic commerce platform that runs two parallel design tracks. The marketing-hero and product-narrative pages live on near-black canvases with full-bleed photography of merchants, giant Neue Haas Grotesk display type at thin weights, and a single black-pill CTA stroked in white. The transactional pages (pricing, signup, dashboards) flip to a cream-mint canvas with pastel aloe and pistachio greens, the same pill button vocabulary, and Inter for UI body. The two tracks share typographic DNA but diverge sharply in canvas polarity — and that choice is the brand.

## 颜色体系 (Colors)

- **primary**: #000000
- **ink**: #000000
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **canvas-night**: #000000
- **canvas-night-elevated**: #0a0a0a
- **canvas-light**: #ffffff
- **canvas-cream**: #fbfbf5
- **surface-elevated-dark**: #1e2c31
- **shade-30**: #d4d4d8
- **shade-40**: #a1a1aa
- **shade-50**: #71717a
- **shade-60**: #52525b
- **shade-70**: #3f3f46
- **hairline-light**: #e4e4e7
- **hairline-dark**: #1e2c31
- **aloe-10**: #c1fbd4
- **pistachio-10**: #d4f9e0
- **link-cool-1**: #9dabad
- **link-cool-2**: #9797a2
- **link-cool-3**: #bdbdca
- **link-mint**: #99b3ad

## 排版体系 (Typography)

- **display-xxl**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 96px | weight: 330 | lh: 1.0 | ls: 2.4px
- **display-xl**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 70px | weight: 330 | lh: 1.0 | ls: 0
- **display-lg**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 55px | weight: 330 | lh: 1.16 | ls: 0
- **display-md**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 48px | weight: 330 | lh: 1.14 | ls: 0
- **heading-xl**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 28px | weight: 500 | lh: 1.28 | ls: 0.42px
- **heading-lg**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 24px | weight: 400 | lh: 1.14 | ls: 0.36px
- **heading-md**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 20px | weight: 500 | lh: 1.4 | ls: 0.3px
- **heading-sm**: font: NeueHaasGrotesk Display, Helvetica, Arial, sans-serif | size: 18px | weight: 500 | lh: 1.25 | ls: 0.72px
- **body-lg**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 18px | weight: 550 | lh: 1.56 | ls: 0
- **body-md**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 16px | weight: 420 | lh: 1.5 | ls: 0
- **body-strong**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 16px | weight: 550 | lh: 1.5 | ls: 0
- **caption**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 14px | weight: 500 | lh: 1.49 | ls: 0.28px
- **micro**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 13px | weight: 500 | lh: 1.5 | ls: -0.13px
- **eyebrow-cap**: font: Inter Variable, Inter, Helvetica, Arial, sans-serif | size: 12px | weight: 400 | lh: 1.2 | ls: 0.72px
- **code**: font: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace | size: 16px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **huge**: 64px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 5px
- **md**: 8px
- **lg**: 12px
- **xl**: 20px
- **pill**: 9999px

## 组件定义 (Components)

### button-primary-pill
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 24px

### button-primary-pill-pressed
backgroundColor: {colors.shade-70}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 24px

### button-outline-on-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 26px

### button-outline-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 24px

### button-aloe-pill
backgroundColor: {colors.aloe-10}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.pill}, padding: 12px 24px

### text-input
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 12px

### card-pricing
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.aloe-10}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-feature-cinematic
backgroundColor: {colors.canvas-night-elevated}, textColor: {colors.on-primary}, typography: {typography.body-lg}, rounded: {rounded.lg}, padding: 32px

### card-pistachio-band
backgroundColor: {colors.pistachio-10}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-photo-frame
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 0px

### pill-tag-mint
backgroundColor: {colors.aloe-10}, textColor: {colors.ink}, typography: {typography.eyebrow-cap}, rounded: {rounded.pill}, padding: 4px 12px

### pill-tag-shade
backgroundColor: {colors.shade-30}, textColor: {colors.ink}, typography: {typography.eyebrow-cap}, rounded: {rounded.pill}, padding: 4px 12px

### nav-bar-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### nav-bar-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### link-on-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 24px

### footer-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 24px
', '["design-brand", "shopify", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (92, 'design_brand', 'slack', 'design_system', '品牌设计规范 — slack', '# 品牌设计规范: Slacc Inspired

An inspired interpretation of Slacc''s design language — a workplace messaging brand built on a deep aubergine primary, with cream-lavender hero gradients, blue inline links, and pill CTAs. The system pairs a proprietary humanist sans for display with a separate utility sans for body, and stages product UI mockups inside soft pastel-mesh hero composites that act as both decoration and feature explanation.

## 颜色体系 (Colors)

- **primary**: #4a154b
- **primary-deep**: #481a54
- **primary-press**: #611f69
- **primary-tint**: #592466
- **on-primary**: #ffffff
- **ink**: #1d1d1d
- **ink-mute**: #696969
- **link-blue**: #1264a3
- **link-hover**: #3860be
- **canvas**: #ffffff
- **canvas-cream**: #f4ede4
- **canvas-lavender**: #f9f0ff
- **surface-elev**: #ffffff
- **surface-aubergine**: #4a154b
- **hairline**: #e6e6e6
- **hairline-strong**: #000000
- **semantic-error**: #cc4117
- **semantic-success**: #007a5a
- **on-aubergine-mute**: #d9bdde

## 排版体系 (Typography)

- **display-xxl**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 64px | weight: 700 | lh: 1.12 | ls: -0.768px
- **display-xl**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 58px | weight: 600 | lh: 1.25 | ls: -0.464px
- **display-lg**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 50px | weight: 700 | lh: 1.12 | ls: -0.6px
- **display-md**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 32px | weight: 700 | lh: 1.25 | ls: -0.256px
- **heading-lg**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 24px | weight: 700 | lh: 1.33 | ls: -0.096px
- **heading-md**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 22px | weight: 600 | lh: 1.4 | ls: 0
- **heading-sm**: font: Salesforce-Avant-Garde, system-ui, -apple-system, BlinkMacSystemFont, sans-serif | size: 18px | weight: 600 | lh: 1.56 | ls: -0.0216px
- **body-lg**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 18px | weight: 400 | lh: 1.55 | ls: -0.0216px
- **body-md**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 16px | weight: 400 | lh: 1.55 | ls: 0
- **body-strong**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 16px | weight: 700 | lh: 1.5 | ls: 0.16px
- **button-lg**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 18px | weight: 700 | lh: 1.0 | ls: 0
- **button-md**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 16px | weight: 700 | lh: 1.38 | ls: 0.2px
- **button-cap**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 14.4px | weight: 700 | lh: 1.0 | ls: 0.144px
- **caption**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.43 | ls: 0.1px
- **micro-cap**: font: Salesforce-Sans, system-ui, -apple-system, sans-serif | size: 12px | weight: 700 | lh: 1.0 | ls: 0.96px

## 间距体系 (Spacing)

- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **huge**: 28px

## 圆角体系 (Border Radius)

- **xs**: 2px
- **sm**: 4px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 48px
- **pill**: 90px

## 组件定义 (Components)

### button-primary-pill
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 14px 28px

### button-primary-pill-pressed
backgroundColor: {colors.primary-press}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 14px 28px

### button-secondary-pill
backgroundColor: {colors.canvas-lavender}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 10px 30px

### button-outline-aubergine
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 14px 28px

### button-outline-on-aubergine
backgroundColor: {colors.surface-aubergine}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 14px 28px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 10px 12px

### pill-cap-shade
backgroundColor: {colors.canvas-cream}, textColor: {colors.ink}, typography: {typography.micro-cap}, rounded: {rounded.pill}, padding: 4px 12px

### card-pricing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.surface-aubergine}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### card-feature-cream
backgroundColor: {colors.canvas-cream}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### card-aubergine-band
backgroundColor: {colors.surface-aubergine}, textColor: {colors.on-primary}, typography: {typography.body-lg}, rounded: {rounded.xl}, padding: 48px

### card-stat
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.display-lg}, rounded: {rounded.xl}, padding: 32px

### nav-bar-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### link-on-light
backgroundColor: {colors.canvas}, textColor: {colors.link-blue}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### link-on-aubergine
backgroundColor: {colors.surface-aubergine}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-aubergine
backgroundColor: {colors.surface-aubergine}, textColor: {colors.on-primary}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 32px 24px
', '["design-brand", "slack", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (94, 'design_brand', 'spotify', 'design_system', '品牌设计规范 — spotify', '# Design System Inspired by Spotify

## 1. Visual Theme & Atmosphere

Spotify''s web interface is a dark, immersive music player that wraps listeners in a near-black cocoon (`#121212`, `#181818`, `#1f1f1f`) where album art and content become the primary source of color. The design philosophy is "content-first darkness" — the UI recedes into shadow so that music, podcasts, and playlists can glow. Every surface is a shade of charcoal, creating a theater-like environment where the only true color comes from the iconic Spotify Green (`#1ed760`) and the album artwork itself.

The typography uses SpotifyMixUI and SpotifyMixUITitle — proprietary fonts from the CircularSp family (Circular by Lineto, customized for Spotify) with an extensive fallback stack that includes Arabic, Hebrew, Cyrillic, Greek, Devanagari, and CJK fonts, reflecting Spotify''s global reach. The type system is compact and functional: 700 (bold) for emphasis and navigation, 600 (semibold) for secondary emphasis, and 400 (regular) for body. Buttons use uppercase with positive letter-spacing (1.4px–2px) for a systematic, label-like quality.

What distinguishes Spotify is its pill-and-circle geometry. Primary buttons use 500px–9999px radius (full pill), circular play buttons use 50% radius, and search inputs are 500px pills. Combined with heavy shadows (`rgba(0,0,0,0.5) 0px 8px 24px`) on elevated elements and a unique inset border-shadow combo (`rgb(18,18,18) 0px 1px 0px, rgb(124,124,124) 0px 0px 0px 1px inset`), the result is an interface that feels like a premium audio device — tactile, rounded, and built for touch.

**Key Characteristics:**
- Near-black immersive dark theme (`#121212`–`#1f1f1f`) — UI disappears behind content
- Spotify Green (`#1ed760`) as singular brand accent — never decorative, always functional
- SpotifyMixUI/CircularSp font family with global script support
- Pill buttons (500px–9999px) and circular controls (50%) — rounded, touch-optimized
- Uppercase button labels with wide letter-', '["design-brand", "spotify"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (95, 'design_brand', 'starbucks', 'design_system', '品牌设计规范 — starbucks', '# Design System Inspired by Starbucks

## 1. Visual Theme & Atmosphere

Starbucks'' design system is a **warm, confident retail flagship** wearing the green of their storefront apron across every surface. The canvas alternates between a neutral-warm cream (`#f2f0eb`) and a ceramic off-white (`#edebe9`) — colors that reference actual store materials: the paper napkins, the café walls, the wood finishes — while the signature **Starbucks Green** (`#006241`) anchors the brand moment on hero bands, CTAs, and the Rewards experience. The greens come in four calibrated shades (Starbucks, Accent, House, Uplift) each mapped to a specific surface role, and gold (`#cba258`) appears only around Rewards-status ceremony — not as a general accent.

Typography carries most of the brand voice. The proprietary **SoDoSans** typeface (custom to Starbucks) sits across nearly every surface with a tight `-0.16px` letter-spacing — it reads confident and friendly rather than fashion-magazine severe. What''s unusual: the Rewards page switches to a warm serif (`"Lander Tall", "Iowan Old Style", Georgia`) for specific headline moments, subtly echoing the nostalgic feel of a coffeehouse chalkboard. And the Careers pages use a handwritten script (`"Kalam", "Comic Sans MS", cursive`) for personal cup-name touches. Three typefaces, three contexts — the system is disciplined about when each appears.

The surfaces breathe through rounded geometry. Every button is a 50px full-pill. Cards take a 12px rounded-rectangle. The "Frap" floating CTA — a 56px circular order button in Green Accent (`#00754A`) — is the product''s signature depth move: it floats bottom-right with a layered shadow stack (`0 0 6px rgba(0,0,0,0.24)` base + `0 8px 12px rgba(0,0,0,0.14)` ambient) and compresses via `scale(0.95)` on press. Elevations are otherwise restrained — card shadows stay at a whispered `0.14/0.24` alpha, global nav gets a quiet three-layer shadow stack. The whole system feels like clean café signage: legible, warm,', '["design-brand", "starbucks"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (96, 'design_brand', 'stripe', 'design_system', '品牌设计规范 — stripe', '# 品牌设计规范: Stripi Inspired

An inspired interpretation of Stripi''s design language — a financial-infrastructure brand built on a deep navy ink, an electric indigo primary, and a recurring atmospheric gradient mesh that occupies the upper third of nearly every marketing page. The system pairs the proprietary Sohne family at thin (300) weights with negative letter-spacing for editorial-density display headlines, and uses tabular-figure body type where money and numerics matter. Buttons are tight-radius pills, cards live on near-white surfaces, and the dashboard track flips polarity to a familiar dark-app shell.

## 颜色体系 (Colors)

- **primary**: #533afd
- **primary-deep**: #4434d4
- **primary-press**: #2e2b8c
- **primary-soft**: #665efd
- **primary-bg-subdued-hover**: #b9b9f9
- **brand-dark-900**: #1c1e54
- **ink**: #0d253d
- **ink-secondary**: #273951
- **ink-mute**: #64748d
- **ink-mute-2**: #61718a
- **on-primary**: #ffffff
- **canvas**: #ffffff
- **canvas-soft**: #f6f9fc
- **canvas-cream**: #f5e9d4
- **hairline**: #e3e8ee
- **hairline-input**: #a8c3de
- **ruby**: #ea2261
- **magenta**: #f96bee
- **lemon**: #9b6829
- **shadow-blue**: #003770

## 排版体系 (Typography)

- **display-xxl**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 56px | weight: 300 | lh: 1.03 | ls: -1.4px
- **display-xl**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 48px | weight: 300 | lh: 1.15 | ls: -0.96px
- **display-lg**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 32px | weight: 300 | lh: 1.1 | ls: -0.64px
- **display-md**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 26px | weight: 300 | lh: 1.12 | ls: -0.26px
- **heading-lg**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 22px | weight: 300 | lh: 1.1 | ls: -0.22px
- **heading-md**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 20px | weight: 300 | lh: 1.4 | ls: -0.2px
- **heading-sm**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 18px | weight: 300 | lh: 1.4 | ls: 0
- **body-lg**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 16px | weight: 300 | lh: 1.4 | ls: 0
- **body-md**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 15px | weight: 300 | lh: 1.4 | ls: 0
- **body-tabular**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 14px | weight: 300 | lh: 1.4 | ls: -0.42px
- **button-md**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 16px | weight: 400 | lh: 1.0 | ls: 0
- **button-sm**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 14px | weight: 400 | lh: 1.0 | ls: 0
- **caption**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 13px | weight: 400 | lh: 1.4 | ls: -0.39px
- **micro**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 11px | weight: 300 | lh: 1.4 | ls: 0
- **micro-cap**: font: sohne-var, ''SF Pro Display'', system-ui, -apple-system, sans-serif | size: 10px | weight: 400 | lh: 1.15 | ls: 0.1px

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **huge**: 64px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **pill**: 9999px

## 组件定义 (Components)

### button-primary-pill
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 8px 16px

### button-primary-pill-pressed
backgroundColor: {colors.primary-press}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 8px 16px

### button-secondary
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 8px 16px

### button-on-dark
backgroundColor: {colors.brand-dark-900}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.pill}, padding: 8px 16px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### text-input-focused
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### card-feature-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.brand-dark-900}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-cream-band
backgroundColor: {colors.canvas-cream}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-dashboard-mockup
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-tabular}, rounded: {rounded.lg}, padding: 24px

### pill-tag-soft
backgroundColor: {colors.primary-bg-subdued-hover}, textColor: {colors.primary-deep}, typography: {typography.micro-cap}, rounded: {rounded.pill}, padding: 4px 8px

### nav-bar-on-mesh
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### link-on-light
backgroundColor: {colors.canvas}, textColor: {colors.primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.ink-mute}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 24px
', '["design-brand", "stripe", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (98, 'design_brand', 'superhuman', 'design_system', '品牌设计规范 — superhuman', '# 品牌设计规范: Superhumon Inspired

An inspired interpretation of Superhumon''s design language — a fast-email productivity brand split between an editorial dark hero (deep indigo navy with violet-sky atmospheric backdrop and a portrait subject) and a quiet white content body with off-warm-grey ink. The system uses a single proprietary variable display sans, heavy weight 460–540 with tight tracking, and a deep-teal closing CTA band that breaks the indigo/white rhythm with a warm dark interlude. Buttons are tight rounded rectangles, pricing is sober and dense, and the brand reads more like a high-end newsletter than a SaaS app.

## 颜色体系 (Colors)

- **primary**: #1b1938
- **primary-deep**: #0e0c1f
- **on-primary**: #ffffff
- **ink**: #292827
- **ink-mute**: #73706d
- **ink-faint**: #9a9794
- **canvas**: #ffffff
- **canvas-soft**: #fafaf8
- **surface-violet-soft**: #c9b4fa
- **surface-teal-deep**: #0e3030
- **surface-teal-mid**: #155555
- **hairline**: #e8e4dd
- **hairline-dark**: #3f3a52
- **on-dark-mute**: #bcbac9
- **on-dark-faint**: #5a5772

## 排版体系 (Typography)

- **display-xxl**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 64px | weight: 540 | lh: 0.96 | ls: 0
- **display-xl**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 48px | weight: 460 | lh: 0.96 | ls: -1.32px
- **display-lg**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 28px | weight: 540 | lh: 1.14 | ls: -0.63px
- **display-md**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 22px | weight: 460 | lh: 1.1 | ls: -0.315px
- **heading-lg**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 20px | weight: 460 | lh: 1.2 | ls: -0.4px
- **body-lg**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 18px | weight: 540 | lh: 1.5 | ls: -0.135px
- **body-md**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 16px | weight: 460 | lh: 1.5 | ls: 0
- **body-strong**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 18.72px | weight: 700 | lh: 1.5 | ls: 0
- **button-md**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 16px | weight: 700 | lh: 1.0 | ls: 0
- **button-cap**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 14px | weight: 600 | lh: 1.0 | ls: 0
- **caption**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 14px | weight: 460 | lh: 1.4 | ls: 0
- **micro**: font: ''Super Sans VF'', system-ui, -apple-system, ''Segoe UI'', Roboto, sans-serif | size: 12px | weight: 540 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **huge**: 64px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary-dark
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 12px 20px

### button-primary-dark-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 12px 20px

### button-on-dark-pill
backgroundColor: {colors.surface-violet-soft}, textColor: {colors.primary}, typography: {typography.button-md}, rounded: {rounded.full}, padding: 12px 20px

### button-secondary-outline
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 12px 20px

### button-on-teal
backgroundColor: {colors.canvas}, textColor: {colors.surface-teal-deep}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 12px 20px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 10px 12px

### card-feature-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-teal-band
backgroundColor: {colors.surface-teal-deep}, textColor: {colors.on-primary}, typography: {typography.body-lg}, rounded: {rounded.lg}, padding: 64px

### card-feature-row
backgroundColor: {colors.canvas-soft}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 24px

### pill-tab-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-cap}, rounded: {rounded.full}, padding: 8px 16px

### nav-bar-dark
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### nav-bar-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### link-on-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.ink-mute}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 24px
', '["design-brand", "superhuman", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (99, 'design_brand', 'tesla', 'design_system', '品牌设计规范 — tesla', '# Design System Inspired by Tesla

## 1. Visual Theme & Atmosphere

Tesla''s website is an exercise in radical subtraction — a digital showroom where the product is everything and the interface is almost nothing. The page opens with a full-viewport hero that fills the entire screen with cinematic car photography: three vehicles arranged on polished concrete against a hazy cityscape sky, with a single model name floating above in translucent white type. There are no decorative borders, no gradients, no patterns, no shadows. The UI exists only to provide just enough navigational structure to get out of the way. Every pixel that isn''t product imagery is white space, and that restraint is the design system''s most powerful statement.

The color philosophy is almost ascetic: a single blue (`#3E6AE1`) for primary calls to action, three shades of dark gray for text hierarchy, and white for everything else. The entire emotional weight is carried by photography — sprawling landscape shots, studio-lit vehicle profiles, and atmospheric environmental compositions that stretch edge-to-edge across each viewport-height section. The UI chrome dissolves into the imagery. The navigation bar floats above the hero with no visible background, border, or shadow — the TESLA wordmark and five navigation labels simply exist in the space, trusting the content beneath them to provide sufficient contrast.

Typography recently transitioned from Gotham to Universal Sans — a custom family split into "Display" for headlines and "Text" for body/UI elements — unifying the website, mobile app, and in-car software into a single typographic voice. The Display variant renders hero titles at 40px weight 500, while the Text variant handles everything from navigation (14px/500) to body copy (14px/400). The font carries a geometric precision with slightly humanist terminals that feels engineered rather than designed — exactly matching Tesla''s brand identity of technology that doesn''t need to announce itself.', '["design-brand", "tesla"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (100, 'design_brand', 'theverge', 'design_system', '品牌设计规范 — theverge', '# Design System Inspired by The Verge

## 1. Visual Theme & Atmosphere

The Verge''s 2024 redesign feels like somebody wired a Condé Nast magazine to a chiptune soundboard. The canvas is almost-black (`#131313`), the headlines are built from a brutally heavy display face (Manuka) that runs up to 107px, and the whole page is peppered with acid-mint `#3cffd0` and ultraviolet `#5200ff` that behave less like brand colors and more like hazard tape. Story tiles are not quiet gray cards — they''re saturated, full-bleed color blocks (yellow, pink, orange, blue, purple) that feel like pasted-up rave flyers arranged into a timeline. The mood is "developer console meets club night meets tech tabloid": serious enough to cover a congressional hearing, loud enough to review a synthesizer.

What makes this system unmistakable is the **StoryStream** timeline: a vertical feed where every post is a rounded rectangle — often 20–40px radius — filled edge-to-edge with color, framed by a thin border, and marked by a mono-uppercase timestamp on its left rail. Stories don''t float on a grid; they stack on a dashed vertical rule like commits in a git log. Above that, a massive **"The Verge" wordmark** dominates the masthead in Manuka at hero scale, letting the reader know before any headline loads that this is editorial territory, not a template.

There is no "light mode" on the homepage — the dark canvas is the product, and the only time the palette inverts is when a single story tile takes a mint or yellow fill. The depth is almost entirely flat: **hairline 1px borders** (`#ffffff`, `#3cffd0`, or `#5200ff`) do the work that shadows would do on a Material-flavored site. Every container is either `#131313` with a 1px outline, a fully saturated accent block, or a slate-gray `#2d2d2d` secondary surface.

**Key Characteristics:**
- Near-black editorial canvas (`#131313`) as the default surface — no light mode on the homepage
- Acid-mint `#3cffd0` + ultraviolet `#5200ff` as hazard-tape accents, ne', '["design-brand", "theverge"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (101, 'design_brand', 'together-ai', 'design_system', '品牌设计规范 — together.ai', '# Design System Inspired by Together AI

## 1. Visual Theme & Atmosphere

Together AI''s interface is a pastel-gradient dreamscape built for enterprise AI infrastructure — a design that somehow makes GPU clusters and model inference feel light, airy, and optimistic. The hero section blooms with soft pink-blue-lavender gradients and abstract, painterly illustrations that evoke clouds and flight, establishing a visual metaphor for the "AI-Native Cloud" proposition. Against this softness, the typography cuts through with precision: "The Future" display font at 64px with aggressive negative tracking (-1.92px) creates dense, authoritative headline blocks.

The design straddles two worlds: a bright, white-canvas light side where pastel gradients and stats cards create an approachable platform overview, and a dark navy universe (`#010120` — not gray-black but a deep midnight blue) where research papers and technical content live. This dual-world approach elegantly separates the "business" messaging (light, friendly, stat-driven) from the "research" messaging (dark, serious, academic).

What makes Together AI distinctive is its type system. "The Future" handles all display and body text with a geometric modernist aesthetic, while "PP Neue Montreal Mono" provides uppercase labels with meticulous letter-spacing — creating a "technical infrastructure company with taste" personality. The brand accents — magenta (`#ef2cc1`) and orange (`#fc4c02`) — appear sparingly in the gradient and illustrations, never polluting the clean UI.

**Key Characteristics:**
- Soft pastel gradients (pink, blue, lavender) against pure white canvas
- Deep midnight blue (`#010120`) for dark/research sections — not gray-black
- Custom "The Future" font with aggressive negative letter-spacing throughout
- PP Neue Montreal Mono for uppercase technical labels
- Sharp geometry (4px, 8px radius) — not rounded, not pill
- Magenta (#ef2cc1) + orange (#fc4c02) brand accents in illustrations only
- Lavender (#bdb', '["design-brand", "together.ai"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (102, 'design_brand', 'uber', 'design_system', '品牌设计规范 — uber', '# Design System Inspired by Uber

## 1. Visual Theme & Atmosphere

Uber''s design language is a masterclass in confident minimalism -- a black-and-white universe where every pixel serves a purpose and nothing decorates without earning its place. The entire experience is built on a stark duality: jet black (`#000000`) and pure white (`#ffffff`), with virtually no mid-tone grays diluting the message. This isn''t the sterile minimalism of a startup that hasn''t finished designing -- it''s the deliberate restraint of a brand so established it can afford to whisper.

The signature typeface, UberMove, is a proprietary geometric sans-serif with a distinctly square, engineered quality. Headlines in UberMove Bold at 52px carry the weight of a billboard -- authoritative, direct, unapologetic. The companion face UberMoveText handles body copy and buttons with a slightly softer, more readable character at medium weight (500). Together, they create a typographic system that feels like a transit map: clear, efficient, built for scanning at speed.

What makes Uber''s design truly distinctive is its use of full-bleed photography and illustration paired with pill-shaped interactive elements (999px border-radius). Navigation chips, CTA buttons, and category selectors all share this capsule shape, creating a tactile, thumb-friendly interface language that''s unmistakably Uber. The illustrations -- warm, slightly stylized scenes of drivers, riders, and cityscapes -- inject humanity into what could otherwise be a cold, monochrome system. The site alternates between white content sections and a full-black footer, with card-based layouts using the gentlest possible shadows (rgba(0,0,0,0.12-0.16)) to create subtle lift without breaking the flat aesthetic.

**Key Characteristics:**
- Pure black-and-white foundation with virtually no mid-tone grays in the UI chrome
- UberMove (headlines) + UberMoveText (body/UI) -- proprietary geometric sans-serif family
- Pill-shaped everything: buttons, chips, n', '["design-brand", "uber"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (103, 'design_brand', 'vercel', 'design_system', '品牌设计规范 — vercel', '# Design System Inspired by Vercel

## 1. Visual Theme & Atmosphere

Vercel''s website is the visual thesis of developer infrastructure made invisible — a design system so restrained it borders on philosophical. The page is overwhelmingly white (`#ffffff`) with near-black (`#171717`) text, creating a gallery-like emptiness where every element earns its pixel. This isn''t minimalism as decoration; it''s minimalism as engineering principle. The Geist design system treats the interface like a compiler treats code — every unnecessary token is stripped away until only structure remains.

The custom Geist font family is the crown jewel. Geist Sans uses aggressive negative letter-spacing (-2.4px to -2.88px at display sizes), creating headlines that feel compressed, urgent, and engineered — like code that''s been minified for production. At body sizes, the tracking relaxes but the geometric precision persists. Geist Mono completes the system as the monospace companion for code, terminal output, and technical labels. Both fonts enable OpenType `"liga"` (ligatures) globally, adding a layer of typographic sophistication that rewards close reading.

What distinguishes Vercel from other monochrome design systems is its shadow-as-border philosophy. Instead of traditional CSS borders, Vercel uses `box-shadow: 0px 0px 0px 1px rgba(0,0,0,0.08)` — a zero-offset, zero-blur, 1px-spread shadow that creates a border-like line without the box model implications. This technique allows borders to exist in the shadow layer, enabling smoother transitions, rounded corners without clipping, and a subtler visual weight than traditional borders. The entire depth system is built on layered, multi-value shadow stacks where each layer serves a specific purpose: one for the border, one for soft elevation, one for ambient depth.

**Key Characteristics:**
- Geist Sans with extreme negative letter-spacing (-2.4px to -2.88px at display) — text as compressed infrastructure
- Geist Mono for code and technical', '["design-brand", "vercel"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (104, 'design_brand', 'vodafone', 'design_system', '品牌设计规范 — vodafone', '# Design System Inspired by Vodafone

## 1. Visual Theme & Atmosphere

Vodafone''s corporate web system carries the confident, broadcast-scale presence of a global telecom brand — built around a single, fiercely-owned brand red and a restrained, editorial layout that lets imagery and type carry the emotional weight. Every page opens the same way: a cinematic dark hero image behind a towering, tight-tracked uppercase display headline ("EVERYONE. CONNECTED.", "INVESTORS", "OUR BUSINESS") followed by a deep red full-width band that acts as a chapter break, then a crisp white editorial grid or a near-black section reserved for institutional content (share ticker, global map, ESG data). The voice is institutional but human: warm documentary photography — cable-laying crews, coral reefs, pine forests, urban twilight — photographed with color-graded realism and set against clean neutral surfaces that never compete with the content.

The typography system is the signature. A custom Vodafone display face runs all the way up to 144px in heavy 800-weight uppercase with negative tracking, and it holds that voice consistently across every page template. Body copy sits in a calm 16-18px mid-weight rhythm. This dual scale — monumental at the top, almost quiet at the bottom — creates the "corporate newsroom" feeling: every page reads like the front of a national paper whose masthead happens to be red.

Surface treatment is disciplined and predictable: a three-surface pass of white (editorial canvas) → Vodafone red (band dividers, CTA buttons, the famous speech-mark logo) → near-black charcoal (footer, share-ticker panel, global-impact map). There is almost no decorative shadow, almost no gradient, and almost no rounded-corner softness. Edges are small and clinical (2px and 6px), buttons operate as a two-tier system — tight 2px rectangles for utility/form actions, and fully-rounded 60px pills for primary content CTAs. This is a design system that trusts the brand color to do the heav', '["design-brand", "vodafone"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28');

-- gaia_knowledge: 172 rows (batch 2)
INSERT INTO "gaia_knowledge" ("id", "source", "source_id", "knowledge_type", "title", "content", "tags", "confidence", "impact_score", "is_active", "vector_embedded", "created_at", "updated_at") VALUES
  (105, 'design_brand', 'voltagent', 'design_system', '品牌设计规范 — voltagent', '# Design System Inspired by VoltAgent

## 1. Visual Theme & Atmosphere

VoltAgent''s interface is a deep-space command terminal for the AI age — a developer-facing darkness built on near-pure-black surfaces (`#050507`) where the only interruption is the electric pulse of emerald green energy. The entire experience evokes the feeling of staring into a high-powered IDE at 2am: dark, focused, and alive with purpose. This is not a friendly SaaS landing page — it''s an engineering platform that announces itself through code snippets, architectural diagrams, and raw technical confidence.

The green accent (`#00d992`) is used with surgical precision — it glows from headlines, borders, and interactive elements like a circuit board carrying a signal. Against the carbon-black canvas, this green reads as "power on" — a deliberate visual metaphor for an AI agent engineering platform. The supporting palette is built entirely from warm-neutral grays (`#3d3a39`, `#8b949e`, `#b8b3b0`) that soften the darkness without introducing color noise, creating a cockpit-like warmth that pure blue-grays would lack.

Typography leans on the system font stack for headings — achieving maximum rendering speed and native-feeling authority — while Inter carries the body and UI text with geometric precision. Code blocks use SFMono-Regular, the same font developers see in their terminals, reinforcing the tool''s credibility at every scroll.

**Key Characteristics:**
- Carbon-black canvas (`#050507`) with warm-gray border containment (`#3d3a39`) — not cold or sterile
- Single-accent identity: Emerald Signal Green (`#00d992`) as the sole chromatic energy source
- Dual-typography system: system-ui for authoritative headings, Inter for precise UI/body text, SFMono for code credibility
- Ultra-tight heading line-heights (1.0–1.11) creating dense, compressed power blocks
- Warm neutral palette (`#3d3a39`, `#8b949e`, `#b8b3b0`) that prevents the dark theme from feeling clinical
- Developer-terminal aesthetic w', '["design-brand", "voltagent"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (106, 'design_brand', 'warp', 'design_system', '品牌设计规范 — warp', '# Design System Inspired by Warp

## 1. Visual Theme & Atmosphere

Warp''s website feels like sitting at a campfire in a deep forest — warm, dark, and alive with quiet confidence. Unlike the cold, blue-tinted blacks favored by most developer tools, Warp wraps everything in a warm near-black that feels like charred wood or dark earth. The text isn''t pure white either — it''s Warm Parchment (`#faf9f6`), a barely-perceptible cream that softens every headline and makes the dark canvas feel inviting rather than austere.

The typography is the secret weapon: Matter, a geometric sans-serif with distinctive character, deployed at Regular weight across virtually all text. The font choice is unusual for a developer tool — Matter has a softness and humanity that signals "this terminal is for everyone, not just greybeards." Combined with tight line-heights and controlled negative letter-spacing on headlines, the effect is refined and approachable simultaneously. Nature photography is woven between terminal screenshots, creating a visual language that says: this tool brings you closer to flow, to calm productivity.

The overall design philosophy is restraint through warmth. Minimal color (almost monochromatic warm grays), minimal ornamentation, and a focus on product showcases set against cinematic dark landscapes. It''s a terminal company that markets like a lifestyle brand.

**Key Characteristics:**
- Warm dark background — not cold black, but earthy near-black with warm gray undertones
- Warm Parchment (`#faf9f6`) text instead of pure white — subtle cream warmth
- Matter font family (Regular weight) — geometric but approachable, not the typical developer-tool typeface
- Nature photography interleaved with product screenshots — lifestyle meets developer tool
- Almost monochromatic warm gray palette — no bold accent colors
- Uppercase labels with wide letter-spacing (2.4px) for categorization — editorial signaling
- Pill-shaped dark buttons (`#353534`, 50px radius) — restrained, m', '["design-brand", "warp"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (107, 'design_brand', 'webflow', 'design_system', '品牌设计规范 — webflow', '# Design System Inspired by Webflow

## 1. Visual Theme & Atmosphere

Webflow''s website is a visually rich, tool-forward platform that communicates "design without code" through clean white surfaces, the signature Webflow Blue (`#146ef5`), and a rich secondary color palette (purple, pink, green, orange, yellow, red). The custom WF Visual Sans Variable font creates a confident, precise typographic system with weight 600 for display and 500 for body.

**Key Characteristics:**
- White canvas with near-black (`#080808`) text
- Webflow Blue (`#146ef5`) as primary brand + interactive color
- WF Visual Sans Variable — custom variable font with weight 500–600
- Rich secondary palette: purple `#7a3dff`, pink `#ed52cb`, green `#00d722`, orange `#ff6b00`, yellow `#ffae13`, red `#ee1d36`
- Conservative 4px–8px border-radius — sharp, not rounded
- Multi-layer shadow stacks (5-layer cascading shadows)
- Uppercase labels: 10px–15px, weight 500–600, wide letter-spacing (0.6px–1.5px)
- translate(6px) hover animation on buttons

## 2. Color Palette & Roles

### Primary
- **Near Black** (`#080808`): Primary text
- **Webflow Blue** (`#146ef5`): `--_color---primary--webflow-blue`, primary CTA and links
- **Blue 400** (`#3b89ff`): `--_color---primary--blue-400`, lighter interactive blue
- **Blue 300** (`#006acc`): `--_color---blue-300`, darker blue variant
- **Button Hover Blue** (`#0055d4`): `--mkto-embed-color-button-hover`

### Secondary Accents
- **Purple** (`#7a3dff`): `--_color---secondary--purple`
- **Pink** (`#ed52cb`): `--_color---secondary--pink`
- **Green** (`#00d722`): `--_color---secondary--green`
- **Orange** (`#ff6b00`): `--_color---secondary--orange`
- **Yellow** (`#ffae13`): `--_color---secondary--yellow`
- **Red** (`#ee1d36`): `--_color---secondary--red`

### Neutral
- **Gray 800** (`#222222`): Dark secondary text
- **Gray 700** (`#363636`): Mid text
- **Gray 300** (`#ababab`): Muted text, placeholder
- **Mid Gray** (`#5a5a5a`): Link text
- **Border Gray** (`#d8d8d8`):', '["design-brand", "webflow"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (108, 'design_brand', 'wired', 'design_system', '品牌设计规范 — wired', '# Design System Inspired by WIRED

## 1. Visual Theme & Atmosphere

WIRED''s homepage feels like a printed broadsheet that someone has plugged into a wall socket. The grid is dense, the rules are thin, the type is loud, and almost every surface is paper-white or pure black with no rounded corners and no decoration that doesn''t earn its place. Image rectangles butt directly against headlines, hairline dividers separate stories the way pica rules separate columns in a real magazine, and the only colors that aren''t grayscale come from the photography itself. There is no "card with shadow" anywhere — the entire layout is held together by typographic weight and the discipline of rules and whitespace, the same way a Condé Nast print page would be assembled in a paste-up room.

The signature move is the **typographic stack**: a brutally large custom serif (WiredDisplay) for the main headline, a humanist serif (BreveText) for body and decks, a geometric sans (Apercu) for UI affordances, and a hard mono uppercase (WiredMono) for the kickers, eyebrows, and timestamps that mark every story. That mono kicker — usually black caps with letter-spacing wide enough to read as a Geiger-counter tick — is what makes a WIRED page instantly recognizable from across the room.

There is exactly one accent color that matters: a saturated link blue (`#057dbc`) that lights up underlined hover states like a CRT scanline. Everything else is black, paper white, and two grays — the design''s confidence comes from refusing to invent more.

**Key Characteristics:**
- Newsstand-density editorial grid: rules and whitespace, never cards or shadows
- Custom serif display + technical mono kickers — the Condé-Nast-meets-engineering-lab voice
- Strictly square corners on every image, container, and ribbon (only icon buttons are circular)
- 2px hard black borders on buttons and links — printerly, not webby
- Mono ALL-CAPS eyebrows on every story with wide tracking (0.9–1.2px)
- Single ink-blue accent for lin', '["design-brand", "wired"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (109, 'design_brand', 'wise', 'design_system', '品牌设计规范 — wise', '# Design System Inspired by Wise

## 1. Visual Theme & Atmosphere

Wise''s website is a bold, confident fintech platform that communicates "money without borders" through massive typography and a distinctive lime-green accent. The design operates on a warm off-white canvas with near-black text (`#0e0f0c`) and a signature Wise Green (`#9fe870`) — a fresh, lime-bright color that feels alive and optimistic, unlike the corporate blues of traditional banking.

The typography uses Wise Sans — a proprietary font used at extreme weight 900 (black) for display headings with a remarkably tight line-height of 0.85 and OpenType `"calt"` (contextual alternates). At 126px, the text is so dense it feels like a protest sign — bold, urgent, and impossible to ignore. Inter serves as the body font with weight 600 as the default for emphasis, creating a consistently confident voice.

What distinguishes Wise is its green-on-white-on-black material palette. Lime Green (`#9fe870`) appears on buttons with dark green text (`#163300`), creating a nature-inspired CTA that feels fresh. Hover states use `scale(1.05)` expansion rather than color changes — buttons physically grow on interaction. The border-radius system uses 9999px for buttons (pill), 30px–40px for cards, and the shadow system is minimal — just `rgba(14,15,12,0.12) 0px 0px 0px 1px` ring shadows.

**Key Characteristics:**
- Wise Sans at weight 900, 0.85 line-height — billboard-scale bold headlines
- Lime Green (`#9fe870`) accent with dark green text (`#163300`) — nature-inspired fintech
- Inter body at weight 600 as default — confident, not light
- Near-black (`#0e0f0c`) primary with warm green undertone
- Scale(1.05) hover animations — buttons physically grow
- OpenType `"calt"` on all text
- Pill buttons (9999px) and large rounded cards (30px–40px)
- Semantic color system with comprehensive state management

## 2. Color Palette & Roles

### Primary Brand
- **Near Black** (`#0e0f0c`): Primary text, background for dark sections
- *', '["design-brand", "wise"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (110, 'design_brand', 'x-ai', 'design_system', '品牌设计规范 — x.ai', '# Design System Inspired by xAI

## 1. Visual Theme & Atmosphere

xAI''s website is a masterclass in dark-first, monospace-driven brutalist minimalism -- a design system that feels like it was built by engineers who understand that restraint is the ultimate form of sophistication. The entire experience is anchored to an almost-black background (`#1f2228`) with pure white text (`#ffffff`), creating a high-contrast, terminal-inspired aesthetic that signals deep technical credibility. There are no gradients, no decorative illustrations, no color accents competing for attention. This is a site that communicates through absence.

The typographic system is split between two carefully chosen typefaces. `GeistMono` (Vercel''s monospace font) handles display-level headlines at an extraordinary 320px with weight 300, and also serves as the button typeface in uppercase with tracked-out letter-spacing (1.4px). `universalSans` handles all body and secondary heading text with a clean, geometric sans-serif voice. The monospace-as-display-font choice is the defining aesthetic decision -- it positions xAI not as a consumer product but as infrastructure, as something built by people who live in terminals.

The spacing system operates on an 8px base grid with values concentrated at the small end (4px, 8px, 24px, 48px), reflecting a dense, information-focused layout philosophy. Border radius is minimal -- the site barely rounds anything, maintaining sharp, architectural edges. There are no decorative shadows, no gradients, no layered elevation. Depth is communicated purely through contrast and whitespace.

**Key Characteristics:**
- Pure dark theme: `#1f2228` background with `#ffffff` text -- no gray middle ground
- GeistMono at extreme display sizes (320px, weight 300) -- monospace as luxury
- Uppercase monospace buttons with 1.4px letter-spacing -- technical, commanding
- universalSans for body text at 16px/1.5 and headings at 30px/1.2 -- clean contrast
- Zero decorative elements: no s', '["design-brand", "x.ai"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (111, 'design_brand', 'zapier', 'design_system', '品牌设计规范 — zapier', '# Design System Inspired by Zapier

## 1. Visual Theme & Atmosphere

Zapier''s website radiates warm, approachable professionalism. It rejects the cold monochrome minimalism of developer tools in favor of a cream-tinted canvas (`#fffefb`) that feels like unbleached paper -- the digital equivalent of a well-organized notebook. The near-black (`#201515`) text has a faint reddish-brown warmth, creating an atmosphere more human than mechanical. This is automation designed to feel effortless, not technical.

The typographic system is a deliberate interplay of two distinct personalities. **Degular Display** -- a geometric, wide-set display face -- handles hero-scale headlines at 56-80px with medium weight (500) and extraordinarily tight line-heights (0.90), creating headlines that compress vertically like stacked blocks. **Inter** serves as the workhorse for everything else, from section headings to body text and navigation, with fallbacks to Helvetica and Arial. **GT Alpina**, an elegant thin-weight serif with aggressive negative letter-spacing (-1.6px to -1.92px), makes occasional appearances for softer editorial moments. This three-font system gives Zapier the ability to shift register -- from bold and punchy (Degular) to clean and functional (Inter) to refined and literary (GT Alpina).

The brand''s signature orange (`#ff4f00`) is unmistakable -- a vivid, saturated red-orange that sits precisely between traffic-cone urgency and sunset warmth. It''s used sparingly but decisively: primary CTA buttons, active state underlines, and accent borders. Against the warm cream background, this orange creates a color relationship that feels energetic without being aggressive.

**Key Characteristics:**
- Warm cream canvas (`#fffefb`) instead of pure white -- organic, paper-like warmth
- Near-black with reddish undertone (`#201515`) -- text that breathes rather than dominates
- Degular Display for hero headlines at 0.90 line-height -- compressed, impactful, modern
- Inter as the unive', '["design-brand", "zapier"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (112, 'design_token', 'token_design_system', 'design_token', 'Design Tokens 系统规范', '# Design Tokens 系统规范

统一的跨平台设计令牌（Design Tokens）系统，用于品牌设计系统的标准化表达。

## 颜色令牌 (Color Tokens)

- **primary.50**: #eff6ff
- **primary.100**: #dbeafe
- **primary.200**: #bfdbfe
- **primary.500**: #3b82f6
- **primary.600**: #2563eb
- **primary.700**: #1d4ed8
- **primary.900**: #1e3a5f
- **neutral.50**: #f8fafc
- **neutral.100**: #f1f5f9
- **neutral.200**: #e2e8f0
- **neutral.700**: #334155
- **neutral.800**: #1e293b
- **neutral.900**: #0f172a
- **accent.amber**: #f59e0b
- **accent.emerald**: #10b981
- **accent.rose**: #f43f5e
- **accent.violet**: #8b5cf6
- **gradients.hero**: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #2563eb 100%)
- **gradients.card**: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)
- **gradients.glow**: 0 0 40px rgba(59,130,246,0.15)

## 排版令牌 (Typography Tokens)

- **fontFamily**: ''Inter'', ''Noto Sans SC'', system-ui, sans-serif
- **headings**: {"h1": "text-5xl md:text-7xl font-bold tracking-tight", "h2": "text-3xl md:text-5xl font-bold", "h3": "text-2xl md:text-3xl font-semibold"}
- **body**: text-base leading-relaxed text-neutral-700
- **caption**: text-sm text-neutral-500

## 间距令牌 (Spacing Tokens)

- **section**: py-16 md:py-24
- **container**: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
- **gap**: gap-6 md:gap-8
', '["design-token", "design-system", "color-token", "typography-token", "spacing-token"]', 0.95, 0.85, 1, 0, '2026-07-02 00:11:28', '2026-07-02 00:11:28'),
  (113, 'design_brand', 'elevenlabs', 'design_system', '品牌设计规范 — elevenlabs', '# 品牌设计规范: ElevenLabs

A voice-AI brand whose marketing surfaces read like a quietly editorial print magazine. The base canvas is off-white (`#f5f5f5`) holding warm near-black ink (`#292524`); the brand voltage is photographic, not chromatic — soft pastel atmospheric gradient orbs (mint → peach → lavender → sky) drift through the page as the only "color" moments. Display runs Waldenburg Light at weight 300 — the editorial signature. Inter carries body, navigation, captions. CTAs are subtle: a near-black ink pill is the primary, a transparent outline is the secondary. The brand trusts atmospheric photography and modest type weights to do all of the brand work; there is no neon accent, no saturated CTA color, no developer-tools dark canvas.

## 颜色体系 (Colors)

- **primary**: #292524
- **primary-active**: #0c0a09
- **ink**: #0c0a09
- **body**: #4e4e4e
- **body-strong**: #292524
- **muted**: #777169
- **muted-soft**: #a8a29e
- **hairline**: #e7e5e4
- **hairline-soft**: #f0efed
- **hairline-strong**: #d6d3d1
- **canvas**: #f5f5f5
- **canvas-soft**: #fafafa
- **canvas-deep**: #0c0a09
- **surface-card**: #ffffff
- **surface-strong**: #f0efed
- **surface-dark**: #0c0a09
- **surface-dark-elevated**: #1c1917
- **on-primary**: #ffffff
- **on-dark**: #ffffff
- **on-dark-soft**: #a8a29e
- **gradient-mint**: #a7e5d3
- **gradient-peach**: #f4c5a8
- **gradient-lavender**: #c8b8e0
- **gradient-sky**: #a8c8e8
- **gradient-rose**: #e8b8c4
- **semantic-error**: #dc2626
- **semantic-success**: #16a34a

## 排版体系 (Typography)

- **display-mega**: font: ''Waldenburg'', ''Times New Roman'', serif | size: 64px | weight: 300 | lh: 1.05 | ls: -1.92px
- **display-xl**: font: ''Waldenburg'', serif | size: 48px | weight: 300 | lh: 1.08 | ls: -0.96px
- **display-lg**: font: ''Waldenburg'', serif | size: 36px | weight: 300 | lh: 1.17 | ls: -0.36px
- **display-md**: font: ''Waldenburg'', serif | size: 32px | weight: 300 | lh: 1.13 | ls: -0.32px
- **display-sm**: font: ''Waldenburg'', serif | size: 24px | weight: 300 | lh: 1.2 | ls: 0
- **title-md**: font: ''Inter'', sans-serif | size: 20px | weight: 500 | lh: 1.35 | ls: 0
- **title-sm**: font: ''Inter'', sans-serif | size: 18px | weight: 500 | lh: 1.44 | ls: 0.18px
- **body-md**: font: ''Inter'', sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0.16px
- **body-strong**: font: ''Inter'', sans-serif | size: 16px | weight: 500 | lh: 1.5 | ls: 0.16px
- **body-sm**: font: ''Inter'', sans-serif | size: 15px | weight: 400 | lh: 1.47 | ls: 0.15px
- **caption**: font: ''Inter'', sans-serif | size: 14px | weight: 400 | lh: 1.5 | ls: 0
- **caption-uppercase**: font: ''Inter'', sans-serif | size: 12px | weight: 600 | lh: 1.4 | ls: 0.96px | transform: uppercase
- **button**: font: ''Inter'', sans-serif | size: 15px | weight: 500 | lh: 1.0 | ls: 0
- **nav-link**: font: ''Inter'', sans-serif | size: 15px | weight: 500 | lh: 1.4 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **base**: 16px
- **md**: 20px
- **lg**: 24px
- **xl**: 32px
- **xxl**: 48px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **xxl**: 24px
- **pill**: 9999px
- **full**: 9999px

## 组件定义 (Components)

### top-nav
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.nav-link}, height: 64px

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button}, rounded: {rounded.pill}, padding: 10px 20px, height: 40px

### button-primary-active
backgroundColor: {colors.primary-active}, textColor: {colors.on-primary}, rounded: {rounded.pill}

### button-outline
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}, rounded: {rounded.pill}, padding: 9px 19px, height: 40px

### button-tertiary-text
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.button}

### hero-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-mega}, padding: 96px

### gradient-orb-card
backgroundColor: {colors.canvas-soft}, textColor: {colors.ink}, rounded: {rounded.xxl}, padding: 32px

### feature-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.title-md}, rounded: {rounded.xl}, padding: 24px

### product-card-stack
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 0

### voice-row
backgroundColor: transparent, textColor: {colors.ink}, typography: {typography.body-md}, padding: 12px 0

### voice-icon-circular
backgroundColor: {colors.surface-strong}, rounded: {rounded.full}, size: 32px

### pricing-tier-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### pricing-tier-featured
backgroundColor: {colors.surface-dark}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### text-input
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 12px 16px, height: 44px

### badge-pill
backgroundColor: {colors.surface-strong}, textColor: {colors.ink}, typography: {typography.caption-uppercase}, rounded: {rounded.pill}, padding: 4px 10px

### cta-band
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.display-lg}, padding: 96px

### testimonial-card
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.body-md}, rounded: {rounded.xl}, padding: 32px

### audio-waveform-card
backgroundColor: {colors.surface-card}, textColor: {colors.ink}, rounded: {rounded.xl}, padding: 24px

### footer
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, padding: 64px 48px

### footer-link
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}
', '["design-brand", "elevenlabs", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:12:40', '2026-07-02 00:12:40'),
  (114, 'design_brand', 'raycast', 'design_system', '品牌设计规范 — raycast', '# 品牌设计规范: Raycast

Raycast''s marketing system reads like an extended product screenshot. The chrome IS the in-product chrome at marketing scale: pure-near-black canvas, hairline 1px borders, command-palette-style cards, Inter typography with the ss03 stylistic set enabled site-wide, white CTA pill, and a small set of saturated category accent colors (yellow / red / green / blue) reserved for extension and feature illustrations. Section rhythm is generous (~96px) but the page never breaks tonal continuity — the whole site sits in one continuous dark mode.


## 颜色体系 (Colors)

- **primary**: #ffffff
- **primary-pressed**: #e8e8e8
- **on-primary**: #000000
- **ink**: #f4f4f6
- **body**: #cdcdcd
- **charcoal**: #d3d3d4
- **mute**: #9c9c9d
- **ash**: #6a6b6c
- **stone**: #434345
- **on-dark**: #ffffff
- **on-dark-mute**: rgba(255,255,255,0.72)
- **canvas**: #07080a
- **surface**: #0d0d0d
- **surface-elevated**: #101111
- **surface-card**: #121212
- **button-fg**: #18191a
- **hairline**: #242728
- **hairline-soft**: rgba(255,255,255,0.08)
- **hairline-strong**: rgba(255,255,255,0.16)
- **accent-blue**: #57c1ff
- **accent-blue-soft**: rgba(87,193,255,0.15)
- **accent-red**: #ff6161
- **accent-red-soft**: rgba(255,97,97,0.15)
- **accent-green**: #59d499
- **accent-green-soft**: rgba(89,212,153,0.15)
- **accent-yellow**: #ffc533
- **accent-yellow-soft**: rgba(255,197,51,0.15)
- **hero-stripe-start**: #ff5757
- **hero-stripe-end**: #a1131a
- **key-bg-start**: #121212
- **key-bg-end**: #0d0d0d

## 排版体系 (Typography)

- **display-xl**: font: Inter | size: 64px | weight: 600 | lh: 1.1 | ls: 0
- **display-lg**: font: Inter | size: 56px | weight: 500 | lh: 1.17 | ls: 0.2px
- **heading-xl**: font: Inter | size: 24px | weight: 500 | lh: 1.6 | ls: 0.2px
- **heading-lg**: font: Inter | size: 22px | weight: 500 | lh: 1.15 | ls: 0
- **heading-md**: font: Inter | size: 20px | weight: 500 | lh: 1.4 | ls: 0.2px
- **heading-sm**: font: Inter | size: 18px | weight: 500 | lh: 1.4 | ls: 0.2px
- **body-lg**: font: Inter | size: 18px | weight: 400 | lh: 1.6 | ls: 0
- **body-md**: font: Inter | size: 16px | weight: 400 | lh: 1.6 | ls: 0
- **body-strong**: font: Inter | size: 16px | weight: 500 | lh: 1.4 | ls: 0.2px
- **body-sm**: font: Inter | size: 14px | weight: 400 | lh: 1.6 | ls: 0
- **body-sm-strong**: font: Inter | size: 14px | weight: 500 | lh: 1.6 | ls: 0.2px
- **caption-md**: font: Inter | size: 13px | weight: 400 | lh: 1.4 | ls: 0.1px
- **caption-sm**: font: Inter | size: 12px | weight: 400 | lh: 1.5 | ls: 0.4px
- **link-md**: font: Inter | size: 16px | weight: 500 | lh: 1.4 | ls: 0.3px
- **button-md**: font: Inter | size: 14px | weight: 500 | lh: 1.6 | ls: 0.2px

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **section**: 96px

## 圆角体系 (Border Radius)

- **none**: 0px
- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 10px
- **xl**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 36px

### button-primary-pressed
backgroundColor: {colors.primary-pressed}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.md}

### button-secondary
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 36px

### button-tertiary
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 8px 16px, height: 36px

### button-disabled
backgroundColor: {colors.surface-elevated}, textColor: {colors.ash}, rounded: {rounded.md}

### install-button
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.md}, padding: 6px 14px

### text-input
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 8px 12px, height: 36px

### text-input-focused
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, rounded: {rounded.md}

### store-search-bar
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 10px 16px, height: 44px

### command-palette-row
backgroundColor: transparent, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 6px 10px

### command-palette-row-active
backgroundColor: {colors.surface-card}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.sm}

### pill-tab
backgroundColor: transparent, textColor: {colors.body}, typography: {typography.body-sm}, rounded: {rounded.full}, padding: 4px 10px

### pill-tab-active
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-sm}, rounded: {rounded.full}

### badge-pro
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark-mute}, typography: {typography.caption-sm}, rounded: {rounded.xs}, padding: 2px 6px

### badge-info-soft
backgroundColor: {colors.accent-blue-soft}, textColor: {colors.accent-blue}, typography: {typography.caption-sm}, rounded: {rounded.xs}, padding: 2px 8px

### keycap
backgroundColor: {colors.surface-card}, textColor: {colors.body}, typography: {typography.caption-md}, rounded: {rounded.xs}, padding: 1px 6px, height: 20px

### command-palette-card
backgroundColor: {colors.surface}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 0px

### feature-card-dark
backgroundColor: {colors.surface}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### feature-card-elevated
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### store-extension-card
backgroundColor: {colors.surface}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.md}, padding: 16px

### pricing-tier-card
backgroundColor: {colors.surface}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### pricing-tier-card-featured
backgroundColor: {colors.surface-elevated}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 24px

### hero-stripe-band
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.display-xl}, rounded: {rounded.none}, padding: 96px 48px

### app-icon-tile
backgroundColor: {colors.surface-card}, rounded: {rounded.md}, size: 48px

### app-icon-tile-large
backgroundColor: {colors.surface-card}, rounded: {rounded.md}, size: 64px

### primary-nav
backgroundColor: {colors.canvas}, textColor: {colors.on-dark}, typography: {typography.body-sm-strong}, rounded: {rounded.none}, height: 56px

### footer-section
backgroundColor: {colors.canvas}, textColor: {colors.body}, typography: {typography.body-sm}, rounded: {rounded.none}, padding: 64px 48px

### link-inline
textColor: {colors.on-dark}, typography: {typography.link-md}
', '["design-brand", "raycast", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:12:40', '2026-07-02 00:12:40'),
  (115, 'design_brand', 'spacex', 'design_system', '品牌设计规范 — spacex', '# 品牌设计规范: Spasex Inspired

An inspired interpretation of Spasex''s design language — a mission-oriented aerospace brand built on pure black canvas, full-bleed photographic and video heroes of rockets and Mars landscapes, and uppercase D-DIN display type set in tight vertical leading. UI chrome is intentionally minimal: a single ghost outlined pill button per band, all-caps eyebrow microtext, and a fixed top nav over photography. The system is unapologetically austere — black, white, and the imagery itself.

## 颜色体系 (Colors)

- **primary**: #000000
- **ink**: #000000
- **on-primary**: #ffffff
- **on-primary-mute**: #f0f0fa
- **canvas-night**: #000000
- **canvas-night-soft**: #0a0a0a
- **canvas-light**: #ffffff
- **canvas-cool**: #f0f0fa
- **hairline-on-dark**: #3a3a3f
- **hairline-on-light**: #e0e0e8
- **link-on-dark**: #ffffff
- **link-blue-fallback**: #0000ee
- **ink-mute**: #5a5a5f

## 排版体系 (Typography)

- **display-xxl**: font: D-DIN-Bold, Arial Narrow, Arial, Verdana, sans-serif | size: 80px | weight: 700 | lh: 0.95 | ls: 1.6px
- **display-xl**: font: D-DIN-Bold, Arial Narrow, Arial, Verdana, sans-serif | size: 60px | weight: 700 | lh: 1.2 | ls: 1.2px
- **display-lg**: font: D-DIN-Bold, Arial Narrow, Arial, Verdana, sans-serif | size: 48px | weight: 700 | lh: 1.25 | ls: 0.96px
- **body-lg**: font: D-DIN, Arial, Verdana, sans-serif | size: 16px | weight: 400 | lh: 1.7 | ls: 0.32px
- **body-md**: font: D-DIN, Arial, Verdana, sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0.32px
- **button-cap**: font: D-DIN, Arial, Verdana, sans-serif | size: 13.008px | weight: 700 | lh: 0.94 | ls: 1.17px
- **micro-cap**: font: D-DIN, Arial, Verdana, sans-serif | size: 12px | weight: 400 | lh: 2.0 | ls: 0.96px
- **caption**: font: D-DIN, Arial, Verdana, sans-serif | size: 13.008px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 4px
- **xs**: 8px
- **sm**: 12px
- **md**: 16px
- **lg**: 18px
- **xl**: 24px
- **xxl**: 32px
- **huge**: 48px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **pill**: 32px
- **full**: 9999px

## 组件定义 (Components)

### button-ghost-on-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.button-cap}, rounded: {rounded.pill}, padding: 18px 24px

### button-ghost-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.button-cap}, rounded: {rounded.pill}, padding: 18px 24px

### button-filled-cool
backgroundColor: {colors.canvas-cool}, textColor: {colors.ink}, typography: {typography.button-cap}, rounded: {rounded.pill}, padding: 18px 24px

### text-input
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 12px 16px

### card-photo-band
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### card-shop-product
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 16px

### nav-bar-overlay
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.button-cap}, rounded: {rounded.xs}, padding: 24px 32px

### link-on-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.link-on-dark}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### link-on-light
backgroundColor: {colors.canvas-light}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-primary}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 32px 24px
', '["design-brand", "spacex", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:12:40', '2026-07-02 00:12:40'),
  (116, 'design_brand', 'supabase', 'design_system', '品牌设计规范 — supabase', '# 品牌设计规范: Supabaze Inspired

An inspired interpretation of Supabaze''s design language — an open-source database platform built on a clean white-and-near-black system with a single signature emerald-green CTA, a custom humanist sans display tier, and dense product UI mockups composited above the hero. The brand reads as quietly technical: minimal chrome, a near-monochrome palette, and the green primary acting as the only chromatic event on the page.

## 颜色体系 (Colors)

- **primary**: #3ecf8e
- **primary-deep**: #24b47e
- **primary-soft**: #4ade80
- **ink**: #171717
- **ink-secondary**: #212121
- **ink-mute**: #707070
- **ink-mute-2**: #9a9a9a
- **ink-faint**: #b2b2b2
- **on-primary**: #171717
- **on-dark**: #ffffff
- **canvas**: #ffffff
- **canvas-soft**: #fafafa
- **canvas-night**: #1c1c1c
- **canvas-night-soft**: #202020
- **hairline**: #dfdfdf
- **hairline-strong**: #c7c7c7
- **hairline-cool**: #ededed
- **hairline-cool-2**: #efefef
- **hairline-cool-3**: #d4d4d4
- **accent-purple**: #6b01c2
- **accent-violet**: #644fc1
- **accent-purple-soft**: #eddbf9
- **accent-yellow**: #ffdb13
- **accent-tomato**: #ff2201
- **accent-pink**: #c7007e
- **accent-indigo**: #054cff
- **accent-crimson**: #e2005a

## 排版体系 (Typography)

- **display-xxl**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 64px | weight: 500 | lh: 1.1 | ls: -1.92px
- **display-xl**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 48px | weight: 500 | lh: 1.1 | ls: -1.44px
- **display-lg**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 36px | weight: 500 | lh: 1.15 | ls: -0.72px
- **display-md**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 28px | weight: 500 | lh: 1.2 | ls: -0.42px
- **heading-lg**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 22px | weight: 500 | lh: 1.2 | ls: 0
- **heading-md**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 18px | weight: 500 | lh: 1.4 | ls: 0
- **body-lg**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 18px | weight: 400 | lh: 1.55 | ls: 0
- **body-md**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 16px | weight: 400 | lh: 1.5 | ls: 0
- **button-md**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 14px | weight: 500 | lh: 1.0 | ls: 0
- **caption**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 13px | weight: 400 | lh: 1.45 | ls: 0
- **micro**: font: Circular, ''Helvetica Neue'', Helvetica, Arial, sans-serif | size: 12px | weight: 400 | lh: 1.45 | ls: 0
- **code**: font: ui-monospace, Menlo, Monaco, Consolas, ''Liberation Mono'', monospace | size: 14px | weight: 400 | lh: 1.5 | ls: 0

## 间距体系 (Spacing)

- **xxs**: 2px
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px
- **xxl**: 32px
- **huge**: 64px

## 圆角体系 (Border Radius)

- **xs**: 4px
- **sm**: 6px
- **md**: 8px
- **lg**: 12px
- **xl**: 16px
- **full**: 9999px

## 组件定义 (Components)

### button-primary-green
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 8px 16px

### button-primary-green-pressed
backgroundColor: {colors.primary-deep}, textColor: {colors.on-primary}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 8px 16px

### button-secondary-outline
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 8px 16px

### button-on-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-dark}, typography: {typography.button-md}, rounded: {rounded.sm}, padding: 8px 16px

### button-link
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.button-md}, rounded: {rounded.xs}, padding: 0px

### text-input
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.sm}, padding: 8px 12px

### card-feature-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-pricing-featured
backgroundColor: {colors.canvas-night}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### card-feature-dark
backgroundColor: {colors.canvas-night}, textColor: {colors.on-dark}, typography: {typography.body-md}, rounded: {rounded.lg}, padding: 32px

### code-block
backgroundColor: {colors.canvas-night}, textColor: {colors.on-dark}, typography: {typography.code}, rounded: {rounded.sm}, padding: 16px

### pill-tag-green
backgroundColor: {colors.primary}, textColor: {colors.on-primary}, typography: {typography.micro}, rounded: {rounded.full}, padding: 2px 8px

### pill-tag-soft
backgroundColor: {colors.canvas-soft}, textColor: {colors.ink}, typography: {typography.micro}, rounded: {rounded.full}, padding: 2px 8px

### nav-bar-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 16px 24px

### link-on-light
backgroundColor: {colors.canvas}, textColor: {colors.ink}, typography: {typography.body-md}, rounded: {rounded.xs}, padding: 0px

### footer-light
backgroundColor: {colors.canvas}, textColor: {colors.ink-mute}, typography: {typography.caption}, rounded: {rounded.xs}, padding: 64px 24px
', '["design-brand", "supabase", "has-colors", "has-typography", "has-components"]', 0.95, 0.85, 1, 0, '2026-07-02 00:12:41', '2026-07-02 00:12:41'),
  (117, 'impeccable', 'command_craft', 'design_command', 'Impeccable Command: Craft (craft)', 'Full confirmed-brief-then-build flow. Runs multi-round shape discovery first, resolves visual probe and north-star mock gates when available, then builds and visually iterates. Use when building a new feature end-to-end.', '["impeccable", "command", "create", "craft"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (118, 'impeccable', 'command_init', 'design_command', 'Impeccable Command: Init (init)', 'Sets up a project for impeccable. Runs a multi-round discovery interview when context is missing and writes PRODUCT.md (strategic: users, brand, principles); offers DESIGN.md (visual: colors, typography, components) when code exists; pre-configures live mode; then recommends the best commands to run next.', '["impeccable", "command", "system", "init"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (119, 'impeccable', 'command_document', 'design_command', 'Impeccable Command: Document (document)', 'Generate a DESIGN.md file that captures the current visual design system. Auto-extracts colors, typography, spacing, radii, and component patterns from the codebase.', '["impeccable", "command", "system", "document"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (120, 'impeccable', 'command_extract', 'design_command', 'Impeccable Command: Extract (extract)', 'Pull reusable patterns, components, and design tokens into the design system. Identifies repeated patterns and consolidates them.', '["impeccable", "command", "refine", "extract"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (121, 'impeccable', 'command_live', 'design_command', 'Impeccable Command: Live (live)', 'Interactive live variant mode. Select elements in the browser, pick a design action, and get AI-generated HTML+CSS variants hot-swapped via HMR.', '["impeccable", "command", "create", "live"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (122, 'impeccable', 'command_adapt', 'design_command', 'Impeccable Command: Adapt (adapt)', 'Adapt designs to work across different screen sizes, devices, contexts, or platforms. Implements breakpoints, fluid layouts, and touch targets.', '["impeccable", "command", "refine", "adapt"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (123, 'impeccable', 'command_animate', 'design_command', 'Impeccable Command: Animate (animate)', 'Review a feature and enhance it with purposeful animations, micro-interactions, and motion effects that improve usability and delight.', '["impeccable", "command", "refine", "animate"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (124, 'impeccable', 'command_audit', 'design_command', 'Impeccable Command: Audit (audit)', 'Run technical quality checks across accessibility, performance, theming, responsive design, and anti-patterns. Generates a scored report with P0-P3 severity ratings.', '["impeccable", "command", "evaluate", "audit"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (125, 'impeccable', 'command_bolder', 'design_command', 'Impeccable Command: Bolder (bolder)', 'Amplify safe or boring designs to make them more visually interesting and stimulating. Increases impact while maintaining usability.', '["impeccable", "command", "refine", "bolder"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (126, 'impeccable', 'command_clarify', 'design_command', 'Impeccable Command: Clarify (clarify)', 'Improve unclear UX copy, error messages, microcopy, labels, and instructions to make interfaces easier to understand.', '["impeccable", "command", "refine", "clarify"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (127, 'impeccable', 'command_colorize', 'design_command', 'Impeccable Command: Colorize (colorize)', 'Add strategic color to features that are too monochromatic or lack visual interest, making interfaces more engaging and expressive.', '["impeccable", "command", "refine", "colorize"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (128, 'impeccable', 'command_critique', 'design_command', 'Impeccable Command: Critique (critique)', 'Evaluate design from a UX perspective, assessing visual hierarchy, information architecture, emotional resonance, cognitive load, and overall quality with quantitative scoring.', '["impeccable", "command", "evaluate", "critique"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (129, 'impeccable', 'command_delight', 'design_command', 'Impeccable Command: Delight (delight)', 'Add moments of joy, personality, and unexpected touches that make interfaces memorable and enjoyable to use.', '["impeccable", "command", "refine", "delight"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (130, 'impeccable', 'command_distill', 'design_command', 'Impeccable Command: Distill (distill)', 'Strip designs to their essence by removing unnecessary complexity. Great design is simple, powerful, and clean.', '["impeccable", "command", "simplify", "distill"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (131, 'impeccable', 'command_harden', 'design_command', 'Impeccable Command: Harden (harden)', 'Make interfaces production-ready: error handling, i18n, text overflow, edge case management, and resilience under real-world data.', '["impeccable", "command", "harden", "harden"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (132, 'impeccable', 'command_onboard', 'design_command', 'Impeccable Command: Onboard (onboard)', 'Design onboarding flows, first-run experiences, and empty states that guide new users to value.', '["impeccable", "command", "create", "onboard"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (133, 'impeccable', 'command_layout', 'design_command', 'Impeccable Command: Layout (layout)', 'Improve layout, spacing, and visual rhythm. Fixes monotonous grids, inconsistent spacing, and weak visual hierarchy.', '["impeccable", "command", "refine", "layout"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (134, 'impeccable', 'command_optimize', 'design_command', 'Impeccable Command: Optimize (optimize)', 'Diagnoses and fixes UI performance across loading speed, rendering, animations, images, and bundle size.', '["impeccable", "command", "harden", "optimize"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (135, 'impeccable', 'command_overdrive', 'design_command', 'Impeccable Command: Overdrive (overdrive)', 'Pushes interfaces past conventional limits with technically ambitious implementations — shaders, spring physics, scroll-driven reveals, 60fps animations.', '["impeccable", "command", "create", "overdrive"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (136, 'impeccable', 'command_polish', 'design_command', 'Impeccable Command: Polish (polish)', 'Performs a final quality pass fixing alignment, spacing, consistency, and micro-detail issues before shipping.', '["impeccable", "command", "refine", "polish"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (137, 'impeccable', 'command_quieter', 'design_command', 'Impeccable Command: Quieter (quieter)', 'Tones down visually aggressive or overstimulating designs, reducing intensity while preserving quality.', '["impeccable", "command", "simplify", "quieter"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (138, 'impeccable', 'command_shape', 'design_command', 'Impeccable Command: Shape (shape)', 'Plan UX and UI before code. Runs a required multi-round discovery interview, uses visual probes when available, and produces a user-confirmed design brief.', '["impeccable", "command", "create", "shape"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (139, 'impeccable', 'command_typeset', 'design_command', 'Impeccable Command: Typeset (typeset)', 'Improves typography by fixing font choices, hierarchy, sizing, weight, and readability so text feels intentional.', '["impeccable", "command", "refine", "typeset"]', 1.0, 0.8, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (140, 'impeccable', 'antipattern_side-tab', 'design_antipattern', 'Anti-Pattern: Side-tab accent border (side-tab)', '**Side-tab accent border** (slop)

Thick colored border on one side of a card — the most recognizable tell of AI-generated UIs. Use a subtler accent or remove it entirely.

Severity: P2
Section: Visual Details', '["impeccable", "antipattern", "slop", "side-tab", "visual_details"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (141, 'impeccable', 'antipattern_border-accent-on-rounded', 'design_antipattern', 'Anti-Pattern: Border accent on rounded element (border-accent-on-rounded)', '**Border accent on rounded element** (slop)

Thick accent border on a rounded card — the border clashes with the rounded corners. Remove the border or the border-radius.

Severity: P2
Section: Visual Details', '["impeccable", "antipattern", "slop", "border-accent-on-rounded", "visual_details"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (142, 'impeccable', 'antipattern_overused-font', 'design_antipattern', 'Anti-Pattern: Overused font (overused-font)', '**Overused font** (slop)

Inter, Roboto, Fraunces, Geist, Plus Jakarta Sans, and Space Grotesk are used on so many sites they no longer feel distinctive. Each new wave of AI-generated UIs converges on the same handful of faces.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "overused-font", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (143, 'impeccable', 'antipattern_single-font', 'design_antipattern', 'Anti-Pattern: Single font for everything (single-font)', '**Single font for everything** (slop)

Only one font family is used for the entire page. Pair a distinctive display font with a refined body font to create typographic hierarchy.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "single-font", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (144, 'impeccable', 'antipattern_flat-type-hierarchy', 'design_antipattern', 'Anti-Pattern: Flat type hierarchy (flat-type-hierarchy)', '**Flat type hierarchy** (slop)

Font sizes are too close together — no clear visual hierarchy. Use fewer sizes with more contrast (aim for at least a 1.25 ratio between steps).

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "flat-type-hierarchy", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (145, 'impeccable', 'antipattern_gradient-text', 'design_antipattern', 'Anti-Pattern: Gradient text (gradient-text)', '**Gradient text** (slop)

Gradient text is decorative rather than meaningful — a common AI tell, especially on headings and metrics. Use solid colors for text.

Severity: P1
Section: Color & Contrast', '["impeccable", "antipattern", "slop", "gradient-text", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (146, 'impeccable', 'antipattern_ai-color-palette', 'design_antipattern', 'Anti-Pattern: AI color palette (ai-color-palette)', '**AI color palette** (slop)

Purple/violet gradients and cyan-on-dark are the most recognizable tells of AI-generated UIs. Choose a distinctive, intentional palette.

Severity: P1
Section: Color & Contrast', '["impeccable", "antipattern", "slop", "ai-color-palette", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (147, 'impeccable', 'antipattern_cream-palette', 'design_antipattern', 'Anti-Pattern: Cream / beige palette (cream-palette)', '**Cream / beige palette** (slop)

A warm cream or beige page background has become the default ''tasteful'' AI surface, reached for by reflex.

Severity: P2
Section: Color & Contrast', '["impeccable", "antipattern", "slop", "cream-palette", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (148, 'impeccable', 'antipattern_nested-cards', 'design_antipattern', 'Anti-Pattern: Nested cards (nested-cards)', '**Nested cards** (slop)

Cards inside cards create visual noise and excessive depth. Flatten the hierarchy — use spacing, typography, and dividers instead of nesting containers.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "slop", "nested-cards", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (149, 'impeccable', 'antipattern_monotonous-spacing', 'design_antipattern', 'Anti-Pattern: Monotonous spacing (monotonous-spacing)', '**Monotonous spacing** (slop)

The same spacing value used everywhere — no rhythm, no variation. Use tight groupings for related items and generous separations between sections.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "slop", "monotonous-spacing", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (150, 'impeccable', 'antipattern_bounce-easing', 'design_antipattern', 'Anti-Pattern: Bounce or elastic easing (bounce-easing)', '**Bounce or elastic easing** (slop)

Bounce and elastic easing feel dated and tacky. Real objects decelerate smoothly — use exponential easing (ease-out-quart/quint/expo) instead.

Severity: P2
Section: Motion', '["impeccable", "antipattern", "slop", "bounce-easing", "motion"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (151, 'impeccable', 'antipattern_dark-glow', 'design_antipattern', 'Anti-Pattern: Dark mode with glowing accents (dark-glow)', '**Dark mode with glowing accents** (slop)

Dark backgrounds with colored box-shadow glows are the default ''cool'' look of AI-generated UIs. Use subtle, purposeful lighting instead.

Severity: P2
Section: Color & Contrast', '["impeccable", "antipattern", "slop", "dark-glow", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (152, 'impeccable', 'antipattern_icon-tile-stack', 'design_antipattern', 'Anti-Pattern: Icon tile stacked above heading (icon-tile-stack)', '**Icon tile stacked above heading** (slop)

A small rounded-square icon container above a heading is the universal AI feature-card template — every generator outputs this exact shape.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "icon-tile-stack", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (153, 'impeccable', 'antipattern_italic-serif-display', 'design_antipattern', 'Anti-Pattern: Italic serif display headline (italic-serif-display)', '**Italic serif display headline** (slop)

Oversized italic serif as the primary hero headline reads as taste in isolation but has become the universal AI-startup landing page hero.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "italic-serif-display", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (154, 'impeccable', 'antipattern_hero-eyebrow-chip', 'design_antipattern', 'Anti-Pattern: Hero eyebrow / pill chip (hero-eyebrow-chip)', '**Hero eyebrow / pill chip** (slop)

A tiny uppercase letter-spaced label sitting immediately above an oversized hero headline is now the default AI SaaS hero.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "hero-eyebrow-chip", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (155, 'impeccable', 'antipattern_repeated-section-kickers', 'design_antipattern', 'Anti-Pattern: Repeated section kicker labels (repeated-section-kickers)', '**Repeated section kicker labels** (slop)

Repeating tiny uppercase tracked labels above section headings turns a brand page into AI editorial scaffolding.

Severity: P3
Section: Typography', '["impeccable", "antipattern", "slop", "repeated-section-kickers", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (156, 'impeccable', 'antipattern_numbered-section-markers', 'design_antipattern', 'Anti-Pattern: Numbered section markers (01 / 02 / 03) (numbered-section-markers)', '**Numbered section markers (01 / 02 / 03)** (slop)

Numbered display markers as section labels (01, 02, 03) are the AI editorial scaffold one tier deeper than tracked eyebrow chips.

Severity: P3
Section: Layout & Space', '["impeccable", "antipattern", "slop", "numbered-section-markers", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (157, 'impeccable', 'antipattern_em-dash-overuse', 'design_antipattern', 'Anti-Pattern: Em-dash overuse (em-dash-overuse)', '**Em-dash overuse** (slop)

More than two em-dashes (— or --) in body copy is an AI cadence tell. Use commas, colons, periods, or parentheses instead.

Severity: P2
Section: Copy', '["impeccable", "antipattern", "slop", "em-dash-overuse", "copy"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (158, 'impeccable', 'antipattern_marketing-buzzword', 'design_antipattern', 'Anti-Pattern: Marketing buzzword (marketing-buzzword)', '**Marketing buzzword** (slop)

Generic SaaS phrases (streamline / empower / supercharge / world-class / enterprise-grade / next-generation / cutting-edge / etc) are instant AI tells.

Severity: P2
Section: Copy', '["impeccable", "antipattern", "slop", "marketing-buzzword", "copy"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (159, 'impeccable', 'antipattern_aphoristic-cadence', 'design_antipattern', 'Anti-Pattern: Aphoristic-cadence copy (aphoristic-cadence)', '**Aphoristic-cadence copy** (slop)

Three or more sections landing on a short rebuttal sentence (''X. No Y.'' / ''X. Just Y.'') reads as AI cadence, not voice.

Severity: P2
Section: Copy', '["impeccable", "antipattern", "slop", "aphoristic-cadence", "copy"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (160, 'impeccable', 'antipattern_oversized-h1', 'design_antipattern', 'Anti-Pattern: Oversized hero headline (oversized-h1)', '**Oversized hero headline** (slop)

A full-sentence headline set at display size ends up dominating the viewport, leaving no room for anything else above the fold.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "oversized-h1", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (161, 'impeccable', 'antipattern_extreme-negative-tracking', 'design_antipattern', 'Anti-Pattern: Crushed letter spacing (extreme-negative-tracking)', '**Crushed letter spacing** (slop)

Letter-spacing pulled tighter than the point where characters keep their own shapes costs legibility. Tighten display type optically, not destructively.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "slop", "extreme-negative-tracking", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (162, 'impeccable', 'antipattern_broken-image', 'design_antipattern', 'Anti-Pattern: Broken or placeholder image (broken-image)', '**Broken or placeholder image** (quality)

<img> tags with empty src, missing src, or placeholder values ship as broken-image boxes. Use real images or remove the tag.

Severity: P1
Section: Imagery', '["impeccable", "antipattern", "quality", "broken-image", "imagery"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (163, 'impeccable', 'antipattern_gray-on-color', 'design_antipattern', 'Anti-Pattern: Gray text on colored background (gray-on-color)', '**Gray text on colored background** (quality)

Gray text looks washed out on colored backgrounds. Use a darker shade of the background color instead, or white/near-white for contrast.

Severity: P1
Section: Color & Contrast', '["impeccable", "antipattern", "quality", "gray-on-color", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (164, 'impeccable', 'antipattern_low-contrast', 'design_antipattern', 'Anti-Pattern: Low contrast text (low-contrast)', '**Low contrast text** (quality)

Text does not meet WCAG AA contrast requirements (4.5:1 for body, 3:1 for large text). Increase the contrast between text and background.

Severity: P0
Section: Color & Contrast', '["impeccable", "antipattern", "quality", "low-contrast", "color_contrast"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (165, 'impeccable', 'antipattern_layout-transition', 'design_antipattern', 'Anti-Pattern: Layout property animation (layout-transition)', '**Layout property animation** (quality)

Animating width, height, padding, or margin causes layout thrash and janky performance. Use transform and opacity instead.

Severity: P1
Section: Motion', '["impeccable", "antipattern", "quality", "layout-transition", "motion"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (166, 'impeccable', 'antipattern_line-length', 'design_antipattern', 'Anti-Pattern: Line length too long (line-length)', '**Line length too long** (quality)

Text lines wider than ~80 characters are hard to read. Add a max-width (65ch to 75ch) to text containers.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "quality", "line-length", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (167, 'impeccable', 'antipattern_cramped-padding', 'design_antipattern', 'Anti-Pattern: Cramped padding (cramped-padding)', '**Cramped padding** (quality)

Text is too close to the edge of its container. Add at least 8px (ideally 12–16px) of padding inside bordered, outlined, or colored containers.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "quality", "cramped-padding", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (168, 'impeccable', 'antipattern_body-text-viewport-edge', 'design_antipattern', 'Anti-Pattern: Body text touching viewport edge (body-text-viewport-edge)', '**Body text touching viewport edge** (quality)

Body paragraphs render flush against the left or right viewport edge with no container providing horizontal padding.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "quality", "body-text-viewport-edge", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (169, 'impeccable', 'antipattern_tight-leading', 'design_antipattern', 'Anti-Pattern: Tight line height (tight-leading)', '**Tight line height** (quality)

Line height below 1.3x the font size makes multi-line text hard to read. Use 1.5 to 1.7 for body text.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "quality", "tight-leading", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (170, 'impeccable', 'antipattern_skipped-heading', 'design_antipattern', 'Anti-Pattern: Skipped heading level (skipped-heading)', '**Skipped heading level** (quality)

Heading levels should not skip (e.g. h1 then h3 with no h2). Screen readers use heading hierarchy for navigation.

Severity: P1
Section: Accessibility', '["impeccable", "antipattern", "quality", "skipped-heading", "accessibility"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (171, 'impeccable', 'antipattern_justified-text', 'design_antipattern', 'Anti-Pattern: Justified text (justified-text)', '**Justified text** (quality)

Justified text without hyphenation creates uneven word spacing (''rivers of white''). Use text-align: left for body text.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "quality", "justified-text", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (172, 'impeccable', 'antipattern_tiny-text', 'design_antipattern', 'Anti-Pattern: Tiny body text (tiny-text)', '**Tiny body text** (quality)

Body text below 12px is hard to read, especially on high-DPI screens. Use at least 14px for body content, 16px is ideal.

Severity: P1
Section: Typography', '["impeccable", "antipattern", "quality", "tiny-text", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (173, 'impeccable', 'antipattern_all-caps-body', 'design_antipattern', 'Anti-Pattern: All-caps body text (all-caps-body)', '**All-caps body text** (quality)

Long passages in uppercase are hard to read. We recognize words by shape (ascenders and descenders), which all-caps removes.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "quality", "all-caps-body", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (174, 'impeccable', 'antipattern_wide-tracking', 'design_antipattern', 'Anti-Pattern: Wide letter spacing on body text (wide-tracking)', '**Wide letter spacing on body text** (quality)

Letter spacing above 0.05em on body text disrupts natural character groupings and slows reading.

Severity: P2
Section: Typography', '["impeccable", "antipattern", "quality", "wide-tracking", "typography"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (175, 'impeccable', 'antipattern_text-overflow', 'design_antipattern', 'Anti-Pattern: Content overflowing its container (text-overflow)', '**Content overflowing its container** (quality)

Content renders wider than its container, spilling out or forcing a horizontal scrollbar.

Severity: P1
Section: Layout & Space', '["impeccable", "antipattern", "quality", "text-overflow", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38'),
  (176, 'impeccable', 'antipattern_clipped-overflow-container', 'design_antipattern', 'Anti-Pattern: Positioned child clipped by overflow container (clipped-overflow-container)', '**Positioned child clipped by overflow container** (quality)

A clipping container (overflow hidden or clip) wrapping an absolutely-positioned child cuts off tooltips, menus, and popovers.

Severity: P2
Section: Layout & Space', '["impeccable", "antipattern", "quality", "clipped-overflow-container", "layout_space"]', 1.0, 0.9, 1, 0, '2026-07-02 00:18:38', '2026-07-02 00:18:38');

-- gaia_model_weights: 42 rows (batch 1)
INSERT INTO "gaia_model_weights" ("id", "module", "weights", "version", "description", "training_run_id", "is_active", "created_at", "updated_at") VALUES
  (1, 'recommendation', '{"preference_weight": 0.3, "behavior_weight": 0.25, "pattern_weight": 0.2, "insight_weight": 0.15, "optimization_weight": 0.1, "diversity_factor": 0.2, "recency_factor": 0.3, "confidence_threshold": 0.6, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (2, 'search', '{"semantic_weight": 0.35, "optimization_weight": 0.25, "rule_weight": 0.2, "insight_weight": 0.1, "behavior_weight": 0.1, "confidence_threshold": 0.5, "rerank_weight": 0.3, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (3, 'extractor', '{"pattern_weight": 0.3, "rule_weight": 0.25, "optimization_weight": 0.2, "insight_weight": 0.15, "behavior_weight": 0.1, "confidence_threshold": 0.8, "field_boost": 1.2, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (4, 'writing', '{"preference_weight": 0.3, "optimization_weight": 0.25, "behavior_weight": 0.2, "pattern_weight": 0.15, "insight_weight": 0.1, "creativity_factor": 0.3, "formality_factor": 0.5, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (5, 'optimization', '{"optimization_weight": 0.4, "pattern_weight": 0.25, "behavior_weight": 0.2, "insight_weight": 0.15, "confidence_threshold": 0.7, "impact_multiplier": 1.5, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (6, 'rag', '{"insight_weight": 0.3, "knowledge_weight": 0.25, "pattern_weight": 0.2, "rule_weight": 0.15, "optimization_weight": 0.1, "context_window_boost": 1.0, "temperature_adjustment": 0.1, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (7, 'knowledge_graph', '{"relation_weight": 0.35, "insight_weight": 0.25, "rule_weight": 0.2, "optimization_weight": 0.1, "behavior_weight": 0.1, "depth_factor": 0.5, "breadth_factor": 0.5, "total_knowledge_basis": 0}', '0.0.1', '训练管线部署 - 知识依据: 0 条', 2, 0, '2026-07-01 11:39:21', '2026-07-01 11:42:18'),
  (8, 'recommendation', '{"preference_weight": 0.5, "behavior_weight": 0.3, "pattern_weight": 0.7225, "insight_weight": 0.1, "confidence_threshold": 0.6, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:18'),
  (9, 'search', '{"semantic_weight": 0.7225, "optimization_weight": 0.3, "rule_weight": 0.2, "insight_weight": 0.1, "confidence_threshold": 0.5, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:18'),
  (10, 'extractor', '{"pattern_weight": 0.7225, "rule_weight": 0.3, "optimization_weight": 0.2, "insight_weight": 0.1, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (11, 'writing', '{"preference_weight": 0.4, "optimization_weight": 0.3, "behavior_weight": 0.2, "pattern_weight": 0.7225, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (12, 'optimization', '{"optimization_weight": 0.5, "pattern_weight": 0.7225, "insight_weight": 0.2, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (13, 'rag', '{"insight_weight": 0.4, "knowledge_weight": 0.3, "pattern_weight": 0.7225, "rule_weight": 0.1, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (14, 'knowledge_graph', '{"relation_weight": 0.7225, "insight_weight": 0.3, "rule_weight": 0.2, "total_knowledge": 1}', '0.0.2', '进化循环自动更新 - 1 条知识', NULL, 0, '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (15, 'recommendation', '{"preference_weight": 0.3, "behavior_weight": 0.25, "pattern_weight": 0.85, "insight_weight": 0.15, "optimization_weight": 0.1, "diversity_factor": 0.2, "recency_factor": 0.3, "confidence_threshold": 0.6, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:18', '2026-07-01 14:56:38'),
  (16, 'search', '{"semantic_weight": 0.85, "optimization_weight": 0.25, "rule_weight": 0.2, "insight_weight": 0.1, "behavior_weight": 0.1, "confidence_threshold": 0.5, "rerank_weight": 0.3, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:18', '2026-07-01 14:56:38'),
  (17, 'extractor', '{"pattern_weight": 0.85, "rule_weight": 0.25, "optimization_weight": 0.2, "insight_weight": 0.15, "behavior_weight": 0.1, "confidence_threshold": 0.8, "field_boost": 1.2, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:19', '2026-07-01 14:56:38'),
  (18, 'writing', '{"preference_weight": 0.3, "optimization_weight": 0.25, "behavior_weight": 0.2, "pattern_weight": 0.85, "insight_weight": 0.1, "creativity_factor": 0.3, "formality_factor": 0.5, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:19', '2026-07-01 14:56:38'),
  (19, 'optimization', '{"optimization_weight": 0.4, "pattern_weight": 0.85, "behavior_weight": 0.2, "insight_weight": 0.15, "confidence_threshold": 0.7, "impact_multiplier": 1.5, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:19', '2026-07-01 14:56:38'),
  (20, 'rag', '{"insight_weight": 0.3, "knowledge_weight": 0.25, "pattern_weight": 0.85, "rule_weight": 0.15, "optimization_weight": 0.1, "context_window_boost": 1.0, "temperature_adjustment": 0.1, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:19', '2026-07-01 14:56:38'),
  (21, 'knowledge_graph', '{"relation_weight": 0.85, "insight_weight": 0.25, "rule_weight": 0.2, "optimization_weight": 0.1, "behavior_weight": 0.1, "depth_factor": 0.5, "breadth_factor": 0.5, "total_knowledge_basis": 1}', '0.0.3', '训练管线部署 - 知识依据: 1 条', 8, 0, '2026-07-01 11:42:19', '2026-07-01 14:56:38'),
  (22, 'recommendation', '{"preference_weight": 0.3333, "behavior_weight": 0.3, "pattern_weight": 0.5704, "insight_weight": 0.1, "confidence_threshold": 0.6, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (23, 'search', '{"semantic_weight": 0.5704, "optimization_weight": 0.3, "rule_weight": 0.2, "insight_weight": 0.1, "confidence_threshold": 0.5, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (24, 'extractor', '{"pattern_weight": 0.5704, "rule_weight": 0.3, "optimization_weight": 0.2, "insight_weight": 0.1, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (25, 'writing', '{"preference_weight": 0.3333, "optimization_weight": 0.3, "behavior_weight": 0.2, "pattern_weight": 0.5704, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (26, 'optimization', '{"optimization_weight": 0.5, "pattern_weight": 0.5704, "insight_weight": 0.2, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (27, 'rag', '{"insight_weight": 0.4, "knowledge_weight": 0.3, "pattern_weight": 0.5704, "rule_weight": 0.1, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (28, 'knowledge_graph', '{"relation_weight": 0.5704, "insight_weight": 0.3, "rule_weight": 0.2, "total_knowledge": 3}', '0.0.4', '进化循环自动更新 - 3 条知识', NULL, 0, '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (29, 'recommendation', '{"preference_weight": 0.3404, "behavior_weight": 0.25, "pattern_weight": 0.6102, "insight_weight": 0.15, "optimization_weight": 0.1, "diversity_factor": 0.2, "recency_factor": 0.3, "confidence_threshold": 0.6, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (30, 'search', '{"semantic_weight": 0.6102, "optimization_weight": 0.25, "rule_weight": 0.2, "insight_weight": 0.1, "behavior_weight": 0.1, "confidence_threshold": 0.5, "rerank_weight": 0.3, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (31, 'extractor', '{"pattern_weight": 0.6102, "rule_weight": 0.25, "optimization_weight": 0.2, "insight_weight": 0.15, "behavior_weight": 0.1, "confidence_threshold": 0.8, "field_boost": 1.2, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (32, 'writing', '{"preference_weight": 0.3404, "optimization_weight": 0.25, "behavior_weight": 0.2, "pattern_weight": 0.6102, "insight_weight": 0.1, "creativity_factor": 0.3, "formality_factor": 0.5, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (33, 'optimization', '{"optimization_weight": 0.4, "pattern_weight": 0.6102, "behavior_weight": 0.2, "insight_weight": 0.15, "confidence_threshold": 0.7, "impact_multiplier": 1.5, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (34, 'rag', '{"insight_weight": 0.3, "knowledge_weight": 0.25, "pattern_weight": 0.6102, "rule_weight": 0.15, "optimization_weight": 0.1, "context_window_boost": 1.0, "temperature_adjustment": 0.1, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (35, 'knowledge_graph', '{"relation_weight": 0.6102, "insight_weight": 0.25, "rule_weight": 0.2, "optimization_weight": 0.1, "behavior_weight": 0.1, "depth_factor": 0.5, "breadth_factor": 0.5, "total_knowledge_basis": 3}', '0.0.5', '训练管线部署 - 知识依据: 3 条', 10, 0, '2026-07-01 14:56:38', '2026-07-01 19:39:55'),
  (36, 'recommendation', '{"preference_weight": 0.0278, "behavior_weight": 0.3, "pattern_weight": 0.7293, "insight_weight": 0.1, "confidence_threshold": 0.6, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (37, 'search', '{"semantic_weight": 0.7293, "optimization_weight": 0.3, "rule_weight": 0.2, "insight_weight": 0.1, "confidence_threshold": 0.5, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (38, 'extractor', '{"pattern_weight": 0.7293, "rule_weight": 0.3, "optimization_weight": 0.2, "insight_weight": 0.1, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (39, 'writing', '{"preference_weight": 0.0278, "optimization_weight": 0.3, "behavior_weight": 0.2, "pattern_weight": 0.7293, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (40, 'optimization', '{"optimization_weight": 0.5, "pattern_weight": 0.7293, "insight_weight": 0.2, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (41, 'rag', '{"insight_weight": 0.4, "knowledge_weight": 0.3, "pattern_weight": 0.7293, "rule_weight": 0.1, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (42, 'knowledge_graph', '{"relation_weight": 0.7293, "insight_weight": 0.3, "rule_weight": 0.2, "total_knowledge": 36}', '0.0.6', '进化循环自动更新 - 36 条知识', NULL, 1, '2026-07-01 19:39:55', '2026-07-01 19:39:55');

-- gaia_training_runs: 12 rows (batch 1)
INSERT INTO "gaia_training_runs" ("id", "status", "trigger", "knowledge_count", "feedback_count", "weights_count", "vector_index_size", "duration_ms", "metrics", "error_message", "started_at", "completed_at", "created_at", "updated_at") VALUES
  (1, 'completed', 'manual', 0, 0, 0, 0, 31, NULL, NULL, '2026-07-01 11:39:21.289324', '2026-07-01 11:39:21.289324', '2026-07-01 11:39:21', '2026-07-01 11:39:21'),
  (2, 'completed', 'manual', 0, 0, 7, 0, 15, '{"knowledge_types": {}, "knowledge_sources": {}, "avg_confidence": 0.0, "high_confidence_entries": 0, "vector_updated": 0, "weights_deployed": 7}', NULL, '2026-07-01 11:39:21.298355', '2026-07-01 11:39:21.323890', '2026-07-01 11:39:21', '2026-07-01 11:39:21'),
  (3, 'completed', 'manual', 0, 0, 0, 0, 61, NULL, NULL, '2026-07-01 11:40:29.797826', '2026-07-01 11:40:29.797826', '2026-07-01 11:40:29', '2026-07-01 11:40:29'),
  (4, 'completed', 'manual', 0, 0, 0, 0, 31, '{"knowledge_types": {}, "knowledge_sources": {}, "avg_confidence": 0.0, "high_confidence_entries": 0, "vector_updated": 0, "weights_deployed": 0}', NULL, '2026-07-01 11:40:29.811667', '2026-07-01 11:40:29.852495', '2026-07-01 11:40:29', '2026-07-01 11:40:29'),
  (5, 'completed', 'manual', 0, 0, 0, 0, 47, NULL, NULL, '2026-07-01 11:40:42.951208', '2026-07-01 11:40:42.951208', '2026-07-01 11:40:42', '2026-07-01 11:40:42'),
  (6, 'completed', 'manual', 0, 0, 0, 0, 15, '{"knowledge_types": {}, "knowledge_sources": {}, "avg_confidence": 0.0, "high_confidence_entries": 0, "vector_updated": 0, "weights_deployed": 0}', NULL, '2026-07-01 11:40:42.960910', '2026-07-01 11:40:42.978705', '2026-07-01 11:40:42', '2026-07-01 11:40:42'),
  (7, 'completed', 'manual', 1, 0, 7, 1, 68765, NULL, NULL, '2026-07-01 11:42:18.956791', '2026-07-01 11:42:18.956791', '2026-07-01 11:42:18', '2026-07-01 11:42:18'),
  (8, 'completed', 'manual', 1, 0, 7, 1, 47, '{"knowledge_types": {"pattern": 1}, "knowledge_sources": {"retrospective": 1}, "avg_confidence": 0.85, "high_confidence_entries": 1, "vector_updated": 0, "weights_deployed": 7}', NULL, '2026-07-01 11:42:18.969902', '2026-07-01 11:42:19.019858', '2026-07-01 11:42:18', '2026-07-01 11:42:19'),
  (9, 'completed', 'manual', 2, 0, 7, 3, 2431078, NULL, NULL, '2026-07-01 14:56:38.064875', '2026-07-01 14:56:38.064875', '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (10, 'completed', 'manual', 3, 1, 7, 3, 30, '{"knowledge_types": {"pattern": 2, "preference": 1}, "knowledge_sources": {"retrospective": 2, "feedback": 1}, "avg_confidence": 0.95, "high_confidence_entries": 3, "vector_updated": 0, "weights_deployed": 7}', NULL, '2026-07-01 14:56:38.069398', '2026-07-01 14:56:38.098285', '2026-07-01 14:56:38', '2026-07-01 14:56:38'),
  (11, 'completed', 'api', 33, 0, 7, 36, 38703, NULL, NULL, '2026-07-01 19:39:55.820075', '2026-07-01 19:39:55.820075', '2026-07-01 19:39:55', '2026-07-01 19:39:55'),
  (12, 'completed', 'manual', 60, 0, 0, 60, 188, '{"commands_synced": 23, "antipatterns_synced": 37, "total_knowledge_entries": 60}', NULL, '2026-07-02 00:18:38.700018', '2026-07-02 00:18:38.700018', '2026-07-02 00:18:38', '2026-07-02 00:18:38');

-- knowledge_models: 37 rows (batch 1)
INSERT INTO "knowledge_models" ("id", "model_id", "category", "name", "source", "source_ref", "content", "tags", "confidence", "version", "is_active", "vector_embedded", "created_at", "updated_at") VALUES
  (1, 'FD-M01', 'design_system', 'Design Token 分层体系', 'design_system', 'D:\AI设计\设计系统\design_tokens.json', 'Design Token 是设计系统中最小的可复用原子，分为三层：
1. 全局Token (Global Tokens) — 跨品牌的原始设计值，如 color-brand-500: #1677ff
2. 别名Token (Alias Tokens) — 语义化映射，如 color-primary: color-brand-500
3. 组件Token (Component Tokens) — 组件级特化，如 Button-background: color-primary

核心原则：
- Token命名规范: {category}-{type}-{property}-{subproperty}-{variant}
- 全局Token不可变，别名Token可随主题切换
- 组件Token应限定在组件边界内，不得跨组件引用

训练要点：Token化使主题切换、品牌定制、响应式适配的维护成本降低70%+。', '["design_token", "\u8bbe\u8ba1\u7cfb\u7edf", "\u4e3b\u9898\u5316", "\u539f\u5b50\u5316\u8bbe\u8ba1"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (2, 'FD-M02', 'design_system', '色彩系统架构', 'design_system', 'D:\AI设计\设计系统\色彩\高频色彩使用比例.md (约89行)', '色彩系统应包含五层架构：
1. 品牌色 (Brand) — 主色+辅色，定义品牌识别
2. 语义色 (Semantic) — success/warning/error/info，功能导向
3. 中性色 (Neutral) — 文本/背景/边框/填充灰度阶梯
4. 数据色 (Data) — 图表/可视化配色序列
5. 覆盖色 (Overlay) — 遮罩/阴影/渐变

设计原则：
- 品牌色12阶阶梯: 50-900 (50最浅, 900最深), 每阶HSL亮度差≈7%
- 中性色需满足WCAG AA对比度: 正文≥4.5:1, 大文本≥3:1
- 语义色应与品牌色协调而非冲突，覆盖在品牌色上叠加透明度
- 高频使用色 (品牌色、中性色) 占设计表面积80%+，低频使用色占20%

训练要点：暗色主题的语义色需重新计算对比度而非简单反转。', '["\u8272\u5f69\u7cfb\u7edf", "\u54c1\u724c\u8272", "\u8bed\u4e49\u8272", "WCAG", "\u4e3b\u9898"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (3, 'FD-M03', 'design_system', '字体层级调制 (Typography Scale)', 'design_system', 'D:\AI设计\设计系统\排版\', '字体层级的数学模型 — 使用等比数列创建协调的字体大小系统：
1. 基准字号: 16px (1rem = 16px, 浏览器默认)
2. 调制比 (Modular Scale): 常用 1.25 (Major Third) 或 1.333 (Perfect Fourth)
3. 层级计算: 基准 × ratio^step, 如:
   - 正文: 16px (step=0)
   - H6: 16×1.25^1 = 20px
   - H5: 16×1.25^2 = 25px
   - H4: 16×1.25^3 = 31px
   - H3: 16×1.25^4 = 39px
   - H2: 16×1.25^5 = 49px
   - H1: 16×1.25^6 = 61px

行高规则: 正文1.5-1.6, 大标题1.1-1.2
字重分配: 正文Regular(400), 强调Medium(500), 标题Semibold(600)或Bold(700)

训练要点：每个设计系统应锁定一个调制比，避免随意选字号。', '["\u6392\u7248", "\u5b57\u4f53\u5c42\u7ea7", "typography", "modular_scale"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (4, 'FD-M04', 'design_system', '间距网格系统 (Spacing & Grid)', 'design_system', 'D:\AI设计\设计系统\间距\', '8px网格基准 — 以8为基本单位构建所有间距、内边距、外边距和尺寸：
1. 基础单位: 8px (4px用于微间距)
2. 间距尺: {0, 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 128}
3. 网格列系统: 12列弹性网格，间距(column-gap)为24px
4. 断点系统:
   - xs: <576px (手机)
   - sm: ≥576px (大屏手机)
   - md: ≥768px (平板)
   - lg: ≥992px (桌面)
   - xl: ≥1200px (宽屏)
   - xxl: ≥1600px (超大屏)

原则：
- 垂直韵律: 所有块级元素的下边距符合间距尺
- 一致性胜过完美: 宁可统一用24px也不混用23px和25px
- 响应式: 间距和网格列数在断点间可调整

训练要点：从ant-design和Stripe的设计中可见，严格的网格系统是专业感的基石。', '["\u95f4\u8ddd", "\u7f51\u683c", "8px\u7f51\u683c", "\u54cd\u5e94\u5f0f", "\u65ad\u70b9"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (5, 'FD-M05', 'design_system', '原子化组件设计 (Atomic Design)', 'design_system', 'D:\AI设计\原子化输出\16_design_atoms.md', '由Brad Frost提出的设计方法论，将UI分解为五个层次：

1. 原子 (Atoms): 最小组件单元
   - Button, Input, Label, Icon, Color, Typography
   - 不可再分，只承载单一职责

2. 分子 (Molecules): 原子组合
   - SearchForm = Input + Button + Icon
   - Card = Image + Title + Description + Actions
   - 承担具体功能单元

3. 组织 (Organisms): 分子组合形成区块
   - Header = Logo(原子) + SearchForm(分子) + Nav(分子)
   - ProductGrid = 多个Card(分子) + Grid(原子)

4. 模板 (Templates): 组织的页面级布局
   - 关注结构而非内容
   - 定义内容区域的位置关系

5. 页面 (Pages): 模板 + 真实内容
   - 验证设计系统的实际效果
   - 发现边缘案例

核心收益: 跨项目复用率可达60-80%，修改一个原子影响所有上层组件。

训练要点：ant-design的83+组件、Stripe的模块化CSS都是原子化设计的实践典范。', '["atomic_design", "\u7ec4\u4ef6\u5316", "\u8bbe\u8ba1\u7cfb\u7edf", "\u65b9\u6cd5\u8bba"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (6, 'FD-M06', 'design_system', '组件状态枚举设计', 'design_system', 'D:\AI设计\ant-design\components (83+组件)', '每个UI组件必须明确定义所有可能的视觉状态：

通用状态集 (9种):
1. Default (默认) — 组件的静止状态
2. Hover (悬停) — 鼠标悬浮时的反馈
3. Active/Pressed (激活) — 点击或按压状态
4. Focus (聚焦) — 键盘/鼠标聚焦，用于可访问性
5. Disabled (禁用) — 不可交互状态
6. Loading (加载中) — 异步操作进行中
7. Error (错误) — 验证失败或异常
8. Empty (空状态) — 无数据时的展示
9. Selected/Checked (选中) — 被选择状态

进阶状态:
- 过渡状态: entering/entered/exiting/exited (动效状态机)
- 拖拽状态: drag-over/dragging/drag-end
- 响应式状态: mobile/tablet/desktop
- 主题状态: light/dark/high-contrast

设计规范: 每个状态应有明确的视觉差异(≥3个视觉属性变化)，且有平滑过渡。

训练要点：IMpeccable设计审核工具的23条审核命令专门检查状态完整性。', '["\u7ec4\u4ef6\u72b6\u6001", "\u4ea4\u4e92\u8bbe\u8ba1", "\u72b6\u6001\u7ba1\u7406", "impeccable"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:16'),
  (7, 'FD-M07', 'design_system', '主题化引擎架构', 'design_system', 'D:\AI设计\design_tokens.json + D:\AI设计\ant-design', '支持设计系统多主题切换的架构模式：

核心机制：
1. Token覆盖层: 主题 = 全局Token + 主题覆盖Token
   - Light模式: 覆盖阴影、背景、文字色
   - Dark模式: 反转亮度通道，重新计算对比度
   - 高对比度: 增强所有对比度到AAA级

2. CSS变量策略 (Runtime Theme):
   :root { --color-bg: #fff; }
   [data-theme="dark"] { --color-bg: #1a1a2e; }
   组件引用: background: var(--color-bg);

3. Token分类:
   - 浅色主题: 品牌色保持，背景减淡，阴影可见
   - 深色主题: 品牌色保持(必要时亮度+20%)，背景加深，阴影用发光替代
   - 所有主题必须通过色盲测试(Deuteranopia/Protanopia/Tritanopia)

4. 过渡策略:
   - Token切换应使用CSS transition: all 0.3s ease
   - 避免闪烁: 在DOM ready前注入主题变量

训练要点：taste-skill的"三旋钮"设计系统(视觉粒度/语言密度/工程纯度)可与主题联动。', '["\u4e3b\u9898\u5316", "\u6697\u8272\u6a21\u5f0f", "CSS\u53d8\u91cf", "design_token", "taste-skill"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (8, 'FD-M08', 'design_system', '设计系统的版本化与发布管理', 'design_system', 'D:\AI设计\d设计系统\design_tokens.json + ant-design', '设计系统应像软件一样进行版本化管理：

1. 语义化版本: MAJOR.MINOR.PATCH
   - MAJOR: 破坏性Token变更(品牌色更换、间距基准改4→8)
   - MINOR: 新增组件/Token(兼容)
   - PATCH: Bug修复(对比度调整、数值微调)

2. ChangeLog管理:
   - 每次发布记录 Token 变更差异
   - 标注 deprecation 计划(如: v2 token将在v4移除)
   - 迁移指南: 旧→新Token映射表

3. 分布式使用:
   - 发布npm包: @company/design-tokens
   - 同时发布CSS变量文件 + JS常量 + Figma Library
   - 消费者锁定版本，按节奏升级

4. 审核流程:
   - 设计审核(Design Review): 使用impeccable的23条审核命令
   - 代码审核(Code Review): 检查Token使用是否正确
   - 可访问性审核(A11Y Audit): 对比度/焦点/屏幕阅读器

训练要点：系统化版本管理使设计系统可持续演进10年+。', '["\u7248\u672c\u7ba1\u7406", "changelog", "\u8bbe\u8ba1\u7cfb\u7edf\u6cbb\u7406", "impeccable"]', 0.85, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (9, 'FD-M09', 'ui_principle', '视觉层级与信息架构', 'design_system', 'D:\AI设计\taste-skill + D:\AI设计\ui-ux-pro-max-skill', '通过视觉属性建立清晰的阅读/浏览优先级：

六大视觉权重控制手段:
1. 尺寸 (Size): 越大越重要。标题 > 副标题 > 正文 > 辅助文字
2. 色彩饱和度: 品牌色 > 中性色 > 灰色。重要信息用高饱和度
3. 对比度: 高对比度(Very important) → 中(Important) → 低(Secondary)
4. 位置: 左上→右下递减。F型扫描模式
5. 留白: 元素周围空间越大，越显得重要
6. 动效: 运动捕获注意力，但过度使用产生噪音

信息架构三原则:
- 分组 (Chunking): 7±2法则，信息块不超过9个
- 分层 (Layering): 全局导航→页面导航→内容→上下文
- 渐进呈现 (Progressive Disclosure): 先给核心，再给细节

训练要点：taste-skill的"反模板化"理念强调层次感而非模板堆砌。', '["\u89c6\u89c9\u5c42\u7ea7", "\u4fe1\u606f\u67b6\u6784", "taste-skill", "UI\u539f\u5219"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (10, 'FD-M10', 'ui_principle', '格式塔原理 (Gestalt Principles) 的UI应用', 'design_system', 'D:\AI设计\taste-skill\skills\ (设计规范)', '人类视觉系统自动将复杂图形组织为整体的心理法则：

1. 接近性 (Proximity): 距离近的元素被视为一组
   → UI应用: 表单标签贴近输入框，按钮组间距小于按钮间距

2. 相似性 (Similarity): 相似外观的元素被视为同一类
   → UI应用: 同层级标题用统一字号/色，所有按钮有统一样式

3. 连续性 (Continuity): 视觉沿平滑路径延伸
   → UI应用: 列表项对齐形成视觉流，分页器的箭头方向

4. 闭合性 (Closure): 大脑自动补全不完整图形
   → UI应用: 加载动画的旋转点阵，卡片缺口的隐式边界

5. 对称性 (Symmetry): 对称图形被视为整体
   → UI应用: 模态框居中设计，导航栏左右对称

6. 图底关系 (Figure-Ground): 自动区分前景和背景
   → UI应用: 卡片阴影分离前后景，模态遮罩区分层级

7. 共同命运 (Common Fate): 同方向运动的元素相关
   → UI应用: 展开/折叠动画的同步元素，滚动触发动效的关联性

训练要点：顶级设计系统(Stripe/Linear/Ant-design)处处体现格式塔原则。', '["\u683c\u5f0f\u5854", "gestalt", "\u611f\u77e5\u5fc3\u7406\u5b66", "UI\u539f\u5219"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (11, 'FD-M11', 'ui_principle', '菲茨定律与交互可访问性 (Fitts''s Law)', 'design_system', 'D:\AI设计\impeccable\docs (设计审核器)', '到达目标的时间 = a + b × log₂(距离/宽度 + 1)

核心推论:
1. 目标越大越好: 最小触控目标44×44px (iOS HIG) / 48×48px (Material)
2. 距离越近越好: 常用操作放在拇指可达区(手机下半部)
3. 屏幕边界是"无限大"目标: 菜单栏放顶部，Mac Dock放底部

UI设计应用:
- 操作按钮: 主要操作使用大按钮(≥44px高)，次要操作使用文本链接
- 表单: 提交按钮靠近最后一个输入项
- 导航: 常用项放在边缘或角落
- 右键菜单: 鼠标悬停展开，避免点击-移动-点击的两次操作

可访问性要求:
- 触控目标: 最小44×44px (iOS)/ 48×48px (Android)
- 功能等效: 触控、鼠标、键盘三种操作方式均支持
- 容错设计: 撤销操作比"确认"(confirm)弹窗更好

训练要点：stripe-clone和impeccable的设计审核都强调交互目标的尺寸合规。', '["\u83f2\u8328\u5b9a\u5f8b", "\u4ea4\u4e92\u8bbe\u8ba1", "\u53ef\u8bbf\u95ee\u6027", "\u89e6\u63a7\u76ee\u6807", "HCI"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (12, 'FD-M12', 'ui_principle', 'Hick''s Law — 选择复杂度管理', 'design_system', 'D:\AI设计\ui-ux-pro-max-skill', '决策时间 = a + b × log₂(n)，其中n=选择数量

核心原则:
1. 选项越少越快: 导航项5-7个为佳(SaaS导航)，超过9个需分组
2. 分组减少选择: 设置用 tab/accordion 分组，每组≤7项
3. 默认值加速: 智能默认值减少思考负担
4. 渐进呈现: 先大类后小类，不一次性展示所有选项

UI设计应用:
- 下拉菜单: 超过15项需加搜索
- 多选表单: 用复选框组(≤7项)或级联选择
- 导航: 主导航≤7项，更多用"更多"折叠
- 定价页: 3个套餐为最佳 (免费/专业/企业)

反例: 过多的配置项导致用户放弃(paradox of choice)。

训练要点：Linear和Stripe的极简配置页是Hick''s Law的最佳实践。', '["Hick''s Law", "\u9009\u62e9\u590d\u6742\u5ea6", "UX\u539f\u5219", "\u8ba4\u77e5\u8d1f\u8377"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (13, 'FD-M13', 'ui_principle', '留白与呼吸感设计 (White Space)', 'design_system', 'D:\AI设计\taste-skill + D:\AI设计\awesome-design-md (Linear/Apple/Stripe)', '空白(负空间)是UI设计中最重要的设计元素之一，不是浪费空间：

四大留白类型:
1. 微留白 (Micro White Space): 字符间距、行高、图标与文字间距
   → 设置: letter-spacing, line-height, gap
2. 宏留白 (Macro White Space): 区块间距、页面边距、卡片间距
   → 设置: padding, margin, 网格间距
3. 主动留白 (Active White Space): 有意识增加的呼吸区域
   → 用空白突出重要内容，创造视觉焦点
4. 被动留白 (Passive White Space): 布局未填满的自然空白
   → 响应式布局中的弹性空白

核心原则:
- 空白与信息密度成反比: 阅读型(多空白) > 工具型(少空白)
- 数据密集型设计(仪表盘/表格)可以更紧凑，但保持24px以上间距
- 空白具有重量感，设计时把它当"元素"而非"剩余"

训练要点：taste-skill提出"反模板化"风格 — 空白必须是设计意图的表达。', '["\u7559\u767d", "\u547c\u5438\u611f", "\u8d1f\u7a7a\u95f4", "taste-skill", "\u6392\u7248"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (14, 'FD-M14', 'ui_principle', '一致性与标准化原则 (Consistency)', 'design_system', 'D:\AI设计\ant-design + D:\AI设计\impeccable', '一致性是设计系统最核心的价值主张：

四层一致性: 
1. 视觉一致性 (Visual): 色彩、间距、字体、圆角、阴影统一
   → 使用Token系统保证，禁止硬编码
2. 行为一致性 (Behavioral): 同类交互有相同行为
   → 所有弹窗按Esc关闭，所有表单Tab切换
3. 语义一致性 (Semantic): 颜色有固定语义
   → 红色=错误(非品牌色)，绿色=成功，蓝色=信息
4. 品牌一致性 (Brand): 跨触点品牌体验统一
   → 网站、App、邮件、打印物使用同一Token体系

检查清单:
- 所有按钮的圆角是否一致？
- 所有输入框的边框色在聚焦时是否一致？
- 所有空状态的插画风格是否一致？
- 所有加载态的骨架屏尺寸是否一致？

收益: 一致性每提升10%，用户完成任务的速度提升约5-7%。

训练要点：impeccable的23条审核命令设计就是为了发现不一致性。', '["\u4e00\u81f4\u6027", "\u6807\u51c6\u5316", "\u8bbe\u8ba1\u7cfb\u7edf", "impeccable", "\u54c1\u724c"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (15, 'FD-M15', 'ui_principle', '渐进式呈现 (Progressive Disclosure)', 'design_system', 'D:\AI设计\ui-ux-pro-max-skill + D:\AI设计\awesome-design-md', '逐步展示信息，只有在用户需要时才显示更多细节：

核心策略:
1. 按角色呈现: 新手→高级→专家，控制面板逐步开放
2. 按任务呈现: 初始→进行中→完成，每个阶段展示当前所需
3. 按关注度呈现: 核心信息(始终可见)→辅助信息(可展开)→细节(深层)

常用UI模式:
- "了解更多"(Show more / Read more)展开
- 手风琴(Accordion)和折叠面板
- 步骤向导(Stepper / Wizard)
- 工具提示(Tooltip)悬停显示附加信息
- 滑动/拖拽揭示隐藏内容

适用场景:
- 复杂表单(注册/结账): 分步骤，每步聚焦一个任务
- 高级设置面板: 基础设置默认可见，高级设置折叠
- 数据详情页: 摘要卡片→弹出详情→完整报表钻取

反模式: 将关键功能藏在深层交互中导致用户找不到。

训练要点：Stripe和Linear的极简初始界面隐藏了80%的复杂性。', '["\u6e10\u8fdb\u5f0f\u5448\u73b0", "progressive_disclosure", "\u4fe1\u606f\u67b6\u6784", "UX"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (16, 'FD-M16', 'ui_principle', '无障碍设计基础 (A11Y)', 'design_system', 'D:\AI设计\impeccable (审核命令含a11y检查) + WCAG标准', '让前端设计对所有人可用，包括残障用户：

WCAG 2.1 四原则 (POUR):
1. 可感知 (Perceivable): 信息必须能以多种方式呈现
   - 所有图片有alt文本
   - 视频有字幕
   - 颜色不唯一传达信息(需搭配图标/文字)
   
2. 可操作 (Operable): 交互组件必须可键盘操作
   - 所有功能可通过键盘完成
   - 焦点顺序符合视觉顺序
   - 触控目标≥44×44px

3. 可理解 (Understandable): 信息和操作必须可理解
   - 表单有明确的Label
   - 错误信息描述清晰
   - 保持一致的导航模式

4. 健壮性 (Robust): 内容能被辅助技术可靠解析
   - 使用语义化HTML (nav, main, article, aside)
   - ARIA属性正确使用
   - 自定义组件有完整的role/state/label

关键指标:
- 对比度: 正文≥4.5:1 (AA) / ≥7:1 (AAA)
- 焦点可见: 焦点环≥2px, 与背景对比≥3:1
- 屏幕阅读器: 所有关键信息可通过语音朗读获取

训练要点：impeccable有专门的a11y审核命令检测这些标准。', '["\u65e0\u969c\u788d", "A11Y", "WCAG", "\u53ef\u8bbf\u95ee\u6027", "\u5305\u5bb9\u6027\u8bbe\u8ba1"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (17, 'FD-M17', 'ux_interaction', '用户心智模型对齐', 'design_system', 'D:\AI设计\ui-ux-pro-max-skill + D:\AI设计\awesome-design-md', '用户在使用产品前已存在的心理模型决定了他们如何理解和使用UI：

核心概念:
1. 系统模型 (System Model): 产品实际如何工作
2. 用户模型 (User''s Mental Model): 用户认为产品如何工作
3. 设计模型 (Designer''s Conceptual Model): 设计师想让用户如何理解

对齐策略:
- 隐喻 (Metaphor): 用现实世界概念降低学习成本 (桌面/文件夹/购物车)
- 模式匹配: 复用用户已熟悉的交互模式
  - 点击Logo回到首页 (所有人都会)
  - 三横线=菜单 (移动端标准)
  - 购物车图标=查看已选商品
- 心理预期管理: 
  - 链接用蓝色+下划线表示可点击
  - 按钮有悬停/按下状态表示交互
  - 加载动画意味着"正在处理，请等待"

测试方法: 
- 首次点击测试 (First Click Test)
- 卡片分类法 (Card Sorting) 验证信息架构
- 五点测试 (5-Second Test) 验证第一印象

训练要点：anti-design的反模式库可帮助理解用户错误预期。', '["\u5fc3\u667a\u6a21\u578b", "\u7528\u6237\u6a21\u578b", "\u9690\u55bb", "UX\u7814\u7a76", "\u4ea4\u4e92\u8bbe\u8ba1"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (18, 'FD-M18', 'ux_interaction', '反馈循环与微交互设计', 'design_system', 'D:\AI设计\react-bits (110+动画组件) + D:\AI设计\awesome-design-md', '每次用户操作都应有即时、恰当、有意义的反馈：

反馈的时间层级:
1. 即时反馈 (0-0.1s): 按钮悬停/按下、键盘按键
2. 延迟反馈 (0.1-1s): 加载动画、表单验证
3. 操作结果 (1-5s): Toast提示、成功/失败通知
4. 长期反馈 (小时-天): 邮件通知、推送消息

微交互四要素 (Dan Saffer):
1. 触发器 (Trigger): 用户操作或系统条件
2. 规则 (Rules): 如何响应的逻辑
3. 反馈 (Feedback): 用户感知到的变化
4. 循环/模式 (Loops/Modes): 重复或例外

UI模式:
- 按钮反馈: 悬停变色→按下内陷→加载旋转→完成打勾
- 表单反馈: 实时验证(失焦触发)→内联错误→提交成功轻提示
- 页面过渡: 路由切换滑入动画→内容淡入
- 数据更新: 新数据高亮闪烁→旧数据淡出

训练要点：react-bits的110+动画组件展示了微交互的丰富可能性。', '["\u5fae\u4ea4\u4e92", "\u53cd\u9988\u5faa\u73af", "\u52a8\u6548", "react-bits", "UX"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (19, 'FD-M19', 'ux_interaction', '状态设计四元组 (Empty/Loading/Error/Edge)', 'design_system', 'D:\AI设计\ant-design + D:\AI设计\impeccable', '产品设计中常被忽视的四种关键状态，决定用户体验质量：

1. 空状态 (Empty State):
   - 首次使用: "尚无数据，开始创建第一个..."
   - 搜索无结果: "未找到相关内容，试试其他关键词"
   - 已完成: "所有任务已完成 🎉"
   - 设计原则: 给用户明确的下一步操作

2. 加载状态 (Loading State):
   - Skeleton屏: 与最终结构一致的骨架占位
   - Spinner: 短时等待(<3s)
   - 进度条: 长时等待(>3s)，有明确进度
   - 设计原则: 永远不要让用户面对白屏

3. 错误状态 (Error State):
   - 网络错误: "连接中断，请检查网络"
   - 服务器错误: "服务器繁忙，请稍后重试"
   - 权限错误: "无访问权限"
   - 设计原则: 错误信息要可理解、可操作、有人情味

4. 边缘状态 (Edge Cases):
   - 超长文本截断
   - 特殊字符处理
   - 极端屏幕尺寸
   - 设计原则: QA测试时必须覆盖

训练要点：impeccable的审核检查要求每个组件都定义这四种状态。', '["\u72b6\u6001\u8bbe\u8ba1", "\u7a7a\u72b6\u6001", "\u52a0\u8f7d\u72b6\u6001", "\u9519\u8bef\u5904\u7406", "impeccable"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (20, 'FD-M20', 'ux_interaction', '导航与寻路设计 (Wayfinding)', 'design_system', 'D:\AI设计\组件库\导航\ + D:\AI设计\awesome-design-md', '帮助用户理解当前位置、去向何方、如何返回的寻路系统：

六大导航模式:
1. 全局导航 (Global Navigation) — 始终可见的顶层导航
   - Top Nav: SaaS标准，7±2项
   - Sidebar: 深度导航，支持分组折叠
   
2. 局部导航 (Local Navigation) — 当前区域的次级导航
   - Tabs: 同一页面的不同视图
   - Sub-nav: 选中全局导航项后的展开

3. 面包屑 (Breadcrumb) — 层级位置指示
   - 位置型: 首页 > 产品 > 详情
   - 路径型: 用户从哪里来
   - 属性型: 当前筛选条件

4. 导航辅助元素:
   - 搜索: 最重要的导航工具
   - 站点地图: 全站内容索引
   - 最近访问: 用户自己的历史路径

5. 寻路信号:
   - "你在这里"指示器 (当前导航项高亮)
   - 页面Title与导航项匹配
   - URL与导航层级对应

6. 移动端适配: 
   - 汉堡菜单(Hamburger Menu)
   - 底部Tab导航 (iOS标准)
   - 手势导航: 滑动返回

训练要点：13个品牌参考(awwwards/siteinspire等)的获奖设计都有出色的寻路设计。', '["\u5bfc\u822a", "\u5bfb\u8def", "\u4fe1\u606f\u67b6\u6784", "wayfinding", "UX"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (21, 'FD-M21', 'ux_interaction', '动效设计原则与性能平衡', 'design_system', 'D:\AI设计\react-bits + D:\AI设计\组件库\动画\', '动效应服务于功能而非装饰：

12条动效原则 (UI改编版):
1. 缓动 (Easing): 自然运动用 ease-in-out，非 linear
   - 进入: ease-out (快速开始，慢速结束)
   - 退出: ease-in (慢速开始，快速结束)
2. 时间感: 0.2-0.5s，大于0.5s感觉卡顿，小于0.1s感觉不到
3. 层次感: 元素按重要性错开进入 (stagger)
4. 关联性: 相关元素同方向/同速度运动
5. 空间连贯: 元素动效前后位置合理
6. 反馈: 操作后50ms内给出视觉反馈

性能要求:
- 优先用 transform 和 opacity (GPU加速)
- 避免: height/width/top/left 的动画 (触发Layout)
- 60fps 是目标，掉帧到30fps以下需简化
- will-change 属性谨慎使用

常用UI动效:
- 页面过渡: 滑入/淡入/缩放
- 列表动效: stagger载入、拖拽重排
- 模态框: 缩放入场 + 遮罩淡入
- Hover: 微妙的上移+阴影加深

训练要点：react-bits提供了110+可直接使用的动效组件示例。', '["\u52a8\u6548", "\u52a8\u753b", "\u6027\u80fd", "react-bits", "CSS\u52a8\u753b"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (22, 'FD-M22', 'ux_interaction', '表单设计最佳实践', 'design_system', 'D:\AI设计\组件库\表单\ + ant-design\components\form', '表单是用户与产品交互的最核心模式:

表单设计九原则:
1. 标签位置: 顶部标签(最快完成) > 左对齐标签(扫描最优) > 右对齐(最慢)
2. 字段分组: 相关字段分组，每步≤7个字段
3. 单列布局: 单列表单完成率比多列高40%
4. 即时验证: 失焦(onBlur)即时校验，不等到提交
5. 智能默认: 预填已知信息(地区、语言、日期格式)
6. 清晰错误: 内联错误(Inline Error) > 顶部错误汇总
7. 进度指示: 多步表单显示当前步骤/总步骤、已完成
8. 键盘优化: Tab顺序=视觉顺序，Enter提交
9. 输入类型: 使用正确的 input type (tel/number/email/date)

移动端特化:
- 使用系统原生键盘类型(数字键盘用于电话号码)
- 大触控目标(≥44px)
- 自动聚焦第一个字段

数据验证层级:
- 格式验证: 邮箱格式、电话号码
- 业务验证: 是否存在、是否可用
- 安全验证: XSS过滤、CSRF防护

训练要点：Ant Design的Form组件是表单设计系统的工业级实现。', '["\u8868\u5355\u8bbe\u8ba1", "UX", "ant-design", "\u6570\u636e\u8f93\u5165", "\u9a8c\u8bc1"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (23, 'FD-M23', 'ux_interaction', '移动端优先设计思维 (Mobile First)', 'design_system', 'D:\AI设计\awesome-design-md (移动端品牌参考)', '从最小的屏幕开始设计，渐进增强到更大的屏幕：

核心方法论:
1. 内容优先级: 最小屏幕上只展示核心内容
2. 渐进增强: 屏幕越大→展示越多、越详细
3. 触控优先: 所有交互为手指设计，而非鼠标

移动端设计约束:
- 单手持握: 拇指覆盖区=手机屏幕下半部40%
- 最小触控: 44×44px (Apple HIG) / 48×48px (Material)
- 网络环境: 假设3G网络(200KB/s)，懒加载优化

响应式断点决策:
1. 不是"适配移动"，而是"从小到大"
2. 每个断点重新审视布局，不只缩放
3. 导航模式切换: 底部Tab(移动)→顶部导航(桌面)
4. 表格响应: 卡片化(移动) → 表格(桌面)

常见反模式:
- 桌面端塞满功能再移到移动端(裁剪很难)
- 隐藏重要功能在汉堡菜单后
- 桌面端hover态交互在触控上不起作用

训练要点：Awwwards获奖移动端设计是移动优先的最佳参考。', '["\u79fb\u52a8\u4f18\u5148", "\u54cd\u5e94\u5f0f\u8bbe\u8ba1", "\u89e6\u63a7", "mobile-first", "UX"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (24, 'FD-M24', 'ux_interaction', '转化率优化设计 (CRO Design)', 'design_system', 'D:\AI设计\stripe-clone + D:\AI设计\awesome-design-md (Stripe/特斯拉)', '通过设计手段提升用户完成目标转化的比率：

CRO设计七原则:
1. 清晰的价值主张 (Value Proposition):
   - 首屏5秒内回答: "这是什么? 对我有什么用?"
   - 使用具体数字而非模糊描述

2. 减少摩擦 (Friction Reduction):
   - 减少表单字段 (每少1个字段提升转化5-10%)
   - 社交登录一键注册
   - 无需注册即可预览产品

3. 信任信号 (Trust Signals):
   - 安全认证标识 (SSL/PCI)
   - 客户Logo墙
   - 真实评价/案例
   - 退款保证

4. 紧迫感 (Urgency & Scarcity):
   - 限时优惠倒计时
   - 库存显示 ("仅剩3件")
   - 合理使用，过度使用降低信任

5. 清晰的CTA (Call to Action):
   - 按钮文案: "开始免费试用" > "提交"
   - 对比色CTA按钮
   - 唯一主要操作

6. 社会证明 (Social Proof):
   - 用户数/下载量展示
   - 实时购买通知
   - 第三方背书

7. 消除焦虑 (Anxiety Reduction):
   - 明确的定价
   - 取消订阅的便捷性
   - 隐私保护说明

训练要点：Stripe-clone是CRO设计的教科书级案例。', '["CRO", "\u8f6c\u5316\u7387", "\u589e\u957f\u8bbe\u8ba1", "Stripe", "UX"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (25, 'FD-M25', 'visual_design', '对比度与可读性设计', 'design_system', 'D:\AI设计\设计系统\色彩\ + WCAG标准', '对比度是阅读体验的基础，直接影响信息传达效率:

对比度层级设计:
1. 极重要信息: 品牌色背景+白色文字，或黑字白底
2. 正文: #1a1a1a 背景#fff (对比度15:1) 
3. 次级信息: #666 背景#fff (对比度5.5:1)
4. 辅助信息: #999 背景#fff (对比度2.8:1, 仅用于装饰)
5. 禁用状态: #ccc 背景#fff (对比度1.6:1)

可访问性对比度标准 (WCAG 2.1):
- AA级: 正文4.5:1, 大文本(≥18pt bold/≥24pt)3:1
- AAA级: 正文7:1, 大文本4.5:1

颜色组合考虑:
- 色盲类型: Deuteranopia(红绿色盲6%)、Protanopia、Tritanopia
- 信息不应仅靠颜色区分: 搭配图标、文字、形状
- 使用亮度对比而非色相对比: 黑白模式下也应可读

工具链:
- 设计时: 对比度检查插件 (Stark, Axe)
- 构建时: CI流水线自动检查Token对比度
- 运行时: 高对比度模式检测 (prefers-contrast: more)

训练要点：awesome-design-md中Apple/特斯拉的设计以高对比度著称。', '["\u5bf9\u6bd4\u5ea6", "\u53ef\u8bfb\u6027", "WCAG", "\u8272\u76f2", "A11Y"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (26, 'FD-M26', 'visual_design', '视觉节奏与重复设计模式', 'design_system', 'D:\AI设计\taste-skill + D:\AI设计\awesome-design-md', '通过有规律的视觉重复创造和谐、可预测的用户体验:

视觉节奏的四种类型:
1. 规律节奏 (Regular Rhythm): 等间距重复
   - 卡片网格、列表项、时间轴
   - 稳定、可靠、可预测

2. 流动节奏 (Flowing Rhythm): 有机重复
   - 曲线排列的插图、手绘风格
   - 动态、自然、亲切

3. 渐进节奏 (Progressive Rhythm): 递进变化
   - 字体层级、色彩阶梯、尺寸递增
   - 引导视线向特定方向

4. 交替节奏 (Alternating Rhythm): 模式交替
   - 斑马纹表格、交替卡片排列
   - 减少视觉疲劳

设计应用:
- 重复: 组件复用 (相同卡片样式), 间距模式 (8px系统)
- 渐变: 颜色从主→辅渐变, 尺寸从大到小
- 强调: 打破节奏吸引注意力 (特殊颜色卡片)

训练要点：taste-skill强调"节奏感"是区分专业和业余设计的标志。', '["\u89c6\u89c9\u8282\u594f", "\u91cd\u590d", "\u8bbe\u8ba1\u6a21\u5f0f", "taste-skill", "\u6392\u7248"]', 0.85, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (27, 'FD-M27', 'visual_design', '品牌视觉语言一致性', 'design_system', 'D:\AI设计\awesome-design-md (73+品牌设计规范)', '品牌的视觉语言必须在所有触点上保持一致:

品牌视觉系统的八大要素:
1. Logo系统: 标准/简化/图标/ Favicon版本
2. 色彩系统: 品牌色+辅助色+中性色+语义色
3. 字体系统: 品牌字体+ Web后备字体
4. 插画风格: 统一线条粗细/着色方式/角色风格
5. 摄影风格: 光线/色调/构图/后期统一
6. 图标系统: 线型/面型统一，圆角/端点统一
7. 空间规则: 留白比例、元素间距标准
8. 动效语言: 缓动函数/时长/运动方向统一

品牌落地检查清单:
- 是否有品牌规范文档 (Brand Guidelines)?
- Token是否跨项目一致 (Web/App/打印)？
- 第三方生态(合作伙伴)是否获得品牌资源？
- 品牌色在不同屏幕(OLED/LCD)是否表现一致？

品牌演进:
- 小步更新: 渐进式优化，避免突变
- 保留核心: Logo/品牌色/字体需高度稳定
- 记录变迁: 每次变更记录原因和时间

训练要点：awesome-design-md收录的73+品牌规范是学习的宝库。', '["\u54c1\u724c\u8bbe\u8ba1", "\u89c6\u89c9\u8bed\u8a00", "brand", "\u8bbe\u8ba1\u89c4\u8303"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (28, 'FD-M28', 'visual_design', '数据可视化设计原则', 'design_system', 'D:\AI设计\组件库\数据展示\ + ant-design', '将数据转化为易于理解的可视化形式：

图表选择决策树:
- 比较: 柱状图 (数量比较) / 雷达图 (多维比较)
- 趋势: 折线图 (时间序列) / 面积图 (趋势+量级)
- 组成: 饼图 (占比, ≤5项) / 堆叠柱状图 (组成变化)
- 分布: 散点图 (相关性) / 直方图 (数值分布)
- 流程: 漏斗图 (转化路径) / 桑基图 (流量分配)
- 关系: 网络图 (节点关系) / 树图 (层次结构)

设计原则:
1. 数据-墨水比 (Data-Ink Ratio): 去除不必要的装饰
2. 零基线: 柱状图从0开始，避免误导
3. 排序: 默认按数值降序排列
4. 标签清晰: 轴线标签、数据标签、图例完整
5. 无障碍: 图表有文字描述、支持键盘导航
6. 交互: 悬停显示详情、点击下钻、缩放

色彩规范:
- 数据色板: 8-12种可区分的颜色
- 色盲友好: 避免红绿同时使用
- 语义色: 好(绿)、坏(红)、中性(蓝/灰)

训练要点：ant-design的图表组件和Stripe的Dashboard是数据可视化典范。', '["\u6570\u636e\u53ef\u89c6\u5316", "\u56fe\u8868", "dashboard", "ant-design", "\u4fe1\u606f\u8bbe\u8ba1"]', 0.85, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (29, 'FD-M29', 'visual_design', '排版与文字层次设计', 'design_system', 'D:\AI设计\设计系统\排版\ + taste-skill', '文字是产品与用户沟通的核心媒介:

排版六维控制:
1. 字号 (Font Size): modular scale等比，确保层级分明
2. 字重 (Font Weight): 400/500/600/700，每跳一级需视觉可见差异
3. 颜色 (Color): 正文近黑、辅助浅灰，颜色=层级
4. 间距 (Spacing): 字距(letter-spacing)、词距(word-spacing)
5. 行高 (Line Height): 正文1.5-1.6、标题1.1-1.2
6. 大小写 (Case): 标题Title Case、正文Sentence case、标签UPPER

文字层级参考 (16px基准, 1.25 scale):
- Display (特大标题): 48/40/32px — 1-2次/页
- H1: 28px — 页面标题，每页1个
- H2: 22px — 区块标题
- H3: 18px — 小组件标题
- Body: 16px — 正文
- Small: 14px — 辅助信息
- Caption: 12px — 标注/注释

响应式排版:
- 移动端: 基准15px, H1=24px
- 桌面端: 基准16px, H1=32px
- 使用 clamp() 实现流畅排版: font-size: clamp(1rem, 1rem + 0.5vw, 1.5rem)

训练要点：taste-skill中"反模板化"的排版策略追求可读性>装饰性。', '["\u6392\u7248", "\u5b57\u4f53\u5c42\u6b21", "typography", "taste-skill", "\u54cd\u5e94\u5f0f"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (30, 'FD-M30', 'visual_design', '设计中的阴影与深度系统', 'design_system', 'D:\AI设计\设计系统\色彩\ + ant-design\design_tokens', '通过阴影和层级创造视觉深度的系统化方法:

阴影层级设计 (Z-Space):
- Level 0 (Base): 无阴影，平面元素
- Level 1 (Raised): 小偏移+小模糊，卡片默认态
  box-shadow: 0 1px 3px rgba(0,0,0,0.08)
- Level 2 (Elevated): 中偏移+中模糊，悬停卡片
  box-shadow: 0 4px 12px rgba(0,0,0,0.12)
- Level 3 (Overlay): 大偏移+大模糊，下拉菜单/弹出层
  box-shadow: 0 8px 24px rgba(0,0,0,0.16)
- Level 4 (Modal): 最大偏移+最大模糊，模态框
  box-shadow: 0 16px 48px rgba(0,0,0,0.24)

阴影的三个维度:
1. 偏移 (Offset): X/Y方向，决定光源方向（统一从上方）
2. 模糊 (Blur): 决定柔和度
3. 扩散 (Spread): 决定生长感

暗色模式适配:
- 阴影透明度降低 (深色背景上看不清阴影)
- 使用发光代替阴影: box-shadow: 0 0 20px rgba(0,0,0,0.3)
- 通过背景色层次区分深度 (surface 1/2/3)

训练要点：Apple的设计强调无阴影的平面层级，Material Design强调阴影的层次。', '["\u9634\u5f71", "\u6df1\u5ea6", "\u5c42\u7ea7", "Material Design", "\u6697\u8272\u6a21\u5f0f"]', 0.85, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (31, 'FD-M31', 'process_methodology', '设计冲刺与迭代设计思维', 'design_system', 'D:\AI设计\taste-skill\skills\ + D:\AI设计\darwin-skill', '加速设计决策、减少猜测的迭代方法论:

设计冲刺五步 (Google Ventures改编):
1. 理解 (Understand): 用户研究、竞品分析、定义问题
2. 发散 (Diverge): Brainstorming、草稿、概念探索
3. 决策 (Decide): 投票、聚焦、确定方案
4. 原型 (Prototype): 快速原型(低保真→高保真)
5. 验证 (Validate): 用户测试、A/B测试、反馈收集

迭代频率建议:
- 探索阶段: 每2-3天一个迭代循环
- 开发阶段: 每1-2周一个设计验收
- 优化阶段: 每月一次设计审核 (Design Audit)

设计评审四维度:
1. 功能完整性: 是否覆盖所有用户场景
2. 视觉质量: 是否符合设计系统标准
3. 交互合理性: 用户是否能自然完成任务
4. 实现可行性: 技术约束下的可落地性

最佳实践:
- 使用darwin-skill的设计进化工具追踪设计版本
- taste-skill的"三旋钮"(视觉粒度/语言密度/工程纯度)做质量评估
- 每周设计复盘：什么有效/什么无效/下次改进

训练要点：darwin-skill是专门用于设计进化和迭代的工具。', '["\u8bbe\u8ba1\u51b2\u523a", "\u8fed\u4ee3", "\u8bbe\u8ba1\u601d\u7ef4", "darwin-skill", "\u65b9\u6cd5\u8bba"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (32, 'FD-M32', 'process_methodology', '设计审核与质量评估体系', 'design_system', 'D:\AI设计\impeccable (23条设计审核命令)', '系统化评估设计质量的标准化流程:

impeccable 23条设计审核命令 (按维度分组):

A. 布局 (Layout):
1. 网格一致性检查
2. 间距合规性
3. 对齐完整性
4. 响应式断点覆盖

B. 视觉 (Visual):
5. Color Token使用检查
6. Typography层级规范
7. Shadow层级检查
8. BorderRadius一致性

C. 状态 (States):
9. Hover状态完整性
10. Focus状态可见性
11. Active状态反馈
12. Disabled状态表现
13. Loading状态存在
14. Empty状态处理
15. Error状态处理

D. 交互 (Interaction):
16. 触控目标尺寸(≥44px)
17. 键盘可操作性
18. 焦点顺序(Tab Order)
19. 页面过渡动效

E. 内容 (Content):
20. 文本截断处理
21. 空状态文案
22. 错误信息质量
23. 多语言适配

评分体系:
- Pass (通过): 完全符合标准
- Warning (警告): 轻微偏差，可接受
- Fail (不通过): 需要修复

训练要点：impeccable旨在实现设计审核自动化，可直接集成到CI/CD。', '["\u8bbe\u8ba1\u5ba1\u6838", "\u8d28\u91cf\u8bc4\u4f30", "impeccable", "\u8bbe\u8ba1QA"]', 0.95, '1.0.0', 1, 1, '2026-07-01 19:37:26', '2026-07-01 19:39:17'),
  (33, 'FD-M33', 'process_methodology', '设计与开发的协同工作流 (Design-Dev Handoff)', 'design_system', 'D:\AI设计\ant-design + D:\AI设计\taste-skill\skills\', '设计到开发的交接流程是产品交付效率的关键瓶颈:

设计交付物规范:
1. 设计稿 → 开发
   - 明确标注: 间距、字号、颜色值(使用Token而非绝对数值)
   - 组件状态覆盖: 每个组件的所有状态截图
   - 响应式说明: 每个断点的布局变化
   - 动效规范: 时长、缓动函数、触发条件

2. Figma→代码工作流:
   - Tokens: 通过 design_tokens.json 直接导出
   - 组件: Figma组件的属性对应到组件Props
   - 样式: 自动生成CSS变量

3. 开发实现阶段:
   - 使用ant-design等组件库保证80%的界面一致
   - 自定义组件严格遵循设计系统Token
   - Storybook作为组件文档和测试平台

4. 设计验收 (Design QA):
   - 开发完成后的像素级对比验收
   - 使用impeccable的自动化审核
   - 回归检查清单

5. 持续同步:
   - 设计师可直接修改CSS变量文件(无需开发介入)
   - Token变更自动生成Changelog
   - 每周设计-开发同步会议

训练要点：Token化是设计与开发同步的关键基础设施。', '["\u8bbe\u8ba1\u4ea4\u4ed8", "\u5f00\u53d1\u534f\u540c", "handoff", "\u6d41\u7a0b", "Token"]', 0.9, '1.0.0', 1, 1, '2026-07-01 19:37:27', '2026-07-01 19:39:17'),
  (34, 'BK-M01', 'backend', '异步SQLAlchemy selectinload铁律', '复盘', 'docs/复盘/2026-07-05_全链路打通复盘.md', '异步模式所有select(Model)查询必须加.options(selectinload(Model.relation))，否则Pydantic model_validate触发MissingGreenlet。create后不能用db.refresh，需重查询。', NULL, 0.8, '1.0.0', 1, 0, '2026-07-05 14:54:48', '2026-07-05 14:54:48'),
  (35, 'ARC-M01', 'architecture', 'API版本中间件白名单', '复盘', 'docs/复盘/2026-07-05_全链路打通复盘.md', 'APIVersionRedirectMiddleware重写/api/v1/xxx→/api/xxx，导致注册在/api/v1/的路由404。所有前缀必须加入_EXPLICIT_V1_PREFIXES。建议自动收集。', NULL, 0.8, '1.0.0', 1, 0, '2026-07-05 14:54:48', '2026-07-05 14:54:48'),
  (36, 'OPS-M01', 'devops', '__pycache__部署陷阱', '复盘', 'docs/复盘/2026-07-05_全链路打通复盘.md', '__pycache__缓存旧.pyc，git pull后进程重启仍加载旧版。修复：启动前清除所有__pycache__目录。', NULL, 0.8, '1.0.0', 1, 0, '2026-07-05 14:54:48', '2026-07-05 14:54:48'),
  (37, 'FE-M01', 'frontend', '微信小程序token生命周期', '复盘', 'docs/复盘/2026-07-05_全链路打通复盘.md', 'wx.getStorageSync(''token'')可能读到过期token。app启动时必须异步验证，401自动清除+reLaunch登录页。所有API 401 handler统一跳登录。', NULL, 0.8, '1.0.0', 1, 0, '2026-07-05 14:54:48', '2026-07-05 14:54:48');

-- match_records: 10 rows (batch 1)
INSERT INTO "match_records" ("id", "user_a_id", "user_b_id", "match_score", "status", "common_tags", "source", "created_at") VALUES
  (1, 64, 56, 0.3546, 'matched', '[]', 'auto', '2026-07-06 03:40:05'),
  (2, 66, 56, 0.3502, 'matched', '[]', 'auto', '2026-07-06 03:44:51'),
  (3, 66, 64, 0.3425, 'matched', '[]', 'auto', '2026-07-06 03:44:51'),
  (4, 73, 56, 0.3942, 'matched', '[]', 'auto', '2026-07-07 00:02:56'),
  (5, 73, 64, 0.3558, 'matched', '[]', 'auto', '2026-07-07 00:02:56'),
  (6, 73, 66, 0.3502, 'matched', '[]', 'auto', '2026-07-07 00:02:56'),
  (7, 120, 64, 0.3483, 'matched', '[]', 'auto', '2026-07-08 02:50:54'),
  (8, 120, 73, 0.3409, 'matched', '[]', 'auto', '2026-07-08 02:50:55'),
  (9, 120, 56, 0.3402, 'matched', '[]', 'auto', '2026-07-08 02:50:55'),
  (10, 120, 66, 0.3284, 'matched', '[]', 'auto', '2026-07-08 02:50:55');

-- pages: 70 rows (batch 1)
INSERT INTO "pages" ("id", "brochure_id", "sort_order", "content_type", "content", "image_url", "media_url", "ai_summary") VALUES
  (1, 1, 0, 'cover', 'roger
ceo
容蓝', '', '', ''),
  (2, 1, 1, 'text', '姓名：roger
职位：ceo
公司：容蓝

', '', '', ''),
  (3, 1, 2, 'image', '📞 未填写', '', '', ''),
  (4, 5, 0, 'cover', 'roger
ceo
容蓝', '', '', ''),
  (5, 5, 1, 'text', '姓名：roger
职位：ceo
公司：容蓝

', '', '', ''),
  (6, 5, 2, 'image', '📞 未填写', '', '', ''),
  (7, 8, 0, 'text', '测试科技 - 创新驱动未来', '', '', ''),
  (8, 8, 1, 'text', '我们是一家专注于AI的科技公司', '', '', ''),
  (9, 10, 0, 'text', '测试科技', '', '', ''),
  (10, 11, 0, 'text', '测试用户
测试科技
产品经理', '', '', ''),
  (11, 12, 0, 'text', 'Hello World', '', '', ''),
  (12, 13, 0, 'text', '测试内容', '', '', ''),
  (13, 14, 0, 'text', '测试通过', '', '', ''),
  (14, 15, 0, 'text', '测试通过', '', '', ''),
  (15, 16, 0, 'text', '测试通过', '', '', ''),
  (16, 17, 0, 'text', 'hello', '', '', ''),
  (17, 18, 0, 'text', 'hello', '', '', ''),
  (18, 19, 0, 'text', '通过', '', '', ''),
  (19, 20, 0, 'text', 'hello', '', '', ''),
  (20, 21, 0, 'text', '通过', '', '', ''),
  (21, 23, 0, 'text', '测试通过', '', '', ''),
  (22, 24, 0, 'text', '测试通过', '', '', ''),
  (23, 25, 0, 'text', '测试通过', '', '', ''),
  (24, 26, 0, 'text', '验证通过', '', '', ''),
  (25, 27, 0, 'text', '验证通过', '', '', ''),
  (26, 28, 0, 'cover', '向海容
CEO、
容蓝', '', '', ''),
  (27, 28, 1, 'text', '姓名：向海容
职位：CEO、
公司：容蓝

', '', '', ''),
  (28, 28, 2, 'image', '📞 未填写', '', '', ''),
  (29, 30, 0, 'text', '测试科技公司简介', '', '', ''),
  (30, 31, 0, 'text', '<img src=x onerror=alert(1)>', '', '', ''),
  (31, 33, 0, 'text', '测试科技公司简介', '', '', ''),
  (32, 36, 0, 'cover', 'roger
ceo
容蓝', '', '', ''),
  (33, 36, 1, 'text', '姓名：roger
职位：ceo
公司：容蓝

', '', '', ''),
  (34, 36, 2, 'image', '📞 未填写', '', '', ''),
  (35, 37, 0, 'cover', 'roger
ceo
容蓝', '', '', ''),
  (36, 37, 1, 'text', '姓名：roger
职位：ceo
公司：容蓝

', '', '', ''),
  (37, 37, 2, 'image', '📞 18117089707', '', '', ''),
  (38, 38, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (39, 38, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (40, 38, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (41, 39, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (42, 39, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (43, 39, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (44, 40, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (45, 40, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (46, 40, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (47, 41, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (48, 41, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (49, 41, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (50, 42, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (51, 42, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (52, 42, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (53, 43, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (54, 43, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (55, 43, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (56, 44, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (57, 44, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (58, 44, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (59, 45, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (60, 45, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (61, 45, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (62, 46, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (63, 46, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (64, 46, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', ''),
  (65, 48, 0, 'cover', '向海容 | AI创业者 | Hermes AI', '', '', ''),
  (66, 48, 1, 'about', 'AI数字军团创始人，专注AI出海与企业智能化', '', '', ''),
  (67, 48, 2, 'contact', '13800138000 | hai@hermes.ai', '', '', ''),
  (68, 49, 0, 'cover', '{&quot;title&quot;: &quot;\u6d4b\u8bd5\u753b\u518c&quot;, &quot;subtitle&quot;: &quot;AI\u6570\u667a\u540d\u7247&quot;}', '', '', ''),
  (69, 49, 1, 'profile', '{&quot;name&quot;: &quot;\u6d4b\u8bd5\u7528\u6237&quot;, &quot;title&quot;: &quot;\u6d4b\u8bd5\u804c\u4f4d&quot;}', '', '', ''),
  (70, 49, 2, 'contact', '{&quot;phone&quot;: &quot;13800138000&quot;, &quot;email&quot;: &quot;test@test.com&quot;}', '', '', '');

-- users: 121 rows (batch 1)
INSERT INTO "users" ("id", "username", "phone", "password_hash", "wechat_openid", "name", "company", "title", "intro", "avatar", "role", "membership_tier", "membership_expires_at", "membership_synced_at", "unlock_quota", "quota_reset_at", "created_at", "updated_at") VALUES
  (1, NULL, '13800000002', '$2b$12$Nldb6qETm.JznURIFWurnOB2AyZ9kFIo5UVgGEBTRQj.Lc0IwlQRG', NULL, 'test2', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-26 07:40:50', '2026-06-26 07:40:50'),
  (2, NULL, '1381bdcce3c', '$2b$12$2RHlQaBeHTSmtkCDfd2xQOYJnOvqqn51Vp/WO3RUf6O4vgRIGFvJC', 'mock_wx_16171bdcce3c', '微信用户_test', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=dcce3c', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-29 21:42:27', '2026-06-29 21:42:27'),
  (3, NULL, '139fc9f0fd2', '$2b$12$RFzkkKVlrcbYtoPV6CD5M.2Yk4lnfsMgn7lJTXrSX6hFLs.Fd4c7q', 'mock_mini_5aedfc9f0fd2', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-29 21:42:30', '2026-06-29 21:42:30'),
  (4, NULL, '139b20682e4', '$2b$12$Q.UA80BS7wdb8G5PEgBrJ.LN.PKS5nxSRPVK20UfiQMakZ6Hs0OT.', 'mock_mini_b161b20682e4', '小程序用户_t123', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 00:03:32', '2026-06-30 00:03:32'),
  (5, NULL, '139569c1d05', '$2b$12$tDIZQWOJ.WwycRYzaaxOgOOsARNEkts47vb2f7zJ5zDmOjjr9/r76', 'mock_mini_6af2569c1d05', '小程序用户_t123', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 00:05:45', '2026-06-30 00:05:45'),
  (6, NULL, '1396d84fd0b', '$2b$12$2bta0Zn.pp8jt2LBhw.uD.votVhRkhPDVzzQxbjPw5WCsaLU60PMi', 'mock_mini_7cea6d84fd0b', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 00:22:15', '2026-06-30 00:22:15'),
  (7, NULL, '13915beebd8', '$2b$12$EcFEsC6UdGveZIp1syseA.9H4iXBM3/Mxe2sYgPsJpGdl/nB4TKTi', 'mock_mini_a14215beebd8', '小程序用户_oJlO', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:17:23', '2026-06-30 17:17:23'),
  (8, NULL, '139cd1173c2', '$2b$12$OMa5cDSkiEyfCJqTJb8PSuP9L7sIA.kjnZIUi0jqaBQa0y9DqrzQm', 'mock_mini_c11dcd1173c2', '小程序用户_WjFH', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:18:06', '2026-06-30 17:18:06'),
  (9, NULL, '139a71335df', '$2b$12$IvGis8wQOasqR6S.6/8uiOGn3sQxv.Ch0O0sjRaRGO9lkGCQ2nHAe', 'mock_mini_1df1a71335df', '小程序用户_YjFQ', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:18:35', '2026-06-30 17:18:35'),
  (10, NULL, '139336aa6c5', '$2b$12$LwDvFuDpr0uaxcaebBVSYews./m8XT/rSCtr79hjaN6Ssw5BVfOha', 'mock_mini_9da4336aa6c5', '小程序用户_nDkk', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:20:26', '2026-06-30 17:20:26'),
  (11, NULL, '139a4362458', '$2b$12$ZTC22ctSCsCAoTIXLoDOG.ihwuTY6ftcFSESofdpN9Ke6f4/eTBeC', 'mock_mini_b5a7a4362458', '小程序用户_aBFZ', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:21:00', '2026-06-30 17:21:00'),
  (12, NULL, '139dc9d8933', '$2b$12$ZQvx.tTMQNZAdnljInjEH.sHaWvYaPqE0W5u6s7.0lFeGdwgQOkny', 'mock_mini_1a84dc9d8933', '小程序用户_s10T', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:31:21', '2026-06-30 17:31:21'),
  (13, NULL, '139132c9395', '$2b$12$10d2oSudobb7SZYTYzvn/OZg1PUnOEDrBW4YrNgjUV/dpSLyEDnT.', 'mock_mini_2a24132c9395', '小程序用户_SBFB', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:32:31', '2026-06-30 17:32:31'),
  (14, NULL, '139baaa6fe0', '$2b$12$UoZ2QNk9x1gP/E7h0CWdEOPI3qwM82P5fas3Jvn5zkJNXPKHFaHua', 'mock_mini_5226baaa6fe0', '小程序用户_W102', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:39:20', '2026-06-30 17:39:20'),
  (15, NULL, '139c1c7aa1f', '$2b$12$nZSNoe1wo0mU69Ly02xyQuS3.S/LBcR6YNb91KUJU6zGcI3oqFPIe', 'mock_mini_518ac1c7aa1f', '小程序用户_klFg', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:40:47', '2026-06-30 17:40:47'),
  (16, NULL, '1394811c29f', '$2b$12$RIdQjulAh29cQnhe55l4m..fInO2npOuIbkh47ROlzwOTB2m5nzki', 'mock_mini_4fc34811c29f', '小程序用户_620l', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:41:56', '2026-06-30 17:41:56'),
  (17, NULL, '139283a8206', '$2b$12$hmoTaV1w.fWzKA40rgsYMu5RDyHAN59nqR7KTVJKHBYLx/87NknJC', 'mock_mini_b0c5283a8206', '小程序用户_IEkz', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:42:21', '2026-06-30 17:42:21'),
  (18, NULL, '1396a48ebdd', '$2b$12$Mn62mxUInddAxGtyOMOtG.196yUiBAZ3O4rrbxObxNYj385BOZmLq', 'mock_mini_faf46a48ebdd', '小程序用户_KEko', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:42:46', '2026-06-30 17:42:46'),
  (19, NULL, '18621514551', '$2b$12$Jcb83KelOycaGZ8N4VCyDeGfurygpjsdo6/ZiZ2j1WmmFR3.Y8Pim', NULL, '向海容', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:43:16', '2026-06-30 17:43:16'),
  (20, NULL, '13912345678', '$2b$12$NqEABOvAh3qvdR9NFw91tuU/F1l515Gv7qiw730S/d7b0wiuqy0SW', NULL, '测试用户', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:46:47', '2026-06-30 17:46:47'),
  (21, NULL, '1391592f8e1', '$2b$12$IIWP1t/E3tLvdrs8rpjHA.Y4V4qlaGJ4IxlF6Myq2KW0FFcKyL.yq', 'mock_mini_b1351592f8e1', '小程序用户_tj00', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:47:11', '2026-06-30 17:47:11'),
  (22, NULL, '1394bedd7f7', '$2b$12$KjN.r0p2wMmQvZu/vlUr3emLwVdYTYd/6o64aURY5dtoLgUPeIoLy', 'mock_mini_18894bedd7f7', '小程序用户_QCFt', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-06-30 17:48:33', '2026-06-30 17:48:33'),
  (23, NULL, '1398acb3fda', '$2b$12$SlqC7QwW8M00isDf/zT2y.skhSSfPn1TxUUnEUvZftTCghw7hVMq.', 'mock_mini_329d8acb3fda', '小程序用户_1234', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 13:33:26', '2026-07-02 13:33:26'),
  (24, NULL, '1392c9e8f4f', '$2b$12$8sUinC7L3d9JHMOEAFYJFO4gcpDyLWOKbQAk7247efiq.C/B.XRI2', 'mock_mini_bf282c9e8f4f', '小程序用户_zw1V', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 13:37:00', '2026-07-02 13:37:00'),
  (25, NULL, '139d621020e', '$2b$12$mxsshxBpCoy0y.79PiQNduufnfgrOsz38w0VDDLGzwEyQ1KCUCwIa', 'mock_mini_bf41d621020e', '小程序用户_nq0t', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 13:37:04', '2026-07-02 13:37:04'),
  (26, NULL, '139b85c7521', '$2b$12$DuClrgRjdYd28saLkKvJ0uCi7/dk8ARgrZ3EQ3p/Ach6dNeVHBsda', 'mock_mini_14c8b85c7521', '小程序用户_1klc', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 13:37:06', '2026-07-02 13:37:06'),
  (27, NULL, '139f11ca222', '$2b$12$DzUMRc20mibH3Vd9ASJ/0uiF6MOFZ/XTLZSrCy6b0JORbO8.IvZfe', 'mock_mini_199cf11ca222', '小程序用户_1234', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 13:43:34', '2026-07-02 13:43:34'),
  (28, NULL, '1398f6769c6', '$2b$12$TsKKY7li50wgXbjRbu4YAOat1PnGac.erRbOM8VdtT8F3fyjwTBE.', 'mock_mini_aacd8f6769c6', '小程序用户_OLFj', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:12:07', '2026-07-02 14:12:07'),
  (29, NULL, '13942989177', '$2b$12$uZNCCEJs58c4ziQfiUW.6Ow8bxDsM6APCoRa.mD/kVeFEXUt6OBI2', 'mock_mini_ed1f42989177', '小程序用户_tb0H', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:12:08', '2026-07-02 14:12:08'),
  (30, NULL, '1397a07f041', '$2b$12$Q1Jwfuk.e5QP7C3Iy3c1MOdL9B6ZdeZyVMmAm0q3T0MzNNHK/0oXa', 'mock_mini_eec67a07f041', '小程序用户_uxFg', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:56:44', '2026-07-02 14:56:44'),
  (31, NULL, '139d95fff38', '$2b$12$jo0HtJeuixZwTlbY27STS.E76cZOCZtPK343CdQwN04x0iH4bLX.m', 'mock_mini_cad9d95fff38', '小程序用户_ok11', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:56:58', '2026-07-02 14:56:58'),
  (32, NULL, '139fff232bb', '$2b$12$tSMxXfeQHJqgIK/Gow9/b.f1MZNxI57qS/CVoMVpeKIJJZ5Xt0bE6', 'mock_mini_c11ffff232bb', '小程序用户_UolO', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:57:00', '2026-07-02 14:57:00'),
  (33, NULL, '139bd20890a', '$2b$12$gOlW6s7/EeXHhyhFJH3mUe3EbfzNoMcFpjY/VM4mNtbTBdxTpLWry', 'mock_mini_5a3ebd20890a', '小程序用户_mM0R', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:57:49', '2026-07-02 14:57:49'),
  (34, NULL, '1393cb817c8', '$2b$12$bfBUcL83wrceWUcoLbNZmORARMXqFkR.vKys78n9aV0hFv8DyIaAu', 'mock_mini_42ba3cb817c8', '小程序用户_wk1Z', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:58:51', '2026-07-02 14:58:51'),
  (35, NULL, '1399f8ea4f0', '$2b$12$JO6tgpPGI.DX3qGP7nISr.j8CGDyrhi5cB210WJoQm4jPZsHJWqOu', 'mock_mini_a2b49f8ea4f0', '小程序用户_DxFb', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 14:59:03', '2026-07-02 14:59:03'),
  (36, NULL, '139b59cc935', '$2b$12$rrdjp1MNKX1r6/XjAlkgW.8Vy9k/hn3EQ3zJ63lm8mshnqJIunlK2', 'mock_mini_effbb59cc935', '小程序用户_dfmy', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:16:11', '2026-07-02 15:16:11'),
  (37, NULL, '1392e92ae97', '$2b$12$OFbyg7NwXUcM/bAvj3c4O.z9zmgxaufktsDEVdIFtbjH89AChxXyi', 'mock_mini_268e2e92ae97', '小程序用户_qf0X', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:16:59', '2026-07-02 15:16:59'),
  (38, NULL, '139a6077515', '$2b$12$VfRKT32oePd/7JRRBSQPU.LW9rhRwweF2xgksYHIWtIrvT25hfEhK', 'mock_mini_d872a6077515', '小程序用户_sf0v', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:17:32', '2026-07-02 15:17:32'),
  (39, NULL, '139b2d1f6de', '$2b$12$iuc9bmCEf0WpA7nXO.v5Du/V9mgwMCAjJEsDPDouYA9Ivf1oeuEFu', 'mock_mini_be48b2d1f6de', '小程序用户_pIlV', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:37:14', '2026-07-02 15:37:14'),
  (40, NULL, '139bb5c2249', '$2b$12$0AS0PNfMgjnjXwapw.6soes9e5XeNixRmL8c1QIWfV6sZXuK2gTdy', 'mock_mini_384fbb5c2249', '小程序用户_YzFP', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:37:22', '2026-07-02 15:37:22'),
  (41, NULL, '1392b48ab66', '$2b$12$AV6.Ta/7zolAXXdGfUc0PeFQWcx8fJkiDFdCmAjd1b8gogNu5YcxW', 'mock_mini_712b2b48ab66', '小程序用户_YzFH', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:37:32', '2026-07-02 15:37:32'),
  (42, NULL, '1393bcfe5ca', '$2b$12$bJ6sJgptwkBAe0CEAHyoGu5eoJ2xvwPBvoyTAhWhCdvbZ5OfStpQe', 'mock_mini_06873bcfe5ca', '小程序用户_OO0R', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:38:02', '2026-07-02 15:38:02'),
  (43, NULL, '139a9504c98', '$2b$12$vPy5P0c9EytjPtJzivmoBubwVWWJYLAh.u0Ea.3EYTP6qlSf/JBUi', 'mock_mini_fc32a9504c98', '小程序用户_Ig0s', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-02 15:38:14', '2026-07-02 15:38:14'),
  (44, NULL, '139a6541c9c', '$2b$12$eGVbofTcz8ttLHYY2gJ9Su3BNTYgJ0Bkw8G/Lcg1sEKRTvRKUSWEi', 'mock_mini_d445a6541c9c', '小程序用户_1234', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:00:36', '2026-07-05 10:00:36'),
  (45, NULL, '139a958c9b3', '$2b$12$sC5UlIujvf.qcwrsbsnWqe3ibqcNcQTLbl12CSkE1.o3gxnpo6a9m', 'mock_mini_27d0a958c9b3', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:00:45', '2026-07-05 10:00:45'),
  (46, NULL, '139149cdfa0', '$2b$12$KuHnOLYqHKNP1EcBvYaJt.1QP.37slZWOzamjznaoTk1ZqKNNdmsK', 'mock_mini_742d149cdfa0', '小程序用户_ph2A', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:20:35', '2026-07-05 10:20:35'),
  (47, NULL, '139e0b8a216', '$2b$12$RyZ7uTq1wx3JtkReHAFcsOwQNsaSZsc84NYG0T5cT7eKgx76DYrMK', 'mock_mini_ed74e0b8a216', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:23:20', '2026-07-05 10:23:20'),
  (48, NULL, '13976272618', '$2b$12$5Dt3AR4Nl5T08ZpifN7Nk.A4Gt3B01VKUJ1Uwo5tEVfIrCOpsMVgG', 'mock_mini_ebb976272618', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:30:26', '2026-07-05 10:30:26'),
  (49, NULL, '13926db7f4a', '$2b$12$JI2Y0.iFPmQuJ38RnleT4.9PYQcr8vYtmUXDzkH91s4cnpIDneHYi', 'mock_mini_abd326db7f4a', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 10:31:31', '2026-07-05 10:31:31'),
  (50, NULL, '1394874cfa7', '$2b$12$Lzigkv3VSS30QUAHWglTE.QqCcFA2MX.A.wjedpbYH7z9XKUA2e/O', 'mock_mini_b6504874cfa7', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 11:35:33', '2026-07-05 11:35:33'),
  (51, NULL, '1397864dbc1', '$2b$12$jXFbUFz2xn0lMIiCzPjpjeP0P87P1xPPpFV2dBvfoZb.4/Ayo.frC', 'mock_mini_c48e7864dbc1', '小程序用户_EB00', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 14:36:04', '2026-07-05 14:36:04'),
  (52, NULL, '139e689a824', '$2b$12$20L31kxNG037h1P2/p8Qk.olz9rE/2GCI.I5WgSpemDN8zgFH8wsu', 'mock_mini_6734e689a824', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 14:45:34', '2026-07-05 14:45:34'),
  (53, NULL, '1395834f97d', '$2b$12$GM6E5w6/MVQ4Kgwl3wucleuyQGglIPq0mKCLqJBTaypWVPcqHL1YC', 'mock_mini_45fc5834f97d', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 14:47:41', '2026-07-05 14:47:41'),
  (54, NULL, '1390fd95999', '$2b$12$f/YF7BrW20BTo3QyfXqNoentdv6KFeNxQ/wuUaqLnTXeGsnfYTVIu', 'mock_mini_1ba20fd95999', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 14:47:57', '2026-07-05 14:47:57'),
  (55, NULL, '13960004a19', '$2b$12$XIsiwjDDWLkBd/UinxMQ7ORpl079omzcbRKsN4T8uKXu7/H5aOQ1u', 'mock_mini_3c7460004a19', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-05 14:49:07', '2026-07-05 14:49:07'),
  (56, NULL, '13900001111', '$2b$12$LFzp5lByYAzHnjuXqNMMm.nc0aP/C7cLQy1ECVlCJ/q5GOwUirt2a', NULL, '测试用户', '测试科技', '产品经理', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:14:02', '2026-07-06 00:14:02'),
  (57, NULL, '13800138000', '$2b$12$J/wAMhKKTK1OqJPNxcu1AOe1MjUHG.oQJRjF8d8eBHCag6WXQQILq', NULL, 'testuser', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:29:46', '2026-07-06 00:29:46'),
  (58, NULL, '13800138001', '$2b$12$uUp6ThvxmFucNJeb0aAwb.8h9OnKBamGbKA3Mq3emp/eAVyqVRErC', NULL, 'testuser2', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:30:20', '2026-07-06 00:30:20'),
  (59, NULL, '13800138002', '$2b$12$HG2hKj6.eXMhku/tdAmOxOyH1kgTsB5KtBOiMFki07nimhX50nGyq', NULL, 'testuser3', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:30:38', '2026-07-06 00:30:38'),
  (60, NULL, '13800138003', '$2b$12$FyRbKPLCtEmuPqIohNJ4RuTxv69VXxLQtGby5u3ji9sx2LyAyTJnW', NULL, 'testuser4', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:31:04', '2026-07-06 00:31:04'),
  (61, NULL, '13800138004', '$2b$12$wPdSKPljyUipJ6w7fJCSJuHMSVaBH1vs9WrhFUVqmQBzVANTxn5eO', NULL, 'testuser5', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:31:22', '2026-07-06 00:31:22'),
  (62, NULL, '13800138006', '$2b$12$HOijyUtKnED/G9arx4idquF7JEDrPf2doomgtA7v2.ShAOVPs8dXK', NULL, 'testuser6', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 00:33:26', '2026-07-06 00:33:26'),
  (63, NULL, '13899a5103a', '$2b$12$J3knOo9sYPefUYPf56LEg.Mlq6/NduOyppIbJmT1ysqqM5/NdRomS', 'mock_wx_921499a5103a', '微信用户_1234', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=a5103a', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 03:38:19', '2026-07-06 03:38:19'),
  (64, NULL, '13800139000', '$2b$12$lWMk9YU3h2I0fXHEMtUcBeBQeZUN06pwR.G0U8IYkiVRVxQw.zNVS', NULL, '测试用户', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 03:39:00', '2026-07-06 03:39:00'),
  (65, NULL, '138d3a5bf51', '$2b$12$49ybAoTs7AyZuhWwiSoSZu2fzGxHHflOe5ozRX3NQC.cWz5kvFM5m', 'mock_wx_ef34d3a5bf51', '微信用户_test', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=a5bf51', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 03:39:03', '2026-07-06 03:39:03'),
  (66, NULL, '13900139001', '$2b$12$Y4gxjesumfnUBHif/tkD8.SJuutSB3bM.wakX4/q/7e7MGYB4kcFa', NULL, '验证用户', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 03:44:30', '2026-07-06 03:44:30'),
  (67, 'redteam2', '13900002222', '$2b$12$SpZeZ3y2XZ0E0Oy3Etbnx.uYjPTWCT4MlLwMOUsCH/r9JYbXmuP2S', NULL, 'RedTeam', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:56:17', '2026-07-06 23:56:17'),
  (68, 'userb', '13900003333', '$2b$12$GJ1cxnB1/St5ipOzpVZxh.VSE5w8DnoXpJnBohB4d68p6loLv4MAy', NULL, 'UserB', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:56:23', '2026-07-06 23:56:23'),
  (69, 'usera', '13900004444', '$2b$12$2jjsuVkCV8cpfSV24/bWZup8KFhJyMfcSCff.es8SQpEGucOdDAKa', NULL, 'UserA', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:56:39', '2026-07-06 23:56:39'),
  (70, 'redteam_main', '13900009999', '$2b$12$/lbZcW3L5cOaINY2vIgN6.T2ND9TkjGcU1BgwURYawft1yHfLxa9a', NULL, 'RedTeam', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:57:43', '2026-07-06 23:57:43'),
  (71, 'userb_test', '13900008888', '$2b$12$IT95Z.gCU/Yji6azbOceE.TF/mGW5Enrr2E5YdP3Gj4/B0iJ.yf12', NULL, 'UserB', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:57:46', '2026-07-06 23:57:46'),
  (72, 'xsstest1', '13900007777', '$2b$12$zGiATJwUppS8XBs1IbmfdeLoi.TYdOFJL/iIQJ.JTXZkPZI3ikcSK', NULL, '<script>alert(document.cookie)</script>', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-06 23:59:02', '2026-07-06 23:59:02'),
  (73, NULL, '13853043036', '$2b$12$lHV8bDu.yObLaSPY2zKtF..75zXr4r.Mkhat87v2o9gIc1uqT760e', NULL, '测试用户_58199659', '测试科技', '产品经理', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:02:39', '2026-07-07 00:02:39'),
  (74, NULL, '13911112222', '$2b$12$LQkpph/049KkjDBCHmbNKuJNWF37Xf8xHwqclbTU05itq3qRlR5LK', NULL, 'audit_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:07:28', '2026-07-07 00:07:28'),
  (75, NULL, '13900139000', '$2b$12$5i3vCuahLq9iFYsko.szQO.4GSYQn6yME8CBQfvLckTunGN/KIZci', NULL, '<script>alert(1)</script>', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:29:42', '2026-07-07 00:29:42'),
  (76, NULL, '13999139999', '$2b$12$cm8UnZQD7M9CAPT7BxRb4e4fb8dHqXSEKuHSy7uwY2EUkOTKEHgES', NULL, 'PenTestUser', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:30:01', '2026-07-07 00:30:01'),
  (77, NULL, '13999139998', '$2b$12$NlMpLCNvhRgOfm7EZ6ibH.Y6a01qAh7IJw152brl/KBidZIAgf2A6', NULL, 'PenTestUser2', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:30:34', '2026-07-07 00:30:34'),
  (78, NULL, '13999139996', '$2b$12$ct8m723ldOI4LTyJOQpRweLsXhfIEt2flb.5fx3dQkp5XlQ58P4Nm', NULL, 'RedTeamOp', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:32:45', '2026-07-07 00:32:45'),
  (79, NULL, '1382fb8346d', '$2b$12$UCEdFlKDnFpZwe6AzkiV9uvEPT68Zl0dJb9lEHuxXLKRWKzr1mvIm', 'mock_wx_47612fb8346d', '微信用户_k123', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=b8346d', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:33:11', '2026-07-07 00:33:11'),
  (80, NULL, '138d1f8b481', '$2b$12$SQGmTHoFmKHNzTvBsCR5pOSi3XZHXS/uzK.ZbdPT8uSw3Utrx7Nwy', 'mock_wx_b216d1f8b481', '微信用户__123', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=f8b481', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:33:37', '2026-07-07 00:33:37'),
  (81, NULL, '13849474da5', '$2b$12$XQ7JIstPyDzbYMqZrmafLeSPzDOTD4KQMBTKUmEV9aJvEySkRB1D.', 'mock_wx_2ab349474da5', '微信用户__123', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=474da5', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:33:47', '2026-07-07 00:33:47'),
  (82, NULL, '1384925a370', '$2b$12$HO8yQqcLjke/7.MiobfSTO.BVH2OHdhDLULRBK4m0S3h7iW.rIq1y', 'mock_wx_6ee44925a370', '微信用户__123', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=25a370', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:34:29', '2026-07-07 00:34:29'),
  (83, NULL, '13900000011', '$2b$12$Nt/i3cp.39TsGfh8plFyXeXeawngaJfHB5da/pY79GcphgehuO1mi', NULL, '<script>alert(1)</script>', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:41:20', '2026-07-07 00:41:20'),
  (84, NULL, '13900000099', '$2b$12$bqeIiCwDyOaxOFRt7IHyz.WChXIgwdMZt6D5PRk3BMyqILJm2vqom', NULL, '&lt;script&gt;alert(1)&lt;/script&gt;', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:44:32', '2026-07-07 00:44:32'),
  (85, NULL, '13900000123', '$2b$12$MvoZ.qa1akJQ4FPTiybbbOpu0T6IkzX8grU6ihwAsrLSRnqLfHZia', NULL, '&lt;img src=x onerror=alert(1)&gt;', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:49:28', '2026-07-07 00:49:28'),
  (86, NULL, '13900000001', '$2b$12$1f.LckYaPFcDoQiYdFPf.OYhYlocnXJ6p5z6ZIMRgUz4k.S8tRInu', NULL, 'TestUser', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:50:09', '2026-07-07 00:50:09'),
  (87, NULL, '13900000100', '$2b$12$yxNqrq86Iekt/NURLbf86eruu7.p5JPWS8EVksndFLWEuOj70dJ9q', NULL, 'TestUser100', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:50:19', '2026-07-07 00:50:19'),
  (88, NULL, '13900000999', '$2b$12$naBVZ.T0CJVYHrEa9.VxN.C1dmwkJYaIUhybkHD6jxse4/4O/oBPu', NULL, '&lt;b&gt;BoldName&lt;/b&gt;', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 00:50:56', '2026-07-07 00:50:56'),
  (89, NULL, '13900000998', '$2b$12$42rnBPzIUts41ph29eiWje.RStafzTn9sY.x3CNtOn7hRjKpB0QBy', NULL, 'TestUser', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:23:55', '2026-07-07 06:23:55'),
  (90, NULL, '13900001091', '$2b$12$ZHiG/ZiSjJq.CglhYt2sQuybD6c6Ny6oUT0RsR75RWgTGXcmAe4zO', NULL, 'TestUser1', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:24:03', '2026-07-07 06:24:03'),
  (91, NULL, '13900001092', '$2b$12$L2pekvZWaGRO7XMiRDzdreJbLsdXiVsnd5zP93t9rUiTEqJHs.8d2', NULL, 'TestUser2', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:24:04', '2026-07-07 06:24:04'),
  (92, NULL, '13900001093', '$2b$12$UC3az5T/Yxlob2hxweDDoO4LjniLWT6X6Xm1CRIv.2By1i57NIUOm', NULL, 'TestUser3', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:24:05', '2026-07-07 06:24:05'),
  (93, NULL, '13900000997', '$2b$12$tTMgs3FNDtfnJD1C2M6L8uLTu4.CimqChfBBteCctY5.kxQOs/OE6', NULL, '&lt;script&gt;alert(1)&lt;/script&gt;', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:26:34', '2026-07-07 06:26:34'),
  (94, NULL, '13900000996', '$2b$12$znHh50FnI2x8/xlDvMutpOV41rtvUiStnd78vO5UlNV0IfgEiIXjG', NULL, 'FinalUser', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 06:26:57', '2026-07-07 06:26:57'),
  (95, NULL, '139054271bb', '$2b$12$LV8BjFspTWEsvuKStdTsRemZRdxOdclaQhy4kd3mnkWGVfT67DXc2', 'mock_mini_029f054271bb', '小程序用户_t123', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:54:50', '2026-07-07 12:54:50'),
  (96, NULL, '139db01370a', '$2b$12$MRLx/qYQoXGyGM0GJwSRAuryD27WGwlXq7C0RO5XqrryaXhlnSSw.', 'mock_mini_dbd9db01370a', '小程序用户_mple', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:55:22', '2026-07-07 12:55:22'),
  (97, NULL, '13987c75921', '$2b$12$SIigJNO4m/jUAJIJGGRRb.37GD7CDabZc23NAJnrWxjEzyJZif13G', 'mock_mini_782187c75921', '小程序用户_t123', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:56:01', '2026-07-07 12:56:01'),
  (98, NULL, '139cdbf468d', '$2b$12$UQczxTyvncVuV66rGfMYYuc3RZH9exI1XoK9lMvp4Qweg9A/1Lil6', 'mock_mini_43e1cdbf468d', 'test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:56:04', '2026-07-07 12:56:04'),
  (99, NULL, '1397af391ef', '$2b$12$IaQi9g5KAwkYXG0XZAhZd.lqvCghLxnqq5h7ng6DYGyMf1gvkWelm', 'mock_mini_5cb07af391ef', '小程序用户_c123', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:56:30', '2026-07-07 12:56:30'),
  (100, NULL, '139f1114a88', '$2b$12$BYR8grqE6oUc7XPq0ikQC.yz.fwcl/v.1gD5MWETHysvGWwQgKIHu', 'mock_mini_1a91f1114a88', '小程序用户_test', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 12:56:58', '2026-07-07 12:56:58');

-- users: 121 rows (batch 2)
INSERT INTO "users" ("id", "username", "phone", "password_hash", "wechat_openid", "name", "company", "title", "intro", "avatar", "role", "membership_tier", "membership_expires_at", "membership_synced_at", "unlock_quota", "quota_reset_at", "created_at", "updated_at") VALUES
  (101, NULL, '13995576aff', '$2b$12$t7Y9g4n560z2klCA6dmvoubxqis3hvrxmUFisRTXo0w9hVBhYW5SK', 'mock_mini_b52495576aff', '小程序用户_t127', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 13:12:23', '2026-07-07 13:12:23'),
  (102, NULL, '139588f9c68', '$2b$12$nzVg7wntEimsc.9IFZqo7uY7hQrYh1MhKiNd0w8u8rAip/ZP/hLSi', 'mock_mini_46d9588f9c68', '小程序用户_9fe1', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 15:59:22', '2026-07-07 15:59:22'),
  (103, NULL, '139411a2f21', '$2b$12$GJV5G8/MEPgIsPiAUUnbF.0Cq6k/z6OS7naU861OmOnGt9IZCrLca', 'mock_mini_c385411a2f21', '小程序用户_063f', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:02:35', '2026-07-07 16:02:35'),
  (104, NULL, '139e821234c', '$2b$12$iHhp9NVLszdhy59sKJXZ8.hkP259.ftVYv2YdevLwQDZg59E2Soai', 'mock_mini_dae7e821234c', '小程序用户_6e21', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:04:44', '2026-07-07 16:04:44'),
  (105, NULL, '139234ae815', '$2b$12$auTmpTtXDvllM8UmCUp5LOcq5F.iFwObYK4vFHx7pCecH48VYyely', 'mock_mini_7057234ae815', '小程序用户_4c74', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:08:24', '2026-07-07 16:08:24'),
  (106, NULL, '139736bed41', '$2b$12$0OfRNxyThP7CkdIBXh71QOZl6QfyHFzsjB2dxizSXj.Xyg6sQlqwW', 'mock_mini_2eec736bed41', '小程序用户_c4b5', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:10:11', '2026-07-07 16:10:11'),
  (107, NULL, '139b8ef59e5', '$2b$12$2mgsoOuOv.Pue8lAvDCv2OKhVpQBpW8Lsshl7RkH7N.qELnxPANse', 'mock_mini_f7f7b8ef59e5', '小程序用户_c690', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:11:38', '2026-07-07 16:11:38'),
  (108, NULL, '139fe8f8169', '$2b$12$Z.3FE7DwVqzLwqqP3O8uJOcJwA9/KqTa2pv3zCmIa06hihooDxhOe', 'mock_mini_3d88fe8f8169', '小程序用户_a8f3', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:14:43', '2026-07-07 16:14:43'),
  (109, NULL, '139ba34a61d', '$2b$12$RdagOAkw/sT/.CgjFb6RseAaauZ9SPHSFTFoseUSjBGi8aY8l2wa.', 'mock_mini_5021ba34a61d', '小程序用户_3970', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:16:07', '2026-07-07 16:16:07'),
  (110, NULL, '13953600a7f', '$2b$12$vIXOI0QjIvThZLB8IPzH9uXktHfU5998pjhPY9d9KIrvv0xqWq.T6', 'mock_mini_8b5d53600a7f', '小程序用户_ce8b', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:18:16', '2026-07-07 16:18:16'),
  (111, NULL, '13940c6dc40', '$2b$12$bR5aq21o7MkGMcfOK.8vBe0iFNreWeHK5AIH8W7vUElrKT5kXG0Ke', 'mock_mini_b9f940c6dc40', '小程序用户_00dd', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-07 16:24:40', '2026-07-07 16:24:40'),
  (112, NULL, '138024ae6c5', '$2b$12$LGpxPiGdeuZ1u5it1EUhauh4D69lhY27nLce4m2u8oNm8LAsazGe2', 'mock_wx_eabb024ae6c5', '微信用户__001', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=4ae6c5', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:48:29', '2026-07-08 02:48:29'),
  (113, NULL, '1386be7ece5', '$2b$12$PTM9PN7e7Y7eWoEscWlLJu860DwQ5TojF/T6W.tjQYgIQDBrTybhi', 'mock_wx_47dc6be7ece5', '微信用户__001', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=e7ece5', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:48:37', '2026-07-08 02:48:37'),
  (114, NULL, '138aac81c90', '$2b$12$5BKdefLe1.hSbtVBYTpcoeRXH09/n6GKyUfomPfisDfLHJwUSri0K', 'mock_wx_61a1aac81c90', '微信用户__002', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=c81c90', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:48:43', '2026-07-08 02:48:43'),
  (115, NULL, '13841bf1cc6', '$2b$12$jd.dGdfhxoIVitnG67zAC.hmwwar176xIfXpBQPxl3Ub7RLl18im6', 'mock_wx_3cb941bf1cc6', '微信用户_t003', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=bf1cc6', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:49:22', '2026-07-08 02:49:22'),
  (116, NULL, '138c8f86e0e', '$2b$12$4VM3s4UyBQl8C/rrtn9wb.PmUCfezgwBPzQtCVgtHkH.etT.2RN.2', 'mock_wx_d048c8f86e0e', '微信用户_t004', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=f86e0e', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:49:27', '2026-07-08 02:49:27'),
  (117, NULL, '13831ccef15', '$2b$12$Ms0xlIMrVvr5sMSqIy0Mzukg0sauNtvmkJLBdoL5OGh3AsLvtFCsq', 'mock_wx_ffd931ccef15', '微信用户_t005', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=ccef15', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:49:31', '2026-07-08 02:49:31'),
  (118, NULL, '138ab3d469b', '$2b$12$uRoGkmNZkxmVUG7eH/0vZe7Wc6a3Tcrp5j7C1X/RSL55vlCtpkUUu', 'mock_wx_0164ab3d469b', '微信用户_t007', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=3d469b', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:49:41', '2026-07-08 02:49:41'),
  (119, NULL, '138122445ce', '$2b$12$gDR5pq/S2CkV78mNJ4YDFe8jwe43kvOQTnYFJ1m5OfOah3r6I80mW', 'mock_wx_d30c122445ce', '微信用户_t010', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=2445ce', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:49:55', '2026-07-08 02:49:55'),
  (120, NULL, '138fe44d715', '$2b$12$wST/iyEqekHPoJV9tbuEz.jflmjUnVf9p0aXNKnbCbpHg4Zdd4Uka', 'mock_wx_da95fe44d715', '微信用户_flow', '', '', '', 'https://api.dicebear.com/7.x/avataaars/svg?seed=44d715', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 02:50:22', '2026-07-08 02:50:22'),
  (121, NULL, '1393acd8ad6', '$2b$12$m5iI4dV061CBV8o0SdZ9rO6HYJoZcOPHjqaK1XNxxUs.I4m9l5.wm', 'mock_mini_9c0d3acd8ad6', '小程序用户_ac4d', '', '', '', '', 'user', 'free', NULL, NULL, 0, NULL, '2026-07-08 04:04:26', '2026-07-08 04:04:26');