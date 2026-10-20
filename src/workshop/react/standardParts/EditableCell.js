import { SortableElement } from 'react-sortable-hoc'
import { Form, Input, InputNumber, Select, Checkbox, TreeSelect } from 'antd'
import { useRef, useState, useEffect, useContext, createContext } from 'react'

const EditableContext = createContext(null)

const SortableItem = SortableElement((props) => <tr {...props} />)

export const EditableRow = ({ index, record, columns, draggable, ...props }) => {

    const [form] = Form.useForm()

    useEffect(() => {
        if (record) {
            const modeCol = columns.find(col => col.dataIndex in record && col.mode)
            const extra = modeCol ? { [modeCol.dataIndex]: record[modeCol.dataIndex]?.toString()?.split(',') || [] } : {}
            form.setFieldsValue({ ...record, ...extra })
        }
    }, [record])

    return (
        <Form form={form} component={false} onValuesChange={(changedValue, allValue) => props?.onValuesChange?.({ changedValue, allValue, form })}>
            <EditableContext.Provider value={form}>
                {draggable ? <SortableItem index={index} {...props} /> : <tr {...props} />}
            </EditableContext.Provider>
        </Form>
    )
}

export const EditableCell = ({ mode, title, record, rowKey, editable, disabled, children, dataIndex, editingKey, dependencies, placeholder, handleSave, defaultEdit, editRender, rules = [], options = [], editType = 'text', ...restProps }) => {

    const inputRef = useRef(null)
    const form = useContext(EditableContext)

    const [editing, setEditing] = useState(record?.[rowKey] === editingKey)

    useEffect(() => {
        if (editing) {
            if (inputRef.current && typeof inputRef.current.focus === 'function') {
                inputRef.current.focus()
            }
        }
    }, [editing])

    const toggleEdit = () => {
        setEditing(prev => !prev)
        form.setFieldsValue({ [dataIndex]: mode ? record[dataIndex]?.toString()?.split(',') || [] : record[dataIndex] })
    }

    const save = async () => {
        try {
            const values = await form.validateFields()
            if (mode) {
                values[dataIndex] = values[dataIndex].join(',')
            }
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
        dependencies,
        name: dataIndex,
        style: { margin: 0 },
    }

    const commonProps = {
        onBlur: save,
        disabled: disabled,
        placeholder: placeholder ?? title,
    }

    switch (editType) {
        case 'number':
            inputNode = <InputNumber ref={inputRef} onPressEnter={save} {...commonProps} />
            break
        case 'select':
            inputNode = <Select ref={inputRef} mode={mode} options={options} {...commonProps} />
            break;
        case 'treeSelect':
            inputNode = <TreeSelect ref={inputRef} treeData={options} {...commonProps} />
            break;
        case 'custom':
            inputNode = editRender({ form, record, save, dataIndex, disabled, toggleEdit, commonProps })
            break
        case 'checkbox':
            inputNode = (
                <div tabIndex={-1} onBlur={e => {
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
                editing || defaultEdit || record[rowKey] === editingKey ?
                    <Form.Item {...(['custom', 'checkbox'].includes(editType) ? { style: formProps.style } : formProps)}>{inputNode}</Form.Item> :
                    <div onClick={toggleEdit} className='editable-cell-value-wrap' style={{ paddingRight: 24, minHeight: 32, cursor: 'pointer' }}>{children}</div>
            ) : (children)}
        </td>
    )
}