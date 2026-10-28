# Agent-Infra Healing System - 快速开始

Multi-Agent Infrastructure Orchestration System（多智能体基础设施自愈系统）

## 功能特性

- 🤖 **多智能体协作**: Diagnosis Agent + Strategy Agent + Execution Agent
- 📊 **实时监控**: Prometheus + Grafana 可视化
- 📝 **日志分析**: Elasticsearch + Kibana 日志检索
- 🔥 **故障注入**: 模拟真实故障场景
- 💾 **数据收集**: 自动收集故障场景用于训练

## 快速部署（一键启动）

### 前置要求

- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- 至少 8GB 内存
- Claude/OpenAI API Key

### 部署步骤

#### Windows

```bash
# 1. 克隆或解压项目
cd agent-infra-healing

# 2. 配置 API Key
copy .env.example .env
# 编辑 .env 文件，填入你的 ANTHROPIC_API_KEY

# 3. 一键部署
deploy.bat
```

#### Linux/Mac

```bash
# 1. 克隆或解压项目
cd agent-infra-healing

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 文件，填入你的 ANTHROPIC_API_KEY

# 3. 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 使用 Docker Compose 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
nano .env  # 填入你的 API keys

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f agent-system

# 4. 停止服务
docker-compose down
```

## 访问服务

部署完成后，可以通过以下地址访问各个服务：

| 服务 | 地址 | 说明 |
|------|------|------|
| Demo App | http://localhost:8080 | 测试应用（可注入故障） |
| Prometheus | http://localhost:9090 | 指标查询 |
| Grafana | http://localhost:3000 | 可视化仪表板（admin/admin） |
| Kibana | http://localhost:5601 | 日志查询 |

## 测试故障注入

### 1. 注入错误率

```bash
curl -X POST http://localhost:8080/inject/errors \
  -H 'Content-Type: application/json' \
  -d '{"rate": 0.5}'
```

Agent 会检测到高错误率并生成诊断和恢复计划。

### 2. 注入高延迟

```bash
curl -X POST http://localhost:8080/inject/latency
```

### 3. 标记服务不健康

```bash
curl -X POST http://localhost:8080/inject/unhealthy
```

### 4. 恢复正常

```bash
curl -X POST http://localhost:8080/recover
```

## 查看 Agent 输出

```bash
# 查看实时日志
docker-compose logs -f agent-system

# 查看最近 100 行
docker-compose logs --tail=100 agent-system
```

Agent 会每 30 秒检测一次，当发现异常时会：
1. 检测异常（Monitor Agent）
2. 诊断根因（Diagnosis Agent）
3. 生成恢复计划（Strategy Agent）
4. 保存场景数据（用于后续训练）

## 查看收集的数据

```bash
# 进入容器
docker exec -it agent-system bash

# 查看收集的故障场景
ls -lh /app/data/scenarios/

# 查看某个场景
cat /app/data/scenarios/scenario_20241028_120000.json
```

## 项目结构

```
agent-infra-healing/
├── docker-compose.yaml       # Docker Compose 配置
├── Dockerfile                # Agent 系统镜像
├── deploy.sh / deploy.bat    # 一键部署脚本
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖
├── src/
│   ├── main.py              # 主入口
│   ├── agents/              # Agent 实现
│   │   └── orchestrator.py # 多 Agent 编排
│   ├── infra/               # 基础设施监控
│   │   └── monitor.py      # Prometheus/ES 集成
│   └── data/                # 数据收集
│       └── collector.py    # 场景数据采集
├── configs/                 # 配置文件
│   ├── prometheus.yml
│   └── grafana-datasources.yaml
└── k8s/                     # Kubernetes 配置（可选）
```

## 常见问题

### 1. 服务启动失败

检查端口占用：
```bash
# Windows
netstat -ano | findstr "8080 9090 3000"

# Linux/Mac
lsof -i :8080,9090,3000
```

### 2. Elasticsearch 内存不足

编辑 `docker-compose.yaml`，减小 Elasticsearch 内存：
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms256m -Xmx256m"  # 从 512m 改为 256m
```

### 3. Agent 无法连接监控服务

等待所有服务完全启动（约 30-60 秒），然后重启 Agent：
```bash
docker-compose restart agent-system
```

### 4. API Key 错误

确保 `.env` 文件中的 API Key 正确：
```bash
cat .env | grep API_KEY
```

## 下一步

### Phase 1（当前）：基础设施搭建 ✅
- [x] Docker Compose 环境
- [x] 监控栈（Prometheus + Grafana）
- [x] 日志栈（Elasticsearch + Kibana）
- [x] Demo 应用 + 故障注入
- [x] 基础 Agent 框架

### Phase 2：Agent 训练
- [ ] 收集 500+ 故障场景
- [ ] 标注诊断和恢复策略
- [ ] 微调 Llama 3 8B
- [ ] 优化多 Agent 协作

### Phase 3：评估与优化
- [ ] 建立 Benchmark
- [ ] 对比 Baseline
- [ ] 性能优化

## 分享给朋友

### 方法 1：打包整个项目

```bash
# 压缩项目目录
tar -czf agent-infra-healing.tar.gz agent-infra-healing/

# 或在 Windows 上右键压缩为 zip
```

发送给朋友后，他们只需：
1. 解压
2. 编辑 `.env` 添加自己的 API Key
3. 运行 `deploy.sh` 或 `deploy.bat`

### 方法 2：推送到 Git

```bash
cd agent-infra-healing
git add .
git commit -m "Initial setup: Phase 1 complete"
git remote add origin <your-repo-url>
git push -u origin main
```

朋友可以直接：
```bash
git clone <your-repo-url>
cd agent-infra-healing
cp .env.example .env
# 编辑 .env
./deploy.sh
```

### 方法 3：Docker Hub（推荐）

```bash
# 构建并推送镜像
docker-compose build
docker tag agent-infra-healing-agent-system:latest <your-dockerhub>/agent-infra-healing:latest
docker push <your-dockerhub>/agent-infra-healing:latest

# 修改 docker-compose.yaml 中的 image 字段
```

## 贡献与支持

项目处于早期开发阶段，欢迎提 Issue 和 PR！

## License

MIT License
