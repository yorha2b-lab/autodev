module.exports = async ({ llm, yorha, dialog, logistics }) => {

    const fs = require('fs')
    const path = require('path')

    const { apiParser } = llm
    const { pod153, commander } = yorha
    const { contextStringify } = logistics.formatter
    const { apiDoc, pagesDir } = logistics.supporter.getConfig()
    const { getLocalScore, getSemanticKeywords } = logistics.analyzer

    if (!apiDoc) return

    pod153.report(dialog.pod153.autonomousAddressing, 'magenta')

    try {
        const apiData = await fetch(apiDoc).then(res => res.json())
        const refinedApis = Object.entries(apiData.paths).flatMap(([apiUrl, methods]) => {
            return Object.entries(methods).map(([method, info]) => ({
                path: apiUrl,
                method: method?.toUpperCase() || '',
                desc: info.summary || info.description || 'N/A',
            }))
        })

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
                    pod153.success(spinner, dialog.pod153.signalSynchronized(Object.keys(result).length))
                    commander.report(dialog.bunker.disclaimer, 'yellow')
                }
            }
        }
        return enumParamsMap
    } catch (e) {
        pod153.report(dialog.pod153.signalLinkFault(e.message), 'red')
    }
}