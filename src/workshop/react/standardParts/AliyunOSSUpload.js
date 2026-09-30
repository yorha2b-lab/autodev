import { Button, Upload } from 'antd'
import { initOSS } from '../utils/utils'
import { useState, useEffect } from 'react'
import { UploadOutlined } from '@ant-design/icons'

/**
 * @component AliyunOSSUpload
 * @description [地堡核心传输单元] 阿里云 OSS 高级上传组件。
 * 集成了“物理路径自动重组”、“STS 令牌自动续期”以及“ Antd 属性无损透传”三大核心协议。
 *
 * @param {Object} props - 构筑参数
 * @param {string} [props.path] - 默认存储扇区：定义文件在云端的物理根路径
 * @param {string} [props.url] - 司令部通信地址：用于申请最新的物理传输令牌 (STS)
 * @param {Array} props.value - 传感器当前封存的文件列表 (符合 Antd fileList 规范)
 * @param {Function} props.onChange - 状态反馈协议：当物理文件状态变更时同步至地堡中枢
 * @param {Object} [props.oss] - 外部空投的初始凭证包。若缺失，组件将启动自主初始化流程。
 * @param {Object} [props.options] - 通信加密/配置参数：在申请令牌时透传给 request 的额外负载
 * @param {Object} [props.originUploadProps] - [重要] 无损透传：支持 Antd Upload 的所有原生属性（如 multiple, accept 等）
 *
 * @example
 * // 基本构筑
 * <AliyunOSSUpload path='project/data' url='/api/oss/token' />
 *
 * // 高级装配（限制文件类型并开启多选）
 * <AliyunOSSUpload accept='.pdf' multiple={true} path='docs' url='/api/oss/token' />
 */
export const AliyunOSSUpload = ({ value, onChange, ...restProps }) => {

    // 💡 物理剥离：将地堡专用参数与 Antd 原生属性分离
    const { oss, url, path, options, expireField = 'expire', ...originUploadProps } = restProps

    const [OSSData, setOSSData] = useState(oss)

    /**
     * @async
     * @function init
     * @description [信号握手] 执行令牌获取协议，从司令部申请最新的物理上传授权
     */
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
        // 💡 自愈逻辑：如果发现能源包 (OSSData) 为空，则自动触发初始化
        if (!OSSData) {
            init()
        }
    }, [])

    const handleChange = ({ fileList }) => onChange?.([...fileList])

    const onRemove = file => {
        const files = (value || []).filter(v => v.uid !== file.uid)
        onChange?.(files)
    }

    /**
     * @function getExtraData
     * @description [数据封装] 将动态生成的物理凭证与目标文件路径压入传输负载
     * @param {Object} file - 待传输的文件对象
     */
    const getExtraData = file => ({
        key: file.url,
        policy: OSSData?.policy,
        Signature: OSSData?.signature,
        OSSAccessKeyId: OSSData?.accessKeyId,
        'x-oss-security-token': OSSData?.stsToken,
    })

    /**
     * @async
     * @function beforeUpload
     * @description [生存期侦察] 在传输启动前执行 TTL 检测。
     * 若令牌已失效（过期），则强行拦截并执行同步刷新协议，同时执行物理路径归一化。
     */
    const beforeUpload = async file => {
        let currentOSS = OSSData
        const expire = Number(OSSData?.[expireField] ?? 0) * 1000
        if (expire < Date.now()) {
            currentOSS = await init()
        }
        // 💡 物理路径重组：通过正则清除多余的路径分隔符，确保存储节点坐标唯一
        file.url = `${currentOSS?.dir ?? path}/${file.uid}_${file.name}`.replace(/\/\//g, '/')
        return file
    }

    /**
     * @constant uploadProps
     * @description [物理合并] 最终生成的 Antd Upload 指令集：
     * 自动优先应用 originUploadProps 中的自定义设置。
     */
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