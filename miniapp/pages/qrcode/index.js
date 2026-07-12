const { MockService } = require('../../utils/mockService')
const { miniappApi } = require('../../utils/api')

Page({
  data: { 
    brochure: null, 
    qrcodeData: '',
    qrcodeImageUrl: '',
    generating: false,
  },

  async onLoad(options) {
    const id = options.id || ''
    let brochure
    
    if (MockService.USE_MOCK) {
      brochure = id ? await MockService.getBrochureById(id) : null
    } else {
      const { brochureApi } = require('../../utils/api')
      try {
        const res = await brochureApi.getById(id)
        brochure = res.data || res
      } catch (e) {
        console.error('获取名片详情失败', e)
      }
    }
    
    if (!brochure) {
      wx.showToast({ title: '请先创建名片', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }

    const shareToken = brochure.share_token || brochure.id
    this.setData({ 
      brochure, 
      qrcodeData: shareToken,
    })
    this.generateQRCode()
  },

  generateQRCode() {
    if (this.data.generating) return
    this.setData({ generating: true })

    const shareToken = this.data.qrcodeData
    const width = 280

    if (MockService.USE_MOCK) {
      // Mock模式：使用Canvas绘制模拟二维码
      this._drawMockQR()
    } else {
      // 真实API模式：调用后端生成二维码图片
      this._loadRealQRCode(shareToken, width)
    }
  },

  /** 调用后端API获取真实二维码图片 */
  async _loadRealQRCode(shareToken, width) {
    try {
      const res = await miniappApi.getQRCode(shareToken, width)
      
      if (res && res.data) {
        // 后端返回的是Base64编码的图片
        this.setData({
          qrcodeImageUrl: res.data,
          generating: false,
        })
        wx.showToast({ title: '二维码已就绪', icon: 'success' })
      } else if (res && res.tempFilePath) {
        // 直接返回临时文件路径
        this.setData({
          qrcodeImageUrl: res.tempFilePath,
          generating: false,
        })
        wx.showToast({ title: '二维码已就绪', icon: 'success' })
      } else {
        throw new Error('无效的二维码响应')
      }
    } catch (e) {
      console.error('[QRCode] 获取二维码失败，降级至本地生成:', e)
      // 降级：自行绘制二维码URL
      this._drawURLQR(shareToken)
    }
  },

  /** 降级方案：在Canvas上绘制二维码URL文本 */
  _drawURLQR(shareToken) {
    const query = wx.createSelectorQuery()
    query.select('#qrcodeCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0]) {
          this.setData({ generating: false })
          return
        }
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getWindowInfo().pixelRatio
        const size = 200
        canvas.width = size * dpr
        canvas.height = size * dpr
        ctx.scale(dpr, dpr)

        // 白色背景
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, size, size)

        // 显示分享链接
        ctx.fillStyle = '#333333'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const url = `https://card.example.com/view/${shareToken}`
        ctx.fillText('扫码查看名片', size / 2, size / 2 - 10)
        ctx.font = '10px sans-serif'
        ctx.fillStyle = '#666666'
        ctx.fillText(url, size / 2, size / 2 + 10)

        this.setData({ generating: false })
        wx.showToast({ title: '二维码已生成（降级模式）', icon: 'success' })
      })
  },

  /** Mock模式：绘制模拟二维码 */
  _drawMockQR() {
    const query = wx.createSelectorQuery()
    query.select('#qrcodeCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getWindowInfo().pixelRatio
        const size = 200
        canvas.width = size * dpr
        canvas.height = size * dpr
        ctx.scale(dpr, dpr)

        // 从qrcodeData生成确定性矩阵
        const data = this.data.qrcodeData || 'default'
        const matrix = this._generateMatrix(data, 21)

        // 计算单元格尺寸（留出白边）
        const margin = 2
        const cellSize = (size - margin * 2) / matrix.length

        // 绘制白色背景
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, size, size)

        // 绘制二维码矩阵
        for (let row = 0; row < matrix.length; row++) {
          for (let col = 0; col < matrix[row].length; col++) {
            const x = margin + col * cellSize
            const y = margin + row * cellSize
            ctx.fillStyle = matrix[row][col] ? '#000000' : '#ffffff'
            ctx.fillRect(x, y, Math.ceil(cellSize), Math.ceil(cellSize))
          }
        }

        // 绘制三个定位图案（finder patterns）
        this._drawFinderPattern(ctx, margin, margin, cellSize)
        this._drawFinderPattern(
          ctx,
          margin + (matrix.length - 7) * cellSize,
          margin,
          cellSize
        )
        this._drawFinderPattern(
          ctx,
          margin,
          margin + (matrix.length - 7) * cellSize,
          cellSize
        )

        this.setData({ generating: false })
        wx.showToast({ title: '二维码已就绪', icon: 'success' })
      })
  },

  // 从字符串生成确定性二进制矩阵
  _generateMatrix(str, size) {
    const matrix = []
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i)
      hash = hash & hash // 转换为32位整数
    }
    let seed = Math.abs(hash) || 1
    for (let r = 0; r < size; r++) {
      matrix[r] = []
      for (let c = 0; c < size; c++) {
        // 保留边缘区域给finder pattern（7x7角落）
        const inTopLeft = r < 7 && c < 7
        const inTopRight = r < 7 && c >= size - 7
        const inBottomLeft = r >= size - 7 && c < 7
        if (inTopLeft || inTopRight || inBottomLeft) {
          matrix[r][c] = 0
        } else {
          seed = (seed * 1103515245 + 12345) & 0x7fffffff
          matrix[r][c] = (seed % 3 !== 0) ? 1 : 0 // ~66% black
        }
      }
    }
    return matrix
  },

  // 绘制QR定位图案（7x7）
  _drawFinderPattern(ctx, startX, startY, cellSize) {
    const outer = 7 * cellSize
    const inner = 5 * cellSize
    const core = 3 * cellSize

    ctx.fillStyle = '#000000'
    ctx.fillRect(startX, startY, outer, outer)

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(
      startX + cellSize,
      startY + cellSize,
      inner,
      inner
    )

    ctx.fillStyle = '#000000'
    ctx.fillRect(
      startX + cellSize * 2,
      startY + cellSize * 2,
      core,
      core
    )
  },

  saveQR() {
    if (this.data.qrcodeImageUrl && !MockService.USE_MOCK) {
      // 真实API模式：直接保存图片
      wx.saveImageToPhotosAlbum({
        filePath: this.data.qrcodeImageUrl,
        success: () => {
          wx.showToast({ title: '已保存到相册', icon: 'success' })
        },
        fail: () => {
          wx.showToast({ title: '保存失败，请授权相册权限', icon: 'none' })
        }
      })
      return
    }

    // Canvas模式：截图保存
    const query = wx.createSelectorQuery()
    query.select('#qrcodeCanvas')
      .fields({ node: true })
      .exec((res) => {
        if (!res[0]) {
          wx.showToast({ title: '二维码尚未生成', icon: 'none' })
          return
        }
        wx.canvasToTempFilePath({
          canvas: res[0].node,
          success: (res2) => {
            wx.saveImageToPhotosAlbum({
              filePath: res2.tempFilePath,
              success: () => {
                wx.showToast({ title: '已保存到相册', icon: 'success' })
              },
              fail: () => {
                wx.showToast({ title: '保存失败，请授权相册权限', icon: 'none' })
              }
            })
          },
          fail: () => {
            wx.showToast({ title: '生成图片失败', icon: 'none' })
          }
        })
      })
  },

  onShareAppMessage() {
    const b = this.data.brochure
    return { 
      title: (b && b.title) || '名片二维码', 
      path: '/pages/qrcode/index?id=' + ((b && b.id) || ''),
      imageUrl: (b && b.cover) || '',
    }
  },

  onShareTimeline() {
    const b = this.data.brochure
    return { title: (b && b.title) || '名片二维码' }
  },
})
