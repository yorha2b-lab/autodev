module.exports = `
# Task: Full-Page UI Analysis & Structural Assembly
执行全页面视觉特征提取，并按照物理布局顺序输出标准的构筑协议。

##模块名
- **来源**: 页面标题/表格列信息
- **目标**: 提取页面主体名称[英文]作为模块名
- **格式**: 驼峰命名,首字母小写,单词之间无下划线空格等一系列不合符文件夹名称的符号

## 核心命名协议 (Naming Convention)
- **驼峰命名**: 所有变量及函数名必须遵循 camelCase。
- **严禁中文**: 绝对禁止在变量名、键名中使用中文字符。
- **屏蔽关键字**: 禁止使用 JS 保留字 (export, delete, const, let, class, default 等)。

## 页面标题 (title)
- **格式**: {title:{english:'页面标题[英文]',chinese:'页面标题[中文]'}}

## 零部件构筑规范 (Component Specifications)

## 标签页 (tabs)
- **基础格式**: [{ tab: '文本', key: 'englishName' }]
- **识别条件**: 底部有显著长横线 (Ink Bar) 或呈现包裹感 (Card style) 时判定。
- **排除项**: 表格上方的独立按钮必须归类为 [functionButton]。

## 搜索项 (formItems)
- **基础格式**: [{ label: '文本', name: 'englishName' }]
- **属性精简规则**:
    - 默认输入框: 仅保留 [label, name] 属性。**严禁出现[type]**。
    - 非默认组件: 仅当类型为 [auto, date, radio, select, upload, checkbox, textarea, daterange] 时才允许添加 type 属性。
- **命名规范**:
    - daterange: name 必须设为 '字段英文名Start,字段英文名End'

## 统计条 (StaticInfo)
- **独立存在**: 位于表格外周的汇总信息。输出格式: { has: boolean, text: '具体内容' }。

## 表格主体 (table)
- **基础格式(columns)**: [{ title: '文本', dataIndex: 'englishName' }]。
- **配置项**: [pagination, expandable, rowSelection] 均为布尔值。
- **行操作 (operation)**: [{ label: '操作名', action: '操作动词+[模块名单数]', request: 'BUNKER_API_ANCHOR_动词+[模块名单数]'}]
- **类型定义 (type)**:
    - enum: 枚举列
    - money: 金额列
    - index: 序号列
    - image: 图片列
    - date: 时间/日期列
    - text: 普通文本（默认）
    - tag: 标签列(有背景色的文本)
    - link: 链接列（蓝色下划线的文本）
    - badge: 徽标列(文本前有颜色小圆点)

## 全局功能按钮 (functionButton)
- **基础格式**: [{ btn: '按钮', action: '操作动词+[模块名复数]', request: 'BUNKER_API_ANCHOR_动词+[模块名复数]'}]。
- **导出数据**: action 设为 'export[模块名]'。
- **逻辑锁定**: 只要页面中出现了非查询、非重置的独立操作按钮，必须识别并存入 [functionButton] 数组。
- **构筑联动**: 若 [functionButton] 数组不为空，则在下文的 [RenderTree] 中必须包含 "FunctionButtons"。

## 布局逻辑编排 (RenderTree)
- **定义**: 定义从上至下的物理堆叠顺序。
- **白名单**: [MyTable, AlertInfo, MySearchForm, FunctionButtons]

## 字典数组 (OptionList)
- **格式**:[{ name: '字段英文名Options', options:[{ label, value}]}]。
- **注释**:label:选项文本,value:文本英文。
- **数据源**:根据对应列的内容去重，生成选项数组。
`.trim()