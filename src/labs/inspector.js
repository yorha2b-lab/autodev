const fs = require('fs')
const path = require('path')
const chalk = require('chalk')

module.exports = ({ llm, yorha, dialog, logistics }) => {

    const { pod153 } = yorha
    const { prdInspector } = llm
    const { pagesDir } = logistics.supporter.getConfig()
    const { dehydratePrd, dehydrateCode } = logistics.formatter
    const sessionDir = path.join(process.cwd(), 'bunker', '.chrome_session')

    const isHttpURL = str => {
        try {
            const url = new URL(str)
            return ['http:', 'https:'].includes(url.protocol)
        } catch {
            return false
        }
    }

    const readModuleFiles = (dir, rootDir = dir) => {
        let files = []
        const list = fs.readdirSync(dir, { withFileTypes: true })
        for (const item of list) {
            const fullPath = path.join(dir, item.name)
            if (item.isDirectory()) {
                if (!['node_modules', '.git', '__tests__'].includes(item.name)) {
                    files = files.concat(readModuleFiles(fullPath, rootDir))
                }
            } else if (/\.(jsx?|tsx?|json)$/i.test(item.name)) {
                files.push({
                    relativeName: path.relative(rootDir, fullPath).replace(/\\/g, '/'),
                    content: fs.readFileSync(fullPath, 'utf-8')
                })
            }
        }
        return files
    }

    return {
        audit: async prdDoc => {

            if (!isHttpURL(prdDoc)) return

            const puppeteer = require('puppeteer')
            pod153.report(dialog.pod153.inspectorStart, 'magenta')
            const browser = await puppeteer.launch({
                headless: false,
                handleSIGINT: false,
                defaultViewport: null,
                userDataDir: sessionDir,
                args: ['--start-maximized']
            })

            const pages = await browser.pages()
            const page = pages.length > 0 ? pages[0] : await browser.newPage()

            await page.exposeFunction('nodeAuditRequirement', async ({ prdText, moduleName }) => {
                if (!prdText || !moduleName) return
                const pageDir = path.join(process.cwd(), pagesDir, moduleName)
                const sourceFiles = readModuleFiles(pageDir)
                if (sourceFiles.length === 0) {
                    pod153.report(dialog.pod153.noCodeFile(moduleName), 'red')
                    return
                }
                const moduleCodeView = sourceFiles.map(file => `### 📄 文件:${file.relativeName}\njavascript:\n${dehydrateCode(file.content)}`).join('\n\n')
                pod153.report(dialog.pod153.loadedFiles(moduleName, sourceFiles.length), 'yellow')
                const startTime = Date.now()
                const spinner = pod153.start(dialog.pod153.comparingCodePrd(moduleName), 'yellow')
                try {
                    const cleanPrdText = dehydratePrd(prdText)
                    const result = await prdInspector({ prdText: cleanPrdText, moduleName, moduleCodeView })
                    const endTime = Date.now()
                    pod153.success(spinner, dialog.pod153.prdAuditFinish)
                    const duration = ((endTime - startTime) / 1000).toFixed(2)
                    const gaps = result.unimplementedGaps || []
                    const hasGaps = gaps.length > 0
                    const divider = '─'.repeat(48)
                    console.log('\n' + chalk.magenta(`╭── 🛰️  [YoRHa TACTICAL INSPECTION PROTOCOL] ──────────────────────────────────────────`))
                    console.log(chalk.magenta(`│ `))
                    const metaPills = [
                        chalk.bgCyan.black.bold(` MODULE `) + ` ` + chalk.bold.white(moduleName),
                        chalk.bgYellow.black.bold(` DURATION `) + ` ` + chalk.bold.white(`${duration}s`),
                        chalk.bgMagenta.black.bold(` AUDIT `) + ` ` + chalk.bold.white(`${sourceFiles.length} source files`),
                    ].join('   ')
                    console.log(chalk.magenta(`│  `) + metaPills)
                    console.log(chalk.magenta(`│ `))
                    if (hasGaps) {
                        console.log(chalk.magenta(`├── `) + chalk.bold.red(`🚨 TACTICAL DEFECTS`) + chalk.magenta(divider))
                        console.log(chalk.magenta(`│ `))
                        gaps.forEach((gap, idx) => {
                            const num = String(idx + 1).padStart(2, '0')
                            console.log(chalk.magenta(`│  `) + chalk.bold.bgRed.white(` GAP #${num} `) + `  ` + chalk.bold.red(gap.feature))
                            if (gap.detail) {
                                console.log(chalk.magenta(`│`) + chalk.gray(`     ├─ `) + chalk.yellow(`🔍 `) + chalk.white(gap.feature))
                                console.log(chalk.magenta(`│`) + chalk.gray(`     └─ `) + chalk.red(`⚠️ `) + chalk.yellow(gap.detail))
                            }
                            console.log(chalk.magenta(`│ `))
                        })
                    }
                    console.log(chalk.magenta(`╰─────────────────────────────── [ Pod 153 Verification Seal ] ────────────────────────\n`))
                } catch (e) {
                    pod153.report(dialog.pod153.inspectorException(e.message), 'red')
                }
            })
            const browserDialog = { inspectorToast: dialog.pod153.inspectorToast }
            await page.evaluateOnNewDocument(({ inspectorToast }) => {

                const showBunkerInput = () => new Promise(resolve => {
                    const overlay = document.createElement('div')
                    overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.65); z-index: 9999999;
            display: flex; align-items: center; justify-content: center;
            backdrop-filter: blur(3px);
        `
                    overlay.innerHTML = `
            <div style="background: #111; border: 2px solid #00ffcc; padding: 24px; border-radius: 6px; box-shadow: 0 0 25px rgba(0,255,204,0.4); font-family: monospace; color: #00ffcc; min-width: 380px;">
                <div style="font-weight: bold; margin-bottom: 8px; font-size: 15px;">⚡ [YoRHa 战术监察官] 需求情报已捕获</div>
                <div style="font-size: 12px; color: #888; margin-bottom: 14px;">请输入要对比的前端模块名 (如: ContractList):</div>
                <input id="bunker-input" placeholder="输入模块名后回车..." style="width: 100%; box-sizing: border-box; background: #222; border: 1px solid #00ffcc; color: #fff; padding: 10px 12px; font-size: 14px; font-family: monospace; outline: none; border-radius: 4px;" />
                <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px;">
                    <span style="font-size: 11px; color: #666; margin-right: auto; line-height: 24px;">[ESC 取消 / Enter 确认]</span>
                </div>
            </div>
        `
                    document.body.appendChild(overlay)
                    const input = overlay.querySelector('#bunker-input')
                    setTimeout(() => input.focus(), 50)
                    input.addEventListener('keydown', e => {
                        if (e.key === 'Enter' && input.value.trim()) {
                            const val = input.value.trim()
                            overlay.remove()
                            resolve(val)
                        }
                        if (e.key === 'Escape') {
                            overlay.remove()
                            resolve(null)
                        }
                    })
                    overlay.addEventListener('click', e => {
                        if (e.target === overlay) {
                            overlay.remove()
                            resolve(null)
                        }
                    })
                })

                window.addEventListener('contextmenu', async (e) => {
                    const selection = window.getSelection().toString().trim()
                    if (selection && selection.length > 5) {
                        e.preventDefault()
                        const moduleName = await showBunkerInput()
                        if (moduleName) {
                            window.nodeAuditRequirement({ prdText: selection, moduleName: moduleName.trim() })
                            const toast = document.createElement('div')
                            toast.innerText = inspectorToast
                            toast.style.cssText = `
                    position: fixed; top: 20px; right: 20px; z-index: 9999999;
                    background: rgba(0, 0, 0, 0.9); color: #ff00ff;
                    border: 1px solid #ff00ff; padding: 12px 24px;
                    font-size: 14px; font-family: monospace; border-radius: 4px;
                    box-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
                    pointer-events: none; transition: opacity 0.4s ease;
                `
                            document.body.appendChild(toast)
                            setTimeout(() => {
                                toast.style.opacity = '0'
                                setTimeout(() => toast.remove(), 400)
                            }, 2000)
                        }
                    }
                })
            }, browserDialog)
            if (prdDoc) {
                await page.goto(prdDoc)
            }
            pod153.report(dialog.pod153.inspectorReady, 'green')
            return browser
        }
    }
}