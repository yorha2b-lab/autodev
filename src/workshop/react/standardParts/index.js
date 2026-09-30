import { AliyunOSSUpload } from './AliyunOSSUpload'
import { Tree, Form, Radio, Input, Upload, Select, Cascader, Checkbox, DatePicker, InputNumber, TreeSelect, AutoComplete } from 'antd'

/**
 * @function formNode
 * @description 智能零部件装配器：根据构筑协议（item.type）动态产出对应的 Ant Design 交互单元。
 *
 * @param {Object} params - 装配参数
 * @param {Object} params.item - 零部件配置对象
 * @param {string|number} [params.item.width] - 宽度校准
 * @param {boolean} [params.item.readOnly] - 物理锁定开关
 * @param {string} [params.item.placeholder] - 视觉占位提示
 * @param {Object} [params.item.props] - 透传给底层组件的原始控制参数
 * @param {Array} [params.item.options] - 数据字典（用于 select/radio/tree 等）
 * @param {string} params.item.type - 构筑类型（date/number/ossUpload/select/daterange 等）
 *
 * @returns {React.ReactNode} 物理装配完成的 UI 单元
 */
export const formNode = ({ item }) => {

    if (item.type === 'group' && Array.isArray(item.groups)) {
        return (
            <Input.Group compact style={{ width: item.width ?? '100%', display: 'flex', ...item.style }}>
                {item.groups.map(subItem => (
                    <Form.Item noStyle key={subItem.name} name={subItem.name} rules={subItem.rules} initialValue={subItem.value}>
                        {formNode({ item: subItem })}
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