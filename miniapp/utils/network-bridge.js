/**
 * 人脉网络 — 统一API桥接
 */
const { trustApi, connectionApi, sixDegreesApi } = require('./api')
const { MockService } = require('../../utils/mockService')

async function getNetwork(useRealApi) {
  return useRealApi ? trustApi.getNetwork() : MockService.getTrustNetwork()
}

async function findPath(fromId, toId, maxDepth, useRealApi) {
  return useRealApi
    ? sixDegreesApi.path(fromId, toId, maxDepth)
    : MockService.findPath(fromId, toId)
}

async function getRelations(userId, useRealApi) {
  return useRealApi
    ? sixDegreesApi.relations(userId)
    : MockService.getRelations(userId)
}

async function addTrust(data, useRealApi) {
  return useRealApi ? trustApi.addTrust(data) : MockService.addTrust(data)
}

module.exports = { getNetwork, findPath, getRelations, addTrust }
