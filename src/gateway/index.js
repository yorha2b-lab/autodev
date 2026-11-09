module.exports = ({ yorha, dialog, logistics, constitution }) => {

    const sharp = require('sharp')

    const { sleep } = logistics.presenter
    const { FRONTEND_ENGINEER } = constitution.system
    const { textModel, visionModel } = logistics.supporter.getConfig()

    const openAI = require('./client')()
    const askAI = require('./protocol')({ yorha, sleep, dialog, openAI })

    return {
        askAI,
        simulation: async ({ columns, fileName }) => {
            return askAI({
                model: textModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    { role: 'user', content: constitution.simulation({ columns, fileName }) }
                ]
            })
        },
        similarity: async ({ fileName, english }) => {
            return askAI({
                model: textModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    { role: 'user', content: constitution.similarity({ fileName, english }) }
                ]
            })
        },
        council: async ({ bunkerAnchors, realApis }) => {
            return askAI({
                model: textModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    { role: 'user', content: constitution.council({ bunkerAnchors, realApis }) }
                ]
            })
        },
        replicate: async ({ schema, prompt, filePath }) => {
            const compressedBuffer = await sharp(filePath)
                .resize(1280, null, { withoutEnlargement: true })
                .jpeg({ quality: 80 })
                .toBuffer()
            const base64Image = compressedBuffer.toString('base64')

            return askAI({
                model: visionModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    {
                        role: 'user',
                        content: [
                            { type: 'text', text: prompt },
                            { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${base64Image}` } }
                        ]
                    }
                ],
                response_format: schema ? { strict: true, type: 'json_schema', json_schema: schema } : { type: 'json_object' }
            })
        },
        reconciler: async ({ responseStr, resourceStr }) => {
            return askAI({
                model: textModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    { role: 'user', content: constitution.reconciler({ responseStr, resourceStr }) }
                ]
            })
        },
        maintain: async ({ prdText, moduleName, moduleCodeView }) => {
            return askAI({
                model: textModel,
                messages: [
                    { role: 'system', content: FRONTEND_ENGINEER },
                    { role: 'user', content: constitution.maintain({ prdText, moduleName, moduleCodeView }) }
                ]
            })
        },
    }
}