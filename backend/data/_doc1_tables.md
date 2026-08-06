
## A.用户与认证

### api_key_usage

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| api_key_id | INTEGER |  | ✅ |  | |
| date | VARCHAR(10) |  | ✅ |  | |
| request_count | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_api_key_usage_api_key_id` (api_key_id) 

### api_keys

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| key | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| permissions | TEXT |  | ✅ |  | |
| rate_limit | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| last_used_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_api_keys_user_id` (user_id) 
- `sqlite_autoindex_api_keys_1` (key) UNIQUE

### developer_reward_balances

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| total_points | INTEGER |  | ✅ |  | |
| used_points | INTEGER |  | ✅ |  | |
| balance | INTEGER |  | ✅ |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_developer_reward_balances_id` (id) 
- `ix_developer_reward_balances_developer_id` (developer_id) UNIQUE

### developer_rewards

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| reward_type | VARCHAR(32) |  | ✅ |  | |
| points | INTEGER |  | ✅ |  | |
| reason | VARCHAR(256) |  |  |  | |
| source_id | INTEGER |  |  |  | |
| source_desc | VARCHAR(128) |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| issued_at | DATETIME |  |  |  | |

**索引**:
- `ix_developer_rewards_id` (id) 
- `ix_developer_rewards_developer_id` (developer_id) 

### invitation_codes

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| code | VARCHAR(8) |  | ✅ |  | |
| batch_id | VARCHAR(32) |  |  |  | |
| max_uses | INTEGER |  |  |  | |
| used_count | INTEGER |  |  |  | |
| created_by | INTEGER |  |  |  | |
| expires_at | DATETIME |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| remark | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_invitation_codes_code` (code) UNIQUE
- `ix_invitation_codes_id` (id) 

### revoked_token ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_revoked_token_id` (id) 

### reward_redemptions

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| points_spent | INTEGER |  | ✅ |  | |
| redemption_type | VARCHAR(32) |  | ✅ |  | |
| quota_amount | INTEGER |  |  |  | |
| description | VARCHAR(256) |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_reward_redemptions_id` (id) 
- `ix_reward_redemptions_developer_id` (developer_id) 

### sdk_apps

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| app_id | VARCHAR(64) |  | ✅ |  | |
| app_secret | VARCHAR(128) |  |  |  | |
| developer_id | INTEGER |  | ✅ |  | |
| sdk_type | VARCHAR(32) |  | ✅ |  | |
| platform | VARCHAR(32) |  |  |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| version | VARCHAR(16) |  |  |  | |
| permissions | TEXT |  |  |  | |
| redirect_uris | TEXT |  |  |  | |
| icon_url | VARCHAR(512) |  |  |  | |
| homepage_url | VARCHAR(512) |  |  |  | |
| privacy_policy_url | VARCHAR(512) |  |  |  | |
| is_verified | BOOLEAN |  | ✅ |  | |
| is_public | BOOLEAN |  | ✅ |  | |
| total_installs | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_sdk_developer` (developer_id) 
- `ix_sdk_apps_developer_id` (developer_id) 
- `idx_sdk_type_status` (sdk_type, status) 
- `idx_sdk_status` (status) 
- `sqlite_autoindex_sdk_apps_1` (app_id) UNIQUE

### tenants

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| slug | VARCHAR(64) |  | ✅ |  | |
| plan | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_tenants_1` (slug) UNIQUE

### user_consents

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| consent_type | VARCHAR(64) |  | ✅ |  | |
| granted | BOOLEAN |  | ✅ |  | |
| consent_version | VARCHAR(16) |  |  |  | |
| source | VARCHAR(64) |  |  |  | |
| ip | VARCHAR(45) |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| detail | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_consent_user_type` (user_id, consent_type) 
- `idx_consent_user_created` (user_id, created_at) 
- `ix_user_consents_user_id` (user_id) 

### user_event ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_user_event_id` (id) 

### users

- **数据量**: 104 行 | **字段数**: 18 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| username | VARCHAR(64) |  |  |  | |
| phone | VARCHAR(20) |  | ✅ |  | |
| password_hash | VARCHAR(128) |  | ✅ |  | |
| wechat_openid | VARCHAR(64) |  |  |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| company | VARCHAR(128) |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| intro | TEXT |  | ✅ |  | |
| avatar | VARCHAR(256) |  | ✅ |  | |
| role | VARCHAR(16) |  | ✅ |  | |
| membership_tier | VARCHAR(16) |  | ✅ |  | |
| membership_expires_at | DATETIME |  |  |  | |
| membership_synced_at | DATETIME |  |  |  | |
| unlock_quota | INTEGER |  | ✅ |  | |
| quota_reset_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_users_3` (wechat_openid) UNIQUE
- `sqlite_autoindex_users_2` (phone) UNIQUE
- `sqlite_autoindex_users_1` (username) UNIQUE

---

## B.名片与画册

### brochures

- **数据量**: 20 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| cover | VARCHAR(256) |  | ✅ |  | |
| purpose | VARCHAR(32) |  | ✅ |  | |
| pages_count | INTEGER |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| share_token | VARCHAR(32) |  | ✅ |  | |
| view_count | INTEGER |  | ✅ |  | |
| album_meta | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| visibility | VARCHAR(16) |  | ✅ | 'public' | |
| platform_id | INTEGER |  |  | NULL | |

**索引**:
- `sqlite_autoindex_brochures_1` (share_token) UNIQUE

### business_card ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_business_card_id` (id) 

### nfc_cards

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| nfc_uid | VARCHAR(64) |  | ✅ |  | |
| card_data_json | TEXT |  | ✅ |  | |
| vcard_raw | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_nfc_cards_user_id` (user_id) 
- `ix_nfc_cards_nfc_uid` (nfc_uid) UNIQUE

### nfc_tap_records

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| nfc_uid | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_nfc_tap_records_from_user_id` (from_user_id) 
- `ix_nfc_tap_records_to_user_id` (to_user_id) 

### pages

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| brochure_id | INTEGER |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| content_type | VARCHAR(16) |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| image_url | VARCHAR(256) |  | ✅ |  | |
| media_url | VARCHAR(512) |  | ✅ |  | |
| ai_summary | TEXT |  | ✅ |  | |

