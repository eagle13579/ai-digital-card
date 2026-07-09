export default {
  pages: [
    'pages/index/index',
    'pages/login/index',
    'pages/card-editor/index',
    'pages/product/index',
    'pages/membership/index',
    'pages/orders/index',
    'pages/notifications/index',
    'pages/activities/index',
    'pages/promoter/index',
    'pages/search/index',
    'pages/supply-demand/index',
    'pages/tutorial/index',
    'pages/mine/index',
    'pages/network/index',
    'pages/visitors/index',
  ],
  window: {
    navigationBarTitleText: 'AI数字名片',
    navigationBarBackgroundColor: '#ffffff',
    navigationBarTextStyle: 'black',
    backgroundColor: '#f5f5f5',
  },
  tabBar: {
    color: '#999999',
    selectedColor: '#3B82F6',
    backgroundColor: '#ffffff',
    borderStyle: 'black',
    list: [
      {
        pagePath: 'pages/index/index',
        text: '首页',
      },
      {
        pagePath: 'pages/product/index',
        text: '产品',
      },
      {
        pagePath: 'pages/mine/index',
        text: '我的',
      },
    ],
  },
}
