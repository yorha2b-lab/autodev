import { Table } from 'antd'
import { EditableRow, EditableCell } from './EditableCell'
import { useRef, useMemo, useEffect, useCallback } from 'react'

/**
 * @component MyTable
 * @description [地堡核心战术平台] 高级数据表格组件。
 * 它是地堡系统的“火力中心”，集成了行内编辑、自动滚动定位、动态分页协议及 Optimistic UI (乐观更新) 等工业级特性。
 *
 * @param {Object} props - 平台配置参数
 * @param {number} props.total - 物资总量：用于构筑分页器的刻度
 * @param {Object} [props.rowSelection] - 战术勾选：配置行选择逻辑
 * @param {string} [props.rowKey='id'] - 唯一标识：每一行物资的数字指纹
 * @param {boolean} [props.loading=false] - 战场负载状态：显示加载动画
 * @param {Array} [props.dataSource=[]] - 物理物资包：表格展示的原始数据
 * @param {Object} props.search - 当前物流状态：包含 pageNo 和 pageSize
 * @param {Object} [props.query] - 侦察参数：包含 rowIndex 用于执行物理追踪定位
 * @param {boolean} [props.autoScroll] - 视觉引导开关：是否开启自动滚动至目标行逻辑
 * @param {Function} [props.lineFormChange] - 行级信号监听：捕获行内表单的实时变动
 * @param {Function} props.onChange - 战位协同回调：分页、排序、筛选变动时的通信协议
 * @param {boolean|Object} [props.pagination] - 分页配置：支持布尔开关或物理对象覆盖
 * @param {Function} [props.customSave] - 物理封存协议：行内编辑保存后的外部持久化回调
 * @param {Array} props.columns - 零部件清单：定义列的构筑协议，支持 editType 等扩展属性
 * @param {Object} [props.scroll={x:'max-content'}] - 滚动配置：默认开启横向物理溢出防护
 * @param {string} [props.size='middle'] - 视觉能级：表格的物理尺寸 (small/middle/large)
 * @param {Function} props.setDataSource - 状态设置器：直接操作地堡的原始数据流（支持函数式更新）
 * @param {string|Function} [props.rowClassName] - 行视觉涂装：支持静态字符串或基于逻辑的动态类名
 *
 * @param {Object} [props.renderAction] - [后期物理绑定协议] 运行时逻辑注入仓库。
 * @description
 * 这是地堡系统的“黑客骇入”接口。
 * 由于 resource.js 必须保持纯净的静态 JSON 格式以确保主权安全性，
 * 凡是涉及“查看图片”、“跳转链接”等需要运行时函数支持的列，
 * 统一通过该协议在渲染阶段执行“逻辑对冲”。
 *
 * @logic
 * 1. 物理寻址：通过 col.dataIndex 锁定目标零部件位点。
 * 2. 逻辑脱壳：删除临时标记字段 [renderAction: true]。
 * 3. 语义注入：将 index.js 中定义的真实 Action 物理焊接到 columns.render 属性上。
 *
 * @example
 * // 1. 在 resource.js 中标记：
 * { title: '图片', dataIndex: 'imgUrl', renderAction: true }
 *
 * // 2. 在 index.js 中提供弹药：
 * <MyTable
 *   total={100}
 *   columns={columns}
 *   dataSource={data}
 *   setDataSource={setData}
 *   customSave={(row) => saveApi(row)}
 *   renderAction={{
 *     imgUrl: (text, record) => <a onClick={() => showImg(record)}>查看物资</a>
 *   }}
 * />
 */
export const MyTable = ({ size, query, total, search, autoScroll, onChange, pagination, renderAction, rowClassName, customSave, setDataSource, lineFormChange, columns = [], rowSelection, rowKey = 'id', loading = false, dataSource = [], scroll = { x: 'max-content' }, isLocalPaging = false, ...restProps }) => {

    const tableRef = useRef(null)
    const hasScrolledRef = useRef(false)

    /**
     * @description [权限侦察] 自动扫描列配置。若存在 editType 型号，则激活“骇入模式（编辑模式）”。
     */
    const isEditable = useMemo(() => columns.some(col => col.editType), [columns])

    /**
     * @function handleSave
     * @description [原子级物理封存] 执行数据更新协议。
     * 采用函数式状态更新（prev => ...）以彻底消除闭航陷阱（Stale Closure），确保数据高频修改时的绝对准确。
     *
     * @param {Object} row - 修改后的行片段
     */
    const handleSave = useCallback((row) => {
        setDataSource(prev => {
            const newData = [...prev]
            const index = newData.findIndex(item => row[rowKey] === item[rowKey])
            const item = newData[index]
            newData.splice(index, 1, { ...item, ...row })
            customSave?.({ ...item, ...row }, newData)
            return newData
        })
    }, [rowKey, customSave, setDataSource])

    /**
     * @constant components
     * @description [零部件注册] 注入地堡特有的可编辑 Row 和 Cell 单元。
     */
    const components = useMemo(() => ({
        body: {
            row: EditableRow,
            cell: EditableCell,
        }
    }), [])

    /**
     * @constant mergedColumns
     * @description [元数据重组] 将指挥官的静态列定义转化为带逻辑注入的“动态作战列”。
     * 自动处理 Cell 级的 disabled 状态和 editable 权限。
     */
    const mergedColumns = useMemo(() => {
        return columns.map(col => {
            if (!col.editType) {
                if (col.renderAction && renderAction?.[col.dataIndex]) {
                    return { ...col, render: renderAction[col.dataIndex] }
                }
                return col
            }
            return {
                ...col,
                onCell: (record) => ({
                    record,
                    handleSave,
                    title: col.title,
                    rules: col.rules,
                    options: col.options,
                    editType: col.editType,
                    dataIndex: col.dataIndex,
                    placeholder: col.placeholder,
                    defaultEdit: col.defaultEdit,
                    // 💡 条件防御逻辑：支持针对单行的物理锁定
                    disabled: col.specialDisabled ? record.disabled : col.disabled,
                    editable: col.specialEditType ? record.needEdit && !!col.editType : !!col.editType,
                }),
            }
        })
    }, [columns, handleSave, renderAction])

    /**
     * @constant paginationConfig
     * @description [后勤对齐协议] 自动将地堡的 search 状态映射为 Antd 分页模型。
     * 具备类型自适应能力：支持 boolean 开关或 Object 属性覆盖。
     */
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

    /**
     * @description [视觉追踪协议] 当检测到 query.rowIndex 信号时，执行“物理重定向”。
     * 表格将自动平滑滚动至目标行并注入高亮背景（#e6f4ff）。
     */
    useEffect(() => {
        if (!autoScroll || !dataSource?.length || query?.rowIndex === undefined) return
        if (hasScrolledRef.current === query.rowIndex) return
        const timer = setTimeout(() => {
            const tableElement = tableRef.current
            if (!tableElement) return
            // 物理侦察：查找底层 Antd 生成的行节点
            const trList = tableElement.getElementsByClassName('ant-table-row')
            const tr = trList[Number(query.rowIndex)]
            if (tr) {
                // 物理定位：平滑引导视觉中心
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
                rowSelection={rowSelection}
                pagination={paginationConfig}
                components={isEditable ? components : undefined}
                // 💡 信号注入：将行监听协议绑定至底层 tr
                onRow={(record, index) => ({ record, index, ...(typeof lineFormChange === 'function' ? { onValuesChange: lineFormChange } : {}) })}
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