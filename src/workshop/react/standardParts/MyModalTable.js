import { MyTable } from './MyTable'
import { useMemo, useState } from 'react'
import { MySearchForm } from './MySearchForm'
import { Form, Modal, Space, Button } from 'antd'
import { useTableQuery } from '../hooks/useTableQuery'

export const MyModalTable = ({ api, onOk, title, width, footer, visible, operate, setModal, formItems, setModalForm, rowSelection, formatResponse, functionButtons, columns: modalColumns, rowKey = 'id', scroll = { y: 400 }, initialParams = {}, modalPagination = true, isLocalPaging = false }) => {

    const [form] = Form.useForm()
    const [pending, setPending] = useState(false)

    const { total, loading, columns, dataSource, search, refresh, setLoading, setSearch, setDataSource } = useTableQuery({ api, cols: modalColumns, initialParams, formatResponse, isLocalPaging })

    const handleSearch = values => setSearch({ ...search, ...values, pageNo: 1 })

    const handleTableChange = (pagination, filters, sorter) => setSearch({ ...search, pageNo: pagination.current, pageSize: pagination.pageSize, orderBy: sorter.column ? sorter.field : undefined })

    const handleOk = async () => {
        if (onOk) {
            try {
                setPending(true)
                await onOk()
            } catch (error) {
                console.log('操作失败:', error)
            } finally {
                setPending(false)
            }
        }
    }

    const finalColumns = useMemo(() => {
        return operate ? columns.concat(operate({ refresh, setModalForm })) : columns
    }, [columns, operate])

    return (
        <Modal centered destroyOnClose title={title} width={width} open={visible} onOk={handleOk} footer={footer?.({ setModal })} onCancel={() => setModal({ visible: false })} confirmLoading={pending} bodyStyle={{ paddingBottom: 0 }}>
            {formItems?.length > 0 && <MySearchForm form={form} search={search} formItems={formItems} setSearch={handleSearch} syncUrlParams={false} />}
            {functionButtons?.length > 0 && <Space style={{ marginBottom: 12 }}>{functionButtons.map(item => <Button key={item.name} type={item.type} loading={loading} disabled={item.disabled} onClick={() => item.onClick({ refresh, setLoading, setSearch, setDataSource })}>{item.name}</Button>)}</Space>}
            <MyTable
                total={total}
                rowKey={rowKey}
                search={search}
                scroll={scroll}
                loading={loading}
                columns={finalColumns}
                dataSource={dataSource}
                rowSelection={rowSelection}
                pagination={modalPagination}
                onChange={handleTableChange}
                isLocalPaging={isLocalPaging}
                setDataSource={setDataSource}
            />
        </Modal>
    )
}