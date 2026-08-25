import { useRef, useState, useEffect, useCallback } from 'react'

/**
 * @hook useTableQuery
 * @description [地堡核心逻辑引擎] 高级异步数据驱动钩子。
 * 负责全自动管理表格的生命周期，包括数据抓取、状态同步、动态列指纹识别及“竞态病毒”物理免疫。
 *
 * @param {Object} params - 引擎配置包
 * @param {Array} [params.cols] - 初始战备物资：前端预设的静态列配置
 * @param {Function} params.api - 任务指令：必须返回 Promise 的数据抓取函数
 * @param {Object} [params.initialParams={}] - 初始导航坐标：包含 pageNo, pageSize 及默认过滤参数
 * @param {Function} params.formatResponse - 数据解码协议：将 API 原始信号转化为 { data, total, columns } 结构
 *
 * @returns {Object} 物理操作句柄包
 * @returns {number} .total - 仓库物资总量
 * @returns {boolean} .loading - 引擎负载状态
 * @returns {Function} .setSearch - 坐标修改器
 * @returns {Array} .dataSource - 已解压的物理物资列表
 * @returns {Function} .setLoading - 负载状态手动干预句柄
 * @returns {Object} .search - 当前导航参数（pageNo, pageSize 等）
 * @returns {Function} .refresh - 强制重启协议：立即执行一次数据抓取
 * @returns {Array} .columns - 当前生效的动态列配置（已通过指纹协议校验）
 * @returns {Function} .setDataSource - 物资流手动修改句柄（用于行内编辑等乐观更新）
 *
 * @example
 * const { dataSource, loading, refresh } = useTableQuery({
 *   api:async params=>await fetchUsers(params),
 *   initialParams: { pageNo: 1, pageSize: 10 },
 *   formatResponse: (res) => ({ data: res.list, total: res.total })
 * });
 */
export const useTableQuery = ({ api, cols = [], initialParams = {}, formatResponse, isLocalPaging = false }) => {

    const [total, setTotal] = useState(0)
    const [columns, setColumns] = useState(cols)
    const [loading, setLoading] = useState(false)
    const [dataSource, setDataSource] = useState([])
    const [search, setSearch] = useState(initialParams)

    // 💡 引用锁定协议：确保异步回调中永远能指向最新的指令地址
    const apiRef = useRef(api)
    // 💡 [核心防御] 信号 ID 计数器：用于物理拦截由于网络时延导致的“竞态病毒（Race Condition）”
    const fetchIdRef = useRef(0)
    // 💡 物理记录仪：记录上一次“真正”的过滤参数（不含分页）
    const lastFilterRef = useRef('')
    // 💡 [核心防御] 数据解码协议引用：确保异步回调中永远能指向最新的指令地址
    const formatResponseRef = useRef(formatResponse)

    useEffect(() => {
        apiRef.current = api
    }, [api])

    useEffect(() => {
        formatResponseRef.current = formatResponse
    }, [formatResponse])

    /**
     * @function getColumnSchema
     * @description [指纹识别协议] 对列配置执行“结构化脱水”。
     * 通过提取标题、字段和排序状态生成物理指纹，用于判定列结构是否发生“基因变异”。
     * @param {Array} cols - 待扫描的列配置
     * @returns {string} 物理指纹字符串
     */
    const getColumnSchema = cols => cols.map(col => `${col.title}-${col.dataIndex}-${col.sortOrder}`).join('|')

    /**
     * @async
     * @function fetchData
     * @description [数据装配任务] 执行核心的数据抓取与物理封存逻辑。
     * 具备信号溯源能力，确保只有最后一次发出的指令能修改地堡状态。
     */
    const fetchData = useCallback(async () => {
        if (!apiRef.current) return

        if (isLocalPaging) {
            const currentFilter = JSON.stringify(Object.fromEntries(Object.entries(search).filter(([k]) => !['pageNo', 'pageSize'].includes(k))))
            if (lastFilterRef.current === currentFilter && dataSource.length > 0) {
                return
            }
            lastFilterRef.current = currentFilter
        }

        setLoading(true)
        // 💡 信号加标：为本次请求分配唯一的物理 ID
        const currentFetchId = ++fetchIdRef.current
        try {
            const response = await apiRef.current(search)
            // 💡 [物理拦截] 信号校准：若当前 ID 不是最新 ID，说明该信号已过期，执行丢弃协议
            if (currentFetchId !== fetchIdRef.current) return
            const { data, total, columns: newCols } = formatResponseRef.current?.(response ?? {}) || {}
            // 💡 [性能装甲] 只有当列指纹发生变化时，才触发 React 的重绘逻辑
            if (newCols) {
                // 使用函数式状态更新，既能拿到最新的 prevCols，又无需将 columns 作为 useCallback 的依赖！
                setColumns(prevCols => {
                    if (getColumnSchema(newCols) !== getColumnSchema(prevCols)) {
                        return newCols
                    }
                    return prevCols
                })
            }
            setDataSource(data ?? [])
            setTotal(total ?? 0)
        } catch (error) {
            console.error('查询失败', error)
        } finally {
            // 💡 状态闭环：确保只有最新的信号能解除 Loading 锁定
            if (currentFetchId === fetchIdRef.current) {
                setLoading(false)
            }
        }
    }, [search, isLocalPaging])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return { total, columns, search, loading, dataSource, setSearch, setLoading, setDataSource, refresh: fetchData }
}