module.exports = bunker => {

    const path = require('path')
    const chokidar = require('chokidar')
    const commander = require('../headquarters/commander')(bunker)

    const settingObserver = chokidar.watch('./bunker/config.js', { persistent: true, ignoreInitial: true })

    const missionObserver = chokidar.watch('./bunker/mission/', {
        persistent: true,
        ignoreInitial: true,
        ignored: /(^|[\/\\])\../,
        awaitWriteFinish: { stabilityThreshold: 500, pollInterval: 100 },
    })

    missionObserver.on('add', filePath => {
        if (['.png', '.jpg', '.jpeg', '.webp'].includes(path.extname(filePath).toLowerCase())) {
            commander.receive({ input: filePath })
        }
    })

    settingObserver.on('change', file => {
        if (file.endsWith('config.js')) {
            bunker.reboot()
        }
    })
}