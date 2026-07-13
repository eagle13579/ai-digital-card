import{r as n,j as s}from"./iframe-BgyFVukn.js";import{c as p}from"./clsx-B-dksMZM.js";import{c as E}from"./createLucideIcon-C5yOfbJT.js";import{C as ps}from"./circle-check-BaVO5NVY.js";import{X as ds}from"./x-CLZ8N8iQ.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const us=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12",key:"1pkeuh"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16",key:"4dfq90"}]],V=E("circle-alert",us);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ms=[["path",{d:"M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z",key:"1rqfz7"}],["path",{d:"M14 2v4a2 2 0 0 0 2 2h4",key:"tnqrlb"}]],fs=E("file",ms);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gs=[["path",{d:"M12 3v12",key:"1x0j5s"}],["path",{d:"m17 8-5-5-5 5",key:"7q97r8"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",key:"ih7n3h"}]],W=E("upload",gs),xs="拖拽文件到此处，或点击上传";function R(r){return r<1024?`${r} B`:r<1024*1024?`${(r/1024).toFixed(1)} KB`:`${(r/(1024*1024)).toFixed(1)} MB`}function hs(r){return r.startsWith("image/")?"text-purple-500":r.includes("pdf")?"text-rose-500":r.includes("sheet")||r.includes("excel")?"text-emerald-500":r.includes("word")||r.includes("document")?"text-sky-500":"text-slate-500"}function $({files:r=[],onSelect:i,onRemove:k,onRetry:D,accept:l="image/*,.pdf,.doc,.docx",multiple:d=!0,maxSize:t=10*1024*1024,maxFiles:u=10,disabled:a=!1,hint:ts=xs,className:as}){const M=n.useRef(null),[C,U]=n.useState(!1),[I,T]=n.useState(null),q=n.useCallback(e=>{T(null);const o=Array.from(e);if(r.length+o.length>u){T(`最多上传 ${u} 个文件`);return}const c=o.find(cs=>cs.size>t);if(c){T(`文件「${c.name}」超过 ${R(t)} 限制`);return}i==null||i(o)},[r.length,u,t,i]),ns=n.useCallback(e=>{e.preventDefault(),e.stopPropagation(),a||U(!0)},[a]),is=n.useCallback(e=>{e.preventDefault(),e.stopPropagation(),U(!1)},[]),os=n.useCallback(e=>{e.preventDefault(),e.stopPropagation(),U(!1),!a&&e.dataTransfer.files.length>0&&q(e.dataTransfer.files)},[a,q]),P=()=>{var e;a||(e=M.current)==null||e.click()},ls=e=>{e.target.files&&e.target.files.length>0&&q(e.target.files),e.target.value=""};return s.jsxs("div",{className:p("w-full",as),children:[s.jsxs("div",{onDragOver:ns,onDragLeave:is,onDrop:os,onClick:P,className:p("relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200","cursor-pointer",C?"border-primary bg-primary/5 scale-[1.02]":"border-border-light hover:border-primary/50 hover:bg-slate-50",a&&"opacity-50 cursor-not-allowed hover:border-border-light hover:bg-transparent"),role:"button",tabIndex:a?-1:0,"aria-label":"文件上传区域",onKeyDown:e=>{(e.key==="Enter"||e.key===" ")&&P()},children:[s.jsx("input",{ref:M,type:"file",accept:l,multiple:d,disabled:a,onChange:ls,className:"hidden","aria-hidden":"true"}),s.jsxs("div",{className:"flex flex-col items-center gap-2",children:[s.jsx("div",{className:p("w-14 h-14 rounded-2xl flex items-center justify-center transition-colors",C?"bg-primary/15":"bg-slate-100"),children:s.jsx(W,{className:p("w-6 h-6",C?"text-primary":"text-text-muted")})}),s.jsxs("div",{children:[s.jsx("p",{className:"text-sm font-medium text-on-surface",children:C?"释放以上传文件":ts}),s.jsxs("p",{className:"text-xs text-text-muted mt-1",children:["支持 ",l.replace(/,/g,"、"),"，单个不超过 ",R(t)]})]})]})]}),I&&s.jsxs("div",{className:"mt-2 flex items-center gap-1.5 text-xs text-error",children:[s.jsx(V,{className:"w-3.5 h-3.5"}),s.jsx("span",{children:I})]}),r.length>0&&s.jsx("ul",{className:"mt-4 space-y-2",children:r.map((e,o)=>s.jsxs("li",{className:"flex items-center gap-3 p-3 bg-surface rounded-xl border border-border-light",children:[s.jsx("div",{className:p("w-10 h-10 rounded-xl flex items-center justify-center shrink-0",e.status==="error"?"bg-error/10":"bg-slate-50"),children:e.status==="success"?s.jsx(ps,{className:"w-5 h-5 text-success"}):e.status==="error"?s.jsx(V,{className:"w-5 h-5 text-error"}):s.jsx(fs,{className:p("w-5 h-5",hs(e.file.type))})}),s.jsxs("div",{className:"flex-1 min-w-0",children:[s.jsx("p",{className:"text-sm font-medium text-on-surface truncate",children:e.file.name}),s.jsxs("p",{className:"text-xs text-text-muted",children:[R(e.file.size),e.status==="uploading"&&e.progress!==void 0&&s.jsxs("span",{className:"ml-2",children:["上传中 ",e.progress,"%"]}),e.status==="success"&&s.jsx("span",{className:"ml-2 text-success",children:"上传成功"}),e.status==="error"&&s.jsx("span",{className:"ml-2 text-error",children:e.error||"上传失败"})]}),e.status==="uploading"&&e.progress!==void 0&&s.jsx("div",{className:"mt-1.5 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden",children:s.jsx("div",{className:"h-full bg-primary rounded-full transition-all duration-300",style:{width:`${e.progress}%`}})})]}),s.jsxs("div",{className:"flex items-center gap-1 shrink-0",children:[e.status==="error"&&D&&s.jsx("button",{onClick:c=>{c.stopPropagation(),D(o)},className:"p-1.5 rounded-lg text-text-muted hover:text-primary hover:bg-primary/10 transition-colors","aria-label":"重试上传",title:"重试",children:s.jsx(W,{className:"w-4 h-4"})}),k&&s.jsx("button",{onClick:c=>{c.stopPropagation(),k(o)},className:"p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error/10 transition-colors","aria-label":"移除文件",title:"移除",children:s.jsx(ds,{className:"w-4 h-4"})})]})]},`${e.file.name}-${o}`))})]})}$.__docgenInfo={description:`UploadZone — 拖拽上传区域组件\r
\r
支持拖拽选择/点击选择、状态管理、文件预览、错误提示`,methods:[],displayName:"UploadZone",props:{files:{required:!1,tsType:{name:"Array",elements:[{name:"UploadedFile"}],raw:"UploadedFile[]"},description:"已上传文件列表",defaultValue:{value:"[]",computed:!1}},onSelect:{required:!1,tsType:{name:"signature",type:"function",raw:"(files: File[]) => void",signature:{arguments:[{type:{name:"Array",elements:[{name:"File"}],raw:"File[]"},name:"files"}],return:{name:"void"}}},description:"文件选择回调"},onRemove:{required:!1,tsType:{name:"signature",type:"function",raw:"(index: number) => void",signature:{arguments:[{type:{name:"number"},name:"index"}],return:{name:"void"}}},description:"移除文件回调"},onRetry:{required:!1,tsType:{name:"signature",type:"function",raw:"(index: number) => void",signature:{arguments:[{type:{name:"number"},name:"index"}],return:{name:"void"}}},description:"重试回调"},accept:{required:!1,tsType:{name:"string"},description:"接受的文件类型（同 input accept 属性）",defaultValue:{value:"'image/*,.pdf,.doc,.docx'",computed:!1}},multiple:{required:!1,tsType:{name:"boolean"},description:"多文件上传",defaultValue:{value:"true",computed:!1}},maxSize:{required:!1,tsType:{name:"number"},description:"最大文件大小（字节）",defaultValue:{value:"10 * 1024 * 1024",computed:!1}},maxFiles:{required:!1,tsType:{name:"number"},description:"最大文件数量",defaultValue:{value:"10",computed:!1}},disabled:{required:!1,tsType:{name:"boolean"},description:"禁用",defaultValue:{value:"false",computed:!1}},hint:{required:!1,tsType:{name:"string"},description:"自定义提示文字",defaultValue:{value:"'拖拽文件到此处，或点击上传'",computed:!1}},className:{required:!1,tsType:{name:"string"},description:"自定义类名"}}};const Ns={title:"Components/UploadZone",component:$,parameters:{layout:"padded",docs:{description:{component:"文件上传区域组件。支持拖拽上传和点击选择，提供文件列表预览、上传状态管理（idle/uploading/success/error）、进度条、大小校验和文件数量限制。"}}},argTypes:{accept:{control:"text",description:"接受的文件类型（同 input accept）"},multiple:{control:"boolean",description:"是否允许多文件上传"},maxSize:{control:"number",description:"最大文件大小（字节）"},maxFiles:{control:"number",description:"最大文件数量"},disabled:{control:"boolean",description:"禁用上传"},hint:{control:"text",description:"自定义提示文字"},onSelect:{action:"onSelect",description:"文件选择回调"},onRemove:{action:"onRemove",description:"移除文件回调"},onRetry:{action:"onRetry",description:"重试回调"}}},m={args:{files:[]}},f={args:{files:[],hint:"拖拽名片图片或证件扫描件到此处"}},g={args:{files:[],multiple:!1,hint:"请选择一张名片图片（仅单文件）"}},x={args:{files:[{file:new File([""],"business_card_front.png",{type:"image/png"}),status:"selected"}]}},h={args:{files:[{file:new File([""],"business_card_front.png",{type:"image/png"}),status:"selected"},{file:new File([""],"business_card_back.png",{type:"image/png"}),status:"selected"},{file:new File([""],"logo.svg",{type:"image/svg+xml"}),status:"selected"}]}},y={args:{files:[{file:new File([""],"business_card.pdf",{type:"application/pdf"}),status:"uploading",progress:45}]}},v={args:{files:[{file:new File([""],"photo.png",{type:"image/png"}),status:"success"},{file:new File([""],"document.pdf",{type:"application/pdf"}),status:"uploading",progress:72},{file:new File([""],"large-file.png",{type:"image/png"}),status:"error",error:"文件大小超过限制"}]}},F={args:{files:[{file:new File([""],"profile_photo.jpg",{type:"image/jpeg"}),status:"success"}]}},b={args:{files:[{file:new File([""],"corrupted_file.png",{type:"image/png"}),status:"error",error:"文件格式不支持"}]}},w={args:{files:[],disabled:!0}},j={args:{files:[{file:new File([""],"uploaded_doc.pdf",{type:"application/pdf"}),status:"success"}],disabled:!0}},N={args:{files:[{file:new File([""],"file-1.pdf",{type:"application/pdf"}),status:"selected"},{file:new File([""],"file-2.pdf",{type:"application/pdf"}),status:"selected"},{file:new File([""],"file-3.pdf",{type:"application/pdf"}),status:"selected"}],maxFiles:3,hint:"已满 3/3，无法继续添加"}},_={args:{files:[{file:new File([""],"document.pdf",{type:"application/pdf"}),status:"selected"}]}},S={render:()=>{const[r,i]=n.useState([]),k=l=>{const d=l.map(t=>({file:t,status:"selected"}));i(t=>[...t,...d])},D=l=>{i(d=>d.filter((t,u)=>u!==l))};return s.jsxs("div",{className:"max-w-lg mx-auto",children:[s.jsx($,{files:r,onSelect:k,onRemove:D,maxFiles:5}),r.length>0&&s.jsxs("p",{className:"text-xs text-text-muted mt-3 text-center",children:["共 ",r.length," 个文件，点击右侧 ✕ 移除"]})]})},parameters:{docs:{description:{story:"完整可交互演示。拖拽或点击上传文件，可移除已选文件，体验完整上传流程。"}}}};var A,Z,H,O,z;m.parameters={...m.parameters,docs:{...(A=m.parameters)==null?void 0:A.docs,source:{originalSource:`{
  args: {
    files: []
  }
}`,...(H=(Z=m.parameters)==null?void 0:Z.docs)==null?void 0:H.source},description:{story:"空状态 — 默认提示",...(z=(O=m.parameters)==null?void 0:O.docs)==null?void 0:z.description}}};var L,B,K,X,G;f.parameters={...f.parameters,docs:{...(L=f.parameters)==null?void 0:L.docs,source:{originalSource:`{
  args: {
    files: [],
    hint: '拖拽名片图片或证件扫描件到此处'
  }
}`,...(K=(B=f.parameters)==null?void 0:B.docs)==null?void 0:K.source},description:{story:"空状态 — 自定义提示语",...(G=(X=f.parameters)==null?void 0:X.docs)==null?void 0:G.description}}};var J,Q,Y,ee,se;g.parameters={...g.parameters,docs:{...(J=g.parameters)==null?void 0:J.docs,source:{originalSource:`{
  args: {
    files: [],
    multiple: false,
    hint: '请选择一张名片图片（仅单文件）'
  }
}`,...(Y=(Q=g.parameters)==null?void 0:Q.docs)==null?void 0:Y.source},description:{story:"仅单文件上传",...(se=(ee=g.parameters)==null?void 0:ee.docs)==null?void 0:se.description}}};var re,te,ae,ne,ie;x.parameters={...x.parameters,docs:{...(re=x.parameters)==null?void 0:re.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'business_card_front.png', {
        type: 'image/png'
      }),
      status: 'selected'
    }]
  }
}`,...(ae=(te=x.parameters)==null?void 0:te.docs)==null?void 0:ae.source},description:{story:"已选择文件",...(ie=(ne=x.parameters)==null?void 0:ne.docs)==null?void 0:ie.description}}};var oe,le,ce,pe,de;h.parameters={...h.parameters,docs:{...(oe=h.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'business_card_front.png', {
        type: 'image/png'
      }),
      status: 'selected'
    }, {
      file: new File([''], 'business_card_back.png', {
        type: 'image/png'
      }),
      status: 'selected'
    }, {
      file: new File([''], 'logo.svg', {
        type: 'image/svg+xml'
      }),
      status: 'selected'
    }]
  }
}`,...(ce=(le=h.parameters)==null?void 0:le.docs)==null?void 0:ce.source},description:{story:"多个已选择文件",...(de=(pe=h.parameters)==null?void 0:pe.docs)==null?void 0:de.description}}};var ue,me,fe,ge,xe;y.parameters={...y.parameters,docs:{...(ue=y.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'business_card.pdf', {
        type: 'application/pdf'
      }),
      status: 'uploading',
      progress: 45
    }]
  }
}`,...(fe=(me=y.parameters)==null?void 0:me.docs)==null?void 0:fe.source},description:{story:"上传中 — 显示进度条",...(xe=(ge=y.parameters)==null?void 0:ge.docs)==null?void 0:xe.description}}};var he,ye,ve,Fe,be;v.parameters={...v.parameters,docs:{...(he=v.parameters)==null?void 0:he.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'photo.png', {
        type: 'image/png'
      }),
      status: 'success'
    }, {
      file: new File([''], 'document.pdf', {
        type: 'application/pdf'
      }),
      status: 'uploading',
      progress: 72
    }, {
      file: new File([''], 'large-file.png', {
        type: 'image/png'
      }),
      status: 'error',
      error: '文件大小超过限制'
    }]
  }
}`,...(ve=(ye=v.parameters)==null?void 0:ye.docs)==null?void 0:ve.source},description:{story:"多文件混合状态",...(be=(Fe=v.parameters)==null?void 0:Fe.docs)==null?void 0:be.description}}};var we,je,Ne,_e,Se;F.parameters={...F.parameters,docs:{...(we=F.parameters)==null?void 0:we.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'profile_photo.jpg', {
        type: 'image/jpeg'
      }),
      status: 'success'
    }]
  }
}`,...(Ne=(je=F.parameters)==null?void 0:je.docs)==null?void 0:Ne.source},description:{story:"上传成功",...(Se=(_e=F.parameters)==null?void 0:_e.docs)==null?void 0:Se.description}}};var ke,De,Ce,Ue,Te;b.parameters={...b.parameters,docs:{...(ke=b.parameters)==null?void 0:ke.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'corrupted_file.png', {
        type: 'image/png'
      }),
      status: 'error',
      error: '文件格式不支持'
    }]
  }
}`,...(Ce=(De=b.parameters)==null?void 0:De.docs)==null?void 0:Ce.source},description:{story:"上传错误",...(Te=(Ue=b.parameters)==null?void 0:Ue.docs)==null?void 0:Te.description}}};var qe,Re,Ee,$e,Me;w.parameters={...w.parameters,docs:{...(qe=w.parameters)==null?void 0:qe.docs,source:{originalSource:`{
  args: {
    files: [],
    disabled: true
  }
}`,...(Ee=(Re=w.parameters)==null?void 0:Re.docs)==null?void 0:Ee.source},description:{story:"禁用状态",...(Me=($e=w.parameters)==null?void 0:$e.docs)==null?void 0:Me.description}}};var Ie,Pe,Ve,We,Ae;j.parameters={...j.parameters,docs:{...(Ie=j.parameters)==null?void 0:Ie.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'uploaded_doc.pdf', {
        type: 'application/pdf'
      }),
      status: 'success'
    }],
    disabled: true
  }
}`,...(Ve=(Pe=j.parameters)==null?void 0:Pe.docs)==null?void 0:Ve.source},description:{story:"禁用 + 已有文件",...(Ae=(We=j.parameters)==null?void 0:We.docs)==null?void 0:Ae.description}}};var Ze,He,Oe,ze,Le;N.parameters={...N.parameters,docs:{...(Ze=N.parameters)==null?void 0:Ze.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'file-1.pdf', {
        type: 'application/pdf'
      }),
      status: 'selected'
    }, {
      file: new File([''], 'file-2.pdf', {
        type: 'application/pdf'
      }),
      status: 'selected'
    }, {
      file: new File([''], 'file-3.pdf', {
        type: 'application/pdf'
      }),
      status: 'selected'
    }],
    maxFiles: 3,
    hint: '已满 3/3，无法继续添加'
  }
}`,...(Oe=(He=N.parameters)==null?void 0:He.docs)==null?void 0:Oe.source},description:{story:"达到文件上限",...(Le=(ze=N.parameters)==null?void 0:ze.docs)==null?void 0:Le.description}}};var Be,Ke,Xe,Ge,Je;_.parameters={..._.parameters,docs:{...(Be=_.parameters)==null?void 0:Be.docs,source:{originalSource:`{
  args: {
    files: [{
      file: new File([''], 'document.pdf', {
        type: 'application/pdf'
      }),
      status: 'selected'
    }]
  }
}`,...(Xe=(Ke=_.parameters)==null?void 0:Ke.docs)==null?void 0:Xe.source},description:{story:"PDF 文件类型",...(Je=(Ge=_.parameters)==null?void 0:Ge.docs)==null?void 0:Je.description}}};var Qe,Ye,es,ss,rs;S.parameters={...S.parameters,docs:{...(Qe=S.parameters)==null?void 0:Qe.docs,source:{originalSource:`{
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const handleSelect = (incoming: File[]) => {
      const newFiles: UploadedFile[] = incoming.map(f => ({
        file: f,
        status: 'selected' as const
      }));
      setFiles(prev => [...prev, ...newFiles]);
    };
    const handleRemove = (idx: number) => {
      setFiles(prev => prev.filter((_, i) => i !== idx));
    };
    return <div className="max-w-lg mx-auto">\r
        <UploadZone files={files} onSelect={handleSelect} onRemove={handleRemove} maxFiles={5} />\r
        {files.length > 0 && <p className="text-xs text-text-muted mt-3 text-center">\r
            共 {files.length} 个文件，点击右侧 ✕ 移除\r
          </p>}\r
      </div>;
  },
  parameters: {
    docs: {
      description: {
        story: '完整可交互演示。拖拽或点击上传文件，可移除已选文件，体验完整上传流程。'
      }
    }
  }
}`,...(es=(Ye=S.parameters)==null?void 0:Ye.docs)==null?void 0:es.source},description:{story:`可交互的上传演示\r
可选择文件并管理上传列表`,...(rs=(ss=S.parameters)==null?void 0:ss.docs)==null?void 0:rs.description}}};const _s=["Empty","EmptyCustomHint","SingleFile","WithSelectedFile","WithMultipleFiles","Uploading","MixedStatus","UploadSuccess","UploadError","Disabled","DisabledWithFiles","MaxFilesReached","PdfFile","Interactive"];export{w as Disabled,j as DisabledWithFiles,m as Empty,f as EmptyCustomHint,S as Interactive,N as MaxFilesReached,v as MixedStatus,_ as PdfFile,g as SingleFile,b as UploadError,F as UploadSuccess,y as Uploading,h as WithMultipleFiles,x as WithSelectedFile,_s as __namedExportsOrder,Ns as default};
