# MobiT

项目结构

```aiignore
MobiT/
├── config.yaml                # 项目配置文件
├── config.template.yaml       # 配置文件模板
├── pyproject.toml            # Poetry 项目配置
├── poetry.lock               # Poetry 依赖锁定文件
├── mobit_main.py             # 主程序入口
├── .gitignore               # Git 忽略文件
├── mobit/                    # 核心代码目录
│   ├── __init__.py
│   ├── config.py             # 配置管理
│   ├── llm.py               # LLM 集成
│   ├── prompts.py           # 提示词模板
│   ├── and_controller.py    # Android 控制器
│   ├── xml_parser.py        # XML/UI 解析器
│   ├── file_utils.py        # 文件操作工具
│   ├── img_utils.py         # 图像处理工具
│   ├── page_graph.py        # 页面关系图生成
│   ├── logic_graph.py       # 功能逻辑图生成
│   └── defect_detection.py  # 缺陷检测
├── data/                     # 数据存储目录
├── examples/                 # 示例数据
└── resources/               # 资源文件目录
```

## ⚙️ Usage

### 安装

1. 确保已安装 Python 3.10+ 和 Poetry
2. 克隆项目并安装依赖：
```bash
git clone https://github.com/your-username/MobiT.git
cd MobiT
poetry install
```

### 配置

在运行项目之前，需要配置 `config.yaml` 文件。复制 `config.template.yaml` 并重命名为 `config.yaml`，然后填写以下必要字段：

```yaml
# 应用配置
APP_PACKAGE: com.example.app  # 被测应用的包名

# LLM 配置
OPENAI_API_KEY: your-api-key  # OpenAI API 密钥
OPENAI_API_BASE: https://api.openai.com/v1  # API 基础 URL
MODEL_NAME: gpt-4o  # 使用的模型名称
```

### 运行

1. 确保 Android 设备/模拟器已连接并启用了 USB 调试
2. 运行完整分析：
```bash
poetry run python -m mobit_main all
```

3. 运行特定阶段：
```bash
# 生成页面关系图
poetry run python -m mobit_main page

# 生成功能逻辑图
poetry run python -m mobit_main logic

# 执行缺陷检测
poetry run python -m mobit_main defect
```