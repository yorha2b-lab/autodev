import dayjs from 'dayjs'
import { request } from './request'

export const parseExcel = async file => {
    /* const arrayBuffer = await file.arrayBuffer()
    const XLSX = require('xlsx')
    const workbook = XLSX.read(arrayBuffer, { type: 'array' })
    const firstSheetName = workbook.SheetNames?.[0]
    const worksheet = workbook.Sheets[firstSheetName]
    const excelData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
    return excelData.filter(item => item.length > 0) */
}

export const flattenFormItems = items => {
    if (!Array.isArray(items)) return []
    return items.flatMap(item => {
        if (item.childItems) {
            return flattenFormItems(item.childItems)
        }
        return item
    })
}

export const initOSS = async (url, options) => {
    /* const OSS = require('ali-oss')
    const crypto = require('crypto-js')
    const response = await request(url, options)
    const { bucket, endpoint, stsToken, expiration, accessKeyId, accessKeySecret } = response?.data || {}
    const client = new OSS({ bucket, endpoint, stsToken, accessKeyId, accessKeySecret })
    const policy = btoa(JSON.stringify({
        expiration,
        conditions: [
            ["content-length-range", 0, 1024 * 1024 * 1024],
        ],
    }))
    const signature = crypto.enc.Base64.stringify(crypto.HmacSHA1(policy, accessKeySecret))
    return { client, policy, signature,host: `https://${bucket}.${endpoint.split('//')[1]}`, ...response?.data } */
}

export const formatQuery = (params, formItems) => {
    const cleanParams = {}
    Object.keys(params).forEach(key => {
        if (formItems.some(item => item.name.includes(key) && item.type?.includes('date')) && params[key]) {
            cleanParams[key] = Number(params[key])
        } else {
            cleanParams[key] = params[key] ?? null
        }
    })
    return cleanParams
}

export const timeRender = ({ time, date, minute }) => {
    if (!time) {
        return ''
    } else {
        if (date) {
            return dayjs(time).format('YYYY-MM-DD')
        }
        if (minute) {
            return dayjs(time).format('YYYY-MM-DD HH:mm')
        }
        return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }
}

export const exportDataToExcel = async ({ url, options, columns, fileName, formatter }) => {
    /* const response = await request(url, options)
    const result = formatter ? formatter(response) : (response?.data ?? [])
    if (result?.length > 0) {
        const XLSX = require('xlsx')
        const datas = result.map(item => Object.fromEntries(columns.map(col => {
            let value = item[col.dataIndex]
            if (col.exportRender) {
                value = col.exportRender(value, item)
            }
            if (col.render&&!col.exportRender) {
                const rendered = col.render(value, item)
                value = typeof rendered === 'object' ? (rendered?.props?.children || value) : rendered
            }
            return [col.title, value]
        })))
        const workbook = XLSX.utils.book_new()
        const header = columns.map(item => item.title)
        const worksheet = XLSX.utils.json_to_sheet(datas, { header })
        worksheet['!cols'] = Array.from(new Array(header.length)).fill({ wpx: 120 })
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1')
        XLSX.writeFile(workbook, `${fileName}.xlsx`)
    } */
}

export const arrayToTree = (list, levels, keys = { title: 'title', value: 'value', children: 'children' }) => {
    const tree = []
    const maps = levels.map(() => new Map())
    list.forEach(item => {
        let parent = tree
        levels.forEach(({ code, name }, index) => {
            const map = maps[index]
            const id = item[code]
            if (!map.has(id)) {
                const node = { [keys.title]: item[name], [keys.value]: id, ...(index < levels.length - 1 ? { [keys.children]: [] } : {}) }
                map.set(id, node)
                parent.push(node)
            }
            const node = map.get(id)
            parent = node[keys.children] ?? []
        })
    })
    return tree
}

export const moneyRender = (value, { decimals = 2, currency = 'CNY', language = 'zh-CN', showSymbol = true } = {}) => {
    if (value === null || value === undefined || value === '') return '-'
    const number = Number(value)
    if (isNaN(number)) return '-'
    const options = showSymbol
        ? { style: 'currency', currency, minimumFractionDigits: decimals }
        : { style: 'decimal', minimumFractionDigits: decimals, maximumFractionDigits: decimals }
    return new Intl.NumberFormat(language, options).format(number)
}

export const formatUnit = (value, { k = 1024, units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'], decimals = 2 } = {}) => {
    if (value === null || value === undefined || isNaN(value) || value === 0) {
        return `0 ${units[0] ?? ''}`
    }
    const absValue = Math.abs(value)
    const i = absValue < 1 ? 0 : Math.floor(Math.log(absValue) / Math.log(k))
    const index = Math.min(i, units.length - 1)
    const result = (value / Math.pow(k, index)).toFixed(decimals)
    return `${parseFloat(result)} ${units[index]}`
}

export const streamDownload = async ({ url, options, headers = { 'Content-Type': 'application/json' } }, fileName = '下载') => {

    const response = await fetch(url, { ...options, headers })

    if (!response.ok) {
        console.error(response.statusText)
        return
    }

    const blob = await response.blob()

    if (!blob.size) {
        console.error('文件为空')
        return
    }

    const slice = blob.slice(0, 10)
    const text = (await slice.text()).trim()

    if (text.startsWith('{') || text.startsWith('[')) {
        try {
            const fullText = await blob.text()
            const json = JSON.parse(fullText)
            console.error(json?.msg ?? '系统异常')
        } catch (error) {
            console.error(error)
        }
        return
    }

    const disposition = response.headers.get('content-disposition')
    let name = fileName

    if (disposition) {
        const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/)
        if (match) {
            name = decodeURIComponent(match[1] || match[2])
        }
    }

    const link = document.createElement('a')
    const urlObj = URL.createObjectURL(blob)

    link.href = urlObj
    link.download = name

    document.body.appendChild(link)
    link.click()
    link.remove()

    setTimeout(() => URL.revokeObjectURL(urlObj), 1000)
}