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

export const MyModalForm = ({ extra, width, title, layout, okText, options, footer, submit, record, visible, setModal, labelCol, modalItems, wrapperCol, cancelText, tableConfig, okButtonProps, renderAction, onValuesChange, handleModalTableOk }) => {

    const rowKey = tableConfig?.rowKey || 'id'

    const [form] = Form.useForm()
    const [pending, setPending] = useState(false)
    const [modalTable, setModalTable] = useState({})
    const [selectedTableRows, setSelectedTableRows] = useState([])

    const prevVisibleRef = useRef(false)

    useEffect(() => {
        if (visible && !prevVisibleRef.current) {
            if (record && Object.keys(record).length > 0) {
                const itemMap = new Map(flattenFormItems(modalItems).map(i => [i.name, i]))
                const initialData = {}
                Object.entries(record).forEach(([key, value]) => {
                    const config = itemMap.get(key)
                    if (config?.type?.includes('date') && value) {
                        if (Array.isArray(value)) {
                            initialData[key] = value.map(v => dayjs(v))
                        } else if (typeof value === 'string' && value.includes(',')) {
                            initialData[key] = value.split(',').map(v => dayjs(v))
                        } else {
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
    }, [visible, record, form, modalItems])

    const handleOk = async (extraParams = {}) => {
        try {
            const values = await form.validateFields()
            const formattedValues = { ...values }
            flattenFormItems(modalItems).forEach(item => {
                const val = formattedValues[item.name]
                if (item.type?.includes('date') && val) {
                    if (Array.isArray(val)) {
                        formattedValues[item.name] = val.map(v => v.valueOf()).join(',')
                    } else {
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
                options={options}
                externalForm={form}
                labelCol={labelCol}
                formItems={modalItems}
                wrapperCol={wrapperCol}
                renderAction={renderAction}
                tableProps={{ tableConfig, setModalTable, setSelectedTableRows }}
                onValuesChange={(changed, all) => onValuesChange?.({ changed, all, form, record })}
            />
            {extra?.footer?.(ctx)}
        </Modal>
    )
}