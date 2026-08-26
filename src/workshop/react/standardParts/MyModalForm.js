import dayjs from 'dayjs'
import { MyBaseForm } from './MyBaseForm'
import { MyModalTable } from './MyModalTable'
import { useRef, useMemo, useState, useEffect } from 'react'
import { Row, Col, Form, Modal, Button, Collapse } from 'antd'

const LAYOUT_PROCESSORS = {
    section: ({ item, renderCore }) => (
        <Col span={item.span ?? 24} style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 'bold', marginBottom: 12, borderLeft: '4px solid #1890ff', paddingLeft: 8 }}>{item.title}</div>
            <Row gutter={[24, 0]}>
                {renderCore(item.childItems || [])}
            </Row>
        </Col>
    ),
    collapse: ({ item, renderCore }) => (
        <Col span={item.span ?? 24} style={{ marginBottom: 16 }}>
            <Collapse defaultActiveKey={['1']}>
                <Collapse.Panel key='1' header={<span style={{ fontWeight: 'bold' }}>{item.title}</span>}>
                    <Row gutter={[24, 0]}>
                        {renderCore(item.childItems || [])}
                    </Row>
                </Collapse.Panel>
            </Collapse>
        </Col>
    ),
    default: ({ item, renderCore }) => <Row gutter={[24, 0]}>{renderCore(item.childItems || [])}</Row>
}

// 定义“零部件增强协议”处理器,以后加任何新功能，只需要在这个对象里加一个 Key，不需要动主逻辑！
const ACTION_PROCESSORS = {
    // 处理尾操作按钮
    addonAfter: (item, { tableConfig, setModalTable, setSelectedTableRows }) => ({
        props: {
            addonAfter: (
                <Button onClick={() => {
                    setSelectedTableRows([])
                    setModalTable({ visible: true, title: `选择${item.label}`, ...tableConfig[item.name] })
                }}>
                    {item.addonAfter}
                </Button>
            )
        }
    }),
    // 以后想加个“前缀图标”？直接加在这里：
    // prefix: (item) => ({ props: { prefix: <Icon type={item.prefix} /> } }),
}

const FormRenderer = ({ form, formItems, tableConfig, setModalTable, setSelectedTableRows }) => {

    // 定义核心渲染逻辑，供递归使用
    const renderCore = items => (
        <FormRenderer
            form={form}
            formItems={items}
            tableConfig={tableConfig}
            setModalTable={setModalTable}
            setSelectedTableRows={setSelectedTableRows}
        />
    )

    // 定义单项动作注入逻辑
    const getRenderItemProps = item => {
        if (!item.renderAction) return {}
        const props = {}
        Object.keys(ACTION_PROCESSORS).forEach(key => {
            if (item[key]) {
                Object.assign(props, ACTION_PROCESSORS[key](item, { tableConfig, setModalTable, setSelectedTableRows }))
            }
        })
        return props
    }

    return formItems.map((item, index) => {
        // 情况 A：发现容器型零件 (含有 layoutType)
        if (item.layoutType && LAYOUT_PROCESSORS[item.layoutType]) {
            const Layout = LAYOUT_PROCESSORS[item.layoutType] ?? LAYOUT_PROCESSORS.default
            return (
                <Layout
                    item={item}
                    key={item.name || index}
                    renderCore={renderCore} // 注入渲染能力，让 Layout 自己去 Map
                />
            )
        }

        // 情况 B：标准作战零件
        return (
            <Col span={item.span ?? 6} key={item.name || index}>
                <MyBaseForm item={{ ...item, ...getRenderItemProps(item) }} form={form} />
            </Col>
        )
    })
}

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
 * @param {Array} props.formItems - 零部件清单：定义表单内部的输入单元
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
export const MyModalForm = ({ width, title, footer, submit, record, visible, setModal, labelCol, formItems, wrapperCol, tableConfig, okButtonProps, onValuesChange, handleModalTableOk }) => {

    const rowKey = tableConfig?.rowKey || 'id'

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
            form.resetFields()
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
    const handleOk = async () => {
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
                await submit({ ...record, ...formattedValues })
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

    return (
        <Modal
            centered
            title={title}
            width={width}
            open={visible}
            destroyOnClose
            onOk={handleOk}
            onCancel={handleCancel}
            confirmLoading={pending}
            okButtonProps={okButtonProps}
            bodyStyle={{ paddingBottom: 0 }}
            footer={footer?.({ form, record, setModal })}
        >
            {modalTable.visible && <MyModalTable rowKey={rowKey} {...modalTable} rowSelection={tableRowSelection} onOk={modalTableOk} setModal={setModalTable} />}
            <Form form={form} preserve={false} labelCol={labelCol} wrapperCol={wrapperCol} onValuesChange={(changed, all) => onValuesChange?.({ changed, all, form, record })}>
                <Row gutter={[24, 0]}>
                    <FormRenderer form={form} formItems={formItems} tableConfig={tableConfig} setModalTable={setModalTable} setSelectedTableRows={setSelectedTableRows} />
                </Row>
            </Form>
        </Modal>
    )
}