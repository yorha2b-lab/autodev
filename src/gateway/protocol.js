module.exports = ({ yorha, sleep, dialog, openAI }) => {

    return async function askAI({ model, messages, response_format = { type: 'json_object' }, retryCount = 0 }) {

        if (retryCount >= 3) {
            yorha.commander.report(dialog.bunker.linkSevered, 'red')
            throw new Error(dialog.bunker.linkSevered)
        }

        try {
            const response = await openAI.chat.completions.create({
                model,
                messages,
                top_p: 0.1,
                response_format,
                temperature: 0.01,
            })
            let raw = response.choices[0].message.content.trim()
            raw = raw.replace(/^```json\n?/, '').replace(/\n?```$/, '')
            const match = raw.match(/[\{\[][\s\S]*[\}\]]/)
            const JSON5 = require('json5')
            return JSON5.parse(match ? match[0] : raw)
        } catch (err) {
            const statusCode = err.status || err.response?.status
            const isAuthError = [401, 402].includes(statusCode)
            if (isAuthError) {
                yorha.commander.report(dialog.bunker.accessDenied, 'red')
                throw new Error(dialog.bunker.accessDenied)
            }

            yorha.commander.report(dialog.bunker.networkInstability(retryCount + 1))
            const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)
            await sleep(delay)
            return askAI({ model, messages, response_format, retryCount: retryCount + 1 })
        }
    }
}