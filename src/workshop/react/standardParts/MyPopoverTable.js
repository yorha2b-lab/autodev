import { Popover } from 'antd'
import { useState } from 'react'
import { MyTable } from './MyTable'

export const MyPopoverTable = ({ api, columns, children, formatter }) => {

    const [loading, setLoading] = useState(false)
    const [dataSource, setDataSource] = useState([])

    const fetchData = async () => {
        if (loading) return
        setLoading(true)
        const response = await api()
        const datas = formatter(response)
        setDataSource(datas)
    }

    return (
        <Popover trigger='click' content={<MyTable columns={columns} loading={loading} dataSource={dataSource} />}>
            <span onClick={fetchData}>{children}</span>
        </Popover>
    )
}