### referral_links

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_user_id | INTEGER |  | ✅ |  | |
| code | VARCHAR(32) |  | ✅ |  | |
| title | VARCHAR(100) |  |  |  | |
| description | VARCHAR(500) |  |  |  | |
| invite_type | VARCHAR(20) |  | ✅ |  | |
| redirect_url | VARCHAR(500) |  |  |  | |
| scan_count | INTEGER |  | ✅ |  | |
| register_count | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| expires_at | DATETIME |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_referral_links_code` (code) UNIQUE
- `ix_referral_links_id` (id) 
- `idx_referral_owner` (owner_user_id, is_active) 
- `ix_referral_links_owner_user_id` (owner_user_id) 

### user_tags

- **数据量**: 806 行 | **字段数**: 7 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| tag_type | VARCHAR(16) |  | ✅ |  | |
| tag | VARCHAR(64) |  | ✅ |  | |
| weight | FLOAT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### visitor_logs

- **数据量**: 25 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| brochure_id | INTEGER |  | ✅ |  | |
| visitor_id | VARCHAR(64) |  |  |  | |
| visitor_ip | VARCHAR(48) |  | ✅ |  | |
| visitor_name | VARCHAR(64) |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| page_viewed | VARCHAR(64) |  | ✅ |  | |
| duration | INTEGER |  | ✅ |  | |
| interested | BOOLEAN |  | ✅ |  | |
| contact_msg | TEXT |  | ✅ |  | |
| visit_time | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

---

## C.匹配与推荐

### connections

- **数据量**: 120 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| strength | FLOAT |  | ✅ |  | |
| label | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_connections_1` (user_id, contact_id) UNIQUE

### match_credit_log ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_match_credit_log_id` (id) 

### match_records

- **数据量**: 7337 行 | **字段数**: 8 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_a_id | INTEGER |  | ✅ |  | |
| user_b_id | INTEGER |  | ✅ |  | |
| match_score | FLOAT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| common_tags | TEXT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### online_matching_events ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_events_id` (id) 

### online_matching_feedback ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_feedback_id` (id) 

### online_matching_registrations ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_online_matching_registrations_id` (id) 

### relation_events

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| relation_id | INTEGER |  | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| event_type | VARCHAR(30) |  | ✅ |  | |
| old_trust_score | FLOAT |  |  |  | |
| new_trust_score | FLOAT |  |  |  | |
| reason | VARCHAR(200) |  |  |  | |
| metadata_json | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_relation_events_created_at` (created_at) 
- `ix_relation_events_to_user_id` (to_user_id) 
- `ix_relation_events_relation_id` (relation_id) 
- `ix_relation_events_from_user_id` (from_user_id) 
- `ix_relation_events_id` (id) 

### six_degree_path_cache

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| path_json | TEXT |  | ✅ |  | |
| path_length | INTEGER |  | ✅ |  | |
| total_trust_score | FLOAT |  | ✅ |  | |
| hit_count | INTEGER |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `idx_path_cache_expires` (expires_at) 
- `ix_six_degree_path_cache_from_user_id` (from_user_id) 
- `ix_six_degree_path_cache_id` (id) 
- `ix_six_degree_path_cache_to_user_id` (to_user_id) 
- `sqlite_autoindex_six_degree_path_cache_1` (from_user_id, to_user_id) UNIQUE

### social_connections

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | VARCHAR(36) | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| message | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| strength | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_social_connections_1` (id) UNIQUE

### trust_network

- **数据量**: 50 行 | **字段数**: 4 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| trusted_user_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### unlock_records

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| target_user_id | INTEGER |  | ✅ |  | |
| match_record_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### user_relations

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 6

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| from_user_id | INTEGER |  | ✅ |  | |
| to_user_id | INTEGER |  | ✅ |  | |
| relation_type | VARCHAR(20) |  | ✅ |  | |
| label | VARCHAR(100) |  |  |  | |
| trust_score | FLOAT |  | ✅ |  | |
| interaction_count | INTEGER |  | ✅ |  | |
| last_interaction_at | DATETIME |  |  |  | |
| bidirectional | BOOLEAN |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| source | VARCHAR(30) |  |  |  | |
| source_detail | VARCHAR(200) |  |  |  | |
| version | BIGINT |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |
| deleted_at | DATETIME |  |  |  | |
| is_deleted | BOOLEAN |  |  |  | |
| organization_id | INTEGER |  |  |  | |

**索引**:
- `idx_user_relation_active` (from_user_id, is_active, trust_score) 
- `ix_user_relations_from_user_id` (from_user_id) 
- `ix_user_relations_id` (id) 
- `ix_user_relations_to_user_id` (to_user_id) 
- `idx_user_relation_to` (to_user_id, is_active) 
- `sqlite_autoindex_user_relations_1` (from_user_id, to_user_id) UNIQUE

---

## D.人脉与CRM

### contacts

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| phone_hash | VARCHAR(64) |  | ✅ |  | |
| phone_enc | TEXT |  | ✅ |  | |
| phone_last4 | VARCHAR(4) |  | ✅ |  | |
| company | VARCHAR(128) |  | ✅ |  | |
| position | VARCHAR(128) |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| is_matched | SMALLINT |  | ✅ |  | |
| matched_user_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| deleted_at | DATETIME |  |  |  | |

**索引**:
- `ix_contacts_user_id` (user_id) 

### crm_activities

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| deal_id | INTEGER |  |  |  | |
| activity_type | VARCHAR(16) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| source_model | VARCHAR(32) |  |  |  | |
| source_record_id | INTEGER |  |  |  | |
| activity_date | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_activities_owner_id` (owner_id) 
- `ix_crm_activities_contact_id` (contact_id) 

### crm_campaign_recipients

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| campaign_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| email | VARCHAR(128) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| tracking_token | VARCHAR(64) |  | ✅ |  | |
| sent | BOOLEAN |  | ✅ |  | |
| sent_at | DATETIME |  |  |  | |
| send_error | TEXT |  | ✅ |  | |
| opened | BOOLEAN |  | ✅ |  | |
| opened_at | DATETIME |  |  |  | |
| unsubscribed | BOOLEAN |  | ✅ |  | |
| unsubscribed_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_campaign_recipients_tracking_token` (tracking_token) UNIQUE
- `ix_crm_campaign_recipients_campaign_id` (campaign_id) 

