import{j as r}from"./iframe-BgyFVukn.js";import{c as z}from"./createLucideIcon-C5yOfbJT.js";import{X as A}from"./x-CLZ8N8iQ.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const C=[["path",{d:"m21 21-4.34-4.34",key:"14j7rj"}],["circle",{cx:"11",cy:"11",r:"8",key:"4ej97u"}]],F=z("search",C);function P({value:i="",onChange:e,onClear:d,placeholder:n="搜索名片...",disabled:L=!1}){const O=X=>{e==null||e(X.target.value)},R=()=>{e==null||e(""),d==null||d()};return r.jsxs("div",{"data-testid":"search-bar",className:"relative flex items-center w-full max-w-md",role:"search",children:[r.jsx(F,{className:"absolute left-3 w-4 h-4 text-text-muted pointer-events-none","aria-hidden":"true"}),r.jsx("input",{type:"text",value:i,onChange:O,placeholder:n,disabled:L,"aria-label":n,className:"w-full pl-9 pr-9 py-2.5 rounded-xl bg-slate-50 border border-border-light text-sm text-on-surface placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed"}),i&&r.jsx("button",{onClick:R,className:"absolute right-2.5 p-1 rounded-md hover:bg-slate-200 transition-colors","aria-label":"清除搜索",children:r.jsx(A,{className:"w-4 h-4 text-text-muted"})})]})}P.__docgenInfo={description:"",methods:[],displayName:"SearchBar",props:{value:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:"''",computed:!1}},onChange:{required:!1,tsType:{name:"signature",type:"function",raw:"(value: string) => void",signature:{arguments:[{type:{name:"string"},name:"value"}],return:{name:"void"}}},description:""},onClear:{required:!1,tsType:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}}},description:""},placeholder:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:"'搜索名片...'",computed:!1}},disabled:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}}}};const M={title:"Components/SearchBar",component:P,parameters:{layout:"centered",docs:{description:{component:"搜索输入框组件。支持搜索图标、清除按钮和禁用状态。"}}},argTypes:{value:{control:"text",description:"当前搜索值"},placeholder:{control:"text",description:"占位文本"},disabled:{control:"boolean",description:"禁用状态"},onChange:{action:"onChange",description:"值变更回调"},onClear:{action:"onClear",description:"清除回调"}}},a={args:{value:"",placeholder:"搜索名片...",disabled:!1}},s={args:{value:"张明",placeholder:"搜索名片...",disabled:!1}},t={args:{value:"",placeholder:"搜索已禁用",disabled:!0}},o={args:{value:"",placeholder:"搜索团队成员、名片...",disabled:!1}},l={args:{value:"测试内容",placeholder:"搜索...",disabled:!0}};var c,p,u,m,f;a.parameters={...a.parameters,docs:{...(c=a.parameters)==null?void 0:c.docs,source:{originalSource:`{
  args: {
    value: '',
    placeholder: '搜索名片...',
    disabled: false
  }
}`,...(u=(p=a.parameters)==null?void 0:p.docs)==null?void 0:u.source},description:{story:"空状态 — 默认占位符",...(f=(m=a.parameters)==null?void 0:m.docs)==null?void 0:f.description}}};var h,b,g,y,v;s.parameters={...s.parameters,docs:{...(h=s.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    value: '张明',
    placeholder: '搜索名片...',
    disabled: false
  }
}`,...(g=(b=s.parameters)==null?void 0:b.docs)==null?void 0:g.source},description:{story:"已输入内容",...(v=(y=s.parameters)==null?void 0:y.docs)==null?void 0:v.description}}};var x,j,S,w,N;t.parameters={...t.parameters,docs:{...(x=t.parameters)==null?void 0:x.docs,source:{originalSource:`{
  args: {
    value: '',
    placeholder: '搜索已禁用',
    disabled: true
  }
}`,...(S=(j=t.parameters)==null?void 0:j.docs)==null?void 0:S.source},description:{story:"禁用状态",...(N=(w=t.parameters)==null?void 0:w.docs)==null?void 0:N.description}}};var V,T,_,q,D;o.parameters={...o.parameters,docs:{...(V=o.parameters)==null?void 0:V.docs,source:{originalSource:`{
  args: {
    value: '',
    placeholder: '搜索团队成员、名片...',
    disabled: false
  }
}`,...(_=(T=o.parameters)==null?void 0:T.docs)==null?void 0:_.source},description:{story:"自定义占位符",...(D=(q=o.parameters)==null?void 0:q.docs)==null?void 0:D.description}}};var E,W,k,B,I;l.parameters={...l.parameters,docs:{...(E=l.parameters)==null?void 0:E.docs,source:{originalSource:`{
  args: {
    value: '测试内容',
    placeholder: '搜索...',
    disabled: true
  }
}`,...(k=(W=l.parameters)==null?void 0:W.docs)==null?void 0:k.source},description:{story:"已输入且禁用",...(I=(B=l.parameters)==null?void 0:B.docs)==null?void 0:I.description}}};const Q=["Empty","WithValue","Disabled","CustomPlaceholder","DisabledWithValue"];export{o as CustomPlaceholder,t as Disabled,l as DisabledWithValue,a as Empty,s as WithValue,Q as __namedExportsOrder,M as default};
