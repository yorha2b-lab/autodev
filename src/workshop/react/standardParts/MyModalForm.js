import dayjs from 'dayjs'
import { MyForm } from './MyForm'
import { Form, Modal } from 'antd'
import { MyModalTable } from './MyModalTable'
import { useRef, useMemo, useState, useEffect } from 'react'

const flattenFormItems = items => {
    if (!Array.isArray(items)) return []
    return items.flatMap(item => {
        if (item.childItems) {
            return flattenFormItems(item.childItems)
        }
        return item
    })
}

/**
 * @component MyModalForm
 * @description [地堡核心构筑舱] 通用弹窗表单组件。
 * 集成了“语义回显自愈”、“自动时间戳转换”及“原子级提交锁定”三大核心协议。
 *
 * @param {Object} props - 构筑参数
 * @param {string} [props.title] - 舱体视觉标题
 * @param {Object} [props.labelCol] - 标签布局校准
 * @param {Object} [props.wrapperCol] - 控件布局校准
 * @param {string|number} [props.width] - 舱体物理宽度
 * @param {boolean} props.visible - 激活信号：控制弹窗的物理显示状态
 * @param {Array} props.modalItems - 零部件清单：定义表单内部的输入单元
 * @param {Object} [props.record] - 初始物资包：用于编辑模式的数据回显
 * @param {Function} props.submit - 数据发射协议：提交表单后的核心回调函数
 * @param {Function} props.setModal - 指令中心：用于更新弹窗状态（开启/关闭）
 * @param {Function} [props.onValuesChange] - 联动传感：捕获表单内部的信号波动
 *
 * @example
 * <MyModalForm
 *   title='构筑新模块'
 *   visible={visible}
 *   submit={async (vals) => await save(vals)}
 *   formItems={[{ label: '截止日期', name: 'deadline', type: 'date' }]}
 * />
 */
export const MyModalForm = ({ extra, width, title, layout, okText, options, footer, submit, record, visible, setModal, labelCol, modalItems, wrapperCol, cancelText, tableConfig, okButtonProps, onValuesChange, handleModalTableOk }) => {

    const rowKey = tableConfig?.rowKey || 'id'
    const formItems = useMemo(() => modalItems.map(item => ({ ...item, ...(['select'].includes(item.type) ? { options: item.options ?? options?.[item.name] ?? [] } : {}) })), [modalItems, options])

    const [form] = Form.useForm()
    const [pending, setPending] = useState(false)
    const [modalTable, setModalTable] = useState({})
    const [selectedTableRows, setSelectedTableRows] = useState([])

    const prevVisibleRef = useRef(false)

    /**
     * @description [数据回显协议] 当构筑舱开启时，自动对初始物资进行“语义格式化”。
     * 将后端传输的字符串/数字时间戳重新转化为地堡可读的 `dayjs` 对象。
     */
    useEffect(() => {
        if (visible && !prevVisibleRef.current) {
            if (record && Object.keys(record).length > 0) {
                const itemMap = new Map(flattenFormItems(formItems).map(i => [i.name, i]))
                const initialData = {}
                Object.entries(record).forEach(([key, value]) => {
                    const config = itemMap.get(key)
                    // 语义识别：若零部件类型为日期且数值存在，执行物理转化
                    if (config?.type?.includes('date') && value) {
                        if (Array.isArray(value)) {
                            // 处理范围日期
                            initialData[key] = value.map(v => dayjs(v))
                        } else if (typeof value === 'string' && value.includes(',')) {
                            // 处理逗号分隔的字符串日期
                            initialData[key] = value.split(',').map(v => dayjs(v))
                        } else {
                            // 处理单日期
                            initialData[key] = dayjs(value)
                        }
                    } else {
                        initialData[key] = value
                    }
                })
                form.setFieldsValue(initialData)
            }
        }
        prevVisibleRef.current = visible
    }, [visible, record, form, formItems])

    /**
     * @async
     * @function handleOk
     * @description [物理加压提交] 执行表单校验，并自动启动“时间戳转换协议”。
     * 确保发射至后端的数据包符合标准 Unix 时间戳（毫秒）规范。
     */
    const handleOk = async (extraParams = {}) => {
        try {
            const values = await form.validateFields()
            const formattedValues = { ...values }
            flattenFormItems(formItems).forEach(item => {
                const val = formattedValues[item.name]
                if (item.type?.includes('date') && val) {
                    if (Array.isArray(val)) {
                        // 物理压实：将范围日期转化为逗号分隔的时间戳字符串
                        formattedValues[item.name] = val.map(v => v.valueOf()).join(',')
                    } else {
                        // 物理转化：将 dayjs 对象还原为原始数值（毫秒）
                        formattedValues[item.name] = val.valueOf()
                    }
                }
            })
            if (submit) {
                setPending(true)
                await submit({ ...record, ...formattedValues, ...extraParams })
            }
        } catch (error) {
            console.log('表单校验失败:', error)
        } finally {
            setPending(false)
        }
    }

    const modalTableOk = () => handleModalTableOk?.({ form, selectedTableRows, setModalTable })

    /**
     * @function handleCancel
     * @description 执行“撤退协议”：关闭构筑舱并清除当前逻辑残留。
     */
    const handleCancel = () => {
        setModal({ visible: false })
        form.resetFields()
    }

    const tableRowSelection = useMemo(() => ({
        selectedRowKeys: selectedTableRows.map(row => row[rowKey]),
        onChange: (selectedRowKeys, selectedRows) => setSelectedTableRows(selectedRows),
    }), [rowKey, modalTable, selectedTableRows])

    const ctx = { form, record, pending, handleOk, handleCancel, setModal }

    return (
        <Modal
            centered
            title={title}
            width={width}
            open={visible}
            destroyOnClose
            okText={okText}
            onOk={() => handleOk()}
            cancelText={cancelText}
            onCancel={handleCancel}
            confirmLoading={pending}
            okButtonProps={okButtonProps}
            footer={typeof footer === 'function' ? footer(ctx) : footer}
            bodyStyle={{ paddingBottom: 0, maxHeight: '80vh', overflowY: 'auto' }}
        >
            {modalTable.visible && <MyModalTable rowKey={rowKey} {...modalTable} rowSelection={tableRowSelection} onOk={modalTableOk} setModal={setModalTable} />}
            {extra?.header?.(ctx)}
            <MyForm
                layout={layout}
                externalForm={form}
                labelCol={labelCol}
                formItems={formItems}
                wrapperCol={wrapperCol}
                tableProps={{ tableConfig, setModalTable, setSelectedTableRows }}
                onValuesChange={(changed, all) => onValuesChange?.({ changed, all, form, record })}
            />
            {extra?.footer?.(ctx)}
        </Modal>
    )
}