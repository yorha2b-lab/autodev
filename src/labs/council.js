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

                const chinese = code.match(/[\u4e00-\u9fa5][\u4e00-\u9fa5A-Za-z0-9？。，、：；！（） ]*/g) || []
                allSemantics.push(...chinese)
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
                        const definitions = (apiData.paths[pagesApi]?.[pagesMethod] ?? apiData.paths[pagesApi]?.[pagesMethod?.toLowerCase()])?.parameters?.flatMap(item => Object.values(item.schema ?? {})?.flatMap(def => def?.split('/')?.at(-1))) || []
                        const parameters = apiData.definitions?.[definitions[0]]?.properties ?? {}
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