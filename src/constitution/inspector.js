module.exports = ({ prdText, moduleName, moduleCodeView }) => `
# Task: Fast PRD vs Code Logic Gap Analysis

## 1. 需求要点 (PRD 核心业务规则)
${prdText}

## 2. 代码逻辑骨架 (${moduleName} 脱水源码)
${moduleCodeView}

## 3. 极速审计准则
1. 从需求中仅聚焦提取：【条件分支】、【联动】、【条件禁用/必填】、【二次确认/弹窗】、【特殊数值/边界限制】。
2. ⚠️【禁止废话】：已实现的功能只用一行短语概括；未实现的问题只挑最致命的缺口
3. 【输出】：仅输出未实现的功能，不输出已实现的功能

## 4. 输出紧凑 JSON:
{
  "unimplementedGaps": [
    { "feature": "状态为草稿时禁止提交", "detail": "代码中未见提交按钮的 disabled 判定" }
  ]
}
`.trim()