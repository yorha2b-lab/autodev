module.exports = accessPoint => {

    const labs = {}

    const { prdDoc, apiDoc, remains, needMock, proxyTarget, enableAutoAlignment } = accessPoint.logistics.supporter.getConfig()

    if (!needMock && proxyTarget && enableAutoAlignment) {
        labs.tower = require('../labs/tower')(accessPoint)
    }

    if (apiDoc && enableAutoAlignment) {
        labs.council = require('../labs/council')(accessPoint)
    }

    if (remains) {
        labs.scout = require('../labs/scout')(accessPoint).archeology(remains)
    }

    if (prdDoc) {
        labs.inspector = require('../labs/inspector')(accessPoint).audit(prdDoc)
    }

    return labs
}