### crm_campaigns

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(256) |  | ✅ |  | |
| subject | VARCHAR(512) |  | ✅ |  | |
| template_name | VARCHAR(64) |  | ✅ |  | |
| template_params | TEXT |  | ✅ |  | |
| target_filter | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| total_recipients | INTEGER |  | ✅ |  | |
| sent_count | INTEGER |  | ✅ |  | |
| opened_count | INTEGER |  | ✅ |  | |
| unsubscribed_count | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_campaigns_owner_id` (owner_id) 

### crm_contacts

- **数据量**: 0 行 | **字段数**: 20 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| phone | VARCHAR(32) |  | ✅ |  | |
| email | VARCHAR(128) |  | ✅ |  | |
| company | VARCHAR(256) |  | ✅ |  | |
| title | VARCHAR(128) |  | ✅ |  | |
| department | VARCHAR(128) |  | ✅ |  | |
| avatar | VARCHAR(512) |  | ✅ |  | |
| intro | TEXT |  | ✅ |  | |
| source | VARCHAR(16) |  | ✅ |  | |
| source_record_id | INTEGER |  |  |  | |
| tags | TEXT |  | ✅ |  | |
| pipeline_stage_id | INTEGER |  |  |  | |
| deal_value | NUMERIC(12, 2) |  |  |  | |
| deal_currency | VARCHAR(8) |  | ✅ |  | |
| last_contacted_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_contacts_user_id` (user_id) 
- `ix_crm_contacts_owner_id` (owner_id) 

### crm_deals

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| pipeline_stage_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| value | NUMERIC(12, 2) |  | ✅ |  | |
| currency | VARCHAR(8) |  | ✅ |  | |
| probability | FLOAT |  | ✅ |  | |
| expected_close_date | DATETIME |  |  |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| lost_reason | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_deals_contact_id` (contact_id) 
- `ix_crm_deals_owner_id` (owner_id) 

### crm_documents

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  |  |  | |
| deal_id | INTEGER |  |  |  | |
| doc_type | VARCHAR(16) |  | ✅ |  | |
| template_name | VARCHAR(64) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| doc_number | VARCHAR(32) |  | ✅ |  | |
| content_html | TEXT |  | ✅ |  | |
| content_data | JSON |  | ✅ |  | |
| total_amount | FLOAT |  | ✅ |  | |
| currency | VARCHAR(8) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_documents_owner_id` (owner_id) 

### crm_form_submission_logs

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| form_id | INTEGER |  | ✅ |  | |
| submitter_ip | VARCHAR(45) |  |  |  | |
| submitter_ua | TEXT |  |  |  | |
| payload | TEXT |  |  |  | |
| contact_id | INTEGER |  |  |  | |
| honeypot_triggered | BOOLEAN |  |  |  | |
| success | BOOLEAN |  |  |  | |
| error_message | TEXT |  |  |  | |
| created_at | DATETIME |  |  | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_form_submission_logs_form_id` (form_id) 

### crm_forms

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| title | VARCHAR(256) |  |  |  | |
| description | TEXT |  |  |  | |
| fields | TEXT |  | ✅ |  | |
| submit_action | VARCHAR(32) |  |  |  | |
| redirect_url | VARCHAR(512) |  |  |  | |
| success_message | VARCHAR(256) |  |  |  | |
| enable_honeypot | BOOLEAN |  |  |  | |
| enable_rate_limit | BOOLEAN |  |  |  | |
| auto_tags | TEXT |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| submission_count | INTEGER |  |  |  | |
| embed_theme | VARCHAR(32) |  |  |  | |
| embed_primary_color | VARCHAR(16) |  |  |  | |
| created_at | DATETIME |  |  | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  |  | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_forms_owner_id` (owner_id) 

### crm_notes

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| contact_id | INTEGER |  |  |  | |
| deal_id | INTEGER |  |  |  | |
| content | TEXT |  | ✅ |  | |
| is_pinned | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_notes_owner_id` (owner_id) 

### crm_pipeline_stages

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| color | VARCHAR(16) |  | ✅ |  | |
| is_default | BOOLEAN |  | ✅ |  | |
| is_closed | BOOLEAN |  | ✅ |  | |
| win_probability | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_pipeline_stages_user_id` (user_id) 

### crm_workflow_logs

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| rule_id | INTEGER |  | ✅ |  | |
| rule_name | VARCHAR(128) |  | ✅ |  | |
| trigger_event | VARCHAR(32) |  | ✅ |  | |
| context_snapshot | TEXT |  | ✅ |  | |
| action_results | TEXT |  | ✅ |  | |
| success | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_workflow_logs_owner_id` (owner_id) 

### crm_workflow_rules

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| trigger_event | VARCHAR(32) |  | ✅ |  | |
| conditions | TEXT |  | ✅ |  | |
| actions | TEXT |  | ✅ |  | |
| enabled | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_crm_workflow_rules_owner_id` (owner_id) 

### customer_journey_stages

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| contact_id | INTEGER |  | ✅ |  | |
| pipeline_id | INTEGER |  |  |  | |
| stage | VARCHAR(20) |  | ✅ |  | |
| entered_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| duration_days | INTEGER |  | ✅ |  | |
| actions_taken | TEXT |  | ✅ |  | |
| score | FLOAT |  | ✅ |  | |
| next_action | VARCHAR(256) |  | ✅ |  | |

**索引**:
- `ix_customer_journey_stages_contact_id` (contact_id) 

### import_history ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_import_history_id` (id) 

---

## E.社群与组织

### approval_requests

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| requester_id | INTEGER |  | ✅ |  | |
| action | VARCHAR(7) |  | ✅ |  | |
| target_user_id | INTEGER |  |  |  | |
| reason | TEXT |  |  |  | |
| status | VARCHAR(8) |  | ✅ |  | |
| reviewer_id | INTEGER |  |  |  | |
| reject_reason | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| reviewed_at | DATETIME |  |  |  | |

### messages

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| sender_id | INTEGER |  | ✅ |  | |
| receiver_id | INTEGER |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| is_read | BOOLEAN |  | ✅ |  | |
| conversation_id | VARCHAR(36) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_messages_created_at` (created_at) 
- `ix_messages_sender_id` (sender_id) 
- `ix_messages_conversation_id` (conversation_id) 
- `ix_messages_is_read` (is_read) 
- `ix_messages_receiver_id` (receiver_id) 

### organization_invites

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| org_id | INTEGER |  | ✅ |  | |
| email | VARCHAR(255) |  | ✅ |  | |
| token | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_organization_invites_id` (id) 
- `ix_organization_invites_token` (token) UNIQUE

### organization_members

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| org_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(20) |  | ✅ |  | |
| joined_at | DATETIME |  |  |  | |

