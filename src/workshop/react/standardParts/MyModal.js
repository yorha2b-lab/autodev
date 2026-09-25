import { Modal } from 'antd'
import { useState } from 'react'

export const MyModal = ({ width, title, okText, footer, record, visible, children, handleOk, setModal, cancelText, okButtonProps }) => {

    const [pending, setPending] = useState(false)

    const handleCancel = () => setModal({ visible: false })

    const ctx = { record, pending, handleOk, handleCancel, setModal, setPending }

    return (
        <Modal
            centered
            title={title}
            width={width}
            open={visible}
            destroyOnClose
            okText={okText}
            onOk={handleOk}
            cancelText={cancelText}
            onCancel={handleCancel}
            confirmLoading={pending}
            okButtonProps={okButtonProps}
            footer={typeof footer === 'function' ? footer(ctx) : footer}
            bodyStyle={{ paddingBottom: 0, maxHeight: '80vh', overflowY: 'auto' }}
        >
            {children}
        </Modal>
    )
}