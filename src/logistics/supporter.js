const fs = require('fs')
const path = require('path')
const http = require('http')
const { execSync } = require('child_process')

const isHttpURL = str => {
    try {
        const url = new URL(str)
        return ['http:', 'https:'].includes(url.protocol)
    } catch {
        return false
    }
}

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

const getJsonFingerprint = obj => {
    if (!obj || typeof obj !== 'object') return ''
    return Object.keys(Array.isArray(obj) ? (obj[0] || {}) : obj).sort().join(',')
}

const derivePageNameFromUrl = rawUrl => {
    const parsed = new URL(rawUrl)
    let routePath = parsed.hash ? parsed.hash.replace(/^#/, '') : parsed.pathname
    routePath = routePath.split('?')[0].replace(/^\/+|\/+$/g, '')
    if (!routePath) return 'Home'
    const parts = routePath.split(/[/\-_]/).filter(Boolean)
    return parts.at(-1) ?? 'capturedPage'
}

const startStaticServer = (dir, port) => {
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml'
    }
    const server = http.createServer((req, res) => {
        const reqPath = decodeURIComponent(req.url.split('?')[0])
        const filePath = path.join(dir, reqPath === '/' ? 'index.html' : reqPath)
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            const ext = path.extname(filePath).toLowerCase()
            res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' })
            fs.createReadStream(filePath).pipe(res)
        } else {
            res.writeHead(404)
            res.end('Not Found')
        }
    })
    return new Promise(resolve => {
        const tryListen = () => server.listen(port, () => resolve({ server }))
        server.once('error', err => {
            if (err.code === 'EADDRINUSE') {
                killZombiePort(port)
                setTimeout(tryListen, 150)
            }
        })
        tryListen()
    })
}

const scanHtmlFiles = (dir, rootDir = dir) => {
    let results = []
    const list = fs.readdirSync(dir)
    for (const file of list) {
        const fullPath = path.join(dir, file)
        const stat = fs.statSync(fullPath)
        if (stat.isDirectory()) {
            // 排除常见的非业务页面文件夹
            if (!['resources', 'plugins', 'images', 'files'].includes(file)) {
                results = results.concat(scanHtmlFiles(fullPath, rootDir))
            }
        } else if (file.endsWith('.html')) {
            if (!['start.html', 'reload.html'].includes(file)) {
                results.push({
                    fullPath,
                    name: path.basename(file, '.html'),
                    relativeUrl: path.relative(rootDir, fullPath).replace(/\\/g, '/'),
                })
            }
        }
    }
    return results
}

const getExistingMenus = (dir = 'src/pages') => {
    const pagesDir = path.join(process.cwd(), dir)
    if (!fs.existsSync(pagesDir)) return []
    return fs.readdirSync(pagesDir).filter(file => fs.statSync(path.join(pagesDir, file)).isDirectory()).map(file => ({ label: file, key: file }))
}

const readModuleFiles = (dir, rootDir = dir) => {
    let files = []
    const list = fs.readdirSync(dir, { withFileTypes: true })
    for (const item of list) {
        if (item.name.startsWith('.')) continue
        const fullPath = path.join(dir, item.name)
        if (item.isDirectory()) {
            if (!['node_modules', '__tests__', 'mock', 'mocks'].includes(item.name)) {
                files = files.concat(readModuleFiles(fullPath, rootDir))
            }
        } else if (/\.(jsx?|tsx?)$/i.test(item.name) && !/\.(test|spec|stories)\.[^.]+$/i.test(item.name)) {
            files.push({
                fullPath,
                name: item.name,
                content: fs.readFileSync(fullPath, 'utf-8'),
                relativeName: path.relative(rootDir, fullPath).replace(/\\/g, '/'),
            })
        }
    }
    return files.sort((a, b) => a.relativeName.localeCompare(b.relativeName))
}

const launchPuppeteer = async (sessionDir, currentBrowser) => {
    const puppeteer = require('puppeteer')
    let isBrowserAlive = false
    if (currentBrowser) {
        try {
            await currentBrowser.pages()
            isBrowserAlive = true
        } catch (e) {
            currentBrowser = null
        }
    }

    if (!isBrowserAlive) {

        ['SingletonLock', 'SingletonSocket', 'SingletonCookie'].forEach(file => {
            try { fs.unlinkSync(path.join(sessionDir, file)) } catch (e) { }
        })

        currentBrowser = await puppeteer.launch({
            headless: false,
            handleSIGINT: false,
            defaultViewport: null,
            userDataDir: sessionDir,
            args: ['--start-maximized']
        })
    }
    return currentBrowser
}

module.exports = {
    isHttpURL,
    getConfig,
    scanHtmlFiles,
    killZombiePort,
    launchPuppeteer,
    readModuleFiles,
    getExistingMenus,
    startStaticServer,
    getJsonFingerprint,
    derivePageNameFromUrl,
}