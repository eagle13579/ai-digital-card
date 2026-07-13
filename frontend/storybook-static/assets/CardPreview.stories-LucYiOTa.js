import{j as e}from"./iframe-BgyFVukn.js";import{c}from"./createLucideIcon-C5yOfbJT.js";import{B as ee}from"./building-2-Cl4-c_pP.js";import{U as ae}from"./user-kvdGHbHj.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const te=[["path",{d:"M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16",key:"jecpp"}],["rect",{width:"20",height:"14",x:"2",y:"6",rx:"2",key:"i6l2r4"}]],se=c("briefcase",te);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const re=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20",key:"13o1zl"}],["path",{d:"M2 12h20",key:"9i4pu4"}]],oe=c("globe",re);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ne=[["path",{d:"m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7",key:"132q7q"}],["rect",{x:"2",y:"4",width:"20",height:"16",rx:"2",key:"izxlao"}]],ce=c("mail",ne);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ie=[["path",{d:"M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",key:"1r0f0z"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}]],le=c("map-pin",ie);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pe=[["path",{d:"M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384",key:"9njp5v"}]],de=c("phone",pe),u={default:{bg:"bg-gradient-to-br from-blue-500 to-blue-700",main:"bg-blue-600",accent:"#60A5FA",text:"text-white"},purple:{bg:"bg-gradient-to-br from-purple-500 to-indigo-800",main:"bg-purple-600",accent:"#A78BFA",text:"text-white"},dark:{bg:"bg-gradient-to-br from-gray-800 to-gray-950",main:"bg-gray-700",accent:"#6B7280",text:"text-white"}};function O({fields:R,template:H="default",compact:l=!1}){const d=u[H]||u.default,{name:m,position:J,company:K,phone:Q,email:W,address:X,website:Y}=R,p=[{icon:se,label:J},{icon:ee,label:K},{icon:de,label:Q},{icon:ce,label:W},{icon:le,label:X},{icon:oe,label:Y}].filter(i=>i.label);return e.jsxs("div",{"data-testid":"card-preview",className:`rounded-2xl overflow-hidden shadow-elevated ${d.bg} ${d.text} ${l?"w-64":"w-80"}`,children:[e.jsxs("div",{className:"glass-card flex flex-col items-center pt-6 pb-4 px-4",children:[e.jsx("div",{className:"glass-card w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3","aria-hidden":"true",children:e.jsx(ae,{className:"glass-card w-8 h-8 text-white/80"})}),m?e.jsx("h3",{className:"glass-card text-lg font-bold text-center",children:m}):e.jsx("h3",{className:"glass-card text-lg font-bold text-center text-white/50",children:"未命名名片"})]}),!l&&p.length>0&&e.jsx("div",{className:"glass-card px-4 pb-5 space-y-2",children:p.map((i,Z)=>e.jsxs("div",{className:"glass-card flex items-center gap-2 text-sm text-white/90",children:[e.jsx(i.icon,{className:"glass-card w-4 h-4 shrink-0","aria-hidden":"true"}),e.jsx("span",{className:"glass-card truncate",children:i.label})]},Z))}),!l&&p.length===0&&e.jsx("div",{className:"glass-card px-4 pb-5 text-center text-sm text-white/50",children:"暂无资料"})]})}O.__docgenInfo={description:"",methods:[],displayName:"CardPreview",props:{fields:{required:!0,tsType:{name:"CardFields"},description:""},template:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:"'default'",computed:!1}},compact:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}}}};const xe={title:"Components/CardPreview",component:O,parameters:{layout:"centered",docs:{description:{component:"AI 数字名片预览组件。支持多种模板主题和紧凑/完整两种显示模式。"}}},argTypes:{template:{control:"select",options:["default","purple","dark"],description:"名片模板主题"},compact:{control:"boolean",description:"紧凑模式（仅显示头像和姓名）"},fields:{control:"object",description:"名片字段数据"}}},a={args:{fields:{name:"张明",position:"全栈工程师",company:"AI数智科技",phone:"+86 138-0000-0000",email:"zhangming@example.com",address:"北京市朝阳区建国路88号",website:"https://zhangming.dev"},template:"default",compact:!1}},t={args:{...a.args,template:"purple"}},s={args:{...a.args,template:"dark"}},r={args:{fields:{name:"李华",position:"产品经理",company:"创新科技"},template:"default",compact:!0}},o={args:{fields:{},template:"default",compact:!1}},n={args:{fields:{name:"王芳"},template:"purple",compact:!1}};var g,f,h,x,b;a.parameters={...a.parameters,docs:{...(g=a.parameters)==null?void 0:g.docs,source:{originalSource:`{
  args: {
    fields: {
      name: '张明',
      position: '全栈工程师',
      company: 'AI数智科技',
      phone: '+86 138-0000-0000',
      email: 'zhangming@example.com',
      address: '北京市朝阳区建国路88号',
      website: 'https://zhangming.dev'
    },
    template: 'default',
    compact: false
  }
}`,...(h=(f=a.parameters)==null?void 0:f.docs)==null?void 0:h.source},description:{story:"默认模板 — 完整信息",...(b=(x=a.parameters)==null?void 0:x.docs)==null?void 0:b.description}}};var y,w,v,j,k;t.parameters={...t.parameters,docs:{...(y=t.parameters)==null?void 0:y.docs,source:{originalSource:`{
  args: {
    ...Default.args,
    template: 'purple'
  }
}`,...(v=(w=t.parameters)==null?void 0:w.docs)==null?void 0:v.source},description:{story:"紫色主题",...(k=(j=t.parameters)==null?void 0:j.docs)==null?void 0:k.description}}};var N,_,A,M,T;s.parameters={...s.parameters,docs:{...(N=s.parameters)==null?void 0:N.docs,source:{originalSource:`{
  args: {
    ...Default.args,
    template: 'dark'
  }
}`,...(A=(_=s.parameters)==null?void 0:_.docs)==null?void 0:A.source},description:{story:"暗色主题",...(T=(M=s.parameters)==null?void 0:M.docs)==null?void 0:T.description}}};var C,P,z,S,$;r.parameters={...r.parameters,docs:{...(C=r.parameters)==null?void 0:C.docs,source:{originalSource:`{
  args: {
    fields: {
      name: '李华',
      position: '产品经理',
      company: '创新科技'
    },
    template: 'default',
    compact: true
  }
}`,...(z=(P=r.parameters)==null?void 0:P.docs)==null?void 0:z.source},description:{story:"紧凑模式 — 仅显示头像和姓名",...($=(S=r.parameters)==null?void 0:S.docs)==null?void 0:$.description}}};var q,D,E,B,I;o.parameters={...o.parameters,docs:{...(q=o.parameters)==null?void 0:q.docs,source:{originalSource:`{
  args: {
    fields: {},
    template: 'default',
    compact: false
  }
}`,...(E=(D=o.parameters)==null?void 0:D.docs)==null?void 0:E.source},description:{story:"空名片 — 无字段数据",...(I=(B=o.parameters)==null?void 0:B.docs)==null?void 0:I.description}}};var F,L,V,U,G;n.parameters={...n.parameters,docs:{...(F=n.parameters)==null?void 0:F.docs,source:{originalSource:`{
  args: {
    fields: {
      name: '王芳'
    },
    template: 'purple',
    compact: false
  }
}`,...(V=(L=n.parameters)==null?void 0:L.docs)==null?void 0:V.source},description:{story:"仅姓名",...(G=(U=n.parameters)==null?void 0:U.docs)==null?void 0:G.description}}};const be=["Default","PurpleTheme","DarkTheme","Compact","Empty","Minimal"];export{r as Compact,s as DarkTheme,a as Default,o as Empty,n as Minimal,t as PurpleTheme,be as __namedExportsOrder,xe as default};
