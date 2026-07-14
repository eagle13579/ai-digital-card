/**
 * AI智能中心 — 统一API导出
 * 根据 useRealApi 自动选择真实API或MockService
 */
const { aiApi, matchApi, ocrApi } = require('../../utils/api')
const { MockService } = require('../../utils/mockService')

/** AI对话 — 发送消息 */
async function chat(message, history, useRealApi) {
  return useRealApi
    ? aiApi.chat(message, history)
    : MockService.aiChat(message, history)
}

/** AI生成内容 */
async function generate(data, useRealApi) {
  return useRealApi
    ? aiApi.generate(data)
    : MockService.aiGenerate(data)
}

/** 获取匹配推荐 */
async function getRecommend(params, useRealApi) {
  return useRealApi
    ? matchApi.getRecommend(params)
    : MockService.getRecommendList(params)
}

/** 扫描名片OCR */
async function scanImage(filePath, useRealApi) {
  return useRealApi
    ? ocrApi.scan(filePath)
    : MockService.scanBusinessCard(filePath)
}

/** 获取AI洞察 */
async function getInsight(brochureId, useRealApi) {
  return useRealApi
    ? aiApi.write({ brochureId, type: 'insight' })
    : MockService.getAiInsights(brochureId)
}

module.exports = { chat, generate, getRecommend, scanImage, getInsight }
