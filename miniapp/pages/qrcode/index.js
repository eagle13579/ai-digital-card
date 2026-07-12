const MockService = require('../../utils/mockService')

Page({
  data: { 
    brochure: null, 
    qrcodeData: '',
    generating: false,
  },

  async onLoad(options) {
    const id = options.id || ''
    const brochure = id ? await MockService.getBrochureById(id) : null
    
    if (!brochure) {
      wx.showToast({ title: '请先创建名片', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }

    this.setData({ 
      brochure, 
      qrcodeData: 'https://card.example.com/brochure/' + brochure.id 
    })
    this.generateQRCode()
  },

  generateQRCode() {
    if (this.data.generating) return
    this.setData({ generating: true })

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
