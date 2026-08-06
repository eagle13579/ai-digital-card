# -*- coding: utf-8 -*-
"""生成数据库设计文档V1.0的表格主体(按业务域分组)"""
import sqlite3, io, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
data = json.load(open('data/_schema_dump.json', encoding='utf-8'))

# 业务域分组: 表名 -> (业务域, 业务说明)
DOMAIN = {}
def add(domain, tables):
    for t in tables:
        DOMAIN[t] = domain

add('A.用户与认证', ['users','user_consents','revoked_token','user_event','invitation_codes','tenants','api_keys','api_key_usage','sdk_apps','developer_rewards','developer_reward_balances','reward_redemptions'])
add('B.名片与画册', ['brochures','pages','business_card','nfc_cards','nfc_tap_records','visitor_logs','referral_links','user_tags'])
add('C.匹配与推荐', ['match_records','unlock_records','match_credit_log','online_matching_events','online_matching_feedback','online_matching_registrations','six_degree_path_cache','user_relations','relation_events','trust_network','connections','social_connections'])
add('D.人脉与CRM', ['contacts','import_history','crm_contacts','crm_activities','crm_deals','crm_pipeline_stages','crm_notes','crm_documents','crm_campaigns','crm_campaign_recipients','crm_forms','crm_form_submission_logs','crm_workflow_rules','crm_workflow_logs','customer_journey_stages'])
add('E.社群与组织', ['organizations','organization_members','organization_invites','teams','team_members','team_invites','approval_requests','platforms','platform_members','platform_opportunities','resource_platforms','messages'])
add('F.支付与商业', ['payment_orders','payment_transaction','order','membership_order','private_board_order','subscription','enterprise_subscriptions','trial_records','invoices','escrow_deals','escrow_milestones','escrow_disputes','wallet','wallet_transaction','withdrawal','product','contract','deal','deal_activity','email_campaigns','usage_counters'])
add('G.权限RBAC与审计', ['rbac_roles','rbac_role_permissions','rbac_user_roles','audit_logs','rate_limit_record','error_logs','analytics_events','metrics_snapshot','retention_cohorts','funnel_definitions'])
add('H.AI与智能引擎', ['gaia_knowledge','gaia_evolution_events','gaia_training_runs','gaia_model_weights','knowledge_models','quality_baselines','quality_samples','quality_eval_jobs','accuracy_baselines','accuracy_check_records','accuracy_calibration_records','accuracy_gate_configs','token_budget_alert','token_consumption_record','prompt_templates','circuit_breaker_state'])
add('I.平台与支撑', ['ab_tests','ab_test_variants','ab_test_events','ab_test_decision_logs','webhook_subscriptions','integrations','activity','api_usage_log','contact','enterprise','enterprise_relation','business_need','app_store_plugins','app_store_plugin_versions','app_store_plugin_reviews','app_store_plugin_installs'])

STUB = {'activity','api_usage_log','business_card','business_need','contact','contract','deal','deal_activity','enterprise','enterprise_relation','import_history','match_credit_log','membership_order','metrics_snapshot','online_matching_events','online_matching_feedback','online_matching_registrations','order','payment_transaction','private_board_order','product','rate_limit_record','review','revoked_token','subscription','user_event','wallet','wallet_transaction','withdrawal'}

# 生成 markdown
out = []
for domain in ['A.用户与认证','B.名片与画册','C.匹配与推荐','D.人脉与CRM','E.社群与组织','F.支付与商业','G.权限RBAC与审计','H.AI与智能引擎','I.平台与支撑']:
    tables = sorted([t for t, d in DOMAIN.items() if d == domain], key=lambda x: x)
    out.append(f'\n## {domain}\n')
    for t in tables:
        v = data[t]
        rows = v['rowcount']
        is_stub = t in STUB and len(v['columns']) <= 1
        stub_note = ' ⚠️占位表(仅id列,待实现)' if is_stub else ''
        out.append(f'### {t}{stub_note}\n')
        out.append(f'- **数据量**: {rows} 行 | **字段数**: {len(v["columns"])} | **索引数**: {len(v["indexes"])}')
        out.append('\n| 字段 | 类型 | 主键 | 非空 | 默认值 | 说明 |')
        out.append('|---|---|---|---|---|---|')
        for c in v['columns']:
            pk = '✅' if c['pk'] else ''
            nn = '✅' if c['notnull'] else ''
            dflt = str(c['default']) if c['default'] is not None else ''
            out.append(f"| {c['name']} | {c['type']} | {pk} | {nn} | {dflt} | |")
        if v['indexes']:
            out.append('\n**索引**:')
            for i in v['indexes']:
                uniq = 'UNIQUE' if i['unique'] else ''
                out.append(f"- `{i['name']}` ({', '.join(i['columns'])}) {uniq}")
        out.append('')
    out.append('---')

# 汇总统计
out.append('\n## 附录: 全库统计\n')
out.append('| 指标 | 数值 |')
out.append('|---|---|')
out.append(f'| 总表数 | {len(data)} |')
out.append(f'| 总字段数 | {sum(len(v["columns"]) for v in data.values())} |')
out.append(f'| 总索引数 | {sum(len(v["indexes"]) for v in data.values())} |')
out.append(f'| 有数据表数 | {sum(1 for v in data.values() if isinstance(v["rowcount"], int) and v["rowcount"]>0)} |')
out.append(f'| 占位表数 | {len(STUB)} |')
out.append('')

with open('data/_doc1_tables.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f'OK, {len(out)} lines written')
