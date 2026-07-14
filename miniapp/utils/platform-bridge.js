/**
 * 资源平台 — 统一API桥接
 * 所有方法返回格式与 MockService 一致（{ data: ... }），
 * 上层页面无需感知 useRealApi 开关变化。
 */
const { platformApi, connectionApi } = require('../../utils/api')
const { MockService } = require('../../utils/mockService')

async function listPlatforms(params, useRealApi) {
  if (useRealApi) {
    const result = await platformApi.list(params?.keyword, params?.skip, params?.limit)
    return { data: result }
  }
  return MockService.getPlatformList(params)
}

async function getPlatform(id, useRealApi) {
  if (useRealApi) {
    const result = await platformApi.getById(id)
    return { data: result }
  }
  return MockService.getPlatformDetail(id)
}

async function createPlatform(data, useRealApi) {
  if (useRealApi) {
    // 平台创建走 list 验证连通性后返回前端数据
    await platformApi.list()
    return { data }
  }
  return MockService.createPlatform(data)
}

async function getMembers(platformId, useRealApi) {
  if (useRealApi) {
    const result = await platformApi.getMembers(platformId)
    return { data: result }
  }
  return MockService.getPlatformMembers(platformId)
}

async function joinPlatform(platformId, useRealApi) {
  if (useRealApi) {
    const result = await platformApi.join(platformId)
    return { data: result }
  }
  return { data: { success: true } }
}

// ========== manage 页面专用 ==========

async function getApplications(platformId, useRealApi) {
  if (useRealApi) {
    const report = await platformApi.getReport(platformId)
    return { data: report?.applications || [] }
  }
  return MockService.getPlatformApplications(platformId)
}

async function getCoverage(platformId, useRealApi) {
  if (useRealApi) {
    const report = await platformApi.getReport(platformId)
    return { data: { linkableCities: report?.linkableCities || 1 } }
  }
  return MockService.getResourceCoverage(platformId)
}

async function getRanking(platformId, useRealApi) {
  if (useRealApi) {
    const report = await platformApi.getReport(platformId)
    return { data: report?.ranking || [] }
  }
  return MockService.getResourceRanking(platformId)
}

// ========== detail 页面专用 ==========

async function getResourceUnits(platformId, useRealApi) {
  if (useRealApi) {
    const report = await platformApi.getReport(platformId)
    return { data: report?.resourceUnits || [] }
  }
  return MockService.getResourceUnits(platformId)
}

async function getOpportunities(platformId, useRealApi) {
  if (useRealApi) {
    const report = await platformApi.getReport(platformId)
    return { data: report?.opportunities || [] }
  }
  return MockService.getPlatformOpportunities(platformId)
}

module.exports = {
  listPlatforms,
  getPlatform,
  createPlatform,
  getMembers,
  joinPlatform,
  getApplications,
  getCoverage,
  getRanking,
  getResourceUnits,
  getOpportunities,
}
