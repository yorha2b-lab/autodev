import { Table, Space } from 'antd'
import { DraggableContainer } from './DraggableContainer'
import { EditableRow, EditableCell } from './EditableCell'
import { useRef, useMemo, useEffect, useCallback } from 'react'

export const MyTable = ({ size, query, total, search, options, autoScroll, onChange, editingKey, setSearch, pagination, editRender = {}, renderAction, rowClassName, customSave, setDataSource, lineFormChange, columns = [], rowSelection, rowKey = 'id', loading = false, dataSource = [], draggable = false, scroll = { x: 'max-content' }, isLocalPaging = false, ...restProps }) => {

    const tableRef = useRef(null)
    const hasScrolledRef = useRef(false)
    const dataSourceRef = useRef(dataSource)
    dataSourceRef.current = dataSource

    const isEditable = useMemo(() => columns.some(col => col.editType), [columns])
    const hasCustomComponents = isEditable || draggable

    const handleSave = useCallback((row) => {
        const prev = dataSourceRef.current
        const index = prev.findIndex(item => row[rowKey] === item[rowKey])
        if (index === -1) return
        const item = prev[index]
        const updatedRow = { ...item, ...row }
        const newData = [...prev]
        newData.splice(index, 1, updatedRow)
        setDataSource(newData)
        customSave?.(updatedRow, newData)
    }, [rowKey, customSave, setDataSource])

    const components = useMemo(() => {
        if (!hasCustomComponents) return undefined
        const c = { body: {} }
        if (isEditable) {
            c.body.row = EditableRow
            c.body.cell = EditableCell
        }
        if (draggable) {
            c.body.wrapper = props => <DraggableContainer props={props} customSave={customSave} setDataSource={setDataSource} dataSourceRef={dataSourceRef} />
        }
        return c
    }, [isEditable, draggable, customSave, setDataSource])

    const mergedColumns = useMemo(() => {
        return columns.map(col => {
            let currentCol = { ...col }
            if (col.renderAction && renderAction?.[col.dataIndex]) {
                currentCol.render = renderAction[col.dataIndex]
            }
            if (col.search) {
                currentCol = {
                    ...currentCol,
                    filterSearch: true,
                    onFilter: (value, record) => col.remote ? undefined : col.customFilter({ value, record, dataIndex: col.dataIndex }),
                    filterDropdown: ({ close, confirm, selectedKeys, clearFilters, setSelectedKeys }) => (
                        <Space direction='vertical' style={{ padding: 12 }}>
                            {col.customFilterDropdown({ dataIndex: col.dataIndex, selectedKeys, setSelectedKeys })}
                            <div style={{ display: 'flex' }}>
                                <a style={{ marginLeft: 'auto', marginRight: 8 }} onClick={() => {
                                    if (col.remote) {
                                        setSearch(prev => ({ ...prev, pageNo: 1, [col.dataIndex]: col.formatFilter?.(selectedKeys) ?? selectedKeys?.toString() }))
                                    }
                                    confirm()
                                }}>确定</a>
                                <a onClick={() => {
                                    if (col.remote) {
                                        setSearch(prev => ({ ...prev, pageNo: 1, [col.dataIndex]: undefined }))
                                    }
                                    clearFilters()
                                }}>重置</a>
                            </div>
                        </Space>
                    ),
                }
            }
            if (!col.editType) {
                return currentCol
            }
            return {
                ...currentCol,
                onCell: (record) => ({
                    ...currentCol,
                    record,
                    rowKey,
                    handleSave,
                    editingKey,
                    editRender: editRender?.[col.dataIndex],
                    options: col.options ?? options?.[col.dataIndex],
                    disabled: col.specialDisabled ? record.disabled : col.disabled,
                    editable: col.specialEditType ? record.needEdit && !!col.editType : !!col.editType,
                }),
            }
        })
    }, [columns, options, handleSave, editRender, renderAction])

    const paginationConfig = useMemo(() => {

        if (!pagination) return false

        return {
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            ...(isLocalPaging ? {} : {
                current: Number(search?.pageNo),
                pageSize: Number(search?.pageSize),
            }),
            ...(typeof pagination === 'object' ? pagination : {})
        }
    }, [total, search, pagination, isLocalPaging])

    useEffect(() => {
        if (!autoScroll || !dataSource?.length || query?.rowIndex === undefined) return
        if (hasScrolledRef.current === query.rowIndex) return
        const timer = setTimeout(() => {
            const tableElement = tableRef.current
            if (!tableElement) return
            const trList = tableElement.getElementsByClassName('ant-table-row')
            const tr = trList[Number(query.rowIndex)]
            if (tr) {
                tr.scrollIntoView({ behavior: 'smooth', block: 'center' })
                tr.style.backgroundColor = '#e6f4ff'
                hasScrolledRef.current = query.rowIndex
            }
        }, 300)
        return () => clearTimeout(timer)
    }, [dataSource, query?.rowIndex, autoScroll, tableRef])

    return (
        <div ref={tableRef}>
            <Table
                {...restProps}
                rowKey={rowKey}
                scroll={scroll}
                loading={loading}
                onChange={onChange}
                columns={mergedColumns}
                dataSource={dataSource}
                size={size ?? 'middle'}
                components={components}
                rowSelection={rowSelection}
                pagination={paginationConfig}
                onRow={(record, index) => ({ record, index, draggable, columns: mergedColumns, ...(typeof lineFormChange === 'function' ? { onValuesChange: lineFormChange } : {}) })}
                rowClassName={(record, index) => {
                    const externalClass = typeof rowClassName === 'function' ? rowClassName(record, index) : rowClassName
                    const classes = [externalClass]
                    if (isEditable) classes.push('editable-row')
                    if (autoScroll && query?.rowIndex === index) classes.push('search-highlight-row')
                    return classes.filter(Boolean).join(' ')
                }}
            />
        </div>
    )
}