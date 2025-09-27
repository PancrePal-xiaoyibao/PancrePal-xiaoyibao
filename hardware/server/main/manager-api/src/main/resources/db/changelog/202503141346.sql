-- 模型供应器表
DROP TABLE IF EXISTS `ai_model_provider`;
CREATE TABLE `ai_model_provider` (
    `id` VARCHAR(32) NOT NULL COMMENT '主键',
    `model_type` VARCHAR(20) COMMENT '模型类型(Memory/ASR/VAD/LLM/TTS)',
    `provider_code` VARCHAR(50) COMMENT '供应器类型',
    `name` VARCHAR(50) COMMENT '供应器名称',
    `fields` JSON COMMENT '供应器字段列表(JSON格式)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_provider_model_type` (`model_type`) COMMENT '创建模型类型的索引，用于快速查找特定类型下的所有供应器信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型配置表';

-- 模型配置表
DROP TABLE IF EXISTS `ai_model_config`;
CREATE TABLE `ai_model_config` (
    `id` VARCHAR(32) NOT NULL COMMENT '主键',
    `model_type` VARCHAR(20) COMMENT '模型类型(Memory/ASR/VAD/LLM/TTS)',
    `model_code` VARCHAR(50) COMMENT '模型编码(如AliLLM、DoubaoTTS)',
    `model_name` VARCHAR(50) COMMENT '模型名称',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT '是否默认配置(0否 1是)',
    `is_enabled` TINYINT(1) DEFAULT 0 COMMENT '是否启用',
    `config_json` JSON COMMENT '模型配置(JSON格式)',
    `doc_link` VARCHAR(200) COMMENT '官方文档链接',
    `remark` VARCHAR(255) COMMENT '备注',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_config_model_type` (`model_type`) COMMENT '创建模型类型的索引，用于快速查找特定类型下的所有配置信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型配置表';

-- TTS 音色表
DROP TABLE IF EXISTS `ai_tts_voice`;
CREATE TABLE `ai_tts_voice` (
    `id` VARCHAR(32) NOT NULL COMMENT '主键',
    `tts_model_id` VARCHAR(32) COMMENT '对应 TTS 模型主键',
    `name` VARCHAR(20) COMMENT '音色名称',
    `tts_voice` VARCHAR(50) COMMENT '音色编码',
    `languages` VARCHAR(50) COMMENT '语言',
    `voice_demo` VARCHAR(500) DEFAULT NULL COMMENT '音色 Demo',
    `remark` VARCHAR(255) COMMENT '备注',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT '创建 TTS 模型主键的索引，用于快速查找对应模型的音色信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS 音色表';

-- 智能体配置模板表
DROP TABLE IF EXISTS `ai_agent_template`;
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT '智能体唯一标识',
    `agent_code` VARCHAR(36) COMMENT '智能体编码',
    `agent_name` VARCHAR(64) COMMENT '智能体名称',
    `asr_model_id` VARCHAR(32) COMMENT '语音识别模型标识',
    `vad_model_id` VARCHAR(64) COMMENT '语音活动检测标识',
    `llm_model_id` VARCHAR(32) COMMENT '大语言模型标识',
    `tts_model_id` VARCHAR(32) COMMENT '语音合成模型标识',
    `tts_voice_id` VARCHAR(32) COMMENT '音色标识',
    `mem_model_id` VARCHAR(32) COMMENT '记忆模型标识',
    `intent_model_id` VARCHAR(32) COMMENT '意图模型标识',
    `system_prompt` TEXT COMMENT '角色设定参数',
    `lang_code` VARCHAR(10) COMMENT '语言编码',
    `language` VARCHAR(10) COMMENT '交互语种',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序权重',
    `creator` BIGINT COMMENT '创建者 ID',
    `created_at` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者 ID',
    `updated_at` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置模板表';

-- 智能体配置表
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT '智能体唯一标识',
    `user_id` BIGINT COMMENT '所属用户 ID',
    `agent_code` VARCHAR(36) COMMENT '智能体编码',
    `agent_name` VARCHAR(64) COMMENT '智能体名称',
    `asr_model_id` VARCHAR(32) COMMENT '语音识别模型标识',
    `vad_model_id` VARCHAR(64) COMMENT '语音活动检测标识',
    `llm_model_id` VARCHAR(32) COMMENT '大语言模型标识',
    `tts_model_id` VARCHAR(32) COMMENT '语音合成模型标识',
    `tts_voice_id` VARCHAR(32) COMMENT '音色标识',
    `mem_model_id` VARCHAR(32) COMMENT '记忆模型标识',
    `intent_model_id` VARCHAR(32) COMMENT '意图模型标识',
    `system_prompt` TEXT COMMENT '角色设定参数',
    `lang_code` VARCHAR(10) COMMENT '语言编码',
    `language` VARCHAR(10) COMMENT '交互语种',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序权重',
    `creator` BIGINT COMMENT '创建者 ID',
    `created_at` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者 ID',
    `updated_at` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_agent_user_id` (`user_id`) COMMENT '创建用户的索引，用于快速查找用户下的智能体信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置表';

-- 设备信息表
DROP TABLE IF EXISTS `ai_device`;
CREATE TABLE `ai_device` (
    `id` VARCHAR(32) NOT NULL COMMENT '设备唯一标识',
    `user_id` BIGINT COMMENT '关联用户 ID',
    `mac_address` VARCHAR(50) COMMENT 'MAC 地址',
    `last_connected_at` DATETIME COMMENT '最后连接时间',
    `auto_update` TINYINT UNSIGNED DEFAULT 0 COMMENT '自动更新开关(0 关闭/1 开启)',
    `board` VARCHAR(50) COMMENT '设备硬件型号',
    `alias` VARCHAR(64) DEFAULT NULL COMMENT '设备别名',
    `agent_id` VARCHAR(32) COMMENT '智能体 ID',
    `app_version` VARCHAR(20) COMMENT '固件版本号',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_device_created_at` (`mac_address`) COMMENT '创建mac的索引，用于快速查找设备信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备信息表';

-- 声纹识别表
DROP TABLE IF EXISTS `ai_voiceprint`;
CREATE TABLE `ai_voiceprint` (
    `id` VARCHAR(32) NOT NULL COMMENT '声纹唯一标识',
    `name` VARCHAR(64) COMMENT '声纹名称',
    `user_id` BIGINT COMMENT '用户 ID（关联用户表）',
    `agent_id` VARCHAR(32) COMMENT '关联智能体 ID',
    `agent_code` VARCHAR(36) COMMENT '关联智能体编码',
    `agent_name` VARCHAR(36) COMMENT '关联智能体名称',
    `description` VARCHAR(255) COMMENT '声纹描述',
    `embedding` LONGTEXT COMMENT '声纹特征向量（JSON 数组格式）',
    `memory` TEXT COMMENT '关联记忆数据',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT '排序权重',
    `creator` BIGINT COMMENT '创建者 ID',
    `created_at` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者 ID',
    `updated_at` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='声纹识别表';

-- 对话历史表
DROP TABLE IF EXISTS `ai_chat_history`;
CREATE TABLE `ai_chat_history` (
    `id` VARCHAR(32) NOT NULL COMMENT '对话编号',
    `user_id` BIGINT COMMENT '用户编号',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT '聊天角色',
    `device_id` VARCHAR(32) DEFAULT NULL COMMENT '设备编号',
    `message_count` INT COMMENT '信息汇总',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史表';

-- 对话信息表
DROP TABLE IF EXISTS `ai_chat_message`;
CREATE TABLE `ai_chat_message` (
    `id` VARCHAR(32) NOT NULL COMMENT '对话记录唯一标识',
    `user_id` BIGINT COMMENT '用户唯一标识',
    `chat_id` VARCHAR(64) COMMENT '对话历史 ID',
    `role` ENUM('user', 'assistant') COMMENT '角色（用户或助理）',
    `content` TEXT COMMENT '对话内容',
    `prompt_tokens` INT UNSIGNED DEFAULT 0 COMMENT '提示令牌数',
    `total_tokens` INT UNSIGNED DEFAULT 0 COMMENT '总令牌数',
    `completion_tokens` INT UNSIGNED DEFAULT 0 COMMENT '完成令牌数',
    `prompt_ms` INT UNSIGNED DEFAULT 0 COMMENT '提示耗时（毫秒）',
    `total_ms` INT UNSIGNED DEFAULT 0 COMMENT '总耗时（毫秒）',
    `completion_ms` INT UNSIGNED DEFAULT 0 COMMENT '完成耗时（毫秒）',
    `creator` BIGINT COMMENT '创建者',
    `create_date` DATETIME COMMENT '创建时间',
    `updater` BIGINT COMMENT '更新者',
    `update_date` DATETIME COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_chat_message_user_id_chat_id_role` (`user_id`, `chat_id`) COMMENT '用户 ID、聊天会话 ID 和角色的联合索引，用于快速检索对话记录',
    INDEX `idx_ai_chat_message_created_at` (`create_date`) COMMENT '创建时间的索引，用于按时间排序或检索对话记录'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话信息表';
