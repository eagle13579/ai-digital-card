import{j as e}from"./iframe-BgyFVukn.js";import{H as d}from"./Header-BwIVaQu5.js";import"./preload-helper-Dp1pzeXC.js";import"./user-kvdGHbHj.js";import"./createLucideIcon-C5yOfbJT.js";import"./settings-BcukFMc5.js";const me={title:"Components/Header",component:d,parameters:{layout:"fullscreen",docs:{description:{component:"顶部导航栏组件。支持登录态（显示用户头像、名称、设置/登出按钮）和未登录态（显示登录按钮）。"}}},argTypes:{title:{control:"text",description:"应用标题"},user:{control:"object",description:"用户信息。传入=已登录，null=未登录"},onLogin:{action:"login",description:"登录回调"},onLogout:{action:"logout",description:"登出回调"},onSettings:{action:"settings",description:"设置回调"}}},r={args:{title:"AI数智名片",user:null}},s={args:{title:"数字名片管理平台",user:null}},a={args:{title:"AI数智名片",user:null}},t={args:{title:"AI数智名片",user:{name:"张明",email:"zhangming@example.com"}}},o={args:{title:"AI数智名片",user:{name:"亚历山大·伊万诺维奇",email:"alex@example.com"}}},n={args:{title:"AI数智名片",user:{name:"李华",email:"lihua@example.com",avatar:"https://api.dicebear.com/7.x/avataaars/svg?seed=lihua"}}},i={args:{title:"AI数智名片",user:{name:"王芳"}}},c={args:{title:"交互演示",user:null},render:se=>e.jsxs("div",{className:"space-y-4",children:[e.jsx(d,{...se}),e.jsxs("div",{className:"px-6 py-4 text-sm text-text-muted bg-slate-50 mx-6 rounded-xl",children:[e.jsxs("p",{children:["💡 点击「登录」按钮触发 ",e.jsx("code",{children:"onLogin"})," 回调（查看 Actions 面板）"]}),e.jsxs("p",{className:"mt-1",children:["该演示展示未登录状态。在 Controls 面板中切换 ",e.jsx("code",{children:"user"})," prop 可观察登录态。"]})]})]})},m={render:()=>e.jsxs("div",{className:"space-y-1",children:[e.jsx(d,{title:"未登录",user:null}),e.jsx(d,{title:"已登录",user:{name:"张明",email:"zhangming@example.com"}}),e.jsx(d,{title:"已登录（带头像）",user:{name:"李华",email:"lihua@example.com",avatar:"https://api.dicebear.com/7.x/avataaars/svg?seed=lihua"}})]}),parameters:{docs:{description:{story:"三种典型状态的并列对比：未登录、已登录（无头像）、已登录（有头像）。"}}}};var p,l,u,g,x;r.parameters={...r.parameters,docs:{...(p=r.parameters)==null?void 0:p.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: null
  }
}`,...(u=(l=r.parameters)==null?void 0:l.docs)==null?void 0:u.source},description:{story:"未登录 — 显示登录按钮",...(x=(g=r.parameters)==null?void 0:g.docs)==null?void 0:x.description}}};var h,v,I,L,A;s.parameters={...s.parameters,docs:{...(h=s.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    title: '数字名片管理平台',
    user: null
  }
}`,...(I=(v=s.parameters)==null?void 0:v.docs)==null?void 0:I.source},description:{story:"未登录（自定义标题）",...(A=(L=s.parameters)==null?void 0:L.docs)==null?void 0:A.description}}};var y,j,S,N,b;a.parameters={...a.parameters,docs:{...(y=a.parameters)==null?void 0:y.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: null
  }
}`,...(S=(j=a.parameters)==null?void 0:j.docs)==null?void 0:S.source},description:{story:"未登录（无登录回调 — 仅显示标题）",...(b=(N=a.parameters)==null?void 0:N.docs)==null?void 0:b.description}}};var H,O,C,f,z;t.parameters={...t.parameters,docs:{...(H=t.parameters)==null?void 0:H.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: {
      name: '张明',
      email: 'zhangming@example.com'
    }
  }
}`,...(C=(O=t.parameters)==null?void 0:O.docs)==null?void 0:C.source},description:{story:"已登录 — 显示用户名、设置和登出按钮",...(z=(f=t.parameters)==null?void 0:f.docs)==null?void 0:z.description}}};var T,E,R,W,_;o.parameters={...o.parameters,docs:{...(T=o.parameters)==null?void 0:T.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: {
      name: '亚历山大·伊万诺维奇',
      email: 'alex@example.com'
    }
  }
}`,...(R=(E=o.parameters)==null?void 0:E.docs)==null?void 0:R.source},description:{story:"已登录（长用户名）",...(_=(W=o.parameters)==null?void 0:W.docs)==null?void 0:_.description}}};var U,k,q,w,B;n.parameters={...n.parameters,docs:{...(U=n.parameters)==null?void 0:U.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: {
      name: '李华',
      email: 'lihua@example.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=lihua'
    }
  }
}`,...(q=(k=n.parameters)==null?void 0:k.docs)==null?void 0:q.source},description:{story:"已登录（带头像URL）",...(B=(w=n.parameters)==null?void 0:w.docs)==null?void 0:B.description}}};var D,F,G,J,K;i.parameters={...i.parameters,docs:{...(D=i.parameters)==null?void 0:D.docs,source:{originalSource:`{
  args: {
    title: 'AI数智名片',
    user: {
      name: '王芳'
    }
  }
}`,...(G=(F=i.parameters)==null?void 0:F.docs)==null?void 0:G.source},description:{story:"已登录（仅登出按钮，无设置）",...(K=(J=i.parameters)==null?void 0:J.docs)==null?void 0:K.description}}};var M,P,Q,V,X;c.parameters={...c.parameters,docs:{...(M=c.parameters)==null?void 0:M.docs,source:{originalSource:`{
  args: {
    title: '交互演示',
    user: null
  },
  render: args => <div className="space-y-4">\r
      <Header {...args} />\r
      <div className="px-6 py-4 text-sm text-text-muted bg-slate-50 mx-6 rounded-xl">\r
        <p>💡 点击「登录」按钮触发 <code>onLogin</code> 回调（查看 Actions 面板）</p>\r
        <p className="mt-1">\r
          该演示展示未登录状态。在 Controls 面板中切换 <code>user</code> prop 可观察登录态。\r
        </p>\r
      </div>\r
    </div>
}`,...(Q=(P=c.parameters)==null?void 0:P.docs)==null?void 0:Q.source},description:{story:"可登录/登出切换的交互演示",...(X=(V=c.parameters)==null?void 0:V.docs)==null?void 0:X.description}}};var Y,Z,$,ee,re;m.parameters={...m.parameters,docs:{...(Y=m.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <div className="space-y-1">\r
      <Header title="未登录" user={null} />\r
      <Header title="已登录" user={{
      name: '张明',
      email: 'zhangming@example.com'
    }} />\r
      <Header title="已登录（带头像）" user={{
      name: '李华',
      email: 'lihua@example.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=lihua'
    }} />\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '三种典型状态的并列对比：未登录、已登录（无头像）、已登录（有头像）。'
      }
    }
  }
}`,...($=(Z=m.parameters)==null?void 0:Z.docs)==null?void 0:$.source},description:{story:"所有状态并列对比",...(re=(ee=m.parameters)==null?void 0:ee.docs)==null?void 0:re.description}}};const de=["LoggedOut","LoggedOutCustomTitle","LoggedOutNoAction","LoggedIn","LoggedInLongName","LoggedInWithAvatar","LoggedInSimple","Interactive","AllStates"];export{m as AllStates,c as Interactive,t as LoggedIn,o as LoggedInLongName,i as LoggedInSimple,n as LoggedInWithAvatar,r as LoggedOut,s as LoggedOutCustomTitle,a as LoggedOutNoAction,de as __namedExportsOrder,me as default};
