let globalBrowser = null

module.exports = ({ yorha, dialog }) => {

    const fs = require('fs')
    const path = require('path')
    const http = require('http')

    const { pod042 } = yorha
    const relayServerPort = 15342

    const isHttpURL = str => {
        try {
            const url = new URL(str)
            return ['http:', 'https:'].includes(url.protocol)
        } catch {
            return false
        }
    }

    const derivePageNameFromUrl = rawUrl => {
        const parsed = new URL(rawUrl)
        let routePath = parsed.hash ? parsed.hash.replace(/^#/, '') : parsed.pathname
        routePath = routePath.split('?')[0].replace(/^\/+|\/+$/g, '')
        if (!routePath) return 'Home'
        const parts = routePath.split(/[/\-_]/).filter(Boolean)
        return parts.at(-1) ?? 'capturedPage'
    }

    const scanHtmlFiles = (dir, rootDir = dir) => {
        let results = []
        const list = fs.readdirSync(dir)
        for (const file of list) {
            const fullPath = path.join(dir, file)
            const stat = fs.statSync(fullPath)
            if (stat.isDirectory()) {
                // 排除常见的非业务页面文件夹
                if (!['resources', 'plugins', 'images', 'files'].includes(file)) {
                    results = results.concat(scanHtmlFiles(fullPath, rootDir))
                }
            } else if (file.endsWith('.html')) {
                if (!['start.html', 'reload.html'].includes(file)) {
                    results.push({
                        fullPath,
                        name: path.basename(file, '.html'),
                        relativeUrl: path.relative(rootDir, fullPath).replace(/\\/g, '/'),
                    })
                }
            }
        }
        return results
    }

    const startStaticServer = staticDir => {
        const mimeTypes = {
            '.html': 'text/html',
            '.js': 'text/javascript',
            '.css': 'text/css',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml'
        }
        const server = http.createServer((req, res) => {
            const reqPath = decodeURIComponent(req.url.split('?')[0])
            const filePath = path.join(staticDir, reqPath === '/' ? 'index.html' : reqPath)
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
                const ext = path.extname(filePath).toLowerCase()
                res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' })
                fs.createReadStream(filePath).pipe(res)
            } else {
                res.writeHead(404)
                res.end('Not Found')
            }
        })
        return new Promise(resolve => server.listen(relayServerPort, () => resolve({ server })))
    }

    return {
        archeology: async targetUrl => {
            const puppeteer = require('puppeteer')
            const missionDir = path.join(process.cwd(), 'bunker', 'mission')

            if (isHttpURL(targetUrl)) {
                pod042.report(dialog.pod042.startScout, 'green')
                const sessionDir = path.join(process.cwd(), 'bunker', '.chrome_session')
                let isBrowserAlive = false
                if (globalBrowser) {
                    try {
                        await globalBrowser.pages()
                        isBrowserAlive = true
                    } catch (e) {
                        globalBrowser = null
                    }
                }

                if (!isBrowserAlive) {

                    ['SingletonLock', 'SingletonSocket', 'SingletonCookie'].forEach(file => {
                        try { fs.unlinkSync(path.join(sessionDir, file)) } catch (e) { }
                    })

                    globalBrowser = await puppeteer.launch({
                        headless: false,
                        handleSIGINT: false,
                        defaultViewport: null,
                        userDataDir: sessionDir,
                        args: ['--start-maximized']
                    })
                }

                const pages = await globalBrowser.pages()
                const page = pages.length > 0 ? pages[0] : await globalBrowser.newPage()

                try {

                    const browserDialog = { capturedToast: dialog.pod042.capturedToast }

                    await page.exposeFunction('nodeTakeScreenshot', async () => {
                        const currentUrl = await page.url()
                        const pageName = derivePageNameFromUrl(currentUrl)
                        const savePath = path.join(missionDir, `${pageName}.png`)
                        await page.screenshot({ path: savePath, fullPage: true })
                        pod042.report(dialog.pod042.capturedPage(pageName), 'green')
                    })

                    await page.evaluateOnNewDocument(({ capturedToast }) => {
                        if (window.__hasBunkerListener__) return
                        window.__hasBunkerListener__ = true
                        window.addEventListener('contextmenu', (e) => {
                            e.preventDefault()
                            if (window.nodeTakeScreenshot) {
                                window.nodeTakeScreenshot()
                            }
                            const toast = document.createElement('div')
                            toast.innerText = capturedToast
                            toast.style.cssText = `
                            position: fixed; top: 20px; right: 20px; z-index: 999999;
                            background: rgba(0, 0, 0, 0.85); color: #00ffcc;
                            border: 1px solid #00ffcc; padding: 12px 24px;
                            font-size: 15px; font-family: monospace; border-radius: 4px;
                            box-shadow: 0 0 15px rgba(0, 255, 204, 0.5);
                            pointer-events: none; transition: opacity 0.4s ease;
                        `
                            document.body.appendChild(toast)
                            setTimeout(() => {
                                toast.style.opacity = '0'
                                setTimeout(() => toast.remove(), 400)
                            }, 1200)
                        })
                    }, browserDialog)
                } catch (error) { }

                await page.goto(targetUrl)
                pod042.report(dialog.pod042.scoutReady, 'green')
                return globalBrowser
            }

            const localDir = path.resolve(targetUrl)
            if (!fs.existsSync(localDir) || !fs.statSync(localDir).isDirectory()) {
                pod042.report(dialog.pod042.relicAccessFailed(localDir), 'red')
                return
            }
            pod042.report(dialog.pod042.swarmScanning(localDir), 'green')
            const htmlPages = scanHtmlFiles(localDir)
            if (!htmlPages.length) {
                pod042.report(dialog.pod042.noAvailablePages, 'yellow')
                return
            }
            pod042.report(dialog.pod042.deployRelayServer(htmlPages.length, relayServerPort), 'cyan')
            const { server } = await startStaticServer(localDir)
            let browser
            try {
                // 💡 锁死标准宽屏分辨率，防止变形折叠
                browser = await puppeteer.launch({
                    headless: 'new',
                    defaultViewport: { width: 1440, height: 900 }
                })
                const page = await browser.newPage()
                let capturedCount = 0

                for (const item of htmlPages) {
                    try {
                        await page.setViewport({ width: 1440, height: 900 })
                        const pageUrl = `http://localhost:${relayServerPort}/${encodeURI(item.relativeUrl)}`
                        await page.goto(pageUrl, { waitUntil: 'networkidle0', timeout: 15000 })
                        // 稍作等待，确保渲染完毕
                        await new Promise(r => setTimeout(r, 600))
                        const contentWidth = await page.evaluate(() => {
                            let maxW = 1440
                            document.querySelectorAll('*').forEach(el => {
                                const style = window.getComputedStyle(el)
                                if (['auto', 'scroll'].includes(style.overflowX) || el.scrollWidth > el.clientWidth) {
                                    el.style.overflowX = 'visible'
                                    el.style.width = 'max-content' // 强行把宽度撑到真实列宽！
                                }
                                // 记录全页面最宽的物理尺寸
                                if (el.scrollWidth > maxW) {
                                    maxW = el.scrollWidth
                                }
                            })
                            return maxW
                        })
                        await page.setViewport({
                            width: Math.min(contentWidth + 80, 3840),
                            height: 900
                        })
                        // 稍等 200ms 让重绘完成
                        await new Promise(r => setTimeout(r, 200))
                        const savePath = path.join(missionDir, `${item.name}.png`)
                        await page.screenshot({ path: savePath, fullPage: true })
                        capturedCount++
                        pod042.report(dialog.pod042.captureProgress(capturedCount, htmlPages.length, item.name), 'green')
                    } catch (err) {
                        pod042.report(dialog.pod042.captureFailed(item.name, err.message), 'yellow')
                    }
                }
                pod042.report(dialog.pod042.swarmVictory(capturedCount), 'magenta')
            } finally {
                // 💡 绝对保证释放资源，绝不霸占 15342 端口
                await browser?.close()
                server?.close()
            }
        }
    }
}