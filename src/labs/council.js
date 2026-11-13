module.exports = async ({ llm, yorha, dialog, logistics }) => {

    const fs = require('fs')
    const path = require('path')
    const JSON5 = require('json5')

    const { council } = llm
    const { pod153, commander } = yorha
    const { contextStringify } = logistics.formatter
    const { apiDoc, pagesDir } = logistics.supporter.getConfig()
    const { getLocalScore, unwrapSchemaRef, getSemanticKeywords } = logistics.analyzer

    if (!apiDoc) return

    pod153.report(dialog.pod153.autonomousAddressing, 'magenta')

    const enumParamsMap = {}
    const apiResponse = await fetch(apiDoc)
    const text = await apiResponse.text()
    const apiData = JSON5.parse(text)

    const validMethods = ['get', 'post', 'put', 'delete', 'patch']
    const refinedApis = Object.entries(apiData.paths || {}).flatMap(([apiUrl, methods]) => {
        return Object.entries(methods)
            .filter(([method]) => validMethods.includes(method.toLowerCase()))
            .map(([method, info]) => ({
                path: apiUrl,
                tags: info.tags,
                method: method?.toUpperCase() || '',
                desc: info.summary || info.description || 'N/A',
            }))
    })

    const falseTruth = (apiUrl, method = 'post') => {
        const cleanUrl = apiUrl.split('?')[0]
        const matchedPath = Object.keys(apiData.paths || {}).find(p => cleanUrl.endsWith(p) || p.endsWith(cleanUrl))
        if (!matchedPath) return null
        const definitions = apiData.definitions || apiData.components?.schemas || {}
        const methodObj = apiData.paths?.[matchedPath]?.[method.toLowerCase()]
        const rootSchema = methodObj?.responses?.['200']?.schema || methodObj?.responses?.['200']?.content?.['application/json']?.schema
        if (!rootSchema) return null

        const resolveRef = (refStr) => {
            if (!refStr) return null
            const refName = refStr.split('/').at(-1)
            return definitions[refName]
        }

        let wrapperDef = resolveRef(rootSchema.$ref)
        const rowRef = unwrapSchemaRef(wrapperDef)
        const rowDef = resolveRef(rowRef)
        if (!rowDef?.properties) return null

        return Object.fromEntries(
            Object.entries(rowDef.properties).map(([fieldName, propMeta]) => [
                fieldName,
                propMeta.description || propMeta.title || fieldName
            ])
        )
    }

    const resurrection = async moduleName => {
        try {
            if (!moduleName) return
            const modulePath = path.join(process.cwd(), pagesDir, moduleName)
            if (!fs.existsSync(modulePath) || !fs.statSync(modulePath).isDirectory()) return

            const subFiles = fs.readdirSync(modulePath).filter(f => f.endsWith('.js') || f.endsWith('.jsx'))
            if (subFiles.length === 0) return

            const fileContents = {}
            const allSemantics = []
            const allAnchors = new Set()

            for (const file of subFiles) {
                const filePath = path.join(modulePath, file)
                const code = fs.readFileSync(filePath, 'utf-8')
                fileContents[filePath] = code

                const anchors = code.match(/BUNKER_API_ANCHOR_\w+/g) || []
                anchors.forEach(a => allAnchors.add(a))

                const textMatches = code.match(/(?:['"`]([^'"`\n]{2,})['"`]|>([^<>{}\n]{2,})<)/g) || []
                const uiSemantics = textMatches
                    .map(str => str.replace(/['"`><]/g, '').trim())
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

                const candidates = refinedApis
                    .map(api => ({ ...api, score: getLocalScore(api, pageKeywords, moduleName) }))
                    .filter(item => item.score > 0)
                    .sort((a, b) => b.score - a.score)
                    .slice(0, 50)

                const finalCandidates = candidates.map(item => `${item.method} ${item.path} ${item.desc}`).join('\n')
                const spinner = pod153.start(dialog.pod153.inactiveModule(moduleName), 'yellow')
                const result = await council({ bunkerAnchors, realApis: finalCandidates })

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

                                let newRequestCode = ''
                                if (method?.toUpperCase() === 'GET') {
                                    newRequestCode = `request(\`${finalUri}?\${qs.stringify(params)}\`)`
                                    if (!hasQsImport) {
                                        code = `import qs from 'qs'\n${code}`
                                        hasQsImport = true
                                    }
                                } else {
                                    newRequestCode = `request(${quotationMark}${finalUri}${quotationMark}, { method: '${method?.toUpperCase()}', body: params })`
                                }

                                const anchorRegex = new RegExp(`request\\(\\s*['"\`][^'"\`]*?${anchor}[^'"\`]*?['"\`][^)]*?\\)|${anchor}`, 'g')
                                code = code.replace(anchorRegex, () => newRequestCode)
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
                        enumParamsMap[moduleName] = contextStringify({
                            maxLength: 100,
                            context: Object.fromEntries(enumParams.map(([key, value]) => [`${key}Options`, value.enum?.map(opt => ({ label: opt, value: opt }))])),
                        })
                    }
                    pod153.success(spinner, dialog.pod153.signalSynchronized(Object.keys(result).length, moduleName))
                    commander.report(dialog.bunker.disclaimer, 'yellow')
                }
            }
        } catch (e) {
            pod153.report(dialog.pod153.signalLinkFault(e.message), 'red')
        }
    }

    const core = { falseTruth, resurrection }

    return new Proxy(core, {
        get(target, prop) {
            if (prop in target) return target[prop]
            return enumParamsMap[prop]
        }
    })
}