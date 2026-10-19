import dayjs from 'dayjs'
import { MyBaseForm } from './MyBaseForm'
import { useMemo, useState, useEffect } from 'react'
import { Row, Col, Form, Button, Space } from 'antd'
import { SearchOutlined, RedoOutlined } from '@ant-design/icons'

export const MySearchForm = ({ form, extra, search, options, loading, labelCol, setSearch, formItems, showLimit = 7, initialValues = {}, initialParams = {}, customReset, customFinish, renderAction, onValuesChange, syncUrlParams = true, defaultPageSize = 10 }) => {

    const [limit, setLimit] = useState(showLimit)

    const searchItems = useMemo(() => formItems.map(item => ({
        ...item,
        ...(item.renderAction ? { render: renderAction?.[item.name] } : {}),
        ...(['select'].includes(item.type) ? { options: item.options ?? options?.[item.name] ?? [] } : {})
    })), [options, formItems, renderAction])

    const handleReset = () => {
        form.resetFields()
        if (syncUrlParams) {
            const defaultQueryEntries = Object.entries(initialValues).filter(([key, _]) => !formItems.some(item => item.name.includes(key)))
            const defaultQuery = Object.fromEntries(defaultQueryEntries)
            const params = new URLSearchParams(defaultQuery)
            const newUrl = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname
            window.history.replaceState(null, '', newUrl)
        }
        if (customReset) {
            customReset()
        } else {
            setSearch({ pageNo: 1, pageSize: search.pageSize ?? defaultPageSize, ...initialParams })
        }
    }

    const handleFinish = values => {
        const formattedValues = { ...values }
        Object.keys(formattedValues).forEach(key => {
            const val = formattedValues[key]
            const isDateType = formItems.find(item => item.name === key)?.type?.includes('date')
            if (isDateType && val) {
                if (Array.isArray(val) && val.length > 0) {
                    const [startKey, endKey] = key.split(',')
                    formattedValues[startKey] = val[0].startOf('day').valueOf()
                    formattedValues[endKey] = val[1].endOf('day').valueOf()
                    delete formattedValues[key]
                } else {
                    formattedValues[key] = val.valueOf()
                }
            }
        })
        if (syncUrlParams) {
            const currentQuery = Object.fromEntries(new URLSearchParams(window.location.search).entries())
            const params = new URLSearchParams(Object.fromEntries(Object.entries({ ...currentQuery, ...formattedValues }).filter(([key, value]) => !['', null, undefined].includes(value))))
            window.history.replaceState(null, '', `${window.location.pathname}?${params.toString()}`)
        }
        if (customFinish) {
            customFinish(formattedValues)
        } else {
            setSearch({ ...search, ...formattedValues, pageNo: 1 })
        }
    }

    useEffect(() => {
        if (Object.values(initialValues).length > 0 && formItems.length > 0) {
            const newValues = {}
            formItems.forEach(item => {
                if (initialValues[item.name] !== undefined) {
                    const value = initialValues[item.name]
                    newValues[item.name] = item.type?.includes('date') ? dayjs(Number(value)) : value
                }
                if (item.name?.includes(',') && item.type?.includes('date')) {
                    const [startKey, endKey] = item.name.split(',')
                    if (initialValues[startKey] && initialValues[endKey]) {
                        newValues[item.name] = [dayjs(Number(initialValues[startKey])), dayjs(Number(initialValues[endKey]))]
                    }
                }
                if (item.hasOwnProperty('mode') && !!initialValues[item.name]) {
                    newValues[item.name] = initialValues[item.name]?.split(',')
                }
            })
            form.setFieldsValue(newValues)
        }
    }, [form, formItems, initialValues])

    return (
        <Form form={form} onFinish={handleFinish} labelCol={labelCol} onValuesChange={onValuesChange} className='searchForm'>
            <Row gutter={24}>
                {searchItems.slice(0, limit)?.map((item, ind) => (
                    <Col key={ind} span={item.span ?? 6}>
                        <MyBaseForm item={item} form={form} />
                    </Col>
                ))}
                <Col flex='auto' style={{ textAlign: 'right' }}>
                    <Form.Item>
                        <Space>
                            <Button type='primary' icon={<SearchOutlined />} loading={loading} htmlType='submit'>查询</Button>
                            <Button icon={<RedoOutlined />} onClick={handleReset} loading={loading} htmlType='reset'>重置</Button>
                            {extra}
                            {formItems.length > showLimit && (<a onClick={() => setLimit(formItems.length > limit ? formItems.length : showLimit)}>{formItems.length > limit ? '展开' : '收起'}</a>)}
                        </Space>
                    </Form.Item>
                </Col>
            </Row>
        </Form>
    )
}