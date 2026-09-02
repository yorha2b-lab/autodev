module.exports = ({ template, logistics, headquarters }) => {

    const { wrapCode, cleanCode, contextStringify } = logistics.formatter
    const { needMock, responseSuccess } = logistics.supporter.getConfig()
    const { indexTpl, resourceTpl } = headquarters.designer({ template, logistics })

    const formatPageconfig = ({ pageConfig }) => {

        const codePresets = {
            money: 'text => moneyRender(text)',
            date: 'text => timeRender({time: text})',
            index: '(_, record, index) => index + 1',
            tag: `text => <Tag color='magenta'>{text}</Tag>`,
            link: `text => <a href='#' target='_blank'>{text}</a>`,
            badge: `text => <Badge status='success' text={text} />`,
            enum: dataIndex => `text => ${dataIndex}Options.find(item => item.value === text)?.label ?? text`,
        }

        const columns = pageConfig.table?.columns ?? pageConfig?.columns ?? []

        const tableDicts = columns?.filter(item => item.type === 'enum')?.map(item => `${item.dataIndex}Options`) ?? []
        const formDicts = pageConfig.formItems?.filter(item => item.type === 'select')?.map(item => `${item.name}Options`) ?? []
        const dictBlocks = Array.from(new Set([...formDicts, ...tableDicts]))

        const formItems = pageConfig.formItems?.map(item => {
            if (item.type === 'text') {
                delete item.type
            }
            return {
                ...item,
                ...(item.type === 'select' ? { options: wrapCode(`${item.name}Options`) } : {})
            }
        })

        const processedColumns = columns?.map(col => {
            if (['image'].includes(col.type)) {
                return { ...col, renderAction: true }
            }
            if (col.type && codePresets[col.type]) {
                const renderCode = typeof codePresets[col.type] === 'function' ? codePresets[col.type](col.dataIndex) : codePresets[col.type]
                return { ...col, render: wrapCode(renderCode) }
            }
            return col
        })

        return { formItems, dictBlocks, processedColumns }
    }

    const generateSmartImports = ({ module, hasTabs, bodyCode, hasFormItems }) => {

        const hooksLib = ['useTableQuery']
        const utilsLib = ['timeRender', 'moneyRender']
        const reactLib = ['useState', 'useEffect', 'useRef', 'useMemo']
        const componentsLib = ['MyTable', 'MyImage', 'MyModalForm', 'MySearchForm']
        const antdLib = ['Tag', 'Card', 'Badge', 'Space', 'Modal', 'Alert', 'Image', 'Table', 'Input', 'Select', 'Button']

        const usedAntd = antdLib.filter(name => new RegExp(`\\b${name}\\b`).test(bodyCode))
        const usedUtils = utilsLib.filter(name => new RegExp(`\\b${name}\\b`).test(bodyCode))
        const usedHooks = hooksLib.filter(name => new RegExp(`\\b${name}\\b`).test(bodyCode))
        const usedReact = reactLib.filter(name => new RegExp(`\\b${name}\\b`).test(bodyCode))
        const usedComps = componentsLib.filter(name => new RegExp(`\\b${name}\\b`).test(bodyCode))

        const imports = [
            usedReact.length && `import { ${usedReact.join(', ')} } from 'react'`,
            usedAntd.length && `import { ${hasFormItems && module === 'index' ? 'Form, ' : ''}${usedAntd.join(', ')} } from 'antd'`,
            ...usedHooks.map(hook => `import { ${hook} } from '../../hooks/${hook}'`),
            ...usedComps.map(comp => `import { ${comp} } from '../../components/${comp}'`),
            ...(module === 'index' ? [
                `import { request } from '../../utils/request'`,
                `import { formatQuery } from '../../utils/utils'`,
                `import { ${hasTabs ? 'tabs, ' : ''}${hasFormItems ? 'formItems, ' : ''}modalItems, tableColumns} from './resource'`
            ] : [
                usedUtils.length && `import { ${usedUtils.join(', ')} } from '../../utils/utils'`
            ]),
        ].sort((a, b) => a.length - b.length)

        return imports.filter(Boolean).join('\n')
    }

    return {
        formatPageconfig,
        resource: ({ pageConfig }) => {

            const { formItems, processedColumns, dictBlocks } = formatPageconfig({ pageConfig })

            const hasTabs = pageConfig.tabs?.length > 0
            const hasFormItems = pageConfig.formItems?.length > 0
            const tabKeys = pageConfig.tabs?.map(tab => tab.key).sort((a, b) => a.length - b.length) ?? []
            const optionDict = pageConfig.optionList?.reduce((acc, item) => ({ ...acc, [item.name]: item.options }), {})

            const columnsData = processedColumns.filter(item => !['操作', 'operation'].includes(item.title?.toLowerCase()))?.map(item => {
                delete item.type
                return item
            })

            const viewData = {
                hasTabs,
                columnsData,
                hasFormItems,
                tabs: pageConfig.tabs,
                dictBlocks: dictBlocks.map(item => ({ name: item, data: optionDict[item] ?? [] })).sort((a, b) => a.name.length - b.name.length),
                tabColumns: contextStringify({ context: Object.fromEntries(tabKeys?.map(tab => [tab, wrapCode('commonColumns')])), maxLength: 100 }),
                formItemsData: !hasTabs ?
                    `export const formItems = ${contextStringify({ context: formItems, maxLength: 120 })}` :
                    `const searchItems = ${contextStringify({ context: formItems, maxLength: 120 })}\n\nexport const formItems = ${contextStringify({ context: Object.fromEntries(tabKeys?.map(tab => [tab, wrapCode('searchItems')])), maxLength: 100 })}`,
            }

            const bodyCode = resourceTpl(viewData)
            const importsStr = generateSmartImports({ module: 'resource', hasTabs, bodyCode, hasFormItems })
            return cleanCode(`${importsStr}\n\n${bodyCode}`)
        },
        index: ({ fileName, pageConfig }) => {
            const hasTabs = pageConfig.tabs?.length > 0
            const hasPagination = pageConfig.table?.pagination
            const hasFormItems = pageConfig.formItems?.length > 0
            const hasOperate = pageConfig.table?.operation?.length > 0
            const hasImageColumn = pageConfig.table?.columns?.some(item => item.type === 'image')
            const functionButtons = pageConfig.functionButton?.filter(item => !['查询', '重置', 'query', 'search', 'reset'].includes(item.btn.toLowerCase().replaceAll(' ', ''))) || []
            const needRenderAction = hasImageColumn

            const pageStruct = ['stateBlock', 'hookBlock', 'handleBlock', hasOperate ? 'operateBlock' : '', 'renderBlock'].filter(Boolean)

            let columnsValue = hasTabs ? 'columns[activeKey]' : 'columns'
            if (hasOperate) {
                columnsValue = `${columnsValue}.concat(operate)`
            }

            const imgAction = Object.fromEntries(pageConfig.table?.columns?.filter(item => item.type === 'image')?.map(item => [item.dataIndex, wrapCode(`(_, record) => <a onClick={() => showImg(record, '${item.dataIndex}')}>查看图片</a>`)]))
            const renderAction = `{${contextStringify({ context: imgAction, maxLength: 120 })}}`.replace(/\n/g, '\n    ')

            const viewData = {
                hasTabs,
                pageStruct,
                columnsValue,
                hasFormItems,
                renderAction,
                hasPagination,
                hasImageColumn,
                functionButtons,
                responseSuccess,
                needRenderAction,
                tabs: pageConfig.tabs,
                renderTree: pageConfig.renderTree,
                hasExpandable: pageConfig.table.expandable,
                staticInfoText: pageConfig.staticInfo?.text,
                hasRowSelection: pageConfig.table.rowSelection,
                formItems: hasFormItems ? (hasTabs ? 'formItems[activeKey]' : 'formItems') : '[]',
                operations: pageConfig.table.operation?.sort((a, b) => a.action.length - b.action.length) || [],
                initParams: `{ ${hasTabs ? 'type: tabs[0].key ,' : ''}${hasPagination ? 'pageNo: 1 , pageSize: 10' : ''}}`,
                uri: needMock ? `request('/api/${fileName}', { method: 'POST', body: params })` : 'BUNKER_API_ANCHOR_pages',
            }

            const bodyCode = indexTpl(viewData)
            const importsStr = generateSmartImports({ module: 'index', hasTabs, bodyCode, hasFormItems })
            return cleanCode(`${importsStr}\n\n${bodyCode}`)
        },
    }
}