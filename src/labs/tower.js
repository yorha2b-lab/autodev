module.exports = ({ yorha, dialog, logistics, headquarters }) => {

    const http = require('http')
    const zlib = require('zlib')
    const httpProxy = require('http-proxy')

    const { pod153, commander } = yorha
    const { unwrapSignal, isQuerySignal } = logistics.analyzer
    const { getConfig, killZombiePort, getJsonFingerprint } = logistics.supporter

    let server
    const TOWER_PORT = 42153
    const hackedRegistry = new Map()
    const sniperRegistry = new Set()
    const resurrectingSet = new Set()
    const proxy = httpProxy.createProxyServer({})
    const { routeMap = {}, proxyTarget } = getConfig()

    proxy.on('error', (err, req, res) => {
        if (!res.headersSent) {
            res.writeHead(502, { 'Content-Type': 'application/json' })
        }
        res.end(JSON.stringify({ error: 'Proxy target unreachable', detail: err.message }))
    })

    const erupt = async () => {
        proxy.on('proxyRes', function (proxyRes, req, res) {
            let body = []
            proxyRes.on('data', chunk => body.push(chunk))
            proxyRes.on('end', async () => {
                const buffer = Buffer.concat(body)
                const encoding = proxyRes.headers['content-encoding']
                try {
                    const rawBody = encoding === 'gzip' ? zlib.gunzipSync(buffer) : buffer
                    const json = JSON.parse(rawBody.toString())
                    const coreData = unwrapSignal(json)
                    if (!isQuerySignal(req, json, coreData)) {
                        return
                    }
                    let sampleData = coreData?.[0]
                    if (!sampleData) {
                        const { labs } = require('../awakening').get()
                        const council = await labs?.council
                        sampleData = council?.falseTruth?.(req.url, req.method)
                    }
                    if (!sampleData) return
                    const referer = req.headers.referer || 'http://localhost'
                    const urlPath = new URL(referer).pathname
                    const fileName = routeMap?.[urlPath] ?? urlPath.split('/').filter(Boolean).at(-1)
                    const fingerprint = getJsonFingerprint(coreData)
                    const lastFingerprint = hackedRegistry.get(fileName)
                    if (lastFingerprint === fingerprint) {
                        return
                    }
                    pod153.report(dialog.pod153.capturedRuntimeSignal(fileName))
                    await headquarters.reconciler({ fileName, data: [sampleData] })
                    hackedRegistry.set(fileName, fingerprint)
                } catch (e) {
                    // 非 JSON 信号，保持静默
                }
            })
        })

        server = http.createServer(async (req, res) => {
            if (!proxyTarget) {
                return
            }
            if (req.url.includes('BUNKER_API_ANCHOR')) {
                const referer = req.headers.referer || 'http://localhost'
                const urlPath = new URL(referer, 'http://localhost').pathname
                const moduleName = routeMap?.[urlPath] ?? urlPath.split('/').filter(Boolean).at(-1)

                if (moduleName && !resurrectingSet.has(moduleName)) {
                    resurrectingSet.add(moduleName)
                    try {
                        const { labs } = require('../awakening').get()
                        const council = await labs?.council
                        const resInfo = await council?.resurrection?.(moduleName)
                        const sniperData = resInfo?.sniperData
                        if (sniperData && Object.keys(sniperData).length > 0 && !sniperRegistry.has(moduleName)) {
                            sniperRegistry.add(moduleName)
                            pod153.report(dialog.pod153.capturedRuntimeSignal(moduleName))
                            await headquarters.reconciler({ fileName: moduleName, data: [sniperData] })
                        }
                    } finally {
                        resurrectingSet.delete(moduleName)
                    }
                }
                res.writeHead(200, { 'Content-Type': 'application/json' })
                res.end('{}')
                return
            }
            proxy.web(req, res, { target: proxyTarget, changeOrigin: true })
        })

        server.on('error', err => {
            if (err.code === 'EADDRINUSE') {
                killZombiePort(TOWER_PORT)
                setTimeout(() => server.listen(TOWER_PORT), 100)
            }
        })

        server.listen(TOWER_PORT, () => {
            commander.report(dialog.bunker.towerOnline(TOWER_PORT), 'magenta')
            commander.report(dialog.bunker.towerConnected(TOWER_PORT), 'magenta')
        })
    }

    const destroy = async () => await server?.close()

    erupt()

    return {
        erupt,
        destroy,
    }
}