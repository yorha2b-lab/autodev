module.exports = ({ responseStr, resourceStr }) => `
目标：执行【前端虚拟字段】与【后端真实响应】的物理重组与对账。

## 1. 核心输入 (Signal Capture)
- **前端现状 (Source Keys)**:
- 前端字段中括号内为中文 label 提示，返回的 JSON key 请只保留括号前的原英文字段名:
${resourceStr}

- **后端样本 (Target Data)**:
${responseStr}

## 2. 匹配算法优先级 (Alignment Protocol)
请严格按以下优先级执行逻辑映射，直到找到唯一目标：
1. **L1 - 物理全等**: 字符完全一致 (例: userId == userId)。
2. **L2 - 格式重组**: 下划线与驼峰转换 (例: user_id == userId)。
3. **L3 - 语义穿透**: 业务含义高度一致 (例: amount == price, phone == mobile)。

## 3. ⚠️ 强制冲突修正 (Conflict Resolution)
若存在多个潜在目标，执行以下强制判定：
- **中文字义优先**: 优先匹配能解释前端视觉标签含义的字段。
- **长度优先**: 若 "createByName" 与 "createBy" 同时存在，强制选择 "createByName"。

## 4. 输出约束 (Output Restrictions)
- **严禁输出解释性文字、严禁 Markdown 标签**。
- **仅输出合法的 JSON 对象**。
- **过滤机制**: 若某字段在后端响应中完全找不到对应映射，物理拦截（不输出）。

## 5. 示例参考 (Example)
Input:
  Source: { dataIndex: 'userName' }, Response: { name: '2B' }
Output:
  {"userName": "name"}
`.trim()