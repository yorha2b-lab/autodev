const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

const getConfig = () => {
    const localConfigPath = path.join(process.cwd(), 'bunker', 'config.js') // 项目配置
    const defaultConfigPath = path.resolve(__dirname, '../../config.js') // 默认配置
    let config = require(defaultConfigPath)
    if (fs.existsSync(localConfigPath)) {
        const userConfig = require(localConfigPath)
        config = { ...config, ...userConfig }
    }
    return config
}

const getExistingMenus = (dir = 'src/pages') => {
    const pagesDir = path.join(process.cwd(), dir)
    if (!fs.existsSync(pagesDir)) return []
    return fs.readdirSync(pagesDir)
        .filter(file => fs.statSync(path.join(pagesDir, file)).isDirectory())
        .map(file => ({ label: file, key: file }))
}

const killZombiePort = port => {
    try {
        if (process.platform === 'win32') {
            const out = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf-8' })
            const pids = out.split('\n')
                .map(line => line.trim().split(/\s+/).at(-1))
                .filter(pid => pid && pid !== '0' && pid !== String(process.pid))
            pids.forEach(pid => execSync(`taskkill /F /PID ${pid}`, { stdio: 'ignore' }))
        } else {
            execSync(`lsof -ti :${port} | xargs kill -9`, { stdio: 'ignore' })
        }
    } catch (e) {
        // 杀完了或没占用，直接静默放行
    }
}

module.exports = {
    getConfig,
    killZombiePort,
    getExistingMenus,
}