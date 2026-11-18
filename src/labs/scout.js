let scoutBrowser = null

module.exports = ({ yorha, dialog, logistics }) => {

    const fs = require('fs')
    const path = require('path')

    const { pod042 } = yorha
    const relayServerPort = 15342
    const { isHttpURL, getConfig, scanHtmlFiles, launchPuppeteer, startStaticServer, derivePageNameFromUrl } = logistics.supporter

    const { remains } = getConfig()
    const missionDir = path.join(process.cwd(), 'bunker', 'mission')
    const sessionDir = path.join(process.cwd(), 'bunker', '.scout_session')

    const swarmSweep = async () => {
        const localDir = path.resolve(remains)
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
        const { server } = await startStaticServer(localDir, relayServerPort)
        let browser
        try {
            // 💡 锁死标准宽屏分辨率，防止变形折叠
            const puppeteer = require('puppeteer')
            browser = await puppeteer.launch({ headless: 'new', defaultViewport: { width: 1440, height: 900 } })
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

    const onlineInvestigation = async () => {
        pod042.report(dialog.pod042.startScout, 'green')
        scoutBrowser = await launchPuppeteer(sessionDir, scoutBrowser)
        const pages = await scoutBrowser.pages()
        const page = pages.length > 0 ? pages[0] : await scoutBrowser.newPage()

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

        if (page.url() === 'about:blank') await page.goto(remains)
        pod042.report(dialog.pod042.scoutReady, 'green')
    }

    const destroy = async () => await scoutBrowser?.close()

    const archeology = () => isHttpURL(remains) ? onlineInvestigation() : swarmSweep()

    archeology()

    return {
        destroy,
        archeology
    }
}