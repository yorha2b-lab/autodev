import { Fragment } from 'react'
import { MyBaseForm } from './MyBaseForm'
import { AliyunOSSUpload } from './AliyunOSSUpload'
import { Tree, Radio, Input, Upload, Select, Cascader, Checkbox, DatePicker, InputNumber, TreeSelect, AutoComplete } from 'antd'

const FormTree = ({ value, onChange, ...rest }) => (<Tree checkedKeys={value} onCheck={keys => onChange?.(Array.isArray(keys) ? keys : keys.checked)} {...rest} />)

const componentDict = {
    date: { Component: DatePicker },
    number: { Component: InputNumber },
    password: { Component: Input.Password },
    ossUpload: { Component: AliyunOSSUpload },
    default: {
        Component: Input,
        props: () => ({ allowClear: true })
    },
    daterange: {
        Component: DatePicker.RangePicker,
        props: () => ({ placeholder: undefined })
    },
    textarea: {
        Component: Input.TextArea,
        props: () => ({ autoSize: { minRows: 4 } })
    },
    upload: {
        Component: Upload,
        props: ({ item }) => ({ ...item.uploadProps })
    },
    auto: {
        Component: AutoComplete,
        props: ({ item }) => ({ options: item.options })
    },
    checkbox: {
        Component: Checkbox.Group,
        props: ({ item }) => ({ options: item.options })
    },
    radio: {
        Component: Radio.Group,
        props: ({ item }) => ({ options: item.options })
    },
    treeSelect: {
        Component: TreeSelect,
        props: ({ item }) => ({ treeData: item.options })
    },
    tree: {
        Component: FormTree,
        props: ({ item }) => ({ checkable: true, treeData: item.options })
    },
    cascader: {
        Component: Cascader,
        props: ({ item }) => ({ allowClear: true, showSearch: true, options: item.options })
    },
    select: {
        Component: Select,
        props: ({ item }) => ({ allowClear: true, showSearch: true, mode: item.mode, options: item.options, optionFilterProp: 'label' })
    },
}

export const formNode = ({ item, form }) => {

    if (item.type === 'group' && Array.isArray(item.groups)) {
        return (
            <Input.Group compact style={{ width: item.width ?? '100%', display: 'flex', ...item.style }}>
                {item.groups.map((subItem, ind) => (
                    <Fragment key={subItem.name}>
                        <div style={{ flex: 1, minWidth: 0, marginRight: 8 }}><MyBaseForm item={subItem} form={form} /></div>
                        {ind < item.groups.length - 1 && <span style={{ color: '#888', whiteSpace: 'nowrap', marginRight: 8 }}>{item.separator}</span>}
                    </Fragment>
                ))}
            </Input.Group>
        )
    }

    const commonProps = {
        disabled: item.readOnly,
        style: { width: item.width ?? '100%' },
        placeholder: item.placeholder ?? `请${['select', 'cascader', 'date'].includes(item.type) ? '选择' : '输入'}`,
    }

    const config = componentDict[item.type] ?? componentDict.default
    const Component = config.Component
    const specialProps = config.props?.({ item, form }) ?? {}

    if (item.type === 'upload') {
        return (
            <Component {...commonProps} {...specialProps} {...item.props}>
                {item.content ?? '上传文件'}
            </Component>
        )
    }

    return <Component {...commonProps} {...specialProps} {...item.props} />
}