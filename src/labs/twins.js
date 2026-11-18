let twinsBrowser = null

module.exports = ({ llm, yorha, dialog, logistics }) => {

    const fs = require('fs')
    const path = require('path')
    const chalk = require('chalk')

    const { maintain } = llm
    const { devola } = yorha
    const { dehydratePrd, dehydrateCode } = logistics.formatter
    const { isHttpURL, getConfig, readModuleFiles, launchPuppeteer } = logistics.supporter

    const { prdDoc, pagesDir } = getConfig()
    const sessionDir = path.join(process.cwd(), 'bunker', '.twins_session')

    const maintenance = async () => {

        if (!isHttpURL(prdDoc)) return

        devola.report(dialog.devola.start, 'magenta')
        twinsBrowser = await launchPuppeteer(sessionDir, twinsBrowser)
        const pages = await twinsBrowser.pages()
        const page = pages.length > 0 ? pages[0] : await twinsBrowser.newPage()

        await page.exposeFunction('nodeMaintainRequirement', async ({ prdText, moduleName }) => {
            if (!prdText || !moduleName) return
            const pageDir = path.join(process.cwd(), pagesDir, moduleName)

            if (!fs.existsSync(pageDir)) {
                devola.report(dialog.devola.noModule(pagesDir, moduleName), 'red')
                return
            }

            const sourceFiles = readModuleFiles(pageDir)
            if (sourceFiles.length === 0) {
                devola.report(dialog.devola.noCode(moduleName), 'red')
                return
            }

            const moduleCodeView = sourceFiles.map(file => `### 📄 文件:${file.relativeName}\njavascript:\n${dehydrateCode(file.content)}`).join('\n\n')
            devola.report(dialog.devola.loadedFiles(moduleName, sourceFiles.length), 'yellow')

            const startTime = Date.now()
            const spinner = devola.start(dialog.devola.comparing(moduleName))

            try {
                const cleanPrdText = dehydratePrd(prdText)
                const result = await maintain({ prdText: cleanPrdText, moduleName, moduleCodeView })
                const endTime = Date.now()

                devola.success(spinner, dialog.devola.finish)

                const duration = ((endTime - startTime) / 1000).toFixed(2)
                const gaps = result.unimplementedGaps || []
                const hasGaps = gaps.length > 0
                const divider = '─'.repeat(48)

                console.log('\n' + chalk.red.bold(`╭── 🔴 [YoRHa TWIN MAINTENANCE: DEVOLA] ──────────────────────────`))
                console.log(chalk.red(`│ `))
                const metaPills = [
                    chalk.bgCyan.black.bold(` MODULE `) + ` ` + chalk.bold.white(moduleName),
                    chalk.bgYellow.black.bold(` DURATION `) + ` ` + chalk.bold.white(`${duration}s`),
                    chalk.bgRed.white.bold(` DEFECTS `) + ` ` + chalk.bold.white(`${gaps.length} gaps`),
                ].join('   ')
                console.log(chalk.red(`│  `) + metaPills)
                console.log(chalk.red(`│ `))

                if (hasGaps) {
                    console.log(chalk.red(`├── `) + chalk.bold.yellow(`🔍 DEVOLA'S DIAGNOSTIC REPORT `) + chalk.red(divider))
                    console.log(chalk.red(`│ `))
                    gaps.forEach((gap, idx) => {
                        const num = String(idx + 1).padStart(2, '0')
                        console.log(chalk.red(`│  `) + chalk.bold.bgRed.white(` GAP #${num} `) + `  ` + chalk.bold.white(gap.feature))
                        if (gap.detail) {
                            console.log(chalk.red(`│`) + chalk.gray(`     ├─ `) + chalk.yellow(`🔍 `) + chalk.white(gap.feature))
                            console.log(chalk.red(`│`) + chalk.gray(`     └─ `) + chalk.red(`⚠️ `) + chalk.yellow(gap.detail))
                        }
                        console.log(chalk.red(`│ `))
                    })
                } else {
                    console.log(chalk.red(`├── `) + chalk.bold.green(`✨ ALL CLEAR `) + chalk.red(divider))
                    console.log(chalk.red(`│  `) + chalk.green(dialog.devola.allClear))
                    console.log(chalk.red(`│ `))
                }
                console.log(chalk.red.bold(`╰───────────────────────── [ Devola & Popola: "We won't let you fall" ] ─────────\n`))
            } catch (e) {
                devola.report(dialog.devola.exception(e.message), 'red')
            }
        })

        const browserDialog = { toastText: dialog.devola.toast }
        await page.evaluateOnNewDocument(({ toastText }) => {

            const showBunkerInput = () => new Promise(resolve => {
                const overlay = document.createElement('div')
                overlay.style.cssText = `
                        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                        background: rgba(0, 0, 0, 0.7); z-index: 9999999;
                        display: flex; align-items: center; justify-content: center;
                        backdrop-filter: blur(4px);
                    `
                overlay.innerHTML = `
                        <div style="background: #111; border: 2px solid #ff0055; padding: 24px; border-radius: 6px; box-shadow: 0 0 25px rgba(255,0,85,0.4); font-family: monospace; color: #ff0055; min-width: 380px;">
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 15px;">⚡ [YoRHa::双子星] 战术整备协议已就绪</div>
                            <div style="font-size: 12px; color: #aaa; margin-bottom: 14px;">请输入要检修与焊接的前端模块名 (如: ContractList):</div>
                            <input id="bunker-input" placeholder="输入模块名后回车..." style="width: 100%; box-sizing: border-box; background: #222; border: 1px solid #ff0055; color: #fff; padding: 10px 12px; font-size: 14px; font-family: monospace; outline: none; border-radius: 4px;" />
                            <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px;">
                                <span style="font-size: 11px; color: #666; margin-right: auto; line-height: 24px;">[ESC 取消 / Enter 确认]</span>
                            </div>
                        </div>
                    `
                document.body.appendChild(overlay)
                const lastModule = window.__lastModuleName || ''
                const input = overlay.querySelector('#bunker-input')
                input.value = lastModule
                setTimeout(() => {
                    input.focus()
                    input.select()
                }, 50)
                input.addEventListener('keydown', e => {
                    if (e.key === 'Enter' && input.value.trim()) {
                        const val = input.value.trim()
                        window.__lastModuleName = val
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
                        window.nodeMaintainRequirement({ prdText: selection, moduleName: moduleName.trim() })
                        const toast = document.createElement('div')
                        toast.innerText = toastText
                        toast.style.cssText = `
                                position: fixed; top: 20px; right: 20px; z-index: 999999;
                                background: rgba(0, 0, 0, 0.85); color: #ff0055;
                                border: 1px solid #ff0055; padding: 12px 24px;
                                font-size: 15px; font-family: monospace; border-radius: 4px;
                                box-shadow: 0 0 15px rgba(255, 0, 85, 0.5);
                                pointer-events: none; transition: opacity 0.4s ease;
                            `
                        document.body.appendChild(toast)
                        setTimeout(() => {
                            toast.style.opacity = '0'
                            setTimeout(() => toast.remove(), 400)
                        }, 1200)
                    }
                }
            })
        }, browserDialog)

        if (prdDoc) await page.goto(prdDoc)
        devola.report(dialog.devola.ready, 'green')
    }

    const destroy = async () => await twinsBrowser?.close()

    maintenance()

    return {
        destroy,
        maintenance,
    }
}