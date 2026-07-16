/**
 * 人脉网络 — 统一API桥接
 */
const { trustApi, connectionApi, sixDegreesApi } = require('./api')
const { MockService } = require('../../utils/mockService')

async function getNetwork(useRealApi) {
  const raw = useRealApi ? await trustApi.getNetwork() : await MockService.getTrustNetwork()
  const data = raw.data || raw || { trusting: [], trusted_by: [] }

  // trustApi returns {trusting, trusted_by} format,
  // but graph page expects {nodes, links} format (六度人脉风格)
  const store = require('./store')
  const state = store.getState()
  const userId = state.userInfo?.id || 'u001'
  const userName = state.userInfo?.name || `${state.userInfo?.nickname || '我'}`

  const nodeMap = new Map()
  const links = []

  // 中心节点（当前用户）
  nodeMap.set(userId, { id: userId, name: userName, depth: 0, group: 0 })

  // 我信任的人（出边）
  if (Array.isArray(data.trusting)) {
    data.trusting.forEach(u => {
      const id = String(u.id || u.user_id)
      if (id && !nodeMap.has(id)) {
        nodeMap.set(id, {
          id,
          name: u.name || u.nickname || '',
          company: u.company || '',
          title: u.title || '',
          depth: 1,
          group: 1,
        })
      }
      if (id) links.push({ source: userId, target: id, type: 'trusting' })
    })
  }

  // 信任我的人（入边）
  if (Array.isArray(data.trusted_by)) {
    data.trusted_by.forEach(u => {
      const id = String(u.id || u.user_id)
      if (id && !nodeMap.has(id)) {
        nodeMap.set(id, {
          id,
          name: u.name || u.nickname || '',
          company: u.company || '',
          title: u.title || '',
          depth: 1,
          group: 2,
        })
      }
      if (id) links.push({ source: id, target: userId, type: 'trusted_by' })
    })
  }

  const result = { nodes: Array.from(nodeMap.values()), links }
  console.log('[network-bridge] 格式转换完成: trusting/trusted_by → nodes/links,', result.nodes.length, 'nodes,', result.links.length, 'links')
  return { data: result }
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
