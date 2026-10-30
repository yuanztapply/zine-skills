# 安装 / Installation

## 推荐：让 Codex 安装

在 Codex 中粘贴：

```text
$skill-installer Install film-zine and ethnography-zine from https://github.com/yuanztapply/zine-skills.
```

## 手动安装 / Manual installation

下载 [最新 Release](https://github.com/yuanztapply/zine-skills/releases/latest) 的技能 ZIP 并解压，或克隆本仓库。以下命令从含有 `film-zine/` 和 `ethnography-zine/` 的目录运行。

macOS / Linux：

```sh
mkdir -p "$HOME/.agents/skills"
cp -R film-zine ethnography-zine "$HOME/.agents/skills/"
```

Windows（PowerShell）：

```powershell
$zineSkillsDir = Join-Path $env:USERPROFILE '.agents/skills'
New-Item -ItemType Directory -Force -Path $zineSkillsDir | Out-Null
Copy-Item -Recurse -Path film-zine, ethnography-zine -Destination $zineSkillsDir
```

如有同名目录，先备份并移走旧版，避免将两个版本混合。用户级技能目录按 [OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills) 使用 `~/.agents/skills/`；已有安装若使用其他有效位置，不要重复保留同名副本。

Codex 自动识别新技能；未出现时重新启动。在对话中用 `$film-zine` 或 `$ethnography-zine` 调用，并附上材料或片名。

**English:** Extract the release bundle and copy both skill folders into your user-level `~/.agents/skills/` directory. Back up an existing version before replacing it. Invoke `$film-zine` or `$ethnography-zine` in Codex; restart if the new skills do not appear.

## 脚本依赖 / Script dependencies

Python 3.10+：

```sh
python -m pip install -r requirements.txt
```

PDF 转图片还需 Poppler 的 `pdftoppm`。可用以下命令查看参数：

```sh
python film-zine/scripts/extract_palette.py --help
python film-zine/scripts/export_pages.py --help
python ethnography-zine/scripts/export_images.py --help
```

The Python helpers require Pillow and pypdf; PDF rasterization also needs Poppler. Film stills, ethnographic texts and fonts are supplied or located for each project.
