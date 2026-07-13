import{j as e}from"./iframe-BgyFVukn.js";import{c as ne}from"./clsx-B-dksMZM.js";import{c as Z}from"./createLucideIcon-C5yOfbJT.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ie=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4",key:"tonef"}],["path",{d:"M9 18c-4.51 2-5-2-7-2",key:"9comsn"}]],ce=Z("github",ie);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const de=[["path",{d:"M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5",key:"mvr1a0"}]],me=Z("heart",de),ue=[{title:"产品",links:[{label:"功能介绍",href:"#"},{label:"定价方案",href:"#"},{label:"更新日志",href:"#"}]},{title:"支持",links:[{label:"帮助中心",href:"#"},{label:"API 文档",href:"#"},{label:"联系我们",href:"#"}]},{title:"法律",links:[{label:"隐私政策",href:"#"},{label:"服务条款",href:"#"},{label:"Cookie 政策",href:"#"}]}],pe=[{label:"隐私政策",href:"#"},{label:"服务条款",href:"#"},{label:"Cookie 设置",href:"#"}];function m({brandName:u="AI 数智名片",year:ee=new Date().getFullYear(),copyrightSuffix:he="All rights reserved.",columns:re=ue,bottomLinks:se=pe,showMadeWith:ae=!0,showGithub:te=!0,githubUrl:oe="https://github.com/example/ai-business-card",className:le}){return e.jsx("footer",{className:ne("bg-surface border-t border-border-light",le),children:e.jsxs("div",{className:"max-w-5xl mx-auto px-6 py-10",children:[e.jsxs("div",{className:"flex flex-col lg:flex-row gap-8 pb-8 border-b border-border-light",children:[e.jsxs("div",{className:"lg:w-1/3",children:[e.jsxs("div",{className:"flex items-center gap-2 mb-3",children:[e.jsx("div",{className:"w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm",children:e.jsx("span",{"aria-hidden":"true",children:"AI"})}),e.jsx("span",{className:"text-base font-bold text-on-surface",children:u})]}),e.jsx("p",{className:"text-sm text-text-muted leading-relaxed max-w-xs",children:"基于 AI 的智能数字名片管理平台，让每一次连接都更有价值。"})]}),e.jsx("div",{className:"flex-1 grid grid-cols-2 sm:grid-cols-3 gap-6",children:re.map(r=>e.jsxs("div",{children:[e.jsx("h4",{className:"text-xs font-semibold text-text-muted uppercase tracking-wider mb-3",children:r.title}),e.jsx("ul",{className:"space-y-2",children:r.links.map(d=>e.jsx("li",{children:e.jsx("a",{href:d.href,className:"text-sm text-on-surface/70 hover:text-primary transition-colors",children:d.label})},d.label))})]},r.title))})]}),e.jsxs("div",{className:"pt-6 flex flex-col sm:flex-row items-center justify-between gap-4",children:[e.jsxs("div",{className:"flex items-center gap-1 text-sm text-text-muted",children:[e.jsxs("span",{children:["© ",ee," ",u]}),ae&&e.jsxs("span",{className:"flex items-center gap-1 ml-2",children:["Made with ",e.jsx(me,{className:"w-3.5 h-3.5 text-rose-400 fill-rose-400"})," in China"]})]}),e.jsxs("div",{className:"flex items-center gap-4",children:[se.map(r=>e.jsx("a",{href:r.href,className:"text-xs text-text-muted hover:text-primary transition-colors",children:r.label},r.label)),te&&e.jsx("a",{href:oe,target:"_blank",rel:"noopener noreferrer",className:"text-text-muted hover:text-on-surface transition-colors","aria-label":"GitHub 仓库",children:e.jsx(ce,{className:"w-4 h-4"})})]})]})]})})}m.__docgenInfo={description:`Footer — 页脚组件\r
\r
支持多栏链接布局、版权信息、品牌展示和底部附加链接。`,methods:[],displayName:"Footer",props:{brandName:{required:!1,tsType:{name:"string"},description:"品牌名称",defaultValue:{value:"'AI 数智名片'",computed:!1}},year:{required:!1,tsType:{name:"number"},description:"版权年份",defaultValue:{value:"new Date().getFullYear()",computed:!0}},copyrightSuffix:{required:!1,tsType:{name:"string"},description:"版权信息后缀",defaultValue:{value:"'All rights reserved.'",computed:!1}},columns:{required:!1,tsType:{name:"Array",elements:[{name:"FooterColumn"}],raw:"FooterColumn[]"},description:"多栏链接",defaultValue:{value:`[\r
  {\r
    title: '产品',\r
    links: [\r
      { label: '功能介绍', href: '#' },\r
      { label: '定价方案', href: '#' },\r
      { label: '更新日志', href: '#' },\r
    ],\r
  },\r
  {\r
    title: '支持',\r
    links: [\r
      { label: '帮助中心', href: '#' },\r
      { label: 'API 文档', href: '#' },\r
      { label: '联系我们', href: '#' },\r
    ],\r
  },\r
  {\r
    title: '法律',\r
    links: [\r
      { label: '隐私政策', href: '#' },\r
      { label: '服务条款', href: '#' },\r
      { label: 'Cookie 政策', href: '#' },\r
    ],\r
  },\r
]`,computed:!1}},bottomLinks:{required:!1,tsType:{name:"Array",elements:[{name:"FooterLink"}],raw:"FooterLink[]"},description:"底部附加链接（如隐私政策、服务条款）",defaultValue:{value:`[\r
  { label: '隐私政策', href: '#' },\r
  { label: '服务条款', href: '#' },\r
  { label: 'Cookie 设置', href: '#' },\r
]`,computed:!1}},showMadeWith:{required:!1,tsType:{name:"boolean"},description:'显示"用爱制作"标识',defaultValue:{value:"true",computed:!1}},showGithub:{required:!1,tsType:{name:"boolean"},description:"显示 GitHub 链接",defaultValue:{value:"true",computed:!1}},githubUrl:{required:!1,tsType:{name:"string"},description:"GitHub 链接",defaultValue:{value:"'https://github.com/example/ai-business-card'",computed:!1}},className:{required:!1,tsType:{name:"string"},description:"自定义类名"}}};const ye={title:"Components/Footer",component:m,parameters:{layout:"fullscreen",docs:{description:{component:"页脚组件。支持多栏链接布局（产品/支持/法律）、品牌展示、版权信息、「用爱制作」标识和 GitHub 链接。"}}},argTypes:{brandName:{control:"text",description:"品牌名称"},year:{control:"number",description:"版权年份"},showMadeWith:{control:"boolean",description:'显示 "Made with ❤️" 标识'},showGithub:{control:"boolean",description:"显示 GitHub 链接"}}},s={args:{}},a={args:{brandName:"数字名片 Pro",year:2025}},t={args:{showMadeWith:!1}},o={args:{showGithub:!1}},l={args:{showMadeWith:!1,showGithub:!1}},n={args:{bottomLinks:[{label:"隐私政策",href:"/privacy"},{label:"服务条款",href:"/terms"}]}},i={args:{columns:[{title:"入门",links:[{label:"快速开始",href:"/docs"},{label:"API 参考",href:"/api"}]},{title:"社区",links:[{label:"博客",href:"/blog"},{label:"论坛",href:"/forum"},{label:"Discord",href:"/discord"}]}]}},c={render:()=>e.jsxs("div",{className:"min-h-screen flex flex-col bg-neutral-bg",children:[e.jsx("main",{className:"flex-1 max-w-5xl mx-auto w-full px-6 py-8",children:e.jsxs("div",{className:"bg-surface rounded-2xl border border-border-light p-8",children:[e.jsx("h2",{className:"text-lg font-bold text-on-surface",children:"主内容区"}),e.jsx("p",{className:"text-sm text-text-muted mt-2",children:"页脚始终保持在页面底部。滚动页面查看页脚效果。"})]})}),e.jsx(m,{})]}),parameters:{docs:{description:{story:"嵌入完整页面布局，展示页脚在真实应用中的视觉效果。"}}}};var p,h,f,b,x;s.parameters={...s.parameters,docs:{...(p=s.parameters)==null?void 0:p.docs,source:{originalSource:`{
  args: {}
}`,...(f=(h=s.parameters)==null?void 0:h.docs)==null?void 0:f.source},description:{story:"默认页脚 — 三栏布局 + 版权信息",...(x=(b=s.parameters)==null?void 0:b.docs)==null?void 0:x.description}}};var g,y,N,j,v;a.parameters={...a.parameters,docs:{...(g=a.parameters)==null?void 0:g.docs,source:{originalSource:`{
  args: {
    brandName: '数字名片 Pro',
    year: 2025
  }
}`,...(N=(y=a.parameters)==null?void 0:y.docs)==null?void 0:N.source},description:{story:"自定义品牌名称",...(v=(j=a.parameters)==null?void 0:j.docs)==null?void 0:v.description}}};var w,k,M,C,A;t.parameters={...t.parameters,docs:{...(w=t.parameters)==null?void 0:w.docs,source:{originalSource:`{
  args: {
    showMadeWith: false
  }
}`,...(M=(k=t.parameters)==null?void 0:k.docs)==null?void 0:M.source},description:{story:'无 "Made with ❤️"',...(A=(C=t.parameters)==null?void 0:C.docs)==null?void 0:A.description}}};var G,L,T,F,I;o.parameters={...o.parameters,docs:{...(G=o.parameters)==null?void 0:G.docs,source:{originalSource:`{
  args: {
    showGithub: false
  }
}`,...(T=(L=o.parameters)==null?void 0:L.docs)==null?void 0:T.source},description:{story:"无 GitHub 链接",...(I=(F=o.parameters)==null?void 0:F.docs)==null?void 0:I.description}}};var W,S,_,q,D;l.parameters={...l.parameters,docs:{...(W=l.parameters)==null?void 0:W.docs,source:{originalSource:`{
  args: {
    showMadeWith: false,
    showGithub: false
  }
}`,...(_=(S=l.parameters)==null?void 0:S.docs)==null?void 0:_.source},description:{story:"简洁模式 — 无 GitHub 无 MadeWith",...(D=(q=l.parameters)==null?void 0:q.docs)==null?void 0:D.description}}};var H,P,V,B,E;n.parameters={...n.parameters,docs:{...(H=n.parameters)==null?void 0:H.docs,source:{originalSource:`{
  args: {
    bottomLinks: [{
      label: '隐私政策',
      href: '/privacy'
    }, {
      label: '服务条款',
      href: '/terms'
    }]
  }
}`,...(V=(P=n.parameters)==null?void 0:P.docs)==null?void 0:V.source},description:{story:"自定义底部链接",...(E=(B=n.parameters)==null?void 0:B.docs)==null?void 0:E.description}}};var O,U,Y,K,R;i.parameters={...i.parameters,docs:{...(O=i.parameters)==null?void 0:O.docs,source:{originalSource:`{
  args: {
    columns: [{
      title: '入门',
      links: [{
        label: '快速开始',
        href: '/docs'
      }, {
        label: 'API 参考',
        href: '/api'
      }]
    }, {
      title: '社区',
      links: [{
        label: '博客',
        href: '/blog'
      }, {
        label: '论坛',
        href: '/forum'
      }, {
        label: 'Discord',
        href: '/discord'
      }]
    }]
  }
}`,...(Y=(U=i.parameters)==null?void 0:U.docs)==null?void 0:Y.source},description:{story:"自定义栏目链接",...(R=(K=i.parameters)==null?void 0:K.docs)==null?void 0:R.description}}};var $,z,J,Q,X;c.parameters={...c.parameters,docs:{...($=c.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <div className="min-h-screen flex flex-col bg-neutral-bg">\r
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">\r
        <div className="bg-surface rounded-2xl border border-border-light p-8">\r
          <h2 className="text-lg font-bold text-on-surface">主内容区</h2>\r
          <p className="text-sm text-text-muted mt-2">\r
            页脚始终保持在页面底部。滚动页面查看页脚效果。\r
          </p>\r
        </div>\r
      </main>\r
      <Footer />\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '嵌入完整页面布局，展示页脚在真实应用中的视觉效果。'
      }
    }
  }
}`,...(J=(z=c.parameters)==null?void 0:z.docs)==null?void 0:J.source},description:{story:`嵌入页面布局的完整效果\r
模拟真实应用场景`,...(X=(Q=c.parameters)==null?void 0:Q.docs)==null?void 0:X.description}}};const Ne=["Default","CustomBrand","WithoutMadeWith","WithoutGithub","Minimal","CustomBottomLinks","CustomColumns","InPageLayout"];export{n as CustomBottomLinks,a as CustomBrand,i as CustomColumns,s as Default,c as InPageLayout,l as Minimal,o as WithoutGithub,t as WithoutMadeWith,Ne as __namedExportsOrder,ye as default};
