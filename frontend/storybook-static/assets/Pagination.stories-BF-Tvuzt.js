import{j as t,r as Ke}from"./iframe-BgyFVukn.js";import{c as m}from"./clsx-B-dksMZM.js";import{c as Re}from"./createLucideIcon-C5yOfbJT.js";import{C as Qe,a as Ue}from"./chevron-right-Dp1TRzSI.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xe=[["path",{d:"m11 17-5-5 5-5",key:"13zhaf"}],["path",{d:"m18 17-5-5 5-5",key:"h8a8et"}]],Ye=Re("chevrons-left",Xe);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ze=[["path",{d:"m6 17 5-5-5-5",key:"xnjwq"}],["path",{d:"m13 17 5-5-5-5",key:"17xmmf"}]],et=Re("chevrons-right",Ze);function I({current:s,total:r,totalItems:c,onChange:l,pageSize:j=10,pageSizeOptions:Ae=[10,20,50,100],onPageSizeChange:w,compact:n=!1,disabled:a=!1,className:De}){if(r<=0)return null;const Ge=(()=>{const e=[],o=n?1:2;e.push(1),s-o>2&&e.push("ellipsis");for(let i=Math.max(2,s-o);i<=Math.min(r-1,s+o);i++)e.push(i);return s+o<r-1&&e.push("ellipsis"),r>1&&e.push(r),e})(),z=c?(s-1)*j+1:void 0,M=c?Math.min(s*j,c):void 0,T=m("inline-flex items-center justify-center rounded-lg text-sm font-medium","transition-colors duration-150 select-none","focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30",a&&"opacity-40 cursor-not-allowed pointer-events-none"),He=e=>m(T,e?"bg-primary text-white hover:bg-primary-container":"text-text-muted hover:text-on-surface hover:bg-slate-100"),N=e=>m(T,"text-text-muted hover:text-on-surface hover:bg-slate-100",e&&"opacity-30 cursor-not-allowed"),Je=(e,o)=>{if(e==="ellipsis")return t.jsx("span",{className:"inline-flex items-center justify-center w-8 h-8 text-xs text-text-muted select-none",children:"…"},`ellipsis-${o}`);const i=e===s;return t.jsx("button",{onClick:()=>!a&&l(e),disabled:a||i,className:m(He(i),n?"w-7 h-7 text-xs":"w-8 h-8 text-sm"),"aria-label":`第 ${e} 页`,"aria-current":i?"page":void 0,children:e},e)};return t.jsxs("nav",{className:m("flex items-center gap-2",n?"flex-row":"flex-wrap",De),"aria-label":"分页导航",children:[c!==void 0&&!n&&t.jsxs("span",{className:"text-xs text-text-muted mr-2 whitespace-nowrap",children:["共 ",c," 条",z&&M&&`（${z}-${M}）`]}),!n&&t.jsx("button",{onClick:()=>!a&&l(1),disabled:a||s===1,className:N(s===1),"aria-label":"首页",children:t.jsx(Ye,{className:"w-4 h-4"})}),t.jsx("button",{onClick:()=>!a&&l(s-1),disabled:a||s===1,className:N(s===1),"aria-label":"上一页",children:t.jsx(Qe,{className:"w-4 h-4"})}),n?t.jsxs("span",{className:"text-sm text-text-muted px-1 whitespace-nowrap",children:[s," / ",r]}):t.jsx("div",{className:"flex items-center gap-1",children:Ge.map((e,o)=>Je(e,o))}),t.jsx("button",{onClick:()=>!a&&l(s+1),disabled:a||s===r,className:N(s===r),"aria-label":"下一页",children:t.jsx(Ue,{className:"w-4 h-4"})}),!n&&t.jsx("button",{onClick:()=>!a&&l(r),disabled:a||s===r,className:N(s===r),"aria-label":"末页",children:t.jsx(et,{className:"w-4 h-4"})}),w&&!n&&t.jsxs("div",{className:"flex items-center gap-1.5 ml-3",children:[t.jsx("span",{className:"text-xs text-text-muted",children:"每页"}),t.jsx("select",{value:j,onChange:e=>w(Number(e.target.value)),disabled:a,className:"text-xs border border-border-light rounded-lg px-2 py-1 bg-surface text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-40","aria-label":"每页条数",children:Ae.map(e=>t.jsxs("option",{value:e,children:[e," 条"]},e))})]})]})}I.__docgenInfo={description:`Pagination — 分页导航组件\r
\r
显示页码控制、条目统计、每页条数切换，支持紧凑模式用于表格/列表底部。`,methods:[],displayName:"Pagination",props:{current:{required:!0,tsType:{name:"number"},description:"当前页（从 1 开始）"},total:{required:!0,tsType:{name:"number"},description:"总页数"},totalItems:{required:!1,tsType:{name:"number"},description:"总数条目"},onChange:{required:!0,tsType:{name:"signature",type:"function",raw:"(page: number) => void",signature:{arguments:[{type:{name:"number"},name:"page"}],return:{name:"void"}}},description:"切换页回调"},pageSize:{required:!1,tsType:{name:"number"},description:"每页条数",defaultValue:{value:"10",computed:!1}},pageSizeOptions:{required:!1,tsType:{name:"Array",elements:[{name:"number"}],raw:"number[]"},description:"每页条数选项",defaultValue:{value:"[10, 20, 50, 100]",computed:!1}},onPageSizeChange:{required:!1,tsType:{name:"signature",type:"function",raw:"(size: number) => void",signature:{arguments:[{type:{name:"number"},name:"size"}],return:{name:"void"}}},description:"切换每页条数回调"},compact:{required:!1,tsType:{name:"boolean"},description:"紧凑模式",defaultValue:{value:"false",computed:!1}},disabled:{required:!1,tsType:{name:"boolean"},description:"禁用",defaultValue:{value:"false",computed:!1}},className:{required:!1,tsType:{name:"string"},description:"自定义类名"}}};const it={title:"Components/Pagination",component:I,parameters:{layout:"centered",docs:{description:{component:"分页导航组件。支持页码切换、首尾页快捷按钮、条目统计、每页条数切换和紧凑模式。适用于列表、表格等大数据量场景。"}}},argTypes:{current:{control:"number",description:"当前页（从 1 开始）"},total:{control:"number",description:"总页数"},totalItems:{control:"number",description:"总条目数（显示统计信息）"},pageSize:{control:"number",description:"每页条数"},pageSizeOptions:{control:"object",description:"每页条数选项"},compact:{control:"boolean",description:"紧凑模式（仅显示当前/总数）"},disabled:{control:"boolean",description:"禁用分页交互"},onChange:{action:"onChange",description:"切换页回调"},onPageSizeChange:{action:"onPageSizeChange",description:"每页条数变更回调"}}},d={args:{current:1,total:3,totalItems:30,onChange:()=>{}}},p={args:{current:5,total:10,totalItems:100,onChange:()=>{}}},u={args:{current:10,total:10,totalItems:100,onChange:()=>{}}},g={args:{current:1,total:10,totalItems:100,onChange:()=>{}}},h={args:{current:5,total:50,totalItems:500,onChange:()=>{}}},x={args:{current:48,total:50,totalItems:500,onChange:()=>{}}},f={args:{current:1,total:1,totalItems:5,onChange:()=>{}}},b={args:{current:3,total:10,totalItems:100,disabled:!0,onChange:()=>{}}},y={args:{current:3,total:10,totalItems:100,compact:!0,onChange:()=>{}}},C={args:{current:25,total:50,totalItems:500,compact:!0,onChange:()=>{}}},v={args:{current:3,total:20,totalItems:200,pageSize:10,onPageSizeChange:()=>{},onChange:()=>{}}},P={args:{current:3,total:10,onChange:()=>{}}},S={render:()=>{const[s,r]=Ke.useState(1);return t.jsxs("div",{className:"space-y-4",children:[t.jsxs("div",{className:"bg-surface rounded-xl border border-border-light p-4 text-sm text-text-muted",children:["当前页: ",t.jsx("strong",{className:"text-on-surface",children:s}),t.jsx("span",{className:"ml-2",children:"（点击页码切换）"})]}),t.jsx(I,{current:s,total:20,totalItems:200,onChange:r,pageSize:10,onPageSizeChange:()=>{}})]})},parameters:{docs:{description:{story:"可交互演示。点击页码实时切换，观察当前页状态变化。"}}}};var k,q,_,V,E;d.parameters={...d.parameters,docs:{...(k=d.parameters)==null?void 0:k.docs,source:{originalSource:`{
  args: {
    current: 1,
    total: 3,
    totalItems: 30,
    onChange: () => {}
  }
}`,...(_=(q=d.parameters)==null?void 0:q.docs)==null?void 0:_.source},description:{story:"少数页 — 3 页",...(E=(V=d.parameters)==null?void 0:V.docs)==null?void 0:E.description}}};var L,$,F,W,B;p.parameters={...p.parameters,docs:{...(L=p.parameters)==null?void 0:L.docs,source:{originalSource:`{
  args: {
    current: 5,
    total: 10,
    totalItems: 100,
    onChange: () => {}
  }
}`,...(F=($=p.parameters)==null?void 0:$.docs)==null?void 0:F.source},description:{story:"中间页 — 第 5 页 / 共 10 页",...(B=(W=p.parameters)==null?void 0:W.docs)==null?void 0:B.description}}};var O,R,A,D,G;u.parameters={...u.parameters,docs:{...(O=u.parameters)==null?void 0:O.docs,source:{originalSource:`{
  args: {
    current: 10,
    total: 10,
    totalItems: 100,
    onChange: () => {}
  }
}`,...(A=(R=u.parameters)==null?void 0:R.docs)==null?void 0:A.source},description:{story:"末页 — 第 10 页 / 共 10 页",...(G=(D=u.parameters)==null?void 0:D.docs)==null?void 0:G.description}}};var H,J,K,Q,U;g.parameters={...g.parameters,docs:{...(H=g.parameters)==null?void 0:H.docs,source:{originalSource:`{
  args: {
    current: 1,
    total: 10,
    totalItems: 100,
    onChange: () => {}
  }
}`,...(K=(J=g.parameters)==null?void 0:J.docs)==null?void 0:K.source},description:{story:"首页 — 第 1 页 / 共 10 页",...(U=(Q=g.parameters)==null?void 0:Q.docs)==null?void 0:U.description}}};var X,Y,Z,ee,te;h.parameters={...h.parameters,docs:{...(X=h.parameters)==null?void 0:X.docs,source:{originalSource:`{
  args: {
    current: 5,
    total: 50,
    totalItems: 500,
    onChange: () => {}
  }
}`,...(Z=(Y=h.parameters)==null?void 0:Y.docs)==null?void 0:Z.source},description:{story:"大量页 — 第 5 页 / 共 50 页（显示省略号）",...(te=(ee=h.parameters)==null?void 0:ee.docs)==null?void 0:te.description}}};var se,re,ae,ne,oe;x.parameters={...x.parameters,docs:{...(se=x.parameters)==null?void 0:se.docs,source:{originalSource:`{
  args: {
    current: 48,
    total: 50,
    totalItems: 500,
    onChange: () => {}
  }
}`,...(ae=(re=x.parameters)==null?void 0:re.docs)==null?void 0:ae.source},description:{story:"大量页 — 第 48 页 / 共 50 页",...(oe=(ne=x.parameters)==null?void 0:ne.docs)==null?void 0:oe.description}}};var ie,ce,le,me,de;f.parameters={...f.parameters,docs:{...(ie=f.parameters)==null?void 0:ie.docs,source:{originalSource:`{
  args: {
    current: 1,
    total: 1,
    totalItems: 5,
    onChange: () => {}
  }
}`,...(le=(ce=f.parameters)==null?void 0:ce.docs)==null?void 0:le.source},description:{story:"无分页 — 仅 1 页",...(de=(me=f.parameters)==null?void 0:me.docs)==null?void 0:de.description}}};var pe,ue,ge,he,xe;b.parameters={...b.parameters,docs:{...(pe=b.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  args: {
    current: 3,
    total: 10,
    totalItems: 100,
    disabled: true,
    onChange: () => {}
  }
}`,...(ge=(ue=b.parameters)==null?void 0:ue.docs)==null?void 0:ge.source},description:{story:"禁用状态",...(xe=(he=b.parameters)==null?void 0:he.docs)==null?void 0:xe.description}}};var fe,be,ye,Ce,ve;y.parameters={...y.parameters,docs:{...(fe=y.parameters)==null?void 0:fe.docs,source:{originalSource:`{
  args: {
    current: 3,
    total: 10,
    totalItems: 100,
    compact: true,
    onChange: () => {}
  }
}`,...(ye=(be=y.parameters)==null?void 0:be.docs)==null?void 0:ye.source},description:{story:'紧凑模式 — 仅显示 "当前 / 总数"',...(ve=(Ce=y.parameters)==null?void 0:Ce.docs)==null?void 0:ve.description}}};var Pe,Se,Ne,je,Ie;C.parameters={...C.parameters,docs:{...(Pe=C.parameters)==null?void 0:Pe.docs,source:{originalSource:`{
  args: {
    current: 25,
    total: 50,
    totalItems: 500,
    compact: true,
    onChange: () => {}
  }
}`,...(Ne=(Se=C.parameters)==null?void 0:Se.docs)==null?void 0:Ne.source},description:{story:"紧凑模式 + 大量页",...(Ie=(je=C.parameters)==null?void 0:je.docs)==null?void 0:Ie.description}}};var we,ze,Me,Te,ke;v.parameters={...v.parameters,docs:{...(we=v.parameters)==null?void 0:we.docs,source:{originalSource:`{
  args: {
    current: 3,
    total: 20,
    totalItems: 200,
    pageSize: 10,
    onPageSizeChange: () => {},
    onChange: () => {}
  }
}`,...(Me=(ze=v.parameters)==null?void 0:ze.docs)==null?void 0:Me.source},description:{story:"带每页条数切换",...(ke=(Te=v.parameters)==null?void 0:Te.docs)==null?void 0:ke.description}}};var qe,_e,Ve,Ee,Le;P.parameters={...P.parameters,docs:{...(qe=P.parameters)==null?void 0:qe.docs,source:{originalSource:`{
  args: {
    current: 3,
    total: 10,
    onChange: () => {}
  }
}`,...(Ve=(_e=P.parameters)==null?void 0:_e.docs)==null?void 0:Ve.source},description:{story:"无 totalItems — 不显示条目统计",...(Le=(Ee=P.parameters)==null?void 0:Ee.docs)==null?void 0:Le.description}}};var $e,Fe,We,Be,Oe;S.parameters={...S.parameters,docs:{...($e=S.parameters)==null?void 0:$e.docs,source:{originalSource:`{
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [page, setPage] = useState(1);
    return <div className="space-y-4">\r
        <div className="bg-surface rounded-xl border border-border-light p-4 text-sm text-text-muted">\r
          当前页: <strong className="text-on-surface">{page}</strong>\r
          <span className="ml-2">（点击页码切换）</span>\r
        </div>\r
        <Pagination current={page} total={20} totalItems={200} onChange={setPage} pageSize={10} onPageSizeChange={() => {}} />\r
      </div>;
  },
  parameters: {
    docs: {
      description: {
        story: '可交互演示。点击页码实时切换，观察当前页状态变化。'
      }
    }
  }
}`,...(We=(Fe=S.parameters)==null?void 0:Fe.docs)==null?void 0:We.source},description:{story:`可交互的分页演示\r
点击页码可实时切换`,...(Oe=(Be=S.parameters)==null?void 0:Be.docs)==null?void 0:Oe.description}}};const ct=["FewPages","MiddlePage","LastPage","FirstPage","ManyPages","NearEndManyPages","SinglePage","Disabled","CompactMode","CompactManyPages","WithPageSizeSelector","WithoutTotalItems","Interactive"];export{C as CompactManyPages,y as CompactMode,b as Disabled,d as FewPages,g as FirstPage,S as Interactive,u as LastPage,h as ManyPages,p as MiddlePage,x as NearEndManyPages,f as SinglePage,v as WithPageSizeSelector,P as WithoutTotalItems,ct as __namedExportsOrder,it as default};
