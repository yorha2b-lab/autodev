module.exports = accessPoint => {

    const labs = {}

    const { prdDoc, apiDoc, remains, needMock, proxyTarget, enableAutoAlignment } = accessPoint.logistics.supporter.getConfig()

    if (prdDoc) {
        labs.twins = require('../labs/twins')(accessPoint)
    }

    if (remains) {
        labs.scout = require('../labs/scout')(accessPoint)
    }

    if (!needMock && proxyTarget && enableAutoAlignment) {
        labs.tower = require('../labs/tower')(accessPoint)
    }

    if (apiDoc && enableAutoAlignment) {
        labs.council = require('../labs/council')(accessPoint)
    }

    return labs
}