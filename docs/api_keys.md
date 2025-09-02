# API Key 使用说明

## 概述

小胰宝平台支持两种认证方式：
1. **JWT令牌认证** - 适用于用户登录和API Key管理
2. **API Key认证** - 适用于长期API访问，无需担心过期和刷新

## 🔄 业务流程

### 标准API访问流程
```
用户登录 → 获取JWT令牌 → 使用JWT创建API Key → 使用API Key访问API接口
```

### 详细步骤
1. **用户登录** (`POST /api/v1/auth/login`)
   - 使用用户名和密码登录
   - 获取JWT访问令牌

2. **创建API Key** (`POST /api/v1/api-keys/`)
   - 使用JWT令牌认证
   - 设置API Key名称、描述、过期时间等
   - 获取完整的API Key

3. **使用API Key访问API**
   - 聊天接口：`POST /api/v1/chat`
   - 文件上传：`POST /api/v1/upload`
   - 在请求头中使用 `Authorization: Bearer YOUR_API_KEY`

## API Key 特性

### 🔐 安全特性
- 使用SHA-256哈希存储，即使数据库泄露也无法还原原始密钥
- 支持设置过期时间，可自动失效
- 支持权限控制，可限制API Key的访问范围
- 支持撤销功能，可立即停用而不删除

### 📊 使用统计
- 记录总调用次数
- 记录今日和本月调用次数
- 记录最后使用时间
- 支持按时间段重置计数

### 👥 权限控制
- 只有**管理员**和**高级用户**可以创建API Key
- 用户只能管理自己创建的API Key
- 管理员可以查看和管理所有API Key

## 创建API Key

### 权限要求
- 用户角色必须是 `admin` 或 `premium`
- 需要有效的JWT令牌

### 请求示例

```bash
# 1. 首先登录获取JWT令牌
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 2. 使用JWT令牌创建API Key
curl -X POST "http://localhost:8000/api/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "聊天API专用密钥",
    "description": "用于访问聊天和文件上传API的密钥",
    "expires_at": "2024-12-31T23:59:59Z",
    "permissions": ["chat", "upload"]
  }'
```

### 响应示例

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "聊天API专用密钥",
  "description": "用于访问聊天和文件上传API的密钥",
  "key_prefix": "a1b2c3d4",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-12-31T23:59:59Z",
  "last_used_at": null,
  "permissions": ["chat", "upload"],
  "is_active": true,
  "created_by": "user_id_here",
  "full_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2"
}
```

**重要**: `full_key` 字段只在创建时返回一次，请妥善保存！

## 使用API Key访问API

### 🔑 聊天接口

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "agent: fastgpt" \
  -d '{
    "message": "你好，请介绍一下胰腺癌",
    "stream": false
  }'
```

### 📁 文件上传接口

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@your_file.pdf" \
  -F "agent=fastgpt" \
  -F "created_by=your_name"
```

### 📋 获取支持的上传智能体

```bash
curl -X GET "http://localhost:8000/api/v1/upload/agents" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 认证方式说明

### 🚫 主要接口仅支持API Key
以下接口**仅支持API Key认证**，不支持JWT令牌：

- `POST /api/v1/chat` - 聊天接口
- `POST /api/v1/upload` - 文件上传接口

### 🔐 用户管理接口仅支持JWT
以下接口**仅支持JWT认证**，不支持API Key：

- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `GET /api/v1/auth/me` - 获取用户信息
- `POST /api/v1/api-keys/` - 创建API Key

## 管理API Key

