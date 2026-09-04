const { Segment, useDefault } = require('segmentit')
const segmentit = useDefault(new Segment())

const unwrapSignal = json => {
    if (!json || typeof json !== 'object') return null
    if (Array.isArray(json)) return json
    const dataKeys = ['data', 'list', 'items', 'datas', 'rows', 'result', 'payload', 'results', 'dataList']
    for (const key of dataKeys) {
        if (json[key] && Array.isArray(json[key])) return json[key]
    }
    for (const key in json) {
        if (json[key] && typeof json[key] === 'object') {
            const nested = unwrapSignal(json[key])
            if (Array.isArray(nested)) return nested
        }
    }
    return null
}

const getSemanticKeywords = text => {
    const content = Array.isArray(text) ? text.join(' ') : (text || '')
    const result = segmentit.doSegment(content, {
        simple: true, // 开启简易模式，提升吞吐效率
        stripPunctuation: true // 过滤掉所有的标点符号
    })
    return Array.from(new Set(result.filter(word => word.length >= 2 && !/^[0-9]+$/.test(word))))
}

const isQuerySignal = (req, json, coreData) => {
    const pathname = req.url.split('?')[0].toLowerCase()
    const actionKeywords = ['add', 'delete', 'update', 'save', 'remove', 'edit', 'insert', 'create', 'export', 'upload']
    if (actionKeywords.some(key => pathname.split(/[/\-_]/).includes(key))) {
        return false
    }
    const hasListData = Array.isArray(coreData) && coreData.length > 0
    const hasPaginationFingerprint = ['total', 'records', 'page', 'size', 'count'].some(key => {
        const k = key.toLowerCase()
        return Object.keys(json).some(rawKey => rawKey.toLowerCase().includes(k))
    })
    return hasListData || hasPaginationFingerprint
}

const normalize = str => str.toLowerCase().replace(/[-_]/g, '')

const getLocalScore = (api, pageKeywords, moduleName) => {
    let score = 0
    const path = api.path.toLowerCase()
    const desc = api.desc.toLowerCase()
    const mod = moduleName.toLowerCase()
    if (normalize(path).includes(normalize(mod))) score += 50
    pageKeywords.forEach(word => {
        if (desc.includes(word.toLowerCase())) score += 10
        if (path.includes(word.toLowerCase())) score += 5
    })
    return score
}

module.exports = {
    unwrapSignal,
    isQuerySignal,
    getLocalScore,
    getSemanticKeywords,
}
