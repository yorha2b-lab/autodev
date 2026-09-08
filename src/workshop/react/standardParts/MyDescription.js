import { Form, Descriptions } from 'antd'
import { MyBaseForm } from './MyBaseForm'

export const MyDescription = ({ title, column, descriptions, form: externalForm, onValuesChange }) => {

    const [internalForm] = Form.useForm()
    const form = externalForm || internalForm

    return (
        <Form form={form} preserve={false} component={false} onValuesChange={onValuesChange}>
            <Descriptions title={title} column={column}>
                {descriptions.map(item => (
                    <Descriptions.Item key={item.label} label={item.name ? undefined : item.label}>
                        {item.name ? <MyBaseForm item={item} form={form} /> : item.value}
                    </Descriptions.Item>))}
            </Descriptions>
        </Form>
    )
}