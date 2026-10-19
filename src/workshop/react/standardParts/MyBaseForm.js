import { Fragment } from 'react'
import { formNode } from './index'
import { Form, Button } from 'antd'
import { PlusOutlined } from '@ant-design/icons'

const getValueFromEvent = e => {
    if (Array.isArray(e)) {
        return e
    }
    return e?.fileList
}

const renderFormContent = ({ item, prefixName = [] }) => {

    if (!item.name) {
        return <span dangerouslySetInnerHTML={{ __html: item.value }} />
    }

    const namePath = Array.isArray(prefixName) ? [...prefixName, ...(Array.isArray(item.name) ? item.name : [item.name])] : item.name

    const inputNode = (
        <Form.Item noStyle name={namePath} rules={item.rules} dependencies={item.dependencies} initialValue={item.value} {...(['upload', 'ossUpload'].includes(item.type) ? { getValueFromEvent, valuePropName: 'fileList' } : { valuePropName: item.valuePropName })}>
            {formNode({ item })}
        </Form.Item>
    )

    if (item.unit) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ flex: 1, minWidth: 0 }}>{inputNode}</div>
                <span style={{ color: '#888', whiteSpace: 'nowrap' }}>{item.unit}</span>
            </div>
        )
    }

    return inputNode
}

export const MyBaseForm = ({ item, form }) => {
    return (
        item.isList ?
            <Form.List name={item.name} initialValue={item.value}>
                {(fields, { add, remove }) => (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {fields.map((field, index) => (
                            <Fragment key={field.key}>
                                {item.render(field, index, { add, remove }, form, renderFormContent)}
                            </Fragment>
                        ))}
                        {fields.length === 0 && <Button type='dashed' onClick={() => add()} block icon={<PlusOutlined />}>添加{item.label || '项'}</Button>}
                    </div>
                )}
            </Form.List> :
            <Form.Item
                label={item.label}
                tooltip={item.tooltip}
                labelCol={item.labelCol}
                wrapperCol={item.wrapperCol}
                extra={item.extra || item.help}
                required={item.required ?? item.rules?.some(v => v.required)}
                style={{ marginBottom: !item.name ? 0 : undefined, ...item.style }}
            >
                {item.render ? (typeof item.render === 'function' ? item.render(item, form) : item.render) : renderFormContent({ item })}
            </Form.Item>
    )
}