**索引**:
- `ix_organization_members_id` (id) 

### organizations

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(200) |  | ✅ |  | |
| slug | VARCHAR(100) |  | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_organizations_slug` (slug) UNIQUE
- `ix_organizations_id` (id) 

### platform_members

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| platform_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(20) |  | ✅ |  | |
| joined_at | INTEGER |  | ✅ |  | |

**索引**:
- `sqlite_autoindex_platform_members_1` (platform_id, user_id) UNIQUE

### platform_opportunities

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| platform_id | INTEGER |  | ✅ |  | |
| creator_id | INTEGER |  | ✅ |  | |
| title | VARCHAR(200) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| industry | VARCHAR(50) |  | ✅ |  | |
| city | VARCHAR(50) |  | ✅ |  | |
| budget | INTEGER |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| created_at | INTEGER |  | ✅ |  | |

### platforms

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| platform_no | VARCHAR(32) |  |  |  | |
| creator_id | INTEGER |  | ✅ |  | |
| annual_fee | FLOAT |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| province | VARCHAR(32) |  |  |  | |
| city | VARCHAR(32) |  |  |  | |
| district | VARCHAR(32) |  |  |  | |
| contact_name | VARCHAR(64) |  |  |  | |
| phone | VARCHAR(20) |  |  |  | |
| industries | TEXT |  |  |  | |

**索引**:
- `sqlite_autoindex_platforms_1` (platform_no) UNIQUE

### resource_platforms

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(100) |  | ✅ |  | |
| platform_no | VARCHAR(50) |  |  |  | |
| creator_id | INTEGER |  | ✅ |  | |
| annual_fee | INTEGER |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| member_limit | INTEGER |  | ✅ |  | |
| visibility | VARCHAR(20) |  | ✅ |  | |
| created_at | INTEGER |  | ✅ |  | |
| updated_at | INTEGER |  | ✅ |  | |

**索引**:
- `sqlite_autoindex_resource_platforms_1` (platform_no) UNIQUE

### team_invites

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| inviter_id | INTEGER |  | ✅ |  | |
| invitee_email | VARCHAR(256) |  | ✅ |  | |
| invitee_phone | VARCHAR(20) |  | ✅ |  | |
| invitee_id | INTEGER |  |  |  | |
| role | VARCHAR(6) |  | ✅ |  | |
| status | VARCHAR(8) |  | ✅ |  | |
| token | VARCHAR(128) |  | ✅ |  | |
| message | TEXT |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_team_invites_1` (token) UNIQUE

### team_members

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| team_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role | VARCHAR(6) |  | ✅ |  | |
| title_in_team | VARCHAR(128) |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| joined_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| invited_by | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### teams

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| slug | VARCHAR(64) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| logo | VARCHAR(256) |  | ✅ |  | |
| website | VARCHAR(256) |  | ✅ |  | |
| industry | VARCHAR(64) |  | ✅ |  | |
| size | VARCHAR(16) |  | ✅ |  | |
| owner_id | INTEGER |  | ✅ |  | |
| max_members | INTEGER |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_teams_1` (slug) UNIQUE

---

## F.支付与商业

### contract ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_contract_id` (id) 

### deal ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_deal_id` (id) 

### deal_activity ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_deal_activity_id` (id) 

### email_campaigns

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(256) |  | ✅ |  | |
| subject | VARCHAR(512) |  | ✅ |  | |
| content_template | TEXT |  | ✅ |  | |
| target_segment | TEXT |  | ✅ |  | |
| scheduled_at | DATETIME |  |  |  | |
| sent_count | INTEGER |  | ✅ |  | |
| open_count | INTEGER |  | ✅ |  | |
| click_count | INTEGER |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### enterprise_subscriptions

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| company_name | VARCHAR(128) |  | ✅ |  | |
| seats | INTEGER |  | ✅ |  | |
| tier | VARCHAR(32) |  | ✅ |  | |
| start_date | DATETIME |  | ✅ |  | |
| end_date | DATETIME |  | ✅ |  | |
| auto_renew | BOOLEAN |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| features | JSON |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### escrow_deals

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| buyer_id | INTEGER |  | ✅ |  | |
| seller_id | INTEGER |  | ✅ |  | |
| amount | FLOAT |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| title | VARCHAR(255) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_deals_id` (id) 
- `ix_escrow_deals_seller_id` (seller_id) 
- `ix_escrow_deals_status` (status) 
- `ix_escrow_deals_buyer_id` (buyer_id) 

### escrow_disputes

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| deal_id | INTEGER |  | ✅ |  | |
| initiator_id | INTEGER |  | ✅ |  | |
| reason | VARCHAR(500) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| evidence | TEXT |  |  |  | |
| resolution | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |
| resolved_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_disputes_deal_id` (deal_id) 
- `ix_escrow_disputes_id` (id) 

### escrow_milestones

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| deal_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(200) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| due_date | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |

**索引**:
- `ix_escrow_milestones_deal_id` (deal_id) 
- `ix_escrow_milestones_id` (id) 

### invoices

- **数据量**: 0 行 | **字段数**: 17 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| invoice_no | VARCHAR(32) |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| amount | FLOAT |  | ✅ |  | |
| tax_rate | FLOAT |  | ✅ |  | |
| tax_amount | FLOAT |  | ✅ |  | |
| total_amount | FLOAT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| order_no | VARCHAR(32) |  | ✅ |  | |
| buyer_name | VARCHAR(128) |  | ✅ |  | |
| buyer_tax_id | VARCHAR(32) |  | ✅ |  | |
| seller_name | VARCHAR(128) |  | ✅ |  | |
| seller_tax_id | VARCHAR(32) |  | ✅ |  | |
| items | JSON |  | ✅ |  | |
| notes | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_invoices_1` (invoice_no) UNIQUE

### membership_order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_membership_order_id` (id) 

### order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_order_id` (id) 

### payment_orders

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| order_no | VARCHAR(32) |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| membership_tier | VARCHAR(16) |  | ✅ |  | |
| channel | VARCHAR(16) |  | ✅ |  | |
| channel_order_no | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| total_cents | INTEGER |  | ✅ |  | |
| paid_at | DATETIME |  |  |  | |
| raw_callback | VARCHAR(2048) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_payment_orders_1` (order_no) UNIQUE

### payment_transaction ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_payment_transaction_id` (id) 

### private_board_order ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_private_board_order_id` (id) 

### product ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_product_id` (id) 

