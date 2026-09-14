module.exports = async ({ llm, yorha, dialog, logistics }) => {

    const fs = require('fs')
    const path = require('path')

    const { apiParser } = llm
    const { pod153, commander } = yorha
    const { contextStringify } = logistics.formatter
    const { apiDoc, pagesDir } = logistics.supporter.getConfig()
    const { getLocalScore, unwrapSchemaRef, getSemanticKeywords } = logistics.analyzer

    if (!apiDoc) return

    pod153.report(dialog.pod153.autonomousAddressing, 'magenta')

    const apiData = await fetch(apiDoc).then(res => res.json())
    const refinedApis = Object.entries(apiData.paths).flatMap(([apiUrl, methods]) => {
        return Object.entries(methods).map(([method, info]) => ({
            path: apiUrl,
            method: method?.toUpperCase() || '',
            desc: info.summary || info.description || 'N/A',
        }))
    })

    const falseTruth = (apiUrl, method = 'post') => {
        const cleanUrl = apiUrl.split('?')[0]
        const matchedPath = Object.keys(apiData.paths || {}).find(p => cleanUrl.endsWith(p) || p.endsWith(cleanUrl))
        if (!matchedPath) return null
        const definitions = apiData.definitions || apiData.components?.schemas || {}
        // 1. 找到该接口 200 响应对应的根 Schema
        const methodObj = apiData.paths?.[apiUrl]?.[method.toLowerCase()]
        const rootSchema = methodObj?.responses?.['200']?.schema || methodObj?.responses?.['200']?.content?.['application/json']?.schema
        if (!rootSchema) return null
        // 辅助函数：根据 $ref 名字解析出实体
        const resolveRef = (refStr) => {
            if (!refStr) return null
            const refName = refStr.split('/').at(-1)
            return definitions[refName]
        }
        // 2. 解析外层包装类 (如 TableResult)
        let wrapperDef = resolveRef(rootSchema.$ref)
        // 3. 在外层属性里寻找我们熟悉的列表字段 (datas, records, list, rows 等)
        const rowRef = unwrapSchemaRef(wrapperDef)
        // 4. 顺藤摸瓜拿到终极行数据定义 (Row DTO)
        const rowDef = resolveRef(rowRef)
        if (!rowDef?.properties) return null
        // 5. 组装成高纯度的伪样本数据！
        // 格式形如：{ contractNum: "合同编号" }
        return Object.fromEntries(
            Object.entries(rowDef.properties).map(([fieldName, propMeta]) => [
                fieldName,
                propMeta.description || propMeta.title || fieldName // 优先拿后端写的中文注释！
            ])
        )
    }

    const resurrection = async () => {
        try {
            const pages = path.join(process.cwd(), pagesDir)
            const files = fs.readdirSync(pages)
            const enumParamsMap = {}

            for (const fileName of files) {
                const pageDir = path.join(pages, fileName)
                if (!fs.existsSync(pageDir) || !fs.statSync(pageDir).isDirectory()) continue

                const subFiles = fs.readdirSync(pageDir).filter(f => f.endsWith('.js') || f.endsWith('.jsx'))
                const fileContents = {}
                const allSemantics = []
                const allAnchors = new Set()

                for (const file of subFiles) {
                    const filePath = path.join(pageDir, file)
                    const code = fs.readFileSync(filePath, 'utf-8')
                    fileContents[filePath] = code

                    const anchors = code.match(/BUNKER_API_ANCHOR_\w+/g) || []
                    anchors.forEach(a => allAnchors.add(a))

                    const textMatches = code.match(/(?:['"`]([^'"`\n]{2,})['"`]|>([^<>{}\n]{2,})<)/g) || []
                    const uiSemantics = textMatches
                        .map(str => str.replace(/['"`><]/g, '').trim())
                        // 过滤掉纯代码路径（/api/xxx）、锚点占位符、纯数字和空字符
                        .filter(text => (
                            text.length >= 2 &&
                            !text.startsWith('/') &&
                            !text.startsWith('http') &&
                            !text.includes('BUNKER_API_ANCHOR') &&
                            !/^[0-9]+$/.test(text)
                        ))

                    allSemantics.push(...uiSemantics)
                }

                if (allAnchors.size > 0) {
                    const bunkerAnchors = Array.from(allAnchors).join('\n')
                    const pageKeywords = getSemanticKeywords(allSemantics)

                    const candidates = refinedApis.map(api => ({ ...api, score: getLocalScore(api, pageKeywords, fileName) }))
                        .filter(item => item.score > 0)
                        .sort((a, b) => b.score - a.score)
                        .slice(0, 20)

                    const finalCandidates = candidates.map(item => `${item.method} ${item.path} ${item.desc}`).join('\n')
                    const spinner = pod153.start(dialog.pod153.inactiveModule(fileName), 'yellow')
                    const result = await apiParser({ bunkerAnchors, realApis: finalCandidates })

                    if (result) {
                        for (const [filePath, rawCode] of Object.entries(fileContents)) {
                            let code = rawCode
                            let isModified = false
                            let hasQsImport = code.includes(`import qs from 'qs'`)

                            Object.entries(result).forEach(([anchor, { uri, method }]) => {
                                if (code.includes(anchor)) {
                                    isModified = true
                                    const cleanPath = uri.startsWith('/') ? uri : `/${uri}`
                                    let finalUri = cleanPath.startsWith('/api') ? cleanPath : `/api${cleanPath}`
                                    finalUri = finalUri.replace(/\{(\w+)\}/g, (_, key) => '${params.' + key + '}')
                                    const quotationMark = finalUri.includes('${params.') ? '`' : "'"
                                    if (method?.toUpperCase() === 'GET') {
                                        code = code.replaceAll(anchor, `request(\`${finalUri}?\${qs.stringify(params)}\`)`)
                                        if (!hasQsImport) {
                                            code = `import qs from 'qs'\n${code}`
                                            hasQsImport = true
                                        }
                                    } else {
                                        code = code.replaceAll(anchor, `request(${quotationMark}${finalUri}${quotationMark}, { method: '${method?.toUpperCase()}', body: params })`)
                                    }
                                }
                            })
                            if (isModified) {
                                fs.writeFileSync(filePath, code)
                            }
                        }

                        const pagesConfig = result?.['BUNKER_API_ANCHOR_pages']
                        if (pagesConfig) {
                            const { uri: pagesApi, method: pagesMethod } = pagesConfig
                            const schemas = apiData.definitions || apiData.components?.schemas || {}
                            const methodObj = apiData.paths[pagesApi]?.[pagesMethod] ?? apiData.paths[pagesApi]?.[pagesMethod?.toLowerCase()]
                            let schemaName = methodObj?.parameters?.flatMap(item => Object.values(item.schema ?? {})?.flatMap(def => def?.split('/')?.at(-1)))?.[0]
                            if (!schemaName && methodObj?.requestBody) {
                                const bodySchema = methodObj.requestBody.content?.['application/json']?.schema
                                schemaName = (bodySchema?.$ref || bodySchema?.items?.$ref)?.split('/')?.at(-1)
                            }
                            const parameters = schemas[schemaName]?.properties ?? {}
                            const enumParams = Object.entries(parameters)?.filter(([_, value]) => value.hasOwnProperty('enum')) || []
                            enumParamsMap[fileName] = contextStringify({
                                maxLength: 100,
                                context: Object.fromEntries(enumParams.map(([key, value]) => [`${key}Options`, value.enum?.map(opt => ({ label: opt, value: opt }))])),
                            })
                        }
                        pod153.success(spinner, dialog.pod153.signalSynchronized(Object.keys(result).length, fileName))
                        commander.report(dialog.bunker.disclaimer, 'yellow')
                    }
                }
            }
            return enumParamsMap
        } catch (e) {
            pod153.report(dialog.pod153.signalLinkFault(e.message), 'red')
        }
    }

    const enumParamsMap = await resurrection()

    return {
        falseTruth,
        resurrection,
        ...enumParamsMap,
    }
}