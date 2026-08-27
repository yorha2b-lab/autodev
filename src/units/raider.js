module.exports = {
    meta: {
        name: 'raider',
        inputs: ['image'],
        outputs: ['component-config'],
        description: 'extract reusable UI component from visual input',
        capabilities: ['vision', 'component-analysis', 'component-generation'],
        mission: `
        ## Partial CRUD Page
            局部 CRUD 页面或 UI 碎片。
            例如：
            - 仅包含表格
            - 仅包含表单
            - 仅包含筛选区域
            - 仅包含某个 CRUD 功能区域
            - 页面结构明显不完整
        `
    },
    execute: async ({ acp, mission }) => {

        const fs = require('fs')
        const chalk = require('chalk')
        const { llm, yorha, dialog, builder, logistics, briefings } = acp

        const { pod042 } = yorha
        const { raider } = briefings
        const { recognizePage } = llm
        const { formatPageconfig } = builder
        const { cleanCode, contextStringify } = logistics.formatter

        const startTime = Date.now()

        const spinner = pod042.start(dialog.pod042.visualPartCaptured)

        try {
            pod042.update(spinner, dialog.pod042.extractingUiMetadata)

            const pageConfig = await recognizePage({ prompt: raider, filePath: mission.input })

            let { tabs = [] } = pageConfig
            tabs = tabs.map(tab => ({ ...tab, children: `<${tab.key.at(0).toUpperCase()}${tab.key.slice(1)}/>` }))

            let { formItems, processedColumns } = formatPageconfig({ pageConfig })
            processedColumns = processedColumns.map(col => {
                delete col.type
                return col
            })

            const result = Object.fromEntries(Object.entries({ tabs, formItems, processedColumns }).filter(([key, value]) => value?.length > 0))

            let mainConfigStr = cleanCode(contextStringify({ context: result }))

            let optionsCodeStr = ''
            Object.keys(pageConfig.optionDict ?? {}).forEach(key => {
                const optionsArray = pageConfig.optionDict?.[key] ?? []
                const arrayItemsStr = optionsArray.map(opt => `    { label: '${opt.label}', value: '${opt.value}' }`).join(',\n')
                optionsCodeStr += `\nexport const ${key} = [\n${arrayItemsStr}\n]\n`
            })

            const finalResult = `${mainConfigStr}\n${optionsCodeStr}`
            const endTime = Date.now()
            spinner.stop()
            console.log(chalk.magenta(`\n┌────────────────── [ YoRHa Construction Output ] ─────────────────┐`))
            console.log(chalk.magenta(`│ Source: ${mission.input}`))
            console.log(chalk.magenta(`│ Protocol: Partial UI Fragment | Status: SUCCESS`))
            console.log(chalk.magenta(`├──────────────────────────────────────────────────────────────────┘`))
            console.log(chalk.white(finalResult))
            pod042.success(spinner, dialog.pod042.partialConstruction((endTime - startTime) / 1000))
            pod042.success(spinner, dialog.pod042.partialRecommendation)

            if (fs.existsSync(mission.input)) {
                fs.unlinkSync(mission.input)
            }

        } catch (error) {
            pod042.fail(spinner, dialog.pod042.partialConstructionAborted(error))
        }
    }
}