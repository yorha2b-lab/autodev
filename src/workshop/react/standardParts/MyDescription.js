import { Form, Descriptions } from 'antd'
import { MyBaseForm } from './MyBaseForm'

export const MyDescription = ({ title, column, layout = 'vertical', labelStyle, contentStyle, descriptions, form: externalForm, onValuesChange }) => {

    const [internalForm] = Form.useForm()
    const form = externalForm || internalForm

    return (
        <Form form={form} preserve={false} component={false} onValuesChange={onValuesChange}>
            <Descriptions title={title} column={column} layout={layout} labelStyle={labelStyle} contentStyle={contentStyle}>
                {descriptions.map(item => (
                    <Descriptions.Item key={item.label} span={item.span ?? 1} label={item.name ? undefined : item.label}>
                        {item.name ? <MyBaseForm item={item} form={form} /> : item.value}
                    </Descriptions.Item>))}
            </Descriptions>
        </Form>
    )
}