const fs = require('fs')
const chalk = require('chalk')

module.exports = ({ dialog }) => ({
    dirs: dir => fs.mkdirSync(dir, { recursive: true }),
    files: ({ from, to, exist, success }) => {
        if (fs.existsSync(to)) {
            if (!!exist) {
                return console.log(chalk.yellow(dialog.bunker[exist]))
            }
            return
        }
        fs.cpSync(from, to, { recursive: true })
        if (!!success) {
            console.log(chalk.green(dialog.bunker[success]))
        }
    }
})