### 获取我的API Key列表

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/my" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 获取API Key详情

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/{api_key_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 更新API Key

```bash
curl -X PUT "http://localhost:8000/api/v1/api-keys/{api_key_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新的名称",
    "description": "新的描述"
  }'
```

### 撤销API Key

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/{api_key_id}/revoke" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 删除API Key

```bash
curl -X DELETE "http://localhost:8000/api/v1/api-keys/{api_key_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 使用统计

### 获取使用统计

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/{api_key_id}/usage" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 统计信息说明

```json
{
  "total_calls": 150,
  "last_used_at": "2024-01-15T10:30:00Z",
  "calls_today": 25,
  "calls_this_month": 150
}
```

- `total_calls`: 总调用次数
- `last_used_at`: 最后使用时间
- `calls_today`: 今日调用次数（每日0点重置）
- `calls_this_month`: 本月调用次数（每月1号重置）

## 管理员功能

### 查看所有API Key

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys/admin/all" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 清理过期API Key

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys/admin/cleanup" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

## 最佳实践

### 🔒 安全建议
1. **立即保存**: 创建API Key后立即保存完整密钥
2. **定期轮换**: 建议每3-6个月轮换一次API Key
3. **最小权限**: 只授予必要的权限
4. **监控使用**: 定期检查使用统计，发现异常及时处理
5. **安全存储**: 不要在代码中硬编码API Key

### 📝 命名规范
- 使用描述性的名称，如：`生产环境聊天API`、`测试环境上传API`
- 包含环境标识，如：`prod-`、`test-`、`dev-`
- 包含用途说明，如：`-chat`、`-upload`、`-admin`

### ⏰ 过期时间设置
- **短期**: 1-30天，适用于临时访问
- **中期**: 1-12个月，适用于常规集成
- **长期**: 1年以上，适用于稳定系统集成
- **永不过期**: 谨慎使用，需要定期手动检查

### 🔄 工作流程建议
1. **开发阶段**: 使用短期API Key进行测试
2. **集成阶段**: 使用中期API Key进行系统集成
3. **生产阶段**: 使用长期API Key，并定期轮换
4. **监控阶段**: 定期检查使用统计和异常情况

## 错误处理

### 常见错误码

| 状态码 | 错误说明 | 解决方案 |
|--------|----------|----------|
| 401 | 无效的API Key | 检查API Key是否正确，是否已过期或被撤销 |
| 403 | 权限不足 | 检查用户角色是否满足要求 |
| 404 | API Key不存在 | 检查API Key ID是否正确 |
| 400 | 请求参数错误 | 检查请求体格式和必填字段 |
| 400 | 此操作需要API Key认证 | 使用API Key而不是JWT令牌访问该接口 |

### 错误响应示例

```json
{
  "detail": "权限不足，只有管理员和高级用户才能创建API Key"
}
```

```json
{
  "detail": "此操作需要API Key认证"
}
```

## 测试

### 运行测试

```bash
# 启动服务
make run

# 在另一个终端运行测试
make test-api-keys
```

### 测试覆盖
- ✅ 权限控制测试
- ✅ 创建、读取、更新、删除测试
- ✅ 认证集成测试
- ✅ 使用统计测试
- ✅ 安全控制测试
- ✅ API接口认证测试

## 技术实现

### 数据库结构

#### api_keys 集合
```json
{
  "_id": "ObjectId",
  "name": "API Key名称",
  "description": "描述信息",
  "key_hash": "SHA-256哈希值",
  "key_prefix": "密钥前缀",
  "created_at": "创建时间",
  "expires_at": "过期时间",
  "last_used_at": "最后使用时间",
  "permissions": ["权限列表"],
  "is_active": true,
  "created_by": "创建者用户ID"
}
```

#### api_key_usage 集合
```json
{
  "api_key_id": "API Key ID",
  "total_calls": 0,
  "last_used_at": "最后使用时间",
  "calls_today": 0,
  "calls_this_month": 0,
  "last_reset_date": "最后重置日期",
  "last_reset_month": "最后重置月份"
}
```

### 安全机制
1. **哈希存储**: 使用SHA-256哈希存储API Key，无法逆向还原
2. **前缀识别**: 使用8位前缀快速识别API Key
3. **过期检查**: 自动检查过期时间，过期后自动失效
4. **权限验证**: 验证用户角色和API Key状态
5. **使用追踪**: 记录每次使用，支持审计和监控

### 认证流程
1. **JWT认证**: 用于用户登录和API Key管理
2. **API Key认证**: 用于主要API接口访问
3. **清晰分离**: 不同接口使用不同的认证方式，确保安全性

## 更新日志

### v0.2.0 (2024-01-01)
- ✨ 新增API Key功能
- 🔐 支持JWT和API Key双重认证
- 📊 添加使用统计功能
- 👥 实现权限控制系统
- 🧪 完整的测试覆盖

### v0.2.1 (2024-01-15)
- 🔄 重构认证流程，主要接口仅支持API Key
- 🚫 移除兼容接口，确保安全性
- 📚 更新文档，说明新的业务流程
- 🚀 优化API Key认证性能
- ✨ 简化认证逻辑，提高安全性

---

如有问题或建议，请联系开发团队或提交Issue。