### subscription ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_subscription_id` (id) 

### trial_records

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 0

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| subscription_id | INTEGER |  | ✅ |  | |
| trial_tier | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| started_at | DATETIME |  | ✅ |  | |
| expires_at | DATETIME |  | ✅ |  | |
| converted_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

### usage_counters

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| feature | VARCHAR(32) |  | ✅ |  | |
| period | VARCHAR(16) |  | ✅ |  | |
| used_count | INTEGER |  | ✅ |  | |
| limit_count | INTEGER |  | ✅ |  | |
| reset_at | DATETIME |  |  |  | |
| model_type | VARCHAR(16) |  | ✅ |  | |
| model_name | VARCHAR(64) |  | ✅ |  | |
| token_type | VARCHAR(16) |  | ✅ |  | |
| prompt_tokens | INTEGER |  | ✅ |  | |
| completion_tokens | INTEGER |  | ✅ |  | |
| total_tokens | INTEGER |  | ✅ |  | |
| token_cost | FLOAT |  | ✅ |  | |
| external_cost | FLOAT |  | ✅ |  | |
| markup_rate | FLOAT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_usage_counters_user_id` (user_id) 
- `sqlite_autoindex_usage_counters_1` (user_id, feature, period) UNIQUE

### wallet ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_wallet_id` (id) 

### wallet_transaction ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_wallet_transaction_id` (id) 

### withdrawal ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_withdrawal_id` (id) 

---

## G.权限RBAC与审计

### analytics_events

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| session_id | VARCHAR(64) |  |  |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| properties | JSON |  |  |  | |
| page_url | VARCHAR(512) |  |  |  | |
| ip_address | VARCHAR(45) |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_analytics_events_session_id` (session_id) 
- `ix_analytics_events_created_at` (created_at) 
- `ix_analytics_events_event_type` (event_type) 
- `ix_analytics_events_user_id` (user_id) 

### audit_logs

- **数据量**: 2608 行 | **字段数**: 8 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| action | VARCHAR(32) |  | ✅ |  | |
| resource | VARCHAR(128) |  | ✅ |  | |
| detail | TEXT |  |  |  | |
| ip | VARCHAR(45) |  | ✅ |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| timestamp | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_audit_user_action` (user_id, timestamp) 
- `idx_audit_user_id` (user_id) 
- `idx_audit_action` (action) 
- `idx_audit_timestamp` (timestamp) 

### error_logs

- **数据量**: 0 行 | **字段数**: 11 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| msg | TEXT |  | ✅ |  | |
| url | VARCHAR(1024) |  |  |  | |
| line | INTEGER |  |  |  | |
| col | INTEGER |  |  |  | |
| stack | TEXT |  |  |  | |
| page | VARCHAR(256) |  |  |  | |
| user_id | INTEGER |  |  |  | |
| user_agent | VARCHAR(512) |  |  |  | |
| ip | VARCHAR(45) |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_error_log_page` (page) 
- `idx_error_log_user_id` (user_id) 
- `idx_error_log_created_at` (created_at) 

### funnel_definitions

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| funnel_name | VARCHAR(32) |  | ✅ |  | |
| step_name | VARCHAR(32) |  | ✅ |  | |
| step_order | INTEGER |  | ✅ |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| time_limit_minutes | INTEGER |  | ✅ |  | |

**索引**:
- `ix_funnel_definitions_funnel_name` (funnel_name) 

### metrics_snapshot ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_metrics_snapshot_id` (id) 

### rate_limit_record ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_rate_limit_record_id` (id) 

### rbac_role_permissions

- **数据量**: 0 行 | **字段数**: 4 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| role_id | INTEGER |  | ✅ |  | |
| permission_key | VARCHAR(64) |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_role_permissions_1` (role_id, permission_key) UNIQUE

### rbac_roles

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| name | VARCHAR(32) |  | ✅ |  | |
| display_name | VARCHAR(64) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| is_system | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_roles_1` (name) UNIQUE

### rbac_user_roles

- **数据量**: 0 行 | **字段数**: 5 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| role_id | INTEGER |  | ✅ |  | |
| granted_by | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `sqlite_autoindex_rbac_user_roles_1` (user_id, role_id) UNIQUE

### retention_cohorts

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| cohort_date | DATETIME |  | ✅ |  | |
| day_offset | INTEGER |  | ✅ |  | |
| user_count | INTEGER |  | ✅ |  | |
| active_count | INTEGER |  | ✅ |  | |
| retention_rate | INTEGER |  | ✅ |  | |

**索引**:
- `ix_retention_cohorts_cohort_date` (cohort_date) 

---

## H.AI与智能引擎

### accuracy_baselines

- **数据量**: 0 行 | **字段数**: 23 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| accuracy_threshold | FLOAT |  | ✅ |  | |
| pass_immediately | FLOAT |  |  |  | |
| warn_threshold | FLOAT |  |  |  | |
| quality_baseline_id | VARCHAR(64) |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| calibration_type | VARCHAR(32) |  |  |  | |
| calibration_id | VARCHAR(64) |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| is_archived | BOOLEAN |  |  |  | |
| meta_data | JSON |  |  |  | |
| effective_from | DATETIME |  | ✅ |  | |
| effective_until | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_accuracy_baseline_effective` (effective_from) 
- `ix_accuracy_baselines_agent_version` (agent_version) 
- `ix_accuracy_baselines_baseline_id` (baseline_id) UNIQUE
- `idx_accuracy_baseline_version` (agent_version) 
- `idx_accuracy_baseline_active` (is_active) 

### accuracy_calibration_records

- **数据量**: 0 行 | **字段数**: 24 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| calibration_id | VARCHAR(64) |  | ✅ |  | |
| calibration_type | VARCHAR(32) |  | ✅ |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| old_baseline_id | VARCHAR(64) |  |  |  | |
| old_accuracy_threshold | FLOAT |  |  |  | |
| new_baseline_id | VARCHAR(64) |  |  |  | |
| new_accuracy_threshold | FLOAT |  |  |  | |
| new_pass_immediately | FLOAT |  |  |  | |
| new_warn_threshold | FLOAT |  |  |  | |
| delta | FLOAT |  |  |  | |
| delta_percent | FLOAT |  |  |  | |
| quality_baseline_id | VARCHAR(64) |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| details | JSON |  |  |  | |
| error_message | TEXT |  |  |  | |
| notification_sent | BOOLEAN |  |  |  | |
| notification_channels | JSON |  |  |  | |
| meta_data | JSON |  |  |  | |
| calibrated_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_accuracy_calibration_records_calibration_id` (calibration_id) UNIQUE
- `idx_accuracy_calib_status` (status) 
- `idx_accuracy_calib_time` (calibrated_at) 
- `idx_accuracy_calib_type` (calibration_type) 

