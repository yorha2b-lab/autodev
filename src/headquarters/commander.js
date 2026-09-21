/**
 * YoRHa Bunker Construction System
 * This file is part of Bunker.
 * Bunker is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 * (c) 2026 [yorha2b-lab]. Glory to Mankind.
 */

module.exports = bunker => {

    const acp = bunker.get()
    const units = Object.values(acp.units)
    const dispatcher = acp.headquarters.dispatcher(acp)

    dispatcher.onIdle(() => acp.yorha.commander.report(acp.dialog.bunker.systemStandby, 'gray'))

    return {
        receive: async mission => {
            dispatcher.add(async () => {
                let unit
                let spinner
                try {
                    if (acp.logistics.supporter.getConfig().useDemo) {
                        unit = units.find(unit => unit.meta.name === 'striker')
                    } else {
                        spinner = acp.yorha.commander.start(acp.dialog.bunker.detectedEnemy)
                        const result = await acp.llm.recognizePage({ filePath: mission.input, prompt: acp.constitution.commander(units) })
                        acp.yorha.commander.success(spinner, acp.dialog.bunker.confirmEnemy)
                        unit = units.map(unit => ({ unit, score: unit.meta.capabilities.filter(cap => result.capabilities.includes(cap)).length }))
                            .filter(item => item.score > 0)
                            .sort((a, b) => b.score - a.score)[0]?.unit
                    }
                    if (!unit) {
                        acp.yorha.commander.fail(spinner, acp.dialog.bunker.missionFailed)
                        return
                    }
                    await unit.execute({ acp, mission })
                } catch (error) {
                    acp.yorha.commander.fail(spinner, acp.dialog.bunker.missionUnknown)
                }
            })
        }
    }
}