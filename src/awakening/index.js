const fs = require('fs')
const path = require('path')

let instance = null

module.exports = {

    init: async ({ template }, dialog, version, local) => {

        const recruiter = require('../headquarters/recruiter')
        const logistics = recruiter(path.join(__dirname, '../logistics'))
        const constitution = recruiter(path.join(__dirname, '../constitution'))
        const headquarters = recruiter(path.join(__dirname, '../headquarters'))

        const yorha = logistics.presenter.yorha()

        const builderPath = path.join(__dirname, `../workshop/${template}/builder`)
        if (!fs.existsSync(builderPath)) {
            yorha.commander.report(dialog.bunker.frameworkNotSupported(template), 'red')
            return
        }

        const accessPoint = {
            yorha,
            dialog,
            template,
            logistics,
            headquarters,
            constitution,
            units: recruiter(path.join(__dirname, '../units')),
            briefings: recruiter(path.join(__dirname, `../workshop/${template}/briefings`)),
        }

        if (version) {
            await logistics.presenter.bootSequence(version, local)
            yorha.operator6O.report(dialog.operator6O.call2B)
        }

        const llm = require('../gateway')(accessPoint)
        const builder = require(builderPath)(accessPoint)
        const labs = require('../labs')({ llm, ...accessPoint })


        instance = { llm, labs, builder, ...accessPoint }
        return instance
    },

    get: () => {
        return new Proxy({}, {
            get(target, prop) {
                if (!instance) {
                    throw new Error()
                }
                return instance[prop]
            }
        })
    },

    reboot() {
        const { template, dialog } = instance
        delete require.cache[require.resolve(path.join(process.cwd(), 'bunker', 'config.js'))]
        instance.labs?.tower?.close()
        instance = null
        return this.init({ template }, dialog)
    }
}