import { SortableElement } from 'react-sortable-hoc'
import { Form, Input, InputNumber, Select, Checkbox } from 'antd'
import React, { useRef, useState, useEffect, useContext } from 'react'

/**
 * @constant EditableContext
 * @description [地堡跨组件通信协议] 用于在行（Row）与单元格（Cell）之间共享 Form 传感器的物理句柄。
 */
const EditableContext = React.createContext(null)

const SortableItem = SortableElement((props) => <tr {...props} />)

/**
 * @component EditableRow
 * @description [地堡战术行容器] 每一行都是一个独立的逻辑闭环。
 * 负责初始化 Form 实例并执行“行级数据同步”与“变动传感监听”。
 *
 * @param {Object} props - 组件属性
 * @param {number} props.index - 行物理索引
 * @param {Object} props.record - 初始物资包（当前行数据）
 * @param {Function} [props.onValuesChange] - 联动传感：监听行内任何零部件的值变动
 */
export const EditableRow = ({ index, record, ...props }) => {

    const [form] = Form.useForm()

    /**
     * @description [数据热更协议] 当外部记录发生变化时，物理同步至内部表单传感器。
     */
    useEffect(() => {
        if (record) {
            form.setFieldsValue(record)
        }
    }, [record])

    return (
        <Form form={form} component={false} onValuesChange={(changedValue, allValue) => props?.onValuesChange?.({ changedValue, allValue, form })}>
            <EditableContext.Provider value={form}>
                <SortableItem index={index} {...props} />
            </EditableContext.Provider>
        </Form>
    )
}

/**
 * @component EditableCell
 * @description [地堡精密编辑单元] 最小物理作战单位。
 * 支持多种装配模式（text/number/select/checkbox），并具备“自动对焦”与“失焦自愈（自动保存）”功能。
 *
 * @param {Object} props - 构筑参数
 * @param {Array} [props.rules=[]] - 逻辑校验准则
 * @param {Object} props.record - 当前行原始物资数据
 * @param {boolean} props.disabled - 物理锁定：是否禁止修改
 * @param {string} props.title - 零部件视觉标题，兼作占位符使用
 * @param {React.ReactNode} props.children - 默认展示的视觉节点
 * @param {boolean} props.editable - 权限协议：是否允许开启编辑模式
 * @param {string} props.dataIndex - 逻辑寻址地址：对应后端数据的字段名
 * @param {Array} [props.options=[]] - 数据字典（仅用于 select/checkbox）
 * @param {Function} props.handleSave - 物理封存协议：数据校验通过后的保存回调
 * @param {boolean} [props.defaultEdit] - 持久化模式：是否默认始终开启编辑状态
 * @param {string} [props.editType='text'] - 零部件型号（text/number/select/checkbox）
 */
export const EditableCell = ({ title, record, editable, disabled, children, dataIndex, placeholder, handleSave, defaultEdit, rules = [], options = [], editType = 'text', ...restProps }) => {

    const inputRef = useRef(null)
    const form = useContext(EditableContext)

    const [editing, setEditing] = useState(false)

    /**
     * @description [自动对焦协议] 当单元格进入“骇入模式”时，光标自动锁定，提升作战效率。
     */
    useEffect(() => {
        if (editing) {
            if (inputRef.current && typeof inputRef.current.focus === 'function') {
                inputRef.current.focus()
            }
        }
    }, [editing])

    /**
     * @function toggleEdit
     * @description 切换“观察/骇入”模式，并执行初始信号同步。
     */
    const toggleEdit = () => {
        setEditing(!editing)
        form.setFieldsValue({ [dataIndex]: record[dataIndex] })
    }

    /**
     * @async
     * @function save
     * @description 执行“物理封存协议”：触发表单校验，通过后自动关闭编辑状态并向中枢发送保存请求。
     */
    const save = async () => {
        try {
            const values = await form.validateFields()
            if (!defaultEdit) {
                toggleEdit()
            }
            handleSave({ ...record, ...values })
        } catch (errInfo) {
            console.log('保存失败:', errInfo)
        }
    }

    let inputNode

    const formProps = {
        rules,
        name: dataIndex,
        style: { margin: 0 },
    }

    const commonProps = {
        onBlur: save,
        disabled: disabled,
        placeholder: placeholder ?? title,
    }

    switch (editType) {
        case 'select':
            inputNode = <Select ref={inputRef} options={options} {...commonProps} />
            break;
        case 'number':
            inputNode = <InputNumber ref={inputRef} onPressEnter={save} {...commonProps} />
            break
        case 'checkbox':
            inputNode = (
                <div tabIndex={-1} onBlur={e => {
                    /**
                     * 💡 [地堡特有防御逻辑]：解决 Checkbox.Group 内部焦点切换导致误触发 save 的问题。
                     * 通过 contains 判定焦点是否真正离开了当前作战区域。
                     */
                    if (!e.currentTarget.contains(e.relatedTarget)) {
                        save()
                    }
                }}>
                    <Form.Item {...formProps}>
                        <Checkbox.Group ref={inputRef} options={options} disabled={disabled} {...(options.length === 1 ? { onChange: save } : {})} />
                    </Form.Item>
                </div>
            )
            break;
        default:
            inputNode = <Input ref={inputRef} onPressEnter={save} {...commonProps} />
    }

    return (
        <td {...restProps}>
            {editable ? (
                editing || defaultEdit ? (
                    // 骇入模式：渲染输入零件
                    <Form.Item {...(['checkbox'].includes(editType) ? { style: formProps.style } : formProps)}>
                        {inputNode}
                    </Form.Item>
                ) : (
                    // 观察模式：渲染静态内容，点击开启骇入
                    <div onClick={toggleEdit} className='editable-cell-value-wrap' style={{ paddingRight: 24, minHeight: 32, cursor: 'pointer' }}>
                        {children}
                    </div>
                )
            ) : (children)}
        </td>
    )
}