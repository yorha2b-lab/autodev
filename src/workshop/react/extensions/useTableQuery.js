import { useRef, useState, useEffect, useCallback } from 'react'

export const useTableQuery = ({ api, cols = [], initialParams = {}, formatResponse, isLocalPaging = false }) => {

    const [total, setTotal] = useState(0)
    const [columns, setColumns] = useState(cols)
    const [loading, setLoading] = useState(false)
    const [dataSource, setDataSource] = useState([])
    const [search, setSearch] = useState(initialParams)

    const apiRef = useRef(api)
    const fetchIdRef = useRef(0)
    const lastFilterRef = useRef('')
    const formatResponseRef = useRef(formatResponse)

    useEffect(() => {
        apiRef.current = api
    }, [api])

    useEffect(() => {
        formatResponseRef.current = formatResponse
    }, [formatResponse])

    const getColumnSchema = cols => cols.map(col => `${col.title}-${col.dataIndex}-${col.sortOrder}`).join('|')

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
        const currentFetchId = ++fetchIdRef.current
        try {
            const response = await apiRef.current(search)
            if (currentFetchId !== fetchIdRef.current) return
            const { data, total, columns: newCols } = formatResponseRef.current?.(response ?? {}) || {}
            if (newCols) {
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