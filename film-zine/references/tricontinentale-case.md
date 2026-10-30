# 本轮案例：Tricontinentale

仅在继续本片、查找本轮最终文件或理解偏好来源时读取。本文件记录案例，不是其他电影的模板。

## 编辑目的与最终选择

影片为 Laura Cazador 的 *Tricontinentale, lettre à ouvrir au cas où*（2026）。用户关注 Global North 的后殖民道义责任，以及反思的长度与限度；剑桥放映感受只作编辑线索，不大段刊入，也不翻译成英文再放回书中。

本轮的切口逐渐收束为：痛苦的反省是否变成团结、赔偿与实际共同介入。书内没有 AI 影评，使用核实的电影原句及 Freire、Ahmed、Fanon、Césaire、Young 的原文；文学性结尾采用用户提供的 horizon 文本，其确切英语译本出版出处未独立确认，不编造出处。

必须核对的原文经验：

- 电影引句以 Chicago International Film Festival 所嵌官方片段的烧录英文字幕为证。未观看全片；自动字幕和原始历史书信不替代片内字幕证明。
- Young 最初选了印页709的一段句中从句，首词小写。为满足完整句与正常大写，后来替换为同一官方原刊印页723的完整24词句，没有强改首字母或补写连接语。
- Fanon 两句不连续，保留 […]；册外保存版本、译者与印页102。
- 用户最后明确要求移除封面两个句点，只改这两处，原始句子另存；这不是其他影片一律去标点的规则。

相关原著核验版本与定位：

| 作者 | 本轮作品与位置 |
| --- | --- |
| Paulo Freire | *Pedagogy of the Oppressed*，Ramos 译，Continuum 30周年版，2005印次，p.49 |
| Sara Ahmed | *On Being Included*，2012，导论 p.5 |
| Frantz Fanon | *The Wretched of the Earth*，Farrington 译，Grove后期印本，p.102 |
| Aimé Césaire | *Discourse on Colonialism*，Pinkham 译，2001平装版，p.45 |
| Iris Marion Young | *Responsibility and Global Justice: A Social Connection Model*，原刊2005年39卷，最终选句 p.723 |

这些版本、页码与引句只供本片复用；新任务仍以实际取到的源文件核验。完整出处与阅读范围位于项目 `research/` 和 `SOURCES.md`，不在此复制大量引文。

## 被修正的设计方向

1. 从早期较多页逐步压到4页，解决一页一句、字体过大、像PPT的问题。4页是本片材料量的结果，并非所有zine的默认页数。
2. 将多条学术原句合并到两张内页，文字沿照片缺口、暗部和台阶边连续排布；减少整行倾斜与独立彩条。
3. 最终字体改为 Courier Prime Regular/Bold，同一家族。正文约11.5–12pt、主标题25pt、页码7.5pt；这些数值需按其他字体与成品尺寸重定，不写死。
4. 红黄从悬空的纸角／色条改为原画面实体：座席染黄、原有钢柱提红、会议厅后墙染红。以真实图像为底，原图遮罩保护人物与档案字样。
5. 用户最后将封面右上肖像改为**整图红色调**，覆盖此前仅背景染黄的选择；封底改为**中性黑白灰**，重新裁切使两位站立者完整并更居中，避免第三人的碎边。
6. 最终按用户要求输出4张PNG，裁去外围多余纸白与导出残边；内部留白和页码保留。8px安全距、240dpi和 `ax=.72` 均为本片实现参数，应重算而非套用。

曾提出“两两拼接，最后6页”的导出请求，随后被用户明确取消；之后没有恢复该方案。以后遵循当次最新页数／拼接要求，不能因旧记录自动拼接。

## 最终文件定位

本地项目根：`<workspace>/tricontinental-zine-final-png/`。

- 最终图片：`output/images/Tricontinentale-01.png` 至 `Tricontinentale-04.png`
- 图片包：`output/Tricontinentale_Final_PNGs.zip`
- 最新布局与导出：`source/build_zine.py`、`source/export_final_png.py`
- 修改及完整图像提示词：`research/png-refinements.json`
- 逐页裁边与尺寸：`research/png-export.json`
- 原句、显示文字与段落：`research/text-register.json`、`research/paragraph-audit.json`
- 本轮内部PDF仍是排版／导出中间文件，不是最终PNG请求的替代交付，也不称印刷就绪。

这些是本机历史定位；文件缺失时不要假定已读取，技能本身不依赖它们运行。其他旧版目录仅用于回溯，不当作当前成品。
