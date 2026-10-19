import { MyBaseForm } from './MyBaseForm'
import { AliyunOSSUpload } from './AliyunOSSUpload'
import { Tree, Form, Radio, Input, Upload, Select, Cascader, Checkbox, DatePicker, InputNumber, TreeSelect, AutoComplete } from 'antd'

export const formNode = ({ item }) => {

    if (item.type === 'group' && Array.isArray(item.groups)) {
        return (
            <Input.Group compact style={{ width: item.width ?? '100%', display: 'flex', ...item.style }}>
                {item.groups.map((subItem, ind) => (
                    <Form.Item noStyle key={subItem.name}>
                        <div style={{ flex: 1, minWidth: 0, marginRight: 8 }}><MyBaseForm item={subItem} key={subItem.name} /></div>
                        {ind < item.groups.length - 1 && <span style={{ color: '#888', whiteSpace: 'nowrap', marginRight: 8 }}>{item.separator}</span>}
                    </Form.Item>
                ))}
            </Input.Group>
        )
    }

    const commonProps = {
        disabled: item.readOnly,
        style: { width: item.width ?? '100%' },
        placeholder: item.placeholder ?? `请${['select', 'cascader', 'date'].includes(item.type) ? '选择' : '输入'}`,
        ...item.props
    }

    const componentDict = {
        date: <DatePicker {...commonProps} />,
        number: <InputNumber  {...commonProps} />,
        default: <Input allowClear {...commonProps} />,
        ossUpload: <AliyunOSSUpload {...commonProps} />,
        auto: <AutoComplete options={item.options} {...commonProps} />,
        radio: <Radio.Group options={item.options} {...commonProps} />,
        tree: <Tree checkable treeData={item.options} {...commonProps} />,
        treeSelect: <TreeSelect treeData={item.options} {...commonProps} />,
        checkbox: <Checkbox.Group options={item.options} {...commonProps} />,
        textarea: <Input.TextArea autoSize={{ minRows: 4 }} {...commonProps} />,
        daterange: <DatePicker.RangePicker {...commonProps} placeholder={undefined} />,
        cascader: <Cascader showSearch allowClear options={item.options} {...commonProps} />,
        upload: <Upload {...item.uploadProps} {...commonProps}>{item.content ?? '上传文件'}</Upload>,
        select: <Select allowClear showSearch mode={item.mode} options={item.options} optionFilterProp='label' {...commonProps} />,
    }

    return componentDict[item.type] ?? componentDict.default
}