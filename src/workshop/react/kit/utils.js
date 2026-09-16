import dayjs from 'dayjs'
import { request } from './request'

/**
 * @namespace BunkerUtils
 * @description 地堡核心工具集：包含文件处理、数据脱水、视觉渲染及后勤传输协议；使用前确保已安装对应模块（如：xlsx、ali-oss、crypto-js）
 * */


/**
 * @async
 * @function parseExcel
 * @description [后勤部] 本地 Excel 解析协议：将二进制表格物资转化为地堡可读的 JSON 序列。
 * @param {File|Blob} file - 待解析的原始文件对象
 * @returns {Promise<Array[]>} 解析后的二维数组数据
 */
export const parseExcel = async file => {
    /* const arrayBuffer = await file.arrayBuffer()
    const XLSX = require('xlsx')
    const workbook = XLSX.read(arrayBuffer, { type: 'array' })
    const firstSheetName = workbook.SheetNames?.[0]
    const worksheet = workbook.Sheets[firstSheetName]
    const excelData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
    return excelData.filter(item => item.length > 0) */
}

/**
 * @async
 * @function initOSS
 * @description [出口协议] 阿里云 OSS 凭证初始化：从司令部申请 STS 令牌并计算物理传输签名。
 * @param {string} url - 令牌申请地址
 * @param {Object} options - 请求配置参数
 * @returns {Promise<Object>} 包含 OSS 客户端实例、上传策略及 Host 节点的配置包
 */
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

/**
 * @function formatQuery
 * @description [数据脱水] 搜索参数校准协议：根据零部件类型（如日期）自动执行类型转换（String -> Number）。
 * @param {Array} formItems - 对应的零部件配置清单
 * @param {Object} params - 原始表单/URL 传感器数据
 * @returns {Object} 经过物理清洗、可直接用于 API 请求的参数包
 */
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

/**
 * @function timeRender
 * @description [视觉渲染] 时间戳格式化：将冷冰冰的数字转化为人类可读的时间字符串。
 * @param {Object} params - 渲染参数
 * @param {number|string} params.time - 原始时间戳
 * @param {boolean} [params.date] - 是否仅保留日期（YYYY-MM-DD）
 * @param {boolean} [params.minute] - 是否精确到分钟（YYYY-MM-DD HH:mm）
 * @returns {string} 格式化后的时间字符串
 */
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

/**
 * @async
 * @function exportDataToExcel
 * @description [物资外运] 数据表格导出协议：支持复杂的渲染逻辑回溯，将页面数据封存为 .xlsx 格式。
 * @param {string} url - 数据源地址
 * @param {Object} options - 请求参数
 * @param {string} fileName - 导出的文件名
 * @param {Function} [formatter] - 数据预处理回调
 * @param {Array} columns - 表格列配置，支持 exportRender 优先级
 */
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

/**
 * @async
 * @function streamDownload
 * @description [后勤传输] 智能流式下载协议：具备“语义侦察”能力，能自动识别被伪装成二进制流的 JSON 报错信息。
 * @param {Object} params - 传输配置
 * @param {string} params.url - 物资下载地址
 * @param {Object} [params.options] - Fetch 配置
 * @param {Object} [params.headers] - 自定义请求头
 * @param {string} [fileName='下载'] - 预设文件名（支持从 Content-Disposition 自动对齐）
 */
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

    // 💡 语义侦察逻辑：检查前 10 个字节，判断是否为 JSON 报错信息
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

    // 物理解析 Content-Disposition 头部，获取指挥官预设的文件名
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

/**
 * @function moneyRender
 * @description [视觉渲染] 金额校准渲染：支持多国语境、货币符号及精度控制。
 * @param {number|string} value - 原始金额数值
 * @param {Object} [options] - 配置参数
 * @param {number} [options.decimals=2] - 小数位数
 * @param {string} [options.currency='CNY'] - 货币代号
 * @param {string} [options.language='zh-CN'] - 语言环境
 * @param {boolean} [options.showSymbol=true] - 是否显示货币符号
 * @returns {string} 格式化后的金额文本
 */
export const moneyRender = (value, { decimals = 2, currency = 'CNY', language = 'zh-CN', showSymbol = true } = {}) => {
    if (value === null || value === undefined || value === '') return '-'
    const number = Number(value)
    if (isNaN(number)) return '-'
    const options = showSymbol
        ? { style: 'currency', currency, minimumFractionDigits: decimals }
        : { style: 'decimal', minimumFractionDigits: decimals, maximumFractionDigits: decimals }
    return new Intl.NumberFormat(language, options).format(number)
}

/**
 * @function formatUnit
 * @description [视觉渲染] 单位自动进阶协议：实现 B/KB/MB... 等数据的物理量级自动折算。
 * @param {number} value - 原始字节数值
 * @param {Object} [options] - 配置参数
 * @param {Array} [options.units] - 单位阶梯
 * @param {number} [options.k=1024] - 进位系数
 * @param {number} [options.decimals=2] - 保留小数位
 * @returns {string} 带单位的物理量级文本
 */
export const formatUnit = (value, { k = 1024, units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'], decimals = 2 } = {}) => {
    if (value === null || value === undefined || isNaN(value) || value === 0) {
        return `0 ${units[0] ?? ''}`
    }
    const absValue = Math.abs(value)
    // 💡 安全屏障：小于 1 的数值直接归入初始级单位，不进行对数拆解
    const i = absValue < 1 ? 0 : Math.floor(Math.log(absValue) / Math.log(k))
    const index = Math.min(i, units.length - 1)
    const result = (value / Math.pow(k, index)).toFixed(decimals)
    return `${parseFloat(result)} ${units[index]}`
}