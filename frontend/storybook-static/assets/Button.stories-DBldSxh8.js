import{j as r}from"./iframe-BgyFVukn.js";import{c as zr}from"./clsx-B-dksMZM.js";import{L as Er}from"./loader-circle-DcTPihAy.js";import{c as g}from"./createLucideIcon-C5yOfbJT.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Gr=[["path",{d:"M5 12h14",key:"1ays0h"}],["path",{d:"m12 5 7 7-7 7",key:"xquz4c"}]],Jr=g("arrow-right",Gr);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Kr=[["path",{d:"M5 12h14",key:"1ays0h"}],["path",{d:"M12 5v14",key:"s699le"}]],Qr=g("plus",Kr);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ur=[["path",{d:"M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",key:"1c8476"}],["path",{d:"M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7",key:"1ydtos"}],["path",{d:"M7 3v4a1 1 0 0 0 1 1h7",key:"t51u73"}]],Dr=g("save",Ur);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xr=[["path",{d:"M10 11v6",key:"nco0om"}],["path",{d:"M14 11v6",key:"outv1u"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6",key:"miytrc"}],["path",{d:"M3 6h18",key:"d0wm0j"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2",key:"e791ji"}]],Yr=g("trash-2",Xr),Zr={primary:"bg-primary text-white hover:bg-primary/90 active:bg-primary/80 focus-visible:ring-primary/40",secondary:"bg-slate-100 text-on-surface hover:bg-slate-200 active:bg-slate-300 focus-visible:ring-slate-300/40",outline:"border border-border-light text-on-surface bg-transparent hover:bg-slate-50 active:bg-slate-100 focus-visible:ring-border-light/40"};function v({variant:e="primary",loading:f=!1,disabled:Fr=!1,icon:x,iconRight:S,fullWidth:Hr=!1,children:N,className:Ar,...$r}){const b=Fr||f;return r.jsxs("button",{disabled:b,className:zr("inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium","transition-all duration-200 select-none","focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1",Zr[e],b&&"opacity-50 cursor-not-allowed pointer-events-none",!b&&"cursor-pointer",Hr&&"w-full",Ar),...$r,children:[f?r.jsx(Er,{className:"w-4 h-4 animate-spin shrink-0","aria-hidden":"true"}):x?r.jsx("span",{className:"shrink-0",children:x}):null,N&&r.jsx("span",{className:"truncate",children:N}),!f&&S&&r.jsx("span",{className:"shrink-0",children:S})]})}v.__docgenInfo={description:"",methods:[],displayName:"Button",props:{variant:{required:!1,tsType:{name:"union",raw:"'primary' | 'secondary' | 'outline'",elements:[{name:"literal",value:"'primary'"},{name:"literal",value:"'secondary'"},{name:"literal",value:"'outline'"}]},description:"按钮变体",defaultValue:{value:"'primary'",computed:!1}},loading:{required:!1,tsType:{name:"boolean"},description:"加载中状态 — 显示旋转图标并禁用交互",defaultValue:{value:"false",computed:!1}},icon:{required:!1,tsType:{name:"ReactNode"},description:"图标（前置）"},iconRight:{required:!1,tsType:{name:"ReactNode"},description:"图标（后置）"},fullWidth:{required:!1,tsType:{name:"boolean"},description:"全宽模式",defaultValue:{value:"false",computed:!1}},children:{required:!1,tsType:{name:"ReactNode"},description:"子元素"},disabled:{defaultValue:{value:"false",computed:!1},required:!1}},composes:["ButtonHTMLAttributes"]};const oe={title:"Components/Button",component:v,parameters:{layout:"centered",docs:{description:{component:"通用按钮组件。支持 primary / secondary / outline 三种变体，以及 loading、disabled 状态和图标插槽。"}}},argTypes:{variant:{control:"select",options:["primary","secondary","outline"],description:"按钮视觉变体"},loading:{control:"boolean",description:"加载中状态 — 显示旋转图标并禁用交互"},disabled:{control:"boolean",description:"禁用状态"},fullWidth:{control:"boolean",description:"全宽模式"},children:{control:"text",description:"按钮文本"},onClick:{action:"clicked",description:"点击回调"}}},a={args:{variant:"primary",children:"Primary 按钮"}},s={args:{variant:"secondary",children:"Secondary 按钮"}},t={args:{variant:"outline",children:"Outline 按钮"}},o={args:{variant:"primary",loading:!0,children:"加载中..."}},i={args:{variant:"primary",disabled:!0,children:"已禁用"}},n={args:{variant:"outline",disabled:!0,children:"禁用 Outline"}},c={args:{variant:"primary",icon:r.jsx(Qr,{className:"w-4 h-4"}),children:"创建名片"}},d={args:{variant:"secondary",iconRight:r.jsx(Jr,{className:"w-4 h-4"}),children:"下一步"}},l={args:{variant:"outline",icon:r.jsx(Yr,{className:"w-4 h-4"}),"aria-label":"删除"},parameters:{docs:{description:{story:"无文字时请务必提供 aria-label 属性保证无障碍访问。"}}}},p={args:{variant:"primary",icon:r.jsx(Dr,{className:"w-4 h-4"}),children:"保存"}},m={args:{variant:"primary",loading:!0,icon:r.jsx(Dr,{className:"w-4 h-4"}),children:"保存中..."}},u={args:{variant:"primary",fullWidth:!0,children:"全宽按钮"},decorators:[e=>r.jsx("div",{className:"w-80",children:r.jsx(e,{})})]},y={args:{variant:"secondary",fullWidth:!0,children:"全宽次要按钮"},decorators:[e=>r.jsx("div",{className:"w-80",children:r.jsx(e,{})})]},h={render:()=>r.jsxs("div",{className:"flex items-center gap-3",children:[r.jsx(v,{variant:"primary",children:"Primary"}),r.jsx(v,{variant:"secondary",children:"Secondary"}),r.jsx(v,{variant:"outline",children:"Outline"})]}),parameters:{docs:{description:{story:"三种按钮变体并列展示，方便对比视觉差异。"}}}};var j,w,k,W,O;a.parameters={...a.parameters,docs:{...(j=a.parameters)==null?void 0:j.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    children: 'Primary 按钮'
  }
}`,...(k=(w=a.parameters)==null?void 0:w.docs)==null?void 0:k.source},description:{story:"Primary — 主要操作按钮",...(O=(W=a.parameters)==null?void 0:W.docs)==null?void 0:O.description}}};var B,M,_,I,P;s.parameters={...s.parameters,docs:{...(B=s.parameters)==null?void 0:B.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    children: 'Secondary 按钮'
  }
}`,...(_=(M=s.parameters)==null?void 0:M.docs)==null?void 0:_.source},description:{story:"Secondary — 次要操作按钮",...(P=(I=s.parameters)==null?void 0:I.docs)==null?void 0:P.description}}};var R,T,V,q,L;t.parameters={...t.parameters,docs:{...(R=t.parameters)==null?void 0:R.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    children: 'Outline 按钮'
  }
}`,...(V=(T=t.parameters)==null?void 0:T.docs)==null?void 0:V.source},description:{story:"Outline — 边框按钮",...(L=(q=t.parameters)==null?void 0:q.docs)==null?void 0:L.description}}};var C,D,F,H,A;o.parameters={...o.parameters,docs:{...(C=o.parameters)==null?void 0:C.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    loading: true,
    children: '加载中...'
  }
}`,...(F=(D=o.parameters)==null?void 0:D.docs)==null?void 0:F.source},description:{story:"加载中 — 显示旋转动画并禁用点击",...(A=(H=o.parameters)==null?void 0:H.docs)==null?void 0:A.description}}};var $,z,E,G,J;i.parameters={...i.parameters,docs:{...($=i.parameters)==null?void 0:$.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    disabled: true,
    children: '已禁用'
  }
}`,...(E=(z=i.parameters)==null?void 0:z.docs)==null?void 0:E.source},description:{story:"禁用状态 — 不可点击",...(J=(G=i.parameters)==null?void 0:G.docs)==null?void 0:J.description}}};var K,Q,U,X,Y;n.parameters={...n.parameters,docs:{...(K=n.parameters)==null?void 0:K.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    disabled: true,
    children: '禁用 Outline'
  }
}`,...(U=(Q=n.parameters)==null?void 0:Q.docs)==null?void 0:U.source},description:{story:"禁用 + Outline",...(Y=(X=n.parameters)==null?void 0:X.docs)==null?void 0:Y.description}}};var Z,rr,er,ar,sr;c.parameters={...c.parameters,docs:{...(Z=c.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    icon: <Plus className="w-4 h-4" />,
    children: '创建名片'
  }
}`,...(er=(rr=c.parameters)==null?void 0:rr.docs)==null?void 0:er.source},description:{story:"前置图标 + 文字",...(sr=(ar=c.parameters)==null?void 0:ar.docs)==null?void 0:sr.description}}};var tr,or,ir,nr,cr;d.parameters={...d.parameters,docs:{...(tr=d.parameters)==null?void 0:tr.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    iconRight: <ArrowRight className="w-4 h-4" />,
    children: '下一步'
  }
}`,...(ir=(or=d.parameters)==null?void 0:or.docs)==null?void 0:ir.source},description:{story:"后置图标 + 文字",...(cr=(nr=d.parameters)==null?void 0:nr.docs)==null?void 0:cr.description}}};var dr,lr,pr,mr,ur;l.parameters={...l.parameters,docs:{...(dr=l.parameters)==null?void 0:dr.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    icon: <Trash2 className="w-4 h-4" />,
    'aria-label': '删除'
  },
  parameters: {
    docs: {
      description: {
        story: '无文字时请务必提供 aria-label 属性保证无障碍访问。'
      }
    }
  }
}`,...(pr=(lr=l.parameters)==null?void 0:lr.docs)==null?void 0:pr.source},description:{story:"仅图标（无文字）",...(ur=(mr=l.parameters)==null?void 0:mr.docs)==null?void 0:ur.description}}};var yr,hr,vr,gr,fr;p.parameters={...p.parameters,docs:{...(yr=p.parameters)==null?void 0:yr.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    icon: <Save className="w-4 h-4" />,
    children: '保存'
  }
}`,...(vr=(hr=p.parameters)==null?void 0:hr.docs)==null?void 0:vr.source},description:{story:"保存按钮（图标 + 文字）",...(fr=(gr=p.parameters)==null?void 0:gr.docs)==null?void 0:fr.description}}};var br,xr,Sr,Nr,jr;m.parameters={...m.parameters,docs:{...(br=m.parameters)==null?void 0:br.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    loading: true,
    icon: <Save className="w-4 h-4" />,
    children: '保存中...'
  }
}`,...(Sr=(xr=m.parameters)==null?void 0:xr.docs)==null?void 0:Sr.source},description:{story:"加载中 + 图标 + 文字",...(jr=(Nr=m.parameters)==null?void 0:Nr.docs)==null?void 0:jr.description}}};var wr,kr,Wr,Or,Br;u.parameters={...u.parameters,docs:{...(wr=u.parameters)==null?void 0:wr.docs,source:{originalSource:`{
  args: {
    variant: 'primary',
    fullWidth: true,
    children: '全宽按钮'
  },
  decorators: [Story => <div className="w-80">\r
        <Story />\r
      </div>]
}`,...(Wr=(kr=u.parameters)==null?void 0:kr.docs)==null?void 0:Wr.source},description:{story:"全宽 Primary",...(Br=(Or=u.parameters)==null?void 0:Or.docs)==null?void 0:Br.description}}};var Mr,_r,Ir,Pr,Rr;y.parameters={...y.parameters,docs:{...(Mr=y.parameters)==null?void 0:Mr.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    fullWidth: true,
    children: '全宽次要按钮'
  },
  decorators: [Story => <div className="w-80">\r
        <Story />\r
      </div>]
}`,...(Ir=(_r=y.parameters)==null?void 0:_r.docs)==null?void 0:Ir.source},description:{story:"全宽 Secondary",...(Rr=(Pr=y.parameters)==null?void 0:Pr.docs)==null?void 0:Rr.description}}};var Tr,Vr,qr,Lr,Cr;h.parameters={...h.parameters,docs:{...(Tr=h.parameters)==null?void 0:Tr.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">\r
      <Button variant="primary">Primary</Button>\r
      <Button variant="secondary">Secondary</Button>\r
      <Button variant="outline">Outline</Button>\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '三种按钮变体并列展示，方便对比视觉差异。'
      }
    }
  }
}`,...(qr=(Vr=h.parameters)==null?void 0:Vr.docs)==null?void 0:qr.source},description:{story:"三种变体并列对比",...(Cr=(Lr=h.parameters)==null?void 0:Lr.docs)==null?void 0:Cr.description}}};const ie=["Primary","Secondary","Outline","Loading","Disabled","DisabledOutline","WithIcon","WithIconRight","IconOnly","SaveButton","LoadingWithIcon","FullWidth","FullWidthSecondary","VariantComparison"];export{i as Disabled,n as DisabledOutline,u as FullWidth,y as FullWidthSecondary,l as IconOnly,o as Loading,m as LoadingWithIcon,t as Outline,a as Primary,p as SaveButton,s as Secondary,h as VariantComparison,c as WithIcon,d as WithIconRight,ie as __namedExportsOrder,oe as default};
