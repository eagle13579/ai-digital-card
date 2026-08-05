\connect aicard_db
INSERT INTO platforms (name, platform_no, creator_id, annual_fee, description, created_at, updated_at) VALUES
('长三角产业资源平台', 'PT20240001', 1, 0.0, '立足长三角，服务区域内企业资源对接、技术合作与市场拓展', NOW(), NOW()),
('粤港澳大湾区创新联盟', 'PT20240002', 1, 0.0, '大湾区科技创新与产业协同平台，连接科创企业与投资机构', NOW(), NOW()),
('数字经济生态圈', 'PT20240003', 1, 0.0, '数字化转型服务商联盟，为企业提供数字化升级一站式服务', NOW(), NOW()),
('中小企业合作网', 'PT20240004', 1, 0.0, '中小企业资源互助平台，共享客户、渠道与供应链资源', NOW(), NOW()),
('AI智造产业基地', 'PT20240005', 1, 0.0, 'AI+智能制造产业集群，汇聚技术、人才与资本', NOW(), NOW());
SELECT COUNT(*) as cnt FROM platforms;
