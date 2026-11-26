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

    const getDefinitions = () => apiData.definitions || apiData.components?.schemas || {}

    const resolveSchema = (schema, visited = new Set()) => {
        if (!schema) return null
        const definitions = getDefinitions()
        let cur = schema
        let nextVisited = visited

        if (cur.$ref) {
            const refName = cur.$ref.split('/').at(-1)
            if (visited.has(refName)) return null
            nextVisited = new Set(visited)
            nextVisited.add(refName)
            cur = definitions[refName]
            if (!cur) return null
            if (cur.$ref) return resolveSchema(cur, nextVisited)
        }

        if (Array.isArray(cur.allOf)) {
            const mergedProps = {}
            let mergedDesc = cur.description || cur.title
            for (const sub of cur.allOf) {
                const { schema: resolved } = resolveSchema(sub, nextVisited) || {}
                if (resolved?.properties) Object.assign(mergedProps, resolved.properties)
                if (!mergedDesc && (resolved?.description || resolved?.title)) {
                    mergedDesc = resolved.description || resolved.title
                }
            }
            return { schema: { ...cur, type: 'object', properties: mergedProps, description: mergedDesc }, visited: nextVisited }
        }

        const variant = cur.oneOf || cur.anyOf
        if (Array.isArray(variant) && variant.length > 0) {
            const picked = variant.find(v => v.type !== 'null') || variant[0]
            return resolveSchema(picked, nextVisited)
        }

        return { schema: cur, visited: nextVisited }
    }

    const unwrapWrapper = (schema, visited = new Set()) => {
        const res = resolveSchema(schema, visited)
        if (!res?.schema?.properties) return res
        const props = res.schema.properties
        const keys = Object.keys(props)
        const payloadKey = ['data', 'result', 'payload', 'body'].find(k => k in props)
        const wrapperSet = new Set(['code', 'msg', 'message', 'success', 'status', 'timestamp', 'traceId', 'data', 'result', 'payload', 'body'])
        if (payloadKey && keys.length <= 6 && keys.every(k => wrapperSet.has(k) || k.toLowerCase().includes('err'))) {
            return resolveSchema(props[payloadKey], res.visited)
        }
        return res
    }

    const flattenSchema = (schema, flat = {}, visited = new Set(), depth = 0) => {
        if (!schema || depth > 5) return flat
        const resolved = resolveSchema(schema, visited)
        if (!resolved?.schema) return flat

        const { schema: cur, visited: nextVisited } = resolved
        if (cur.type === 'array' || cur.items) {
            return flattenSchema(cur.items, flat, nextVisited, depth + 1)
        }

        if (cur.properties) {
            for (const [propKey, propSchema] of Object.entries(cur.properties)) {
                const subResolved = resolveSchema(propSchema, nextVisited)
                const sub = subResolved?.schema
                const desc = propSchema.description || propSchema.title || sub?.description || sub?.title || propKey

                const isObj = Boolean(sub?.properties || sub?.allOf)
                const isArr = Boolean(sub?.type === 'array' || sub?.items)

                if (isObj) {
                    flattenSchema(propSchema, flat, nextVisited, depth + 1)
                } else if (isArr) {
                    if (!(propKey in flat)) flat[propKey] = desc
                    flattenSchema(sub.items, flat, subResolved.visited, depth + 1)
                } else {
                    if (!(propKey in flat)) flat[propKey] = desc
                }
            }
        }
        return flat
    }

    const findMatchedPath = apiUrl => {
        const cleanUrl = (apiUrl || '').split('?')[0]
        const noApiPrefix = cleanUrl.replace(/^\/api(?=\/)/, '')
        return Object.keys(apiData.paths || {}).find(p => (p === cleanUrl || p === noApiPrefix || cleanUrl.endsWith(p) || p.endsWith(noApiPrefix)))
    }

    const resurrection = async moduleName => {
        try {
            if (!moduleName) return null
            const modulePath = path.join(process.cwd(), pagesDir, moduleName)
            if (!fs.existsSync(modulePath) || !fs.statSync(modulePath).isDirectory()) return null

            const subFiles = fs.readdirSync(modulePath).filter(f => f.endsWith('.js') || f.endsWith('.jsx'))
            if (subFiles.length === 0) return null

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
                    const sniperData = {}

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

                    // 只要存在 sniper 锚点，顺手把匹配到的接口请求体/响应体全部拍平合并
                    Object.entries(result).forEach(([anchor, { uri, method }]) => {
                        if (/sniper/i.test(anchor)) {
                            const extracted = soulBox(uri, method)
                            Object.entries(extracted).forEach(([k, v]) => {
                                if (!(k in sniperData)) sniperData[k] = v
                            })
                        }
                    })

                    const pagesConfig = result?.['BUNKER_API_ANCHOR_pages']
                    if (pagesConfig) {
                        const { uri: pagesApi, method: pagesMethod } = pagesConfig
                        const schemas = getDefinitions()
                        const methodObj = apiData.paths[pagesApi]?.[pagesMethod] ?? apiData.paths[pagesApi]?.[pagesMethod?.toLowerCase()]
                        let schemaName = methodObj?.parameters?.flatMap(item => Object.values(item.schema ?? {})?.flatMap(def => typeof def === 'string' ? def.split('/')?.at(-1) : []))?.[0]
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
                    return { result, sniperData }
                }
            }
            return null
        } catch (e) {
            pod153.report(dialog.pod153.signalLinkFault(e.message), 'red')
            return null
        }
    }

    const soulBox = (apiUrl, method = 'post') => {
        const matchedPath = findMatchedPath(apiUrl)
        if (!matchedPath) return {}

        const pathObj = apiData.paths?.[matchedPath] || {}
        const methodObj = pathObj[method.toLowerCase()] || pathObj.post || pathObj.put || pathObj.get
        if (!methodObj) return {}

        const reqSchema = methodObj?.requestBody?.content?.['application/json']?.schema ||
            Object.values(methodObj?.requestBody?.content || {})[0]?.schema ||
            methodObj?.parameters?.find(p => p.in === 'body')?.schema

        const reqFlat = {}
        if (reqSchema) {
            flattenSchema(reqSchema, reqFlat)
        }
        (methodObj?.parameters || []).forEach(p => {
            if (['query', 'formData'].includes(p.in) && p.name && !(p.name in reqFlat)) {
                reqFlat[p.name] = p.description || p.title || p.name
            }
        })

        const resSchema = methodObj?.responses?.['200']?.schema || methodObj?.responses?.['200']?.content?.['application/json']?.schema

        const resFlat = {}
        if (resSchema) {
            const unwrapped = unwrapWrapper(resSchema)
            if (unwrapped?.schema) {
                flattenSchema(unwrapped.schema, resFlat, unwrapped.visited, 0)
            }
        }

        // 详情查询优先保留响应体字段，编辑/保存优先保留请求体字段
        const isDetailApi = /detail|info|view|get/i.test(matchedPath) || method.toLowerCase() === 'get'
        return isDetailApi ? { ...reqFlat, ...resFlat } : { ...resFlat, ...reqFlat }
    }

    const falseTruth = (apiUrl, method = 'post') => {
        const matchedPath = findMatchedPath(apiUrl)
        if (!matchedPath) return null
        const definitions = getDefinitions()
        const methodObj = apiData.paths?.[matchedPath]?.[method.toLowerCase()]
        const rootSchema = methodObj?.responses?.['200']?.schema || methodObj?.responses?.['200']?.content?.['application/json']?.schema
        if (!rootSchema) return null

        const resolveRef = refStr => {
            if (!refStr) return null
            return definitions[refStr.split('/').at(-1)]
        }

        const wrapperDef = resolveRef(rootSchema.$ref)
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

    const core = { soulBox, falseTruth, resurrection }

    return new Proxy(core, {
        get(target, prop) {
            if (prop in target) return target[prop]
            return enumParamsMap[prop]
        }
    })
}