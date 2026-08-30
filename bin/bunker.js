#!/usr/bin/env node
const fs = require('fs')
const path = require('path')
const chalk = require('chalk')
const pkg = require('../package.json')
const { program } = require('commander')
const local = Intl.DateTimeFormat().resolvedOptions().locale.toUpperCase()

const { matchDialog, terminalCollapse } = require('../src/logistics/presenter')

let isTerminating = false
const recruiter = require('../src/headquarters/recruiter')
const dialogues = recruiter(path.join(__dirname, '../src/dialogues'))
const dialog = matchDialog(local, dialogues) ?? dialogues['EN-US']

program
    .version(pkg.version)
    .description(dialog.bunker.desc)

program.option('-t, --template <type>', dialog.bunker.argDesc, 'react')

program
    .command('init')
    .description(dialog.bunker.initDesc)
    .action(() => {

        const equipments = []
        const root = process.cwd()
        const { template } = program.opts()
        const workshop = path.join(__dirname, `../src/workshop/${template}`)
        const quartermaster = require('../src/headquarters/quartermaster')({ dialog })
        const { hbsDir, hooksDir, utilsDir, componentsDir } = require('../src/logistics/supporter').getConfig()

        if (!hbsDir) {
            equipments.push(...fs.readdirSync(`${workshop}/kit`).map(file => ({ from: `${workshop}/kit/${file}`, to: `${path.join(root, utilsDir, file)}` })))
            equipments.push(...fs.readdirSync(`${workshop}/extensions`).map(file => ({ from: `${workshop}/extensions/${file}`, to: `${path.join(root, hooksDir, file)}` })))
            equipments.push(...fs.readdirSync(`${workshop}/standardParts`).map(file => ({ from: `${workshop}/standardParts/${file}`, to: `${path.join(root, componentsDir, file)}` })))
        }

        const outpost = {
            dirs: [`${path.join(root, 'bunker', 'mission')}`],
            files: [
                ...equipments,
                { from: path.join(__dirname, `../.env.example`), to: `${path.join(root, 'bunker', '.env')}`, exist: 'envCheck', success: 'envCopy' },
                { from: path.join(__dirname, `../config.js`), to: `${path.join(root, 'bunker', 'config.js')}`, exist: 'configCheck', success: 'configCopy' }
            ]
        }
        Object.entries(outpost).forEach(([type, items]) => items.forEach(quartermaster[type]))
        const bunkerCmd = chalk.yellow(`'bunker': 'bunker boot'`)
        console.log(chalk.cyan(dialog.bunker.initComplete(bunkerCmd)))
    })

program
    .command('boot')
    .alias('start')
    .description(dialog.bunker.bootDesc)
    .action(async () => {
        const bunker = require('../src/awakening')
        const result = await bunker.init(program.opts(), dialog, pkg.version, local)
        if (!result) {
            return
        }
        require('../src/headquarters/observer')(bunker)
        process.on('SIGINT', async () => {
            if (isTerminating) return
            isTerminating = true
            process.stdout.write('\r\x1b[K')
            const currentBunker = bunker.get()
            currentBunker.yorha.commander.report(dialog.bunker.systemOffline, 'gray')
            terminalCollapse(500, dialog, currentBunker)
            const scout = await currentBunker.labs?.scout
            scout?.close()
        })
    })

program.parse(process.argv)