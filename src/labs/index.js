module.exports = accessPoint => {

    const labs = {}

    const { prdDoc, apiDoc, remains, needMock, proxyTarget, enableAutoAlignment } = accessPoint.logistics.supporter.getConfig()

    if (!needMock && proxyTarget && enableAutoAlignment) {
        labs.tower = require('../labs/tower')(accessPoint)
    }

    if (apiDoc && enableAutoAlignment) {
        labs.council = require('../labs/council')(accessPoint)
    }

    if (prdDoc) {
        labs.twins = require('../labs/twins')(accessPoint).maintain(prdDoc)
    }

    if (remains) {
        labs.scout = require('../labs/scout')(accessPoint).archeology(remains)
    }

    return labs
}