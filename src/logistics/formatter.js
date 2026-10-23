const stringify = require('json-stringify-pretty-compact')

const wrapCode = code => `_CODE_${code}_CODE_`

const cleanCode = str => str
    .replace(/```[a-z]*\n?/gi, '')// 物理超度 Markdown 糖衣（解决```json 报错）
    .replace(/```/g, '')
    .replace(/\\"/g, '"') // 逻辑自愈 处理 AI 错误转义的引号（把 \" 还原回 "）
    .replace(/['"]?_CODE_([\s\S]*?)_CODE_['"]?/g, '$1') // 去掉 _CODE_ 包裹的代码
    .replace(/_CODE_/g, '')      // 兜底清理
    .replace(/"(\w+)":/g, '$1:') // 去掉 key 的双引号
    .replace(/"/g, "'")          // 双引号全部转单引号
    .replace(/[ \t]+$/gm, '')    // 去除每一行行尾的多余空格
    .replace(/\n{3,}/g, '\n\n')  // 将3个或以上的换行符压缩成2个换行符
    .replace(/^\s+/, '')         // 去掉文件头部的空行
    .trim() + '\n'

const contextStringify = ({ context, indent = 4, maxLength = 200 }) => stringify.default(context, { indent, maxLength })

const dehydrateCode = code => code
    // 1. 物理砍掉所有的 import 依赖声明 (省 20-30 行废话)
    .replace(/^import\s+.*?;\s*$/gm, '')
    .replace(/^import\s+[\s\S]*?from\s+['"].*?['"];?\s*$/gm, '')
    // 2. 物理砍掉所有内联 style 样式 (与业务对账毫无关系)
    .replace(/style=\{\{[\s\S]*?\}\}/g, '')
    // 3. 物理砍掉所有 className 和无关的 UI 属性
    .replace(/className=['"][^'"]*['"]/g, '')
    // 4. 物理砍掉常见的纯排版外壳标签 (<Row>, <Col>, <Card>, <Space>)，只留内容
    .replace(/<\/?(Row|Col|Card|Space|Fragment)[^>]*>/g, '')
    // 5. 压缩多余连续空格和空行
    .replace(/[ \t]+$/gm, '')
    .replace(/\n{2,}/g, '\n')
    .trim()

const dehydratePrd = text => text
    // 1. 过滤掉从 Wiki 复制时带过来的各种 HTML 隐藏标签和实体
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    // 2. 过滤掉公文废话（这些绝对不是业务规则）
    .replace(/(本功能旨在|为了提升.*?体验|根据.*?业务要求|原则上需由|系统应当支持|请业务方注意).*?[。；\n]/g, '')
    // 3. 过滤纯 UI 视觉修饰描述（这些由设计稿决定，对账不关心）
    .replace(/(字体大小为.*?|居中显示|背景色为.*?|间距.*?px|左右对齐).*?[。；\n]/g, '')
    // 4. 将连续换行折叠为单换行，剔除每一行首尾无意义字符
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 3) // 过滤掉无意义的单字标点行
    .join('\n')
    .trim()

module.exports = {
    wrapCode,
    cleanCode,
    dehydratePrd,
    dehydrateCode,
    contextStringify,
}
