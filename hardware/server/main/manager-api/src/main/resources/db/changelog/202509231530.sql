-- 202509231030-xiaoxbao-integration.sql
-- 小X宝模型集成配置
-- 作者: 您的姓名 <your.email@company.com>
-- 关联任务: PROJ-456
-- 部署说明: 
--   1. 需先在智控台创建用户(用户ID: 1946554867105284097)
--   2. 部署时需替换占位符 YOUR_API_KEY

-- =============== 清理旧配置 (确保幂等性) ===============
DELETE FROM `ai_model_config` WHERE id = 'LLM_XiaoXBaoLLM';
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_LLM_XiaoXBao';

-- =============== ai_model_config 表更新 ===============
INSERT INTO `ai_model_config` (
  id, model_type, model_code, model_name, 
  is_default, is_enabled, config_json, 
  doc_link, remark, sort, 
  creator, create_date, updater, update_date
) VALUES (
  'LLM_XiaoXBaoLLM', 
  'llm', 
  'xiaoxbao', 
  '小X宝', 
  1, 
  1, 
  '{
    "type": "xiaoxbao",
    "detail": "False",
    "api_key": "YOUR_API_KEY",  -- 部署时替换
    "base_url": "https://admin.xiaoyibao.com.cn",
    "variables": {
      "k": "v",
      "k2": "v2"
    }
  }',
  '',
  '',
  0,
  1946554867105284097,
  NOW(),  -- 使用动态时间戳
  1946554867105284097,
  NOW()
);

-- =============== ai_model_provider 表更新 ===============
INSERT INTO `ai_model_provider` (
  id, model_type, provider_code, name, 
  fields, sort, 
  creator, create_date, updater, update_date
) VALUES (
  'SYSTEM_LLM_XiaoXBao',
  'LLM',
  'xiaoxbao',
  'XiaoXBao接口',
  '[
    {
      "key": "base_url",
      "type": "string",
      "label": "模型地址",
      "default": "https://admin.xiaoyibao.com.cn",
      "editing": false,
      "selected": false
    },
    {
      "key": "api_key",
      "type": "string",
      "label": "API Key",
      "default": "YOUR_API_KEY",  -- 部署时替换
      "editing": false,
      "selected": false
    },
    {
      "key": "detail",
      "type": "boolean",
      "label": "Detail",
      "default": "False",
      "editing": false,
      "selected": false
    },
    {
      "key": "variables",
      "type": "dict",
      "label": "Variables",
      "default": "{\\"k\\": \\"v\\", \\"k2\\": \\"v2\\"}",
      "editing": false,
      "selected": false
    }
  ]',
  9,
  1946554867105284097,
  NOW(),
  1946554867105284097,
  NOW()
);