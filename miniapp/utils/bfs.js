/**
 * BFS 最短路径查找算法
 * 在信任网络中查找两个用户之间的最短触达路径
 * 最大搜索深度：3度人脉（4层BFS队列）
 */
class BFSFinder {
  /**
   * 查找从 userId 到 targetUserId 的最短路径
   * @param {string} userId - 起始用户ID
   * @param {string} targetUserId - 目标用户ID
   * @param {Function} getFriends - 获取好友列表的异步函数 (userId) => Promise<Array<{id, name}>>
   * @param {number} maxDepth - 最大搜索深度（默认3度）
   * @returns {Promise<{distance: number, path: Array, message: string}>}
   */
  static async findPath(userId, targetUserId, getFriends, maxDepth = 3) {
    if (userId === targetUserId) {
      return { distance: 0, path: [{ id: userId }], message: '自己' }
    }

    const visited = new Set()
    // 队列中存储 { id, path }，path 是已经过的节点数组 [{ id, name }]
    const queue = [{ id: userId, path: [{ id: userId, name: '我' }] }]
    visited.add(userId)

    while (queue.length > 0) {
      const current = queue.shift()

      // 超过最大深度限制，跳过
      if (current.path.length - 1 >= maxDepth) continue

      try {
        const friends = await getFriends(current.id)

        for (const friend of friends) {
          const friendId = friend.id || friend

          if (friendId === targetUserId) {
            // 找到目标
            const fullPath = [...current.path, { id: targetUserId, name: friend.name || '目标' }]
            return {
              distance: current.path.length,
              path: fullPath,
              message: `${current.path.length}度人脉`,
            }
          }

          if (!visited.has(friendId)) {
            visited.add(friendId)
            queue.push({
              id: friendId,
              path: [...current.path, { id: friendId, name: friend.name || '未知' }],
            })
          }
        }
      } catch (err) {
        console.warn(`[BFS] 获取用户 ${current.id} 的好友列表失败:`, err)
      }
    }

    return { distance: -1, path: [], message: '未找到可触达路径' }
  }

  /**
   * 从网络中查找所有节点（用于图谱展示）
   * @param {Array} nodes - 节点数组
   * @param {Array} edges - 边数组
   * @param {string} startId - 起始节点ID
   * @param {number} depth - BFS深度
   * @returns {{ nodes: Set, edges: Set }}
   */
  static getSubGraph(nodes, edges, startId, depth = 2) {
    const visited = new Set()
    const queue = [{ id: startId, d: 0 }]
    visited.add(startId)

    const subNodeIds = new Set()
    const subEdgeKeys = new Set()

    while (queue.length > 0) {
      const current = queue.shift()
      subNodeIds.add(current.id)

      if (current.d >= depth) continue

      edges.forEach((edge) => {
        let neighborId = null
        if (edge.from === current.id) neighborId = edge.to
        else if (edge.to === current.id) neighborId = edge.from

        if (neighborId && !visited.has(neighborId)) {
          visited.add(neighborId)
          queue.push({ id: neighborId, d: current.d + 1 })
          subNodeIds.add(neighborId)
          subEdgeKeys.add(`${Math.min(current.id, neighborId)}-${Math.max(current.id, neighborId)}`)
        }
      })
    }

    const subEdges = edges.filter(
      (e) =>
        subNodeIds.has(e.from) &&
        subNodeIds.has(e.to) &&
        subEdgeKeys.has(`${Math.min(e.from, e.to)}-${Math.max(e.from, e.to)}`)
    )

    return {
      nodes: nodes.filter((n) => subNodeIds.has(n.id)),
      edges: subEdges,
    }
  }
}

module.exports = { BFSFinder }
