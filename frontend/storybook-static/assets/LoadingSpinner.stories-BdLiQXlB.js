import{j as e}from"./iframe-BgyFVukn.js";import{c as p}from"./clsx-B-dksMZM.js";import{L as oe}from"./loader-circle-DcTPihAy.js";import"./preload-helper-Dp1pzeXC.js";import"./createLucideIcon-C5yOfbJT.js";const ce={sm:"w-4 h-4",md:"w-8 h-8",lg:"w-12 h-12"},me={sm:"text-xs",md:"text-sm",lg:"text-base"};function s({size:x="md",fullPage:g=!1,label:d,className:le}){const u=e.jsxs("div",{className:p("flex flex-col items-center justify-center gap-3",g&&"min-h-[200px]",le),role:"status","aria-label":d||"加载中",children:[e.jsx(oe,{className:p("animate-spin text-primary",ce[x]),"aria-hidden":"true"}),d&&e.jsx("span",{className:p("text-text-muted",me[x]),children:d})]});return g?e.jsx("div",{className:"fixed inset-0 z-50 bg-white/60 backdrop-blur-sm flex items-center justify-center",children:u}):u}s.__docgenInfo={description:`LoadingSpinner — 加载旋转器组件\r
\r
支持 sm / md / lg 三种尺寸，可独立使用或作为全页覆盖层。`,methods:[],displayName:"LoadingSpinner",props:{size:{required:!1,tsType:{name:"union",raw:"'sm' | 'md' | 'lg'",elements:[{name:"literal",value:"'sm'"},{name:"literal",value:"'md'"},{name:"literal",value:"'lg'"}]},description:"尺寸",defaultValue:{value:"'md'",computed:!1}},fullPage:{required:!1,tsType:{name:"boolean"},description:"全页模式 — 居中覆盖整个父容器",defaultValue:{value:"false",computed:!1}},label:{required:!1,tsType:{name:"string"},description:"自定义提示文字（显示在旋转器下方）"},className:{required:!1,tsType:{name:"string"},description:"自定义类名"}}};const fe={title:"Components/LoadingSpinner",component:s,parameters:{layout:"centered",docs:{description:{component:"加载旋转器组件。支持 sm / md / lg 三种尺寸，以及内联模式和全页覆盖模式。全页模式下会覆盖整个视口并添加毛玻璃遮罩。"}}},argTypes:{size:{control:"select",options:["sm","md","lg"],description:"旋转器尺寸"},fullPage:{control:"boolean",description:"全页覆盖模式 — 覆盖整个视口并添加半透明遮罩"},label:{control:"text",description:"旋转器下方的提示文字"}}},r={args:{size:"sm"}},a={args:{size:"md"}},t={args:{size:"lg"}},i={args:{size:"sm",label:"加载中..."}},n={args:{size:"md",label:"正在加载名片数据..."}},l={args:{size:"lg",label:"正在为您生成智能名片..."}},o={args:{size:"lg",fullPage:!0,label:"页面加载中..."},parameters:{layout:"fullscreen",docs:{description:{story:"全页覆盖模式。固定定位覆盖整个视口，带毛玻璃遮罩，适合页面级加载场景。"}}}},c={render:()=>e.jsxs("div",{className:"flex items-end gap-8",children:[e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"sm"}),e.jsx("span",{className:"text-xs text-text-muted",children:"sm"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"md"}),e.jsx("span",{className:"text-xs text-text-muted",children:"md"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"lg"}),e.jsx("span",{className:"text-xs text-text-muted",children:"lg"})]})]}),parameters:{docs:{description:{story:"三种尺寸（sm / md / lg）并列对比。"}}}},m={render:()=>e.jsxs("div",{className:"flex items-end gap-8",children:[e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"sm",label:"小"}),e.jsx("span",{className:"text-xs text-text-muted",children:"sm"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"md",label:"中"}),e.jsx("span",{className:"text-xs text-text-muted",children:"md"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(s,{size:"lg",label:"大"}),e.jsx("span",{className:"text-xs text-text-muted",children:"lg"})]})]}),parameters:{docs:{description:{story:"带提示文字时三种尺寸的视觉效果对比。"}}}};var f,N,h,z,v;r.parameters={...r.parameters,docs:{...(f=r.parameters)==null?void 0:f.docs,source:{originalSource:`{
  args: {
    size: 'sm'
  }
}`,...(h=(N=r.parameters)==null?void 0:N.docs)==null?void 0:h.source},description:{story:"小尺寸 — 适合按钮内部或行内使用",...(v=(z=r.parameters)==null?void 0:z.docs)==null?void 0:v.description}}};var b,j,y,S,L;a.parameters={...a.parameters,docs:{...(b=a.parameters)==null?void 0:b.docs,source:{originalSource:`{
  args: {
    size: 'md'
  }
}`,...(y=(j=a.parameters)==null?void 0:j.docs)==null?void 0:y.source},description:{story:"中等尺寸 — 默认值，适合卡片或区块加载",...(L=(S=a.parameters)==null?void 0:S.docs)==null?void 0:L.description}}};var W,C,M,w,P;t.parameters={...t.parameters,docs:{...(W=t.parameters)==null?void 0:W.docs,source:{originalSource:`{
  args: {
    size: 'lg'
  }
}`,...(M=(C=t.parameters)==null?void 0:C.docs)==null?void 0:M.source},description:{story:"大尺寸 — 适合独立加载状态展示",...(P=(w=t.parameters)==null?void 0:w.docs)==null?void 0:P.description}}};var T,q,_,E,F;i.parameters={...i.parameters,docs:{...(T=i.parameters)==null?void 0:T.docs,source:{originalSource:`{
  args: {
    size: 'sm',
    label: '加载中...'
  }
}`,...(_=(q=i.parameters)==null?void 0:q.docs)==null?void 0:_.source},description:{story:"小尺寸 + 提示文字",...(F=(E=i.parameters)==null?void 0:E.docs)==null?void 0:F.description}}};var V,k,I,O,R;n.parameters={...n.parameters,docs:{...(V=n.parameters)==null?void 0:V.docs,source:{originalSource:`{
  args: {
    size: 'md',
    label: '正在加载名片数据...'
  }
}`,...(I=(k=n.parameters)==null?void 0:k.docs)==null?void 0:I.source},description:{story:"中等尺寸 + 提示文字",...(R=(O=n.parameters)==null?void 0:O.docs)==null?void 0:R.description}}};var A,B,D,G,H;l.parameters={...l.parameters,docs:{...(A=l.parameters)==null?void 0:A.docs,source:{originalSource:`{
  args: {
    size: 'lg',
    label: '正在为您生成智能名片...'
  }
}`,...(D=(B=l.parameters)==null?void 0:B.docs)==null?void 0:D.source},description:{story:"大尺寸 + 提示文字",...(H=(G=l.parameters)==null?void 0:G.docs)==null?void 0:H.description}}};var J,K,Q,U,X;o.parameters={...o.parameters,docs:{...(J=o.parameters)==null?void 0:J.docs,source:{originalSource:`{
  args: {
    size: 'lg',
    fullPage: true,
    label: '页面加载中...'
  },
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: '全页覆盖模式。固定定位覆盖整个视口，带毛玻璃遮罩，适合页面级加载场景。'
      }
    }
  }
}`,...(Q=(K=o.parameters)==null?void 0:K.docs)==null?void 0:Q.source},description:{story:`全页覆盖模式 — 覆盖整个视口并添加毛玻璃遮罩\r
适合页面级或路由切换的加载状态`,...(X=(U=o.parameters)==null?void 0:U.docs)==null?void 0:X.description}}};var Y,Z,$,ee,se;c.parameters={...c.parameters,docs:{...(Y=c.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <div className="flex items-end gap-8">\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="sm" />\r
        <span className="text-xs text-text-muted">sm</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="md" />\r
        <span className="text-xs text-text-muted">md</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="lg" />\r
        <span className="text-xs text-text-muted">lg</span>\r
      </div>\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '三种尺寸（sm / md / lg）并列对比。'
      }
    }
  }
}`,...($=(Z=c.parameters)==null?void 0:Z.docs)==null?void 0:$.source},description:{story:"三种尺寸并列对比",...(se=(ee=c.parameters)==null?void 0:ee.docs)==null?void 0:se.description}}};var re,ae,te,ie,ne;m.parameters={...m.parameters,docs:{...(re=m.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <div className="flex items-end gap-8">\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="sm" label="小" />\r
        <span className="text-xs text-text-muted">sm</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="md" label="中" />\r
        <span className="text-xs text-text-muted">md</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <LoadingSpinner size="lg" label="大" />\r
        <span className="text-xs text-text-muted">lg</span>\r
      </div>\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '带提示文字时三种尺寸的视觉效果对比。'
      }
    }
  }
}`,...(te=(ae=m.parameters)==null?void 0:ae.docs)==null?void 0:te.source},description:{story:"带文字的尺寸对比",...(ne=(ie=m.parameters)==null?void 0:ie.docs)==null?void 0:ne.description}}};const Ne=["Small","Medium","Large","SmallWithLabel","MediumWithLabel","LargeWithLabel","FullPage","SizeComparison","WithLabelComparison"];export{o as FullPage,t as Large,l as LargeWithLabel,a as Medium,n as MediumWithLabel,c as SizeComparison,r as Small,i as SmallWithLabel,m as WithLabelComparison,Ne as __namedExportsOrder,fe as default};
