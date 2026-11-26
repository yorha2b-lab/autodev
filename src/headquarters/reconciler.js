const fs = require('fs')
const path = require('path')
const chalk = require('chalk')

module.exports = async ({ data, fileName }) => {

    const { llm, labs, yorha, dialog, logistics } = require('../awakening').get()

    const { reconciler } = llm
    const { nineS, pod153 } = yorha
    const { cleanCode } = logistics.formatter
    const { pagesDir } = logistics.supporter.getConfig()

    const startTime = Date.now()
    const resourcePath = path.join(process.cwd(), pagesDir, fileName, 'resource.js')
    const enumParams = (await labs?.council)?.[fileName] ?? '{}'

    const extractFields = str => {
        const fieldMap = new Map()
        const stack = []
        let i = 0

        const skipString = quote => {
            i++
            while (i < str.length) {
                if (str[i] === '\\') { i += 2; continue }
                if (str[i] === quote) break
                i++
            }
        }

        while (i < str.length) {
            const ch = str[i]
            if (ch === "'" || ch === '"' || ch === '`') {
                skipString(ch)
            } else if (ch === '/' && str[i + 1] === '/') {
                while (i < str.length && str[i] !== '\n') i++
            } else if (ch === '/' && str[i + 1] === '*') {
                i += 2
                while (i < str.length && !(str[i] === '*' && str[i + 1] === '/')) i++
                i++
            } else if (ch === '{' || ch === '[') {
                stack.push({ type: ch, start: i, children: [] })
            } else if ((ch === '}' || ch === ']') && stack.length > 0) {
                const top = stack[stack.length - 1]
                if ((top.type === '{' && ch === '}') || (top.type === '[' && ch === ']')) {
                    stack.pop()
                    if (stack.length > 0) {
                        stack[stack.length - 1].children.push([top.start, i + 1])
                    }
                    if (top.type === '{') {
                        let cleanObj = ''
                        let cursor = top.start
                        for (const [cStart, cEnd] of top.children) {
                            cleanObj += str.slice(cursor, cStart)
                            cursor = cEnd
                        }
                        cleanObj += str.slice(cursor, i + 1)

                        const keyMatch = cleanObj.match(/(?:dataIndex|name)\s*:\s*(?:'([^']*)'|"([^"]*)")/)
                        const key = keyMatch?.[1] ?? keyMatch?.[2]
                        if (key && key !== 'index') {
                            const labelMatch = cleanObj.match(/(?:title|label)\s*:\s*(?:'([^']*)'|"([^"]*)")/)
                            const label = (labelMatch?.[1] ?? labelMatch?.[2] ?? '').trim()
                            if (!fieldMap.has(key) || (!fieldMap.get(key) && label)) {
                                fieldMap.set(key, label)
                            }
                        }
                    }
                }
            }
            i++
        }

        return Array.from(fieldMap.entries()).map(([key, label]) => (label ? `${key}(${label})` : key))
    }

    const spinner = pod153.start(dialog.pod153.reconEncryptedData(fileName))

    try {
        if (!fs.existsSync(resourcePath)) {
            pod153.fail(spinner, dialog.pod153.unknownModule(fileName))
            return
        }

        let resourceStr = fs.readFileSync(resourcePath, 'utf8')

        nineS.update(spinner, dialog.nineS.scanningField)

        const fieldsWithLabel = extractFields(resourceStr)
        const result = await reconciler({ responseStr: JSON.stringify(data), resourceStr: fieldsWithLabel.join(',') })

        const pendingMap = {}
        Object.entries(result || {}).forEach(([rawOld, rawNew]) => {
            const oldField = String(rawOld).split('(')[0].trim()
            const newField = String(rawNew ?? '').split('(')[0].trim()
            if (oldField && newField && oldField !== newField) {
                pendingMap[oldField] = newField
            }
        })

        const resultMapping = {}
        const keys = Object.keys(pendingMap)
        if (keys.length > 0) {
            const escaped = keys.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
            const replaceRegex = new RegExp(`(dataIndex|name)\\s*:\\s*(['"])(${escaped})\\2`, 'g')
            resourceStr = resourceStr.replace(replaceRegex, (full, prop, quote, oldField) => {
                const newField = pendingMap[oldField]
                if (!newField || oldField === newField) return full
                resultMapping[oldField] = newField
                return `${prop}: '${newField}'`
            })
        }

        const changeCount = Object.keys(resultMapping).length
        if (changeCount > 0) {
            fs.writeFileSync(resourcePath, resourceStr)
        }

        const endTime = Date.now()

        pod153.success(spinner, dialog.pod153.bridgeProtocolComplete(changeCount, (endTime - startTime) / 1000))

        if (changeCount > 0) {
            console.log(chalk.magenta(`\n┌────── [ YoRHa Autonomous Backend Alignment ] ──────┐`))
            const maxOldFieldLength = Math.max(...Object.keys(resultMapping).map(key => key.length))
            Object.entries(resultMapping).forEach(([oldField, newField]) => {
                const padding = ' '.repeat(Math.max(1, maxOldFieldLength + 1 - oldField.length))
                console.log(
                    chalk.yellow(` │  `) +
                    chalk.yellow(oldField) +
                    padding +
                    chalk.cyan(` ->  `) +
                    chalk.white(newField)
                )
            })
            console.log(chalk.magenta(`└────────────────────────────────────────────────────┘`))
        }

        if (enumParams !== '{}') {
            console.log(chalk.magenta(`\n┌──────── [ YoRHa Physical Assembly: Enum Genomes ] ────────┐`))
            console.log(chalk.gray(dialog.bunker.copyEnum))
            console.log(chalk.white(cleanCode(enumParams)))
            console.log(chalk.magenta(`├───────────────────────────────────────────────────────────┘`))
        }

    } catch (error) {
        pod153.fail(spinner, dialog.pod153.alignmentFailed(error))
    }
}