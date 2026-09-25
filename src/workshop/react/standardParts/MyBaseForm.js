import { Fragment } from 'react'
import { formNode } from './index'
import { Form, Button } from 'antd'
import { PlusOutlined } from '@ant-design/icons'

/**
 * @function getValueFromEvent
 * @description [数据拦截协议] 专门针对上传类组件的物理补丁。
 * 修正 Antd 默认将 Event 对象存入 Form 的行为，强制提取物理文件列表 (fileList)。
 * @param {Object|Array} e - 原始触发事件或文件数组
 * @returns {Array} 归一化后的文件列表
 */
const getValueFromEvent = e => {
    if (Array.isArray(e)) {
        return e
    }
    return e?.fileList
}

/**
 * @function renderFormContent
 * @description [中枢渲染逻辑] 负责装配 Form.Item 的内核。
 * 具备“路径递归”与“单位挂件”两大核心功能。
 *
 * @param {Object} params - 渲染参数
 * @param {Object} params.item - 零部件配置对象
 * @param {Array} [params.prefixName=[]] - 物理路径前缀，用于支持 Form.List 的深层嵌套
 * @returns {React.ReactNode} 装配完成的输入单元
 */
const renderFormContent = ({ item, prefixName = [] }) => {

    // 💡 物理占位逻辑：若无 name 属性，则直接输出原始 value 文本
    if (!item.name) {
        return item.value
    }

    // 💡 路径自动对齐：支持字符串或数组格式的 name，自动合并前缀实现“逻辑寻址”
    const namePath = Array.isArray(prefixName) ? [...prefixName, ...(Array.isArray(item.name) ? item.name : [item.name])] : item.name

    const inputNode = (
        <Form.Item noStyle name={namePath} rules={item.rules} dependencies={item.dependencies} initialValue={item.value} {...(['upload', 'ossUpload'].includes(item.type) ? { getValueFromEvent, valuePropName: 'fileList' } : { valuePropName: item.valuePropName })}>
            {formNode({ item })}
        </Form.Item>
    )

    // 💡 视觉单位挂件逻辑：实现类似“金额(元)”的自动横向排版
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

/**
 * @component MyBaseForm
 * @description [地堡通用零部件单元] 表单系统的物理外壳。
 * 具备“单兵作战（Item）”与“集群协同（List）”两种模式切换能力。
 *
 * @param {Object} props - 组件属性
 * @param {Object} props.item - 构筑协议对象
 * @param {Object} props.form - Antd Form 实例，用于实现复杂的跨组件联动
 * @param {boolean} [props.item.isList] - 模式切换：是否开启动态增减列表模式
 * @param {Function} [props.item.render] - 逻辑劫持：支持自定义渲染函数，可完全改写渲染行为
 *
 * @example
 * // 模式 A：标准表单项
 * <MyBaseForm item={{ label: '姓名', name: 'name' }} />
 *
 * // 模式 B：动态列表项
 * <MyBaseForm item={{ isList: true, name: 'users', render: (field) => <Input {...field} /> }} />
 */
export const MyBaseForm = ({ item, form }) => {
    return (
        item.isList ?
            // 💡 集群模式：处理动态数组类型的表单构筑
            <Form.List name={item.name} initialValue={item.value}>
                {(fields, { add, remove }) => (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {fields.map((field, index) => (
                            <Fragment key={field.key}>
                                {/* 物理映射：将 field 控制器回传给指挥官自定义的 render 逻辑 */}
                                {item.render(field, index, { add, remove }, form, renderFormContent)}
                            </Fragment>
                        ))}
                        {/* 零信号兜底：若列表为空，显示添加按钮 */}
                        {fields.length === 0 && <Button type='dashed' onClick={() => add()} block icon={<PlusOutlined />}>添加{item.label || '项'}</Button>}
                    </div>
                )}
            </Form.List> :
            // 💡 单兵模式：标准 Form.Item 构筑
            <Form.Item
                label={item.label}
                tooltip={item.tooltip}
                labelCol={item.labelCol}
                wrapperCol={item.wrapperCol}
                extra={item.extra || item.help}
                required={item.required ?? item.rules?.some(v => v.required)}
                style={{ marginBottom: !item.name ? 0 : undefined, ...item.style }}
            >
                {/*
                  逻辑优先级：
                  1. 优先使用 item.render 执行语义劫持
                  2. 否则使用 renderFormContent 进行标准构筑
                */}
                {item.render ? (typeof item.render === 'function' ? item.render(item, form) : item.render) : renderFormContent({ item })}
            </Form.Item>
    )
}