### accuracy_check_records

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| check_id | VARCHAR(64) |  | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| baseline_threshold | FLOAT |  | ✅ |  | |
| baseline_name | VARCHAR(128) |  |  |  | |
| current_accuracy | FLOAT |  | ✅ |  | |
| current_sample_count | INTEGER |  |  |  | |
| current_passing_count | INTEGER |  |  |  | |
| deviation | FLOAT |  |  |  | |
| deviation_percent | FLOAT |  |  |  | |
| decision | VARCHAR(32) |  | ✅ |  | |
| passed | BOOLEAN |  | ✅ |  | |
| blocked | BOOLEAN |  |  |  | |
| quality_avg_total | FLOAT |  |  |  | |
| quality_baseline_total | FLOAT |  |  |  | |
| block_reason | TEXT |  |  |  | |
| block_details | JSON |  |  |  | |
| ci_pipeline_id | VARCHAR(128) |  |  |  | |
| ci_build_number | VARCHAR(64) |  |  |  | |
| ci_commit_sha | VARCHAR(64) |  |  |  | |
| ci_branch | VARCHAR(128) |  |  |  | |
| meta_data | JSON |  |  |  | |
| checked_at | DATETIME |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_accuracy_check_source` (source) 
- `ix_accuracy_check_records_check_id` (check_id) UNIQUE
- `idx_accuracy_check_time` (checked_at) 
- `idx_accuracy_check_decision` (decision) 
- `idx_accuracy_check_baseline` (baseline_id) 

### accuracy_gate_configs

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| gate_config_id | VARCHAR(64) |  | ✅ |  | |
| enabled | BOOLEAN |  |  |  | |
| ci_block_enabled | BOOLEAN |  |  |  | |
| default_accuracy_threshold | FLOAT |  |  |  | |
| default_pass_immediately | FLOAT |  |  |  | |
| default_warn_threshold | FLOAT |  |  |  | |
| ci_block_on_warn | BOOLEAN |  |  |  | |
| ci_required_samples | INTEGER |  |  |  | |
| ci_auto_calibrate_on_degradation | BOOLEAN |  |  |  | |
| auto_calibrate | BOOLEAN |  |  |  | |
| monthly_calibration_day | INTEGER |  |  |  | |
| quarterly_calibration_month | INTEGER |  |  |  | |
| notify_on_calibration | BOOLEAN |  |  |  | |
| notification_channels | JSON |  |  |  | |
| meta_data | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_accuracy_gate_configs_gate_config_id` (gate_config_id) UNIQUE

### circuit_breaker_state

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_circuit_breaker_state_id` (id) 

### gaia_evolution_events

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| event_source | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| metadata | JSON |  |  |  | |
| reference_type | VARCHAR(32) |  |  |  | |
| reference_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_gaia_evolution_events_created_at` (created_at) 
- `ix_gaia_evolution_events_event_type` (event_type) 
- `idx_gaia_event_ref` (reference_type, reference_id) 
- `idx_gaia_event_type_time` (event_type, created_at) 

### gaia_knowledge

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| source | VARCHAR(32) |  | ✅ |  | |
| source_id | VARCHAR(64) |  |  |  | |
| knowledge_type | VARCHAR(32) |  | ✅ |  | |
| title | VARCHAR(256) |  | ✅ |  | |
| content | TEXT |  | ✅ |  | |
| tags | JSON |  |  |  | |
| confidence | FLOAT |  | ✅ |  | |
| impact_score | FLOAT |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| vector_embedded | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_knowledge_active` (is_active, created_at) 
- `idx_gaia_knowledge_source` (source, source_id) 
- `ix_gaia_knowledge_knowledge_type` (knowledge_type) 
- `ix_gaia_knowledge_source` (source) 
- `idx_gaia_knowledge_type` (knowledge_type, confidence) 

### gaia_model_weights

- **数据量**: 0 行 | **字段数**: 9 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| module | VARCHAR(64) |  | ✅ |  | |
| weights | JSON |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| training_run_id | INTEGER |  |  |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_weights_module_active` (module, is_active, version) 
- `ix_gaia_model_weights_module` (module) 

### gaia_training_runs

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| trigger | VARCHAR(32) |  | ✅ |  | |
| knowledge_count | INTEGER |  | ✅ |  | |
| feedback_count | INTEGER |  | ✅ |  | |
| weights_count | INTEGER |  | ✅ |  | |
| vector_index_size | INTEGER |  | ✅ |  | |
| duration_ms | INTEGER |  | ✅ |  | |
| metrics | JSON |  |  |  | |
| error_message | TEXT |  |  |  | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `idx_gaia_training_status` (status, created_at) 
- `ix_gaia_training_runs_status` (status) 

### knowledge_models

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| model_id | VARCHAR(32) |  | ✅ |  | |
| category | VARCHAR(32) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| source | VARCHAR(64) |  | ✅ |  | |
| source_ref | VARCHAR(256) |  |  |  | |
| content | TEXT |  | ✅ |  | |
| tags | JSON |  |  |  | |
| confidence | FLOAT |  | ✅ |  | |
| version | VARCHAR(16) |  | ✅ |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| vector_embedded | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_knowledge_models_category` (category) 
- `idx_km_category` (category, confidence) 
- `idx_km_model_id` (model_id) 
- `ix_knowledge_models_model_id` (model_id) UNIQUE
- `idx_km_active` (is_active, created_at) 

### prompt_templates

- **数据量**: 0 行 | **字段数**: 13 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | VARCHAR(64) | ✅ | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| category | VARCHAR(18) |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| description | VARCHAR(512) |  | ✅ |  | |
| system_prompt | TEXT |  | ✅ |  | |
| user_prompt_template | TEXT |  | ✅ |  | |
| parameters_schema | JSON |  |  |  | |
| output_schema | JSON |  |  |  | |
| tags | JSON |  |  |  | |
| is_active | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_prompt_category` (category) 
- `idx_prompt_active` (is_active) 
- `sqlite_autoindex_prompt_templates_1` (id) UNIQUE

