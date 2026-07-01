import{b as h,c as d,u as x,r as y,j as e}from"./iframe-D0-E4Z0o.js";import{F as m,S as p}from"./sparkles-IPsRl5Xk.js";import{c as s}from"./createLucideIcon-CW88hA_D.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u=[["path",{d:"m15 18-6-6 6-6",key:"1wnfg3"}]],b=s("chevron-left",u);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f=[["path",{d:"m9 18 6-6-6-6",key:"mthhwq"}]],g=s("chevron-right",f);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k=[["rect",{width:"20",height:"14",x:"2",y:"5",rx:"2",key:"ynyp8z"}],["line",{x1:"2",x2:"22",y1:"10",y2:"10",key:"1b3vmo"}]],N=s("credit-card",k);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4",key:"g0fldk"}],["path",{d:"m21 2-9.6 9.6",key:"1j0ho8"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5",key:"yqb3hr"}]],j=s("key",w);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v=[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1",key:"10lvy0"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1",key:"16une8"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1",key:"1hutg5"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1",key:"ldoo1y"}]],_=s("layout-dashboard",v);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const K=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915",key:"1i5ecw"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]],S=s("settings",K);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744",key:"16gr8j"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}]],C=s("users",$),L=[{path:"/",labelKey:"仪表盘",icon:e.jsx(_,{className:"w-5 h-5"})},{path:"/cards",labelKey:"名片编辑",icon:e.jsx(N,{className:"w-5 h-5"})},{path:"/matching",labelKey:"匹配中心",icon:e.jsx(p,{className:"w-5 h-5"})},{path:"/network",labelKey:"信任网络",icon:e.jsx(C,{className:"w-5 h-5"})},{path:"/api-keys",labelKey:"开发者门户",icon:e.jsx(j,{className:"w-5 h-5"})},{path:"/settings",labelKey:"设置",icon:e.jsx(S,{className:"w-5 h-5"})}];function M(){const o=h(),n=d(),r=x(),[a,i]=y.useState(!1),l=t=>t==="/"?o.pathname==="/":o.pathname.startsWith(t);return e.jsxs("aside",{className:`bg-white border-r border-border-light flex flex-col transition-all duration-300 ${a?"w-16":"w-56"}`,children:[e.jsxs("div",{className:"flex items-center gap-3 px-4 h-16 border-b border-border-light shrink-0",children:[e.jsx("div",{className:"w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0",children:e.jsx(m,{className:"w-4 h-4"})}),!a&&e.jsx("span",{className:"text-sm font-bold text-on-surface truncate",children:r("card.title")})]}),e.jsx("nav",{className:"flex-1 py-4 px-2 space-y-1 overflow-y-auto no-scrollbar",children:L.map(t=>{const c=l(t.path);return e.jsxs("button",{onClick:()=>n(t.path),className:`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${c?"bg-primary/10 text-primary shadow-sm":"text-text-muted hover:bg-slate-50 hover:text-on-surface"}`,title:a?r(t.labelKey):void 0,children:[e.jsx("span",{className:"shrink-0",children:t.icon}),!a&&e.jsx("span",{className:"truncate",children:r(t.labelKey)}),c&&e.jsx("span",{className:"ml-auto w-1.5 h-1.5 rounded-full bg-primary shrink-0"})]},t.path)})}),e.jsx("div",{className:"p-2 border-t border-border-light",children:e.jsx("button",{onClick:()=>i(t=>!t),className:"w-full flex items-center justify-center py-2 rounded-xl text-text-muted hover:bg-slate-50 hover:text-on-surface transition-colors",title:r(a?"展开侧栏":"收起侧栏"),children:a?e.jsx(g,{className:"w-4 h-4"}):e.jsx(b,{className:"w-4 h-4"})})})]})}M.__docgenInfo={description:"",methods:[],displayName:"Sidebar"};export{M as S};
