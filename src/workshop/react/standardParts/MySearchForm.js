import dayjs from 'dayjs'
import { MyBaseForm } from './MyBaseForm'
import { useMemo, useState, useEffect } from 'react'
import { Row, Col, Form, Button, Space } from 'antd'
import { SearchOutlined, RedoOutlined } from '@ant-design/icons'

/**
 * @component MySearchForm
 * @description [地堡战术搜索中心] 高级搜索表单组件。
 * 集成了“URL 状态同步（持久化）”、“日期范围物理拆解”以及“动态伸缩布局”三大核心能力。
 *
 * @param {Object} props - 指挥官指令包
 * @param {Object} props.form - Antd Form 实例，表单的主控舵盘
 * @param {Function} [props.customReset] - 逻辑劫持：自定义重置协议
 * @param {Function} [props.customFinish] - 逻辑劫持：自定义提交协议
 * @param {Array} props.formItems - 零部件清单：定义所有的搜索输入单元
 * @param {number} [props.showLimit=7] - 初始可见能级：默认展示的零部件数量
 * @param {number} [props.defaultPageSize=10] - 默认吞吐量：重置时的初始每页条数
 * @param {Function} [props.onValuesChange] - 联动传感：当表单值变动时的即时反馈
 * @param {Object} props.initialValues - 初始信号：从 URL 或缓存中解析出的初始参数
 * @param {React.ReactNode} [props.extra] - 额外挂件：在按钮区域注入自定义战术单元
 * @param {Function} props.setSearch - 状态分发器：用于更新全局搜索参数并触发重新构筑
 * @param {Object} props.search - 当前的全局搜索状态（包含 pageNo, pageSize 及各过滤项）
 * @param {boolean} props.loading - 战场负载状态：请求中时锁定按钮，防止由于重复指令导致的逻辑冲突
 * @param {boolean} [props.syncUrlParams=true] - 物理同步开关：是否将搜索状态实时镜像至 URL 链接中
 *
 * @example
 * <MySearchForm
 *   form={form}
 *   search={search}
 *   setSearch={setSearch}
 *   formItems={[{ label: '状态', name: 'status', type: 'select', options: [...] }]}
 * />
 */
export const MySearchForm = ({ form, search, options, loading, labelCol, setSearch, formItems, showLimit = 7, initialValues, initialParams, customReset, extra, customFinish, onValuesChange, syncUrlParams = true, defaultPageSize = 10 }) => {

    const [limit, setLimit] = useState(showLimit)

    const searchItems = useMemo(() => formItems.map(item => ({ ...item, ...(['select'].includes(item.type) ? { options: item.options ?? options?.[item.name] ?? [] } : {}) })), [formItems, options])

    /**
     * @function handleReset
     * @description 执行“归零协议”：清除当前所有搜索信号，并可选择性擦除 URL 中的物理记录。
     */
    const handleReset = () => {
        form.resetFields()
        if (syncUrlParams) {
            // 💡 修正逻辑：只有当 formItems 里【没有任何一项】包含这个 key 时，才视为默认参数
            const defaultQueryEntries = Object.entries(initialValues).filter(([key, _]) => !formItems.some(item => item.name.includes(key)))
            const defaultQuery = Object.fromEntries(defaultQueryEntries)
            const params = new URLSearchParams(defaultQuery)
            // 💡 执行物理重写：将 URL 恢复为仅含默认参数的状态
            const newUrl = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname
            window.history.replaceState(null, '', newUrl)
        }
        if (customReset) {
            customReset()
        } else {
            // 逻辑重置：强制返回第一页，并恢复默认吞吐量
            setSearch({ pageNo: 1, pageSize: search.pageSize ?? defaultPageSize, ...initialParams })
        }
    }

    /**
     * @function handleFinish
     * @description 执行“数据发射协议”：对原始表单数据进行脱水和转换，尤其处理复杂的日期范围协议。
     * @param {Object} values - 原始表单数据包
     */
    const handleFinish = values => {
        const formattedValues = { ...values }
        Object.keys(formattedValues).forEach(key => {
            const val = formattedValues[key]
            const isDateType = formItems.find(item => item.name === key)?.type?.includes('date')
            // 💡 [黑科技 1] 日期自动转换与拆解
            if (isDateType && val) {
                if (Array.isArray(val) && val.length > 0) {
                    // 物理拆分：当 name 为 'start,end' 格式时，自动拆解为两个独立的后端参数
                    const [startKey, endKey] = key.split(',')
                    formattedValues[startKey] = val[0].startOf('day').valueOf()// 修正为当日 00:00:00
                    formattedValues[endKey] = val[1].endOf('day').valueOf()// 修正为当日 23:59:59
                    delete formattedValues[key]
                } else {
                    // 单日转换：转化为毫秒级数字
                    formattedValues[key] = val.valueOf()
                }
            }
        })
        if (syncUrlParams) {
            // 💡 [黑科技 2] 镜像至 URL
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

    /**
     * @description [信号自愈] 初始化逻辑：
     * 将来自 URL 的字符串信号重新转化为地堡可读的 `dayjs` 对象。
     */
    useEffect(() => {
        if (Object.values(initialValues).length > 0 && formItems.length > 0) {
            const newValues = {}
            formItems.forEach(item => {
                // 处理单字段回显
                if (initialValues[item.name] !== undefined) {
                    const value = initialValues[item.name]
                    newValues[item.name] = item.type?.includes('date') ? dayjs(Number(value)) : value
                }
                // 处理双字段（日期范围）回显：执行物理重组
                if (item.name?.includes(',') && item.type?.includes('date')) {
                    const [startKey, endKey] = item.name.split(',')
                    if (initialValues[startKey] && initialValues[endKey]) {
                        newValues[item.name] = [dayjs(Number(initialValues[startKey])), dayjs(Number(initialValues[endKey]))]
                    }
                }
                // 处理多选框回显
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
                        {/* 物理装配：利用底层 MyBaseForm 单元进行渲染 */}
                        <MyBaseForm item={item} form={form} />
                    </Col>
                ))}
                {/*
                  战术控制区：
                  1. 'flex=auto' 确保按钮组始终靠右对齐。
                  2. 'showLimit' 控制页面纵向熵值，防止过多搜索项挤占战场视野。
                */}
                <Col flex='auto' style={{ textAlign: 'right' }}>
                    <Form.Item>
                        <Space>
                            <Button type='primary' icon={<SearchOutlined />} loading={loading} htmlType='submit'>查询</Button>
                            <Button icon={<RedoOutlined />} onClick={handleReset} loading={loading} htmlType='reset'>重置</Button>
                            {extra}
                            {/* 动态伸缩协议：根据当前零部件数量决定是否显示展开/收起按钮 */}
                            {formItems.length > showLimit && (<a onClick={() => setLimit(formItems.length > limit ? formItems.length : showLimit)}>{formItems.length > limit ? '展开' : '收起'}</a>)}
                        </Space>
                    </Form.Item>
                </Col>
            </Row>
        </Form>
    )
}