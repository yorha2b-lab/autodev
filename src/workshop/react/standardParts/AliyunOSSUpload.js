import { Button, Upload } from 'antd'
import { initOSS } from '../utils/utils'
import { useState, useEffect } from 'react'
import { UploadOutlined } from '@ant-design/icons'

export const AliyunOSSUpload = ({ value, onChange, ...restProps }) => {

    const { oss, url, path, options, expireField = 'expire', ...originUploadProps } = restProps

    const [OSSData, setOSSData] = useState(oss)

    const init = async () => {
        try {
            const result = await initOSS(url, options)
            setOSSData(result)
            return result
        } catch (err) {
            console.log(err)
        }
    }

    useEffect(() => {
        if (!OSSData) {
            init()
        }
    }, [])

    const handleChange = ({ fileList }) => onChange?.([...fileList])

    const onRemove = file => {
        const files = (value || []).filter(v => v.uid !== file.uid)
        onChange?.(files)
    }

    const getExtraData = file => ({
        key: file.url,
        policy: OSSData?.policy,
        Signature: OSSData?.signature,
        OSSAccessKeyId: OSSData?.accessKeyId,
        'x-oss-security-token': OSSData?.stsToken,
    })

    const beforeUpload = async file => {
        let currentOSS = OSSData
        const expire = Number(OSSData?.[expireField] ?? 0) * 1000
        if (expire < Date.now()) {
            currentOSS = await init()
        }
        file.url = `${currentOSS?.dir ?? path}/${file.uid}_${file.name}`.replace(/\/\//g, '/')
        return file
    }

    const uploadProps = {
        onRemove,
        name: 'file',
        beforeUpload,
        fileList: value,
        data: getExtraData,
        action: OSSData?.host,
        onChange: handleChange,
        ...originUploadProps
    }

    return (
        <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>
    )
}