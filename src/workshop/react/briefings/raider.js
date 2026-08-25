module.exports = `
识别图片页面结构输出一个JSON对象

任务模式：请根据图片内容，分别识别页面结构。如果图片是表单组件，请按Form规则输出；如果是列表组件，请按Table规则输出；如果是页签组件，请按Tabs规则输出。

1. 严禁包含任何 Markdown 标签。
2. 严禁包含注释或解释文字。
3. 必须严格遵守以下字段规范。

## 1. 表格 (Table)
- 结构: { columns: [{ title: '列名', dataIndex: '***englishName***', type: '' }] }
- ⚠️ 字段白名单: [title, dataIndex, sorter, render, filters, onFilter]
- **注意**: type为text时必须省略type属性。
- 禁止输出:
    - 严禁在 columns 中包含“操作”列。
    - ***⚠️⚠️⚠️严禁输出formItems,只允许输出columns⚠️⚠️⚠️***
- **标准定义 (Columns)**:
    - ⚠️ **操作锁定**: 严禁在 columns 数组中包含“操作”列。
    - enum: 枚举列
    - money: 金额列
    - index: 序号列
    - image: 图片列
    - date: 时间/日期列
    - text: 普通文本（默认）
    - tag: 标签列(有背景色的文本)
    - link: 链接列（蓝色下划线的文本）
    - badge: 徽标列(文本前有颜色小圆点)
    - **行操作 (Operation)**: [{label:'操作名', action:'动词ByRecord'}]

## 2. 表单 (Form)
- **基础格式**: [{ label: '文本', name: 'englishName',type:''}]
- **高级格式**: [{ title: '文本', layoutType:'',childItems:[{ label: '文本', name: 'englishName',type:'' }] }]
- ***⚠️⚠️⚠️注意⚠️⚠️⚠️***：当存在明显的粗体标题或者有明显的分组式结构时，必须使用高级格式。
- 禁止输出:
    - ***⚠️⚠️⚠️严禁输出columns,只允许输出formItems⚠️⚠️⚠️***
- ⚠️ 属性精简规则:
    - 默认输入框: 仅保留 [label, name] 属性。**严禁出现 type 属性**。
    - 非默认组件: 仅当类型为 [auto, date, radio, select, upload, checkbox, textarea, daterange] 时才允许添加 type 属性。
- ***⚠️⚠️⚠️layoutType⚠️⚠️⚠️***:
    - section: 段落布局(分段title+childItems项，无明显背景色，纯文本title)
    - collapse: 折叠布局(折叠展开title+childItems项，有明显背景色，或文本前有展开箭头)
**标准定义 (FormItem)**:
    - date: 单日期
    - enum: 枚举类型
    - daterange: 日期范围
    - text: 普通文本（默认）
- 命名规范:
    - daterange: name 必须设为 '字段英文名start,字段英文名end'。
- 增强属性:
    - 文字单位: 若项末尾有单位（如 元/kg），必须存入 unit 属性。
    - 尾操作: 若项末尾有操作按钮（如 选择、编辑 等操作），必须存入 {renderAction:true,addonAfter:'尾操作名'} 属性。
    - 必填校验: 若图片中 label 前有红色星号，必须加入 rules:[{required:true,message:'xxx不能为空'}]。

## 3. 页签 (Tabs)
- 结构: tabs: [{label:'页签名',key:'页签英文'}]

## 4. 下拉选项字典 (OptionDict)
- 结构: optionDict: { 字段英文名Options: [] }
- 内容: 数组元素必须为 {label: '', value: ''} 格式。
`.trim()