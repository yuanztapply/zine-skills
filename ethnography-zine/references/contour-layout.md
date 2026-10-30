# 轮廓、浅弧与不规则纸片

## 先解决结构

把“几段文字＋角落插图”改成一个图文场。先找内容中的轮廓：物件的凸起与凹口、人物肩背、树枝间隙、地形或制度边界。图像影响文字的起点、终点、行宽与前后关系，不能只在原矩形上加一点旋转。

- 背包：正文中部变宽，上下收窄；清单进入袋形。
- 袜子：窄袜筒接住短段，脚跟与脚掌承载更长、逐渐收放的段落。
- 枝杈：窄纸舌伸入空隙，再逐渐展开为长段；按从上到下顺序读。
- 图中出现的人物：浅弧可以沿肩背走，避开眼睛、面孔和重要动作。

这些是找形的方法，不是要求每本都画背包或袜子。长段落主要改变左右边界；不将整段文字逐字扭成波浪，不用螺旋或反向路线牺牲阅读。

## 可选排版组件

`assets/contour_engine.js` 可内嵌到离线 HTML。它依据实际字体测量完整单词，顺序装入行宽；纸底根据实际文字行生成独立 SVG，曲线文字使用原生 SVG textPath。

使用前查看代码与当前浏览器能力。组件适合以空格分词的原文；中文等文本需采用适合该文字的断行方法，不能把一整段锁在一个不可折行的 `.word` 中，也不能为了分词新增正文空格。

组件不包含字体、照片或民族志文本。每次从本期材料重新提供。

### 页面与文字约定

```html
<article class="page" data-page="2">
  <div class="t read contour white"
       data-edit data-raw="The complete selected original passage."
       data-profile="[[12,75],[8,83],[3,91],[0,96],[4,90]]"
       style="position:absolute;left:28mm;top:77mm;width:110mm;font-size:20pt">
    <!-- Each span holds one complete original word, separated by actual spaces. -->
    <span class="word">The</span> <span class="word">complete</span>
    <span class="word">selected</span> <span class="word">original</span>
    <span class="word">passage.</span>
  </div>
  <div class="folio">02</div>
</article>
```

每对数字是该行相对于文字容器的“左缩进 mm、可用宽度 mm”。上下位置由实际字号计算，单词不拆断。扩展例子中的行数与宽度以容纳全部选文，不把示例短句当作原著材料。

`data-raw` 保存完整选段；布局后的可见文本应与它仅存在排版空白差别。容量不足时引擎仍放出尾文并标记 `data-spill-lines`，不能据此交付溢出的页面。调整轮廓、位置、页面安排或选材；不隐藏剩余单词。

最小 CSS 约定如下，字体与色彩由本期设计提供：

```css
.page { position:relative; isolation:isolate; overflow:hidden; }
.t { position:absolute; font-weight:700; }
.word { display:inline-block; white-space:nowrap; }
.g { display:inline-block; white-space:pre; }
.paper,.blackslip { isolation:isolate; background:transparent; clip-path:none; }
.paper-ground { position:absolute; z-index:-1; pointer-events:none; }
.paper-ground path { pointer-events:fill; }
.contour { padding:0; pointer-events:none; }
.contour .word { pointer-events:auto; }
.contour-line { position:absolute; white-space:nowrap; font:inherit; pointer-events:none; }
.curve-wrap { font-size:0; line-height:1; isolation:isolate; }
.curve-text { display:block; overflow:visible; }
```

`.paper` 与 `.blackslip` 指纸底颜色；可以通过 CSS 自定义属性 `--paper`、`--ink` 提供本期配色。不要再给文字父容器加裁切路径，否则字母笔势和标点会被一起裁断。

### 浅弧短句

在 `.t.curve-wrap[data-raw]` 内放 SVG：`defs path` 定义浅弧，`text > textPath` 承载同一条完整原句。`startOffset="50%"` 配合 `text-anchor="middle"` 可以居中；弧度需要人工检查。

SVG 的 viewBox 使用毫米坐标时，字体的用户单位大小为 `pt × 25.4 / 72`。曲线纸带另画在文字下方，给升部、降部和标点留余量。

组件用路径长度检查是否容纳完整句子。默认不把曲线字缩到 18pt 以下；可用 `data-min-pt` 根据实际字体与版面设置。若仍不能容纳，`data-curve-fit` 为 false：延长路径、换行或把短句分配到更合适的页面，不靠不可读的小字通过检查。

不要直接让一条独有长句跑到路径之外，或以 textLength 强行压扁到既定长度。

### 不规则纸底

给正文或标题添加 `.paper`／`.blackslip`。组件沿文字行外侧生成凹口和撕边，文字本身保持未裁切。标题的安全余量较大，用于手写字形的外伸笔势。

纸片可以与图像、其他纸片重叠；独有文字不能因此被遮没。底层重要内容需要移位继续读，不能藏在上层纸底下。不要全刊使用相同毛边框或等宽长条。

### 离线、编辑与导出

- 在 HTML 末尾、页面 DOM 已存在时内嵌组件，字体和图像一并内嵌。
- 组件暴露 `window.contourReady`；等待它完成后再截图、测量或导出。
- 使用配套 `editBtn` 按钮调用 `toggleEdit()`，`saveCopy()` 保存副本。曲线文字点击编辑；轮廓段落失焦后重排。
- 输入改变后检查重排容量。保存的 HTML 重新打开后再比较文字，不把一次下载成功当作编辑功能验证。
- 字体字号是实际效果的判断起点。A5 的 Caveat 案例正文约 17–23pt、短弧约 23–28pt；其他字体须重新看字面大小和打印阅读性，不照抄数值。

## 常见失误

1. 白字留在容器边界内，却越出了黑色物件：以实际字形和背景检查。
2. 黑色重点词落在黑色玉米颗粒上：给字组独立纸底或改变层级。
3. 袜口横线穿过正文：移动线条或文字，不让装饰损害清楚程度。
4. 标题纸片紧贴笔势，截掉最后的逗号／引号：文字层与纸底分开，扩大余量。
5. 末段纸底压住前段尾行：叠纸只发生在字形之外；用实际文字命中与视觉复核共同检查。
6. 整段弧排靠自动缩字号才装得下：改成轮廓段落，短弧只承载短句。
