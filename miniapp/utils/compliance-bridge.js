/**
 * 安全合规 — 统一API桥接
 */
const { authApi, brochureApi, trustApi, visitorApi } = require('./api')
const { MockService } = require('./mockService')

async function getProfile(useRealApi) {
  return useRealApi ? authApi.getProfile() : MockService.getProfile()
}

async function getBrochures(useRealApi) {
  return useRealApi ? brochureApi.list() : MockService.getBrochures()
}

async function getTrustNetwork(useRealApi) {
  return useRealApi ? trustApi.getNetwork() : MockService.getTrustNetwork()
}

async function getVisitorStats(useRealApi) {
  return useRealApi ? visitorApi.getStats() : MockService.getVisitorStats()
}

module.exports = { getProfile, getBrochures, getTrustNetwork, getVisitorStats }
