import dayjs from 'dayjs'
import { MyBaseForm } from './MyBaseForm'
import { flattenFormItems } from '../utils/utils'
import { useContext, createContext } from 'react'
import { Row, Col, Form, Button, Collapse } from 'antd'

const FormContext = createContext({})

const LAYOUT_PROCESSORS = {
    section: ({ item, renderCore }) => (
        <Col span={item.span ?? 24} style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 'bold', marginBottom: 12, borderLeft: '4px solid #1890ff', paddingLeft: 8 }}>{item.title}</div>
            <Row gutter={[24, 0]}>
                {renderCore(item.childItems || [])}
            </Row>
        </Col>
    ),
    collapse: ({ item, renderCore }) => (
        <Col span={item.span ?? 24} style={{ marginBottom: 16 }}>
            <Collapse defaultActiveKey={['1']}>
                <Collapse.Panel key='1' header={<span style={{ fontWeight: 'bold' }}>{item.title}</span>}>
                    <Row gutter={[24, 0]}>
                        {renderCore(item.childItems || [])}
                    </Row>
                </Collapse.Panel>
            </Collapse>
        </Col>
    ),
    default: ({ item, renderCore }) => <Row gutter={[24, 0]}>{renderCore(item.childItems || [])}</Row>
}

const ACTION_PROCESSORS = {
    addonAfter: (item, { tableConfig, setModalTable, setSelectedTableRows }) => ({
        props: {
            addonAfter: (
                <Button onClick={() => {
                    setSelectedTableRows([])
                    setModalTable({ visible: true, title: `选择${item.label}`, ...tableConfig[item.name] })
                }}>
                    {item.addonAfter}
                </Button>
            )
        }
    }),
    // 以后想加个“前缀图标”？直接加在这里：
    // prefix: (item) => ({ props: { prefix: <Icon type={item.prefix} /> } }),
}

const FormRenderer = ({ form, options, formItems }) => {

    const { tableProps, renderAction } = useContext(FormContext)

    const renderCore = items => <FormRenderer form={form} options={options} formItems={items} />

    const getRenderItemProps = item => {
        if (!item.renderAction) return {}
        const props = {}
        Object.keys(ACTION_PROCESSORS).forEach(key => {
            if (item[key]) {
                Object.assign(props, ACTION_PROCESSORS[key](item, tableProps))
            }
        })
        return props
    }

    return formItems.map((item, index) => {
        const processedItem = {
            ...item,
            ...(item.renderAction && renderAction?.[item.name] ? { render: renderAction[item.name] } : {}),
            ...(['select', 'radio', 'checkbox'].includes(item.type) && !item.options ? { options: options?.[item.name] || [] } : {})
        }

        if (processedItem.layoutType && LAYOUT_PROCESSORS[processedItem.layoutType]) {
            const Layout = LAYOUT_PROCESSORS[processedItem.layoutType] ?? LAYOUT_PROCESSORS.default
            return (
                <Layout
                    item={processedItem}
                    key={processedItem.name || index}
                    renderCore={renderCore}
                />
            )
        }

        return (
            <Col span={processedItem.span ?? 6} key={processedItem.name || index}>
                <MyBaseForm item={{ ...processedItem, ...getRenderItemProps(processedItem) }} form={form} />
            </Col>
        )
    })
}

export const MyForm = ({ record, formItems = [], externalForm, labelCol, wrapperCol, tableProps, onValuesChange, layout = 'horizontal', options = {}, renderAction = {} }) => {

    const [internalForm] = Form.useForm()
    const form = externalForm || internalForm

    useEffect(() => {
        if (record && Object.keys(record).length > 0) {
            const itemMap = new Map(flattenFormItems(formItems).map(i => [i.name, i]))
            const initialData = {}
            Object.entries(record).forEach(([key, value]) => {
                const config = itemMap.get(key)
                if (config?.type?.includes('date') && value) {
                    if (Array.isArray(value)) {
                        initialData[key] = value.map(v => dayjs(v))
                    } else if (typeof value === 'string' && value.includes(',')) {
                        initialData[key] = value.split(',').map(v => dayjs(v))
                    } else {
                        initialData[key] = dayjs(value)
                    }
                } else if ((config?.type === 'select' && config.mode) || config?.type === 'checkbox') {
                    initialData[key] = Array.isArray(value) ? value : value.split(config.separator ?? ',')
                } else {
                    initialData[key] = value
                }
            })
            form.setFieldsValue(initialData)
        }
    }, [form, record, formItems])

    return (
        <FormContext.Provider value={{ tableProps, renderAction }}>
            <Form form={form} layout={layout} preserve={false} labelCol={labelCol} wrapperCol={wrapperCol} onValuesChange={onValuesChange} scrollToFirstError={{ behavior: 'smooth', block: 'center' }}>
                <Row gutter={[24, 0]}>
                    <FormRenderer form={form} options={options} formItems={formItems} />
                </Row>
            </Form>
        </FormContext.Provider>
    )
}