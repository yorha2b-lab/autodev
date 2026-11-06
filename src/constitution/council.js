module.exports = ({ bunkerAnchors, realApis }) => `
# MISSION: Multi-Point API Alignment
目标：为地堡生成的多个作战动作匹配真实的后端接口。

## 1. 待匹配指令清单 (Target Anchors)
${bunkerAnchors}

## 2. 后端情报库 (Swagger Docs)
${realApis}

## 3. 匹配协议
- 识别后缀（如 edit, delete, add）。
- 结合 UI 语义，在 API 库中寻找对应路径。
- **输出格式**：请只输出一个 JSON 映射表。
- **例如**：{"BUNKER_API_ANCHOR_editByRecord": {"uri": "/api/records/{recordId}", "method": "POST"}}

## 4. 后端动作黑话映射准则 (API Action Synonyms)
由于后端开发命名极其不规范，匹配时可以按以下业务黑话等价映射：
- 【删除 / 移除 / 作废】等价于: delete, del, remove, drop, invalid, cancel, void, status, updateStatus, trash
- 【审核 / 审批 / 确认】等价于: audit, approve, pass, check, verify, review, examine
- 【编辑 / 更新 / 修改】等价于: edit, update, modify, change, save, handle
- 【新增 / 创建 / 提交】等价于: add, create, insert, save, submit, post
- 【导出 / 下载】等价于: export, download, out, dump, file

⚠️ 强制注意：
1. 后端极度喜欢用 POST 方法配合 status / invalid / state 实现逻辑软删除，切勿死板寻找 DELETE 方法！
2. 单行操作通常路径带 /{id} 或接收单个 id 参数；批量操作通常接收 ids 数组。

⚠️ 严禁解释，严禁输出 JSON 之外的内容。
`.trim()