# 哈弗克军火商（JHS）开源版

这是从 `jhs.py` 整理出的独立开源目录，包含运行脚本、模板图片、依赖清单和配置示例。

> 提醒：本工具会监听热键、截图 OCR、移动鼠标并自动点击。请仅在你有权操作的环境中使用，风险自负。

## 目录结构

```text
jhs-open-source/
├─ jhs.py                    # 主程序
├─ version.py                # 版本号
├─ requirements.txt          # Python 依赖
├─ config.example.json       # 配置示例
├─ image/
│  ├─ quanmianzhanchang.png  # 自动切换模式识别模板
│  └─ fenghuodidai.png       # 自动切换模式识别模板
└─ .gitignore
```

运行后会自动生成：

- `config.json`：保存界面输入项
- `logs/`：日志目录
- `debug_images/`：OCR 调试截图目录

## 环境要求

- Windows 10/11
- Python 3.9+（建议 3.10 或 3.11）
- 管理员权限运行终端（`keyboard` 热键监听、鼠标点击在部分环境需要管理员权限）
- 游戏建议使用全屏窗口/无边框窗口，并保持 UI 缩放稳定

已适配分辨率：

- 1920×1080
- 2560×1440
- 3840×2160
- 2560×1600
- 1920×1200
- 1600×900
- 3440×1440

## 安装

```powershell
cd jhs-open-source
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

EasyOCR 首次运行会下载 OCR 模型；如果你要离线运行，可自行准备 `model/` 目录。

## 运行

```powershell
python jhs.py
```

打开程序后，在交易行界面按 **F12** 开始/暂停；如果设置了开始时间，按 F12 后会进入倒计时，再按 F12 可取消倒计时。

## 界面配置说明

| 配置项 | 说明 |
| --- | --- |
| 物品名称 | 要搜索的物品名；留空默认抢列表第一个 |
| 物品是否是枪械 | 枪械商品勾选后识别绿色按钮价格区域 |
| 购买页是否可兑换 | 可兑换商品使用另一套按钮/价格坐标 |
| 1k显示屏备用方案 | 1080p 下使用由 2K 坐标缩放得到的备用坐标 |
| 购买数量是否拉满 | 自动点击 200/拉满按钮 |
| 最高购买价格 | 识别价格低于该值才会购买 |
| 开始时间 | 小时:分钟；不填立即开始；时间已过则默认明天同一时间 |
| 定时停止（分钟） | 达到指定分钟数后停止；不填则不自动停止 |
| 检测间隔 | OCR 前额外等待时间，默认 `0.05` 秒 |
| 鼠标点击延迟 | 鼠标移动到点击之间的等待，默认 `0.15` 秒 |
| 购买成功次数 | 达到成功次数后停止；不填不限次数 |
| 关闭误购保护 | 关闭后只判断价格上下限，风险较高 |
| 最低购买价格 | 关闭误购保护时启用，用于设置购买下限 |
| 启用定时切换模式 | 每隔指定分钟自动执行模式切换流程 |
| 重启间隔 | 定时切换模式间隔，默认 `10` 分钟 |

## 配置文件

你可以复制示例配置：

```powershell
Copy-Item config.example.json config.json
```

也可以直接通过界面填写，点击开始时程序会自动保存当前输入。

## 打包为 exe（可选）

安装 PyInstaller：

```powershell
pip install pyinstaller
```

在线下载 OCR 模型的打包方式：

```powershell
pyinstaller --onefile --add-data "image;image" jhs.py
```

如果你已经准备了本地 `model/` 目录：

```powershell
pyinstaller --onefile --add-data "image;image" --add-data "model;model" jhs.py
```

Windows 下 `--add-data` 使用分号 `;` 分隔源路径和目标路径。

## 开源前建议

1. 不要提交 `config.json`、`logs/`、`debug_images/`、`model/` 等本地运行数据。
2. 如果要发布到 GitHub，建议补充 `LICENSE` 文件，例如 MIT、Apache-2.0 或 GPL。
3. README 中如涉及游戏或第三方平台，请自行确认是否符合相关条款。
4. 发布前建议在干净虚拟环境中执行一次：

```powershell
python -m py_compile jhs.py
python jhs.py
```
