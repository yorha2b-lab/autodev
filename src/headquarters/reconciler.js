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

    const spinner = pod153.start(dialog.pod153.reconEncryptedData(fileName))

    try {
        if (!fs.existsSync(resourcePath)) {
            pod153.fail(spinner, dialog.pod153.unknownModule(fileName))
            return
        }

        let resourceStr = fs.readFileSync(resourcePath, 'utf8')

        nineS.update(spinner, dialog.nineS.scanningField)

        const extractKeys = str => {
            const keys = []
            const regex = /(dataIndex|name)\s*:\s*['"]([^'"]+)['"]/g
            let match
            while ((match = regex.exec(str)) !== null) {
                keys.push(match[2])
            }
            return Array.from(new Set(keys.filter(key => key !== 'index')))
        }

        const result = await reconciler({ responseStr: JSON.stringify(data), resourceStr: extractKeys(resourceStr).join(',') })
        let changeCount = 0
        const resultMapping = {}
        Object.entries(result).forEach(([oldField, newField]) => {
            if (oldField === newField) return
            const regex = new RegExp(`(dataIndex|name)\\s*:\\s*['"]${oldField}['"]`, 'g')
            resourceStr = resourceStr.replace(regex, `$1: '${newField}'`)
            changeCount++
            resultMapping[oldField] = newField
        })

        fs.writeFileSync(resourcePath, resourceStr)
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