### quality_baselines

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| baseline_id | VARCHAR(64) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| canary_deployment_id | VARCHAR(64) |  |  |  | |
| avg_usefulness | FLOAT |  |  |  | |
| avg_accuracy | FLOAT |  |  |  | |
| avg_completeness | FLOAT |  |  |  | |
| avg_coherence | FLOAT |  |  |  | |
| avg_harmlessness | FLOAT |  |  |  | |
| avg_total | FLOAT |  |  |  | |
| sample_count | INTEGER |  |  |  | |
| passing_count | INTEGER |  |  |  | |
| passing_rate | FLOAT |  |  |  | |
| passing_threshold | FLOAT |  |  |  | |
| score_distribution | JSON |  |  |  | |
| tags | JSON |  |  |  | |
| sample_meta | JSON |  |  |  | |
| is_active | BOOLEAN |  |  |  | |
| is_archived | BOOLEAN |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |
| evaluated_at | DATETIME |  |  |  | |

**索引**:
- `idx_quality_baseline_version` (agent_version, model_name) 
- `idx_quality_baseline_active` (is_active) 
- `ix_quality_baselines_agent_version` (agent_version) 
- `ix_quality_baselines_baseline_id` (baseline_id) UNIQUE
- `ix_quality_baselines_model_name` (model_name) 

### quality_eval_jobs

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| job_id | VARCHAR(64) |  | ✅ |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| eval_method | VARCHAR(32) |  |  |  | |
| sample_ids | JSON |  |  |  | |
| model_config | JSON |  |  |  | |
| total_samples | INTEGER |  |  |  | |
| completed_samples | INTEGER |  |  |  | |
| failed_samples | INTEGER |  |  |  | |
| baseline_id | VARCHAR(64) |  |  |  | |
| summary | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |

**索引**:
- `ix_quality_eval_jobs_job_id` (job_id) UNIQUE

### quality_samples

- **数据量**: 0 行 | **字段数**: 25 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| sample_id | VARCHAR(64) |  | ✅ |  | |
| input_text | TEXT |  | ✅ |  | |
| agent_output | TEXT |  | ✅ |  | |
| expected_output | TEXT |  |  |  | |
| category | VARCHAR(64) |  |  |  | |
| tags | JSON |  |  |  | |
| sample_meta | JSON |  |  |  | |
| canary_deployment_id | VARCHAR(64) |  |  |  | |
| agent_version | VARCHAR(64) |  |  |  | |
| model_name | VARCHAR(128) |  |  |  | |
| status | VARCHAR(32) |  | ✅ |  | |
| eval_method | VARCHAR(32) |  | ✅ |  | |
| score_usefulness | FLOAT |  |  |  | |
| score_accuracy | FLOAT |  |  |  | |
| score_completeness | FLOAT |  |  |  | |
| score_coherence | FLOAT |  |  |  | |
| score_harmlessness | FLOAT |  |  |  | |
| score_total | FLOAT |  |  |  | |
| eval_detail | JSON |  |  |  | |
| eval_log | TEXT |  |  |  | |
| error_message | TEXT |  |  |  | |
| evaluated_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |
| updated_at | DATETIME |  | ✅ |  | |

**索引**:
- `idx_quality_sample_category` (category) 
- `idx_quality_sample_status` (status) 
- `idx_quality_sample_created` (created_at) 
- `ix_quality_samples_category` (category) 
- `ix_quality_samples_sample_id` (sample_id) UNIQUE

### token_budget_alert

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| alert_id | VARCHAR(64) |  | ✅ |  | |
| rule_name | VARCHAR(128) |  | ✅ |  | |
| alert_level | VARCHAR(16) |  | ✅ |  | |
| current_usage | INTEGER |  |  |  | |
| token_limit | INTEGER |  |  |  | |
| usage_ratio | FLOAT |  |  |  | |
| threshold | FLOAT |  |  |  | |
| agent_name | VARCHAR(128) |  |  |  | |
| user_id | INTEGER |  |  |  | |
| message | TEXT |  |  |  | |
| detail | TEXT |  |  |  | |
| is_resolved | BOOLEAN |  |  |  | |
| resolved_at | DATETIME |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_token_budget_alert_rule_name` (rule_name) 
- `ix_token_budget_alert_alert_id` (alert_id) UNIQUE
- `ix_token_budget_alert_created_at` (created_at) 
- `ix_token_budget_alert_id` (id) 

### token_consumption_record

- **数据量**: 0 行 | **字段数**: 19 | **索引数**: 7

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| record_id | VARCHAR(64) |  | ✅ |  | |
| agent_name | VARCHAR(128) |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| session_id | VARCHAR(64) |  |  |  | |
| rule_name | VARCHAR(128) |  |  |  | |
| prompt_tokens | INTEGER |  |  |  | |
| completion_tokens | INTEGER |  |  |  | |
| total_tokens | INTEGER |  |  |  | |
| is_truncated | BOOLEAN |  |  |  | |
| is_downgraded | BOOLEAN |  |  |  | |
| degrade_strategy | VARCHAR(32) |  |  |  | |
| estimated_cost | FLOAT |  |  |  | |
| cost_per_token | FLOAT |  |  |  | |
| model_name | VARCHAR(64) |  |  |  | |
| operation | VARCHAR(64) |  |  |  | |
| status | VARCHAR(32) |  |  |  | |
| metadata_json | TEXT |  |  |  | |
| created_at | DATETIME |  | ✅ |  | |

**索引**:
- `ix_token_consumption_record_created_at` (created_at) 
- `ix_token_consumption_record_rule_name` (rule_name) 
- `ix_token_consumption_record_id` (id) 
- `ix_token_consumption_record_agent_name` (agent_name) 
- `ix_token_consumption_record_record_id` (record_id) UNIQUE
- `ix_token_consumption_record_session_id` (session_id) 
- `ix_token_consumption_record_user_id` (user_id) 

---

## I.平台与支撑

### ab_test_decision_logs

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| decision | VARCHAR(16) |  | ✅ |  | |
| variant_name | VARCHAR(64) |  |  |  | |
| p_value | FLOAT |  |  |  | |
| reason | TEXT |  | ✅ |  | |
| details | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_decision_logs_created_at` (created_at) 
- `ix_ab_test_decision_logs_experiment_id` (experiment_id) 

### ab_test_events

