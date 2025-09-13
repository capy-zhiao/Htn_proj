# MCP Chat Logger - DynamoDB Integration

这个增强版的MCP Chat Logger现在支持将对话内容总结为JSON格式并存储到DynamoDB数据库中。

## 新功能

- ✅ 将对话转换为结构化的JSON格式
- ✅ 支持存储到Amazon DynamoDB
- ✅ 支持本地JSON文件存储
- ✅ 保留原有的Markdown文件功能
- ✅ 可配置的TTL（生存时间）
- ✅ 数据验证和类型安全

## 安装依赖

```bash
# 安装新的依赖
pip install boto3 pydantic

# 或者使用uv
uv sync
```

## 配置

### 1. 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
# DynamoDB配置
export DYNAMODB_TABLE_NAME="chat_conversations"
export DYNAMODB_REGION="us-east-1"

# AWS凭证（可选，如果使用AWS CLI配置则不需要）
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_SESSION_TOKEN="your_session_token"  # 可选

# 其他配置
export LOGS_DIRECTORY="chat_logs"
export DEFAULT_TTL_DAYS="30"
```

### 2. AWS凭证配置

确保您的AWS凭证已正确配置：

```bash
# 使用AWS CLI配置
aws configure

# 或设置环境变量
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
```

## 设置DynamoDB表

运行以下脚本创建DynamoDB表：

```bash
python create_dynamodb_table.py
```

这将创建一个名为 `chat_conversations` 的表，包含以下特性：
- 主键：`conversation_id` (String)
- 全局二级索引：`created_at-index`
- TTL：`ttl` 属性（自动删除过期记录）
- 按需计费模式

## 使用方法

### 1. 基本用法

```python
from chat_logger import save_chat_history

# 保存到DynamoDB和JSON文件
result = await save_chat_history(
    messages=[
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    conversation_id="conv-001",
    title="Greeting Conversation",
    summary="A simple greeting exchange"
)
```

### 2. 只保存到JSON文件

```python
result = await save_chat_history(
    messages=messages,
    conversation_id="conv-002",
    save_to_db=False,  # 不保存到DynamoDB
    save_to_file=True  # 保存到JSON文件
)
```

### 3. 只保存到DynamoDB

```python
result = await save_chat_history(
    messages=messages,
    conversation_id="conv-003",
    save_to_db=True,   # 保存到DynamoDB
    save_to_file=False # 不保存到文件
)
```

### 4. 使用原有的Markdown功能

```python
from chat_logger import save_chat_history_markdown

result = await save_chat_history_markdown(
    messages=messages,
    conversation_id="conv-004"
)
```

## JSON数据结构

生成的JSON文件包含以下结构：

```json
{
  "conversation_id": "uuid-string",
  "title": "Conversation Title",
  "summary": "Brief summary",
  "message_count": 4,
  "participants": ["user", "assistant"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant", 
      "content": "Hi there!",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ]
}
```

## DynamoDB表结构

| 属性名 | 类型 | 描述 |
|--------|------|------|
| conversation_id | String | 主键，对话唯一标识符 |
| title | String | 对话标题（可选） |
| summary | String | 对话摘要（可选） |
| message_count | Number | 消息数量 |
| participants | List<String> | 参与者列表 |
| created_at | String | 创建时间（ISO格式） |
| updated_at | String | 更新时间（ISO格式） |
| messages | List<Map> | 消息列表 |
| ttl | Number | 生存时间戳（自动删除） |

## 运行示例

```bash
# 运行示例脚本
python example_usage.py
```

## 错误处理

- 如果AWS凭证未配置，将显示错误信息但不会中断程序
- 如果DynamoDB表不存在，将显示错误信息
- 所有错误都会被捕获并显示友好的错误消息

## 注意事项

1. **成本控制**：DynamoDB按需计费，请监控使用量
2. **TTL设置**：默认30天自动删除，可在配置中修改
3. **权限**：确保AWS用户有DynamoDB的读写权限
4. **区域**：确保DynamoDB表在正确的AWS区域

## 故障排除

### 常见问题

1. **AWS凭证错误**
   ```
   AWS credentials not found. Please configure AWS credentials.
   ```
   解决：配置AWS凭证或设置环境变量

2. **DynamoDB表不存在**
   ```
   Error initializing DynamoDB: An error occurred (ResourceNotFoundException)
   ```
   解决：运行 `python create_dynamodb_table.py` 创建表

3. **权限不足**
   ```
   Error saving to DynamoDB: User is not authorized to perform: dynamodb:PutItem
   ```
   解决：确保AWS用户有DynamoDB的PutItem权限
