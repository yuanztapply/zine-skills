# Zine Skills

两套可复用的 Codex 技能，分别用于制作电影小志与民族志小志。每个技能包含工作流程、核验说明和辅助脚本；当次用户要求优先于默认偏好。

- **film-zine**：从片名或电影链接开始，核实原句与真实剧照，以图文编排制作电影 zine；支持逐页 PNG 导出与裁边。
- **ethnography-zine**：阅读用户提供的民族志材料，精选真实原文，结合轮廓排字与剪贴版式，交付小志 PDF、可编辑来源及按需导出的图片。

## 目录

```text
film-zine/
  SKILL.md          # 技能说明
  agents/           # Codex 展示信息
  references/       # 取材、版式与导出说明
  scripts/          # 取色、PNG 导出工具
ethnography-zine/
  SKILL.md
  agents/
  assets/           # 浏览器轮廓排版组件
  references/
  scripts/          # 页面图片导出工具
requirements.txt
```

## 安装到 Codex

下载或克隆本仓库后，在仓库根目录运行。

macOS / Linux：

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R film-zine ethnography-zine "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Windows（PowerShell）：

```powershell
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
Copy-Item -Recurse -Path film-zine, ethnography-zine -Destination $skillsDir
```

如果已有同名技能，先备份并移走旧目录，再复制。安装后在 Codex 中使用 `$film-zine` 或 `$ethnography-zine`，并提供片名、原著或具体制作要求。

## 辅助脚本依赖

Python 3.10 或更新版本；Python 包通过以下命令安装：

```sh
python -m pip install -r requirements.txt
```

PDF 转图片还需要系统安装 **Poppler**，并确保 `pdftoppm` 可执行程序在 `PATH` 中。macOS 可通过 Homebrew 安装 `poppler`；Linux 可安装发行版的 `poppler-utils`；Windows 安装适合本机的 Poppler 并将其 `bin` 目录加入 `PATH`。

脚本参数请查看实际帮助，例如：

```sh
python film-zine/scripts/extract_palette.py --help
python film-zine/scripts/export_pages.py --help
python ethnography-zine/scripts/export_images.py --help
```

`ethnography-zine/assets/contour_engine.js` 使用浏览器原生功能，无额外 JavaScript 包依赖。

## 素材与使用范围

真实剧照、海报、原著全文和字体需另行提供，或在具体任务中从可访问且适合使用的来源获取；仓库不包含这些素材。技能要求记录出处、实际阅读范围及图像处理情况，不能把生成内容冒充原著、真实台词或田野记录。

案例文件用于解释特定项目的设计选择；`<workspace>` 是通用路径占位符，案例中列出的成品不随技能分发。技能制作任务不会自动授权对外发布或联系第三方。
