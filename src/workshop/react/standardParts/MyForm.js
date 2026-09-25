import { MyBaseForm } from './MyBaseForm'
import { Row, Col, Form, Button, Collapse } from 'antd'

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

// 定义“零部件增强协议”处理器,以后加任何新功能，只需要在这个对象里加一个 Key，不需要动主逻辑！
const ACTION_PROCESSORS = {
    // 处理尾操作按钮
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

const FormRenderer = ({ form, formItems, tableProps = {} }) => {

    // 定义核心渲染逻辑，供递归使用
    const renderCore = items => <FormRenderer form={form} formItems={items} tableProps={tableProps} />

    // 定义单项动作注入逻辑
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
        // 情况 A：发现容器型零件 (含有 layoutType)
        if (item.layoutType && LAYOUT_PROCESSORS[item.layoutType]) {
            const Layout = LAYOUT_PROCESSORS[item.layoutType] ?? LAYOUT_PROCESSORS.default
            return (
                <Layout
                    item={item}
                    key={item.name || index}
                    renderCore={renderCore} // 注入渲染能力，让 Layout 自己去 Map
                />
            )
        }

        // 情况 B：标准作战零件
        return (
            <Col span={item.span ?? 6} key={item.name || index}>
                <MyBaseForm item={{ ...item, ...getRenderItemProps(item) }} form={form} />
            </Col>
        )
    })
}

export const MyForm = ({ formItems, externalForm, labelCol, wrapperCol, tableProps, layout = 'horizontal', onValuesChange }) => {

    const [internalForm] = Form.useForm()
    const form = externalForm || internalForm

    return (
        <Form form={form} layout={layout} preserve={false} labelCol={labelCol} wrapperCol={wrapperCol} onValuesChange={onValuesChange}>
            <Row gutter={[24, 0]}>
                <FormRenderer form={form} formItems={formItems} tableProps={tableProps} />
            </Row>
        </Form>
    )
}