- **数据量**: 0 行 | **字段数**: 8 | **索引数**: 5

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| variant_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  |  |  | |
| visitor_id | VARCHAR(64) |  |  |  | |
| event_type | VARCHAR(32) |  | ✅ |  | |
| metadata | JSON |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_events_variant_id` (variant_id) 
- `ix_ab_test_events_experiment_id` (experiment_id) 
- `ix_ab_test_events_visitor_id` (visitor_id) 
- `ix_ab_test_events_user_id` (user_id) 
- `ix_ab_test_events_created_at` (created_at) 

### ab_test_variants

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| experiment_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(64) |  | ✅ |  | |
| description | VARCHAR(256) |  | ✅ |  | |
| sort_order | INTEGER |  | ✅ |  | |
| is_control | BOOLEAN |  | ✅ |  | |
| config | JSON |  |  |  | |
| weight | FLOAT |  | ✅ |  | |
| is_default | BOOLEAN |  | ✅ |  | |
| impressions | INTEGER |  | ✅ |  | |
| clicks | INTEGER |  | ✅ |  | |
| conversions | INTEGER |  | ✅ |  | |
| views | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_ab_test_variants_experiment_id` (experiment_id) 

### ab_tests

- **数据量**: 0 行 | **字段数**: 15 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  | ✅ |  | |
| status | VARCHAR(16) |  | ✅ |  | |
| traffic_fraction | FLOAT |  | ✅ |  | |
| min_sample_size | INTEGER |  | ✅ |  | |
| significance_level | FLOAT |  | ✅ |  | |
| metric | VARCHAR(32) |  | ✅ |  | |
| target_brochure_id | INTEGER |  |  |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| started_at | DATETIME |  |  |  | |
| completed_at | DATETIME |  |  |  | |
| cached_results | JSON |  |  |  | |

**索引**:
- `ix_ab_tests_user_id` (user_id) 
- `ix_ab_tests_target_brochure_id` (target_brochure_id) 
- `ix_ab_tests_status` (status) 

### activity ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_activity_id` (id) 

### api_usage_log ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_api_usage_log_id` (id) 

### app_store_plugin_installs

- **数据量**: 0 行 | **字段数**: 7 | **索引数**: 3

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| version_id | INTEGER |  |  |  | |
| is_active | INTEGER |  | ✅ |  | |
| installed_at | DATETIME |  |  |  | |
| uninstalled_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_installs_user_id` (user_id) 
- `ix_app_store_plugin_installs_plugin_id` (plugin_id) 
- `ix_app_store_plugin_installs_id` (id) 

### app_store_plugin_reviews

- **数据量**: 0 行 | **字段数**: 6 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| reviewer_id | INTEGER |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| comments | TEXT |  |  |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_reviews_plugin_id` (plugin_id) 
- `ix_app_store_plugin_reviews_id` (id) 

### app_store_plugin_versions

- **数据量**: 0 行 | **字段数**: 10 | **索引数**: 2

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| plugin_id | INTEGER |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| changelog | TEXT |  |  |  | |
| download_url | VARCHAR(512) |  |  |  | |
| required_api_version | VARCHAR(32) |  | ✅ |  | |
| file_size | INTEGER |  |  |  | |
| checksum | VARCHAR(128) |  |  |  | |
| is_published | INTEGER |  | ✅ |  | |
| created_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugin_versions_plugin_id` (plugin_id) 
- `ix_app_store_plugin_versions_id` (id) 

### app_store_plugins

- **数据量**: 0 行 | **字段数**: 18 | **索引数**: 4

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| developer_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| description | TEXT |  |  |  | |
| icon_url | VARCHAR(512) |  |  |  | |
| category | VARCHAR(64) |  | ✅ |  | |
| version | VARCHAR(32) |  | ✅ |  | |
| price | FLOAT |  | ✅ |  | |
| status | VARCHAR(20) |  | ✅ |  | |
| install_count | INTEGER |  | ✅ |  | |
| rating | FLOAT |  | ✅ |  | |
| rating_count | INTEGER |  | ✅ |  | |
| homepage_url | VARCHAR(512) |  |  |  | |
| documentation_url | VARCHAR(512) |  |  |  | |
| repository_url | VARCHAR(512) |  |  |  | |
| tags | VARCHAR(512) |  |  |  | |
| created_at | DATETIME |  |  |  | |
| updated_at | DATETIME |  |  |  | |

**索引**:
- `ix_app_store_plugins_developer_id` (developer_id) 
- `ix_app_store_plugins_id` (id) 
- `ix_app_store_plugins_category` (category) 
- `ix_app_store_plugins_status` (status) 

### business_need ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_business_need_id` (id) 

### contact ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_contact_id` (id) 

### enterprise ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_enterprise_id` (id) 

### enterprise_relation ⚠️占位表(仅id列,待实现)

- **数据量**: 0 行 | **字段数**: 1 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |

**索引**:
- `ix_enterprise_relation_id` (id) 

### integrations

- **数据量**: 0 行 | **字段数**: 12 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| provider | VARCHAR(32) |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| enabled | BOOLEAN |  | ✅ |  | |
| config | TEXT |  | ✅ |  | |
| last_sync_at | DATETIME |  |  |  | |
| webhook_url | VARCHAR(512) |  | ✅ |  | |
| webhook_secret | VARCHAR(128) |  | ✅ |  | |
| webhook_enabled | BOOLEAN |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_integrations_user_id` (user_id) 

### webhook_subscriptions

- **数据量**: 0 行 | **字段数**: 14 | **索引数**: 1

| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | ✅ | ✅ |  | |
| user_id | INTEGER |  | ✅ |  | |
| name | VARCHAR(128) |  | ✅ |  | |
| url | VARCHAR(512) |  | ✅ |  | |
| secret | VARCHAR(128) |  | ✅ |  | |
| events | TEXT |  | ✅ |  | |
| active | BOOLEAN |  | ✅ |  | |
| retry_count | INTEGER |  | ✅ |  | |
| timeout_seconds | INTEGER |  | ✅ |  | |
| last_triggered_at | DATETIME |  |  |  | |
| last_response_code | INTEGER |  |  |  | |
| last_error | TEXT |  | ✅ |  | |
| created_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |
| updated_at | DATETIME |  | ✅ | CURRENT_TIMESTAMP | |

**索引**:
- `ix_webhook_subscriptions_user_id` (user_id) 

---

## 附录: 全库统计

| 指标 | 数值 |
|---|---|
| 总表数 | 123 |
| 总字段数 | 1085 |
| 总索引数 | 223 |
| 有数据表数 | 8 |
| 占位表数 | 29 |
