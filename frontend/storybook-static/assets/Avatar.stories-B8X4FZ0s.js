import{j as e}from"./iframe-BgyFVukn.js";import{c as o}from"./clsx-B-dksMZM.js";import{U as ls}from"./user-kvdGHbHj.js";import"./preload-helper-Dp1pzeXC.js";import"./createLucideIcon-C5yOfbJT.js";const A={sm:"w-8 h-8 text-xs",md:"w-10 h-10 text-sm",lg:"w-14 h-14 text-base",xl:"w-20 h-20 text-xl"},L={sm:"w-2 h-2 right-0 bottom-0",md:"w-2.5 h-2.5 right-0 bottom-0",lg:"w-3 h-3 right-0.5 bottom-0.5",xl:"w-3.5 h-3.5 right-0.5 bottom-0.5"},ms={online:"bg-emerald-500",offline:"bg-slate-400",away:"bg-amber-400"};function ds(s){const t=s.trim().split(/\s+/);return t.length>=2?(t[0][0]+t[1][0]).toUpperCase():s.slice(0,2).toUpperCase()}function ps(s){const t=["bg-sky-500","bg-purple-500","bg-emerald-500","bg-amber-500","bg-rose-500","bg-indigo-500","bg-teal-500","bg-pink-500","bg-cyan-500","bg-orange-500"];let r=0;for(let a=0;a<s.length;a++)r=s.charCodeAt(a)+((r<<5)-r);return t[Math.abs(r)%t.length]}function n({src:s,alt:t="",name:r,size:a="md",shape:C="circle",status:w,className:is}){var U;const j=C==="circle"?"rounded-full":"rounded-xl",cs=C==="circle"?L[a]:(U=L[a])==null?void 0:U.replace("right-0","right-0.5").replace("bottom-0","bottom-0.5");return e.jsxs("div",{className:o("relative inline-flex shrink-0",is),children:[s?e.jsx("img",{src:s,alt:t||r||"avatar",className:o("object-cover",A[a],j,"ring-2 ring-white")}):r?e.jsx("div",{className:o("flex items-center justify-center font-bold text-white",A[a],j,ps(r)),"aria-label":r,children:ds(r)}):e.jsx("div",{className:o("flex items-center justify-center bg-slate-200 text-slate-400",A[a],j),children:e.jsx(ls,{className:a==="sm"?"w-4 h-4":a==="md"?"w-5 h-5":a==="lg"?"w-7 h-7":"w-10 h-10"})}),w&&e.jsx("span",{className:o("absolute block rounded-full ring-2 ring-white",cs,ms[w]),"aria-label":w})]})}n.__docgenInfo={description:`Avatar — 用户头像组件\r
\r
优先展示图片；无图片但有姓名时展示首字母色块；兜底展示 User 图标。\r
支持在线/离线/离开状态指示器。`,methods:[],displayName:"Avatar",props:{src:{required:!1,tsType:{name:"string"},description:"头像图片 URL（可选）"},alt:{required:!1,tsType:{name:"string"},description:"替代文本",defaultValue:{value:"''",computed:!1}},name:{required:!1,tsType:{name:"string"},description:"用户姓名（用于生成首字母兜底）"},size:{required:!1,tsType:{name:"union",raw:"'sm' | 'md' | 'lg' | 'xl'",elements:[{name:"literal",value:"'sm'"},{name:"literal",value:"'md'"},{name:"literal",value:"'lg'"},{name:"literal",value:"'xl'"}]},description:"尺寸",defaultValue:{value:"'md'",computed:!1}},shape:{required:!1,tsType:{name:"union",raw:"'circle' | 'rounded'",elements:[{name:"literal",value:"'circle'"},{name:"literal",value:"'rounded'"}]},description:"形状 — circle（默认）| rounded（圆角方形）",defaultValue:{value:"'circle'",computed:!1}},status:{required:!1,tsType:{name:"union",raw:"'online' | 'offline' | 'away'",elements:[{name:"literal",value:"'online'"},{name:"literal",value:"'offline'"},{name:"literal",value:"'away'"}]},description:"在线状态指示器"},className:{required:!1,tsType:{name:"string"},description:"自定义类名"}}};const vs={title:"Components/Avatar",component:n,parameters:{layout:"centered",docs:{description:{component:"用户头像组件。支持三种展示模式：图片（优先）、姓名首字母色块（兜底）、默认 User 图标（无数据时）。提供 4 种尺寸和 online/offline/away 状态指示器。"}}},argTypes:{src:{control:"text",description:"头像图片 URL"},alt:{control:"text",description:"替代文本"},name:{control:"text",description:"用户姓名（用于首字母兜底）"},size:{control:"select",options:["sm","md","lg","xl"],description:"头像尺寸"},shape:{control:"select",options:["circle","rounded"],description:"形状 — 圆形或圆角方形"},status:{control:"select",options:[void 0,"online","offline","away"],description:"在线状态指示器"}}},i={args:{}},c={args:{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=default",alt:"用户头像"}},l={args:{name:"张明"}},m={args:{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming",name:"张明",alt:"张明的头像"}},d={args:{name:"张明",size:"sm"}},p={args:{name:"张明",size:"md"}},g={args:{name:"张明",size:"lg"}},u={args:{name:"张明",size:"xl"}},x={args:{name:"李华",size:"lg",shape:"rounded"}},f={args:{name:"张明",size:"lg",status:"online"}},h={args:{name:"李华",size:"lg",status:"offline"}},v={args:{name:"王芳",size:"lg",status:"away"}},y={args:{name:"张",size:"xl"},parameters:{docs:{description:{story:"单字姓名（姓）— 显示前两个字符。"}}}},z={args:{name:"亚历山大·伊万诺维奇·彼得罗夫",size:"xl"},parameters:{docs:{description:{story:"长姓名 — 取前两个单词的首字母（约→彼）。"}}}},N={args:{name:"John Doe",size:"lg"}},b={render:()=>e.jsx("div",{className:"flex items-end gap-6",children:["sm","md","lg","xl"].map(s=>e.jsxs("div",{className:"flex flex-col items-center gap-3",children:[e.jsx(n,{name:"张明",size:s,status:"online"}),e.jsx(n,{name:"李华",size:s,status:"offline"}),e.jsx(n,{name:"王芳",size:s,status:"away"}),e.jsx("span",{className:"text-xs text-text-muted mt-1",children:s})]},s))}),parameters:{docs:{description:{story:"四种尺寸（sm / md / lg / xl）加上三种状态（online / offline / away）的完整对比矩阵。"}}}},S={render:()=>e.jsxs("div",{className:"flex items-end gap-8",children:[e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(n,{size:"lg"}),e.jsx("span",{className:"text-xs text-text-muted",children:"默认图标"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(n,{name:"张明",size:"lg"}),e.jsx("span",{className:"text-xs text-text-muted",children:"首字母"})]}),e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx(n,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming",name:"张明",size:"lg"}),e.jsx("span",{className:"text-xs text-text-muted",children:"图片"})]})]}),parameters:{docs:{description:{story:"三种兜底层级并列对比：默认图标 → 首字母色块 → 图片。"}}}};var M,T,W,q,D;i.parameters={...i.parameters,docs:{...(M=i.parameters)==null?void 0:M.docs,source:{originalSource:`{
  args: {}
}`,...(W=(T=i.parameters)==null?void 0:T.docs)==null?void 0:W.source},description:{story:"无数据 — 显示默认 User 图标",...(D=(q=i.parameters)==null?void 0:q.docs)==null?void 0:D.description}}};var I,k,O,R,E;c.parameters={...c.parameters,docs:{...(I=c.parameters)==null?void 0:I.docs,source:{originalSource:`{
  args: {
    src: 'https://api.dicebear.com/7.x/avataaars/svg?seed=default',
    alt: '用户头像'
  }
}`,...(O=(k=c.parameters)==null?void 0:k.docs)==null?void 0:O.source},description:{story:"仅头像图片",...(E=(R=c.parameters)==null?void 0:R.docs)==null?void 0:E.description}}};var _,V,J,X,F;l.parameters={...l.parameters,docs:{...(_=l.parameters)==null?void 0:_.docs,source:{originalSource:`{
  args: {
    name: '张明'
  }
}`,...(J=(V=l.parameters)==null?void 0:V.docs)==null?void 0:J.source},description:{story:"仅姓名 — 显示首字母色块",...(F=(X=l.parameters)==null?void 0:X.docs)==null?void 0:F.description}}};var P,B,G,H,K;m.parameters={...m.parameters,docs:{...(P=m.parameters)==null?void 0:P.docs,source:{originalSource:`{
  args: {
    src: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming',
    name: '张明',
    alt: '张明的头像'
  }
}`,...(G=(B=m.parameters)==null?void 0:B.docs)==null?void 0:G.source},description:{story:"姓名 + 图片（图片优先）",...(K=(H=m.parameters)==null?void 0:H.docs)==null?void 0:K.description}}};var Q,Y,Z,$,ee;d.parameters={...d.parameters,docs:{...(Q=d.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  args: {
    name: '张明',
    size: 'sm'
  }
}`,...(Z=(Y=d.parameters)==null?void 0:Y.docs)==null?void 0:Z.source},description:{story:"小尺寸 (sm) — 32px",...(ee=($=d.parameters)==null?void 0:$.docs)==null?void 0:ee.description}}};var se,ae,re,te,ne;p.parameters={...p.parameters,docs:{...(se=p.parameters)==null?void 0:se.docs,source:{originalSource:`{
  args: {
    name: '张明',
    size: 'md'
  }
}`,...(re=(ae=p.parameters)==null?void 0:ae.docs)==null?void 0:re.source},description:{story:"中等尺寸 (md) — 40px",...(ne=(te=p.parameters)==null?void 0:te.docs)==null?void 0:ne.description}}};var oe,ie,ce,le,me;g.parameters={...g.parameters,docs:{...(oe=g.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  args: {
    name: '张明',
    size: 'lg'
  }
}`,...(ce=(ie=g.parameters)==null?void 0:ie.docs)==null?void 0:ce.source},description:{story:"大尺寸 (lg) — 56px",...(me=(le=g.parameters)==null?void 0:le.docs)==null?void 0:me.description}}};var de,pe,ge,ue,xe;u.parameters={...u.parameters,docs:{...(de=u.parameters)==null?void 0:de.docs,source:{originalSource:`{
  args: {
    name: '张明',
    size: 'xl'
  }
}`,...(ge=(pe=u.parameters)==null?void 0:pe.docs)==null?void 0:ge.source},description:{story:"超大尺寸 (xl) — 80px",...(xe=(ue=u.parameters)==null?void 0:ue.docs)==null?void 0:xe.description}}};var fe,he,ve,ye,ze;x.parameters={...x.parameters,docs:{...(fe=x.parameters)==null?void 0:fe.docs,source:{originalSource:`{
  args: {
    name: '李华',
    size: 'lg',
    shape: 'rounded'
  }
}`,...(ve=(he=x.parameters)==null?void 0:he.docs)==null?void 0:ve.source},description:{story:"圆角方形 (rounded)",...(ze=(ye=x.parameters)==null?void 0:ye.docs)==null?void 0:ze.description}}};var Ne,be,Se,we,je;f.parameters={...f.parameters,docs:{...(Ne=f.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
  args: {
    name: '张明',
    size: 'lg',
    status: 'online'
  }
}`,...(Se=(be=f.parameters)==null?void 0:be.docs)==null?void 0:Se.source},description:{story:"在线状态指示器",...(je=(we=f.parameters)==null?void 0:we.docs)==null?void 0:je.description}}};var Ae,Ce,Ue,Le,Me;h.parameters={...h.parameters,docs:{...(Ae=h.parameters)==null?void 0:Ae.docs,source:{originalSource:`{
  args: {
    name: '李华',
    size: 'lg',
    status: 'offline'
  }
}`,...(Ue=(Ce=h.parameters)==null?void 0:Ce.docs)==null?void 0:Ue.source},description:{story:"离线状态指示器",...(Me=(Le=h.parameters)==null?void 0:Le.docs)==null?void 0:Me.description}}};var Te,We,qe,De,Ie;v.parameters={...v.parameters,docs:{...(Te=v.parameters)==null?void 0:Te.docs,source:{originalSource:`{
  args: {
    name: '王芳',
    size: 'lg',
    status: 'away'
  }
}`,...(qe=(We=v.parameters)==null?void 0:We.docs)==null?void 0:qe.source},description:{story:"离开状态指示器",...(Ie=(De=v.parameters)==null?void 0:De.docs)==null?void 0:Ie.description}}};var ke,Oe,Re,Ee,_e;y.parameters={...y.parameters,docs:{...(ke=y.parameters)==null?void 0:ke.docs,source:{originalSource:`{
  args: {
    name: '张',
    size: 'xl'
  },
  parameters: {
    docs: {
      description: {
        story: '单字姓名（姓）— 显示前两个字符。'
      }
    }
  }
}`,...(Re=(Oe=y.parameters)==null?void 0:Oe.docs)==null?void 0:Re.source},description:{story:"单字姓名",...(_e=(Ee=y.parameters)==null?void 0:Ee.docs)==null?void 0:_e.description}}};var Ve,Je,Xe,Fe,Pe;z.parameters={...z.parameters,docs:{...(Ve=z.parameters)==null?void 0:Ve.docs,source:{originalSource:`{
  args: {
    name: '亚历山大·伊万诺维奇·彼得罗夫',
    size: 'xl'
  },
  parameters: {
    docs: {
      description: {
        story: '长姓名 — 取前两个单词的首字母（约→彼）。'
      }
    }
  }
}`,...(Xe=(Je=z.parameters)==null?void 0:Je.docs)==null?void 0:Xe.source},description:{story:"长姓名",...(Pe=(Fe=z.parameters)==null?void 0:Fe.docs)==null?void 0:Pe.description}}};var Be,Ge,He,Ke,Qe;N.parameters={...N.parameters,docs:{...(Be=N.parameters)==null?void 0:Be.docs,source:{originalSource:`{
  args: {
    name: 'John Doe',
    size: 'lg'
  }
}`,...(He=(Ge=N.parameters)==null?void 0:Ge.docs)==null?void 0:He.source},description:{story:"英文姓名",...(Qe=(Ke=N.parameters)==null?void 0:Ke.docs)==null?void 0:Qe.description}}};var Ye,Ze,$e,es,ss;b.parameters={...b.parameters,docs:{...(Ye=b.parameters)==null?void 0:Ye.docs,source:{originalSource:`{
  render: () => <div className="flex items-end gap-6">\r
      {(['sm', 'md', 'lg', 'xl'] as const).map(size => <div key={size} className="flex flex-col items-center gap-3">\r
          <Avatar name="张明" size={size} status="online" />\r
          <Avatar name="李华" size={size} status="offline" />\r
          <Avatar name="王芳" size={size} status="away" />\r
          <span className="text-xs text-text-muted mt-1">{size}</span>\r
        </div>)}\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '四种尺寸（sm / md / lg / xl）加上三种状态（online / offline / away）的完整对比矩阵。'
      }
    }
  }
}`,...($e=(Ze=b.parameters)==null?void 0:Ze.docs)==null?void 0:$e.source},description:{story:"所有尺寸 + 状态对比",...(ss=(es=b.parameters)==null?void 0:es.docs)==null?void 0:ss.description}}};var as,rs,ts,ns,os;S.parameters={...S.parameters,docs:{...(as=S.parameters)==null?void 0:as.docs,source:{originalSource:`{
  render: () => <div className="flex items-end gap-8">\r
      <div className="flex flex-col items-center gap-2">\r
        <Avatar size="lg" />\r
        <span className="text-xs text-text-muted">默认图标</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <Avatar name="张明" size="lg" />\r
        <span className="text-xs text-text-muted">首字母</span>\r
      </div>\r
      <div className="flex flex-col items-center gap-2">\r
        <Avatar src="https://api.dicebear.com/7.x/avataaars/svg?seed=zhangming" name="张明" size="lg" />\r
        <span className="text-xs text-text-muted">图片</span>\r
      </div>\r
    </div>,
  parameters: {
    docs: {
      description: {
        story: '三种兜底层级并列对比：默认图标 → 首字母色块 → 图片。'
      }
    }
  }
}`,...(ts=(rs=S.parameters)==null?void 0:rs.docs)==null?void 0:ts.source},description:{story:"三种展示模式对比",...(os=(ns=S.parameters)==null?void 0:ns.docs)==null?void 0:os.description}}};const ys=["Default","WithImage","WithName","ImageWithName","SizeSmall","SizeMedium","SizeLarge","SizeXLarge","RoundedShape","Online","Offline","Away","SingleCharacterName","LongName","EnglishName","AllSizesWithStatus","DisplayModes"];export{b as AllSizesWithStatus,v as Away,i as Default,S as DisplayModes,N as EnglishName,m as ImageWithName,z as LongName,h as Offline,f as Online,x as RoundedShape,y as SingleCharacterName,g as SizeLarge,p as SizeMedium,d as SizeSmall,u as SizeXLarge,c as WithImage,l as WithName,ys as __namedExportsOrder,vs as default};
