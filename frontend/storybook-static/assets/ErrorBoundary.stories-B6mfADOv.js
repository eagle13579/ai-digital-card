import{r as M,j as r,u as z}from"./iframe-BgyFVukn.js";import{T as D,R as J}from"./triangle-alert-COz0z5ux.js";import{c as q}from"./createLucideIcon-C5yOfbJT.js";import"./preload-helper-Dp1pzeXC.js";/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const L=[["path",{d:"m12 19-7-7 7-7",key:"1l729n"}],["path",{d:"M19 12H5",key:"x3x0zl"}]],W=q("arrow-left",L);/**
 * @license lucide-react v0.546.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const O=[["path",{d:"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8",key:"5wwlr5"}],["path",{d:"M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",key:"r6nss1"}]],$=q("house",O);class o extends M.Component{constructor(e){super(e),this.handleRetry=()=>{this.setState({hasError:!1,error:null,errorInfo:null})},this.handleGoHome=()=>{this.setState({hasError:!1,error:null,errorInfo:null}),window.location.href="/"},this.handleGoBack=()=>{this.setState({hasError:!1,error:null,errorInfo:null}),window.history.back()},this.state={hasError:!1,error:null,errorInfo:null}}static getDerivedStateFromError(e){return{hasError:!0,error:e}}componentDidCatch(e,a){this.setState({errorInfo:a}),console.error("[ErrorBoundary] Caught:",e,a),this.props.onError&&this.props.onError(e,a)}render(){return this.state.hasError?this.props.fallback?this.props.fallback:r.jsx(K,{error:this.state.error,onRetry:this.handleRetry,onGoBack:this.handleGoBack,onGoHome:this.handleGoHome}):this.props.children}}function K({error:t,onRetry:e,onGoBack:a,onGoHome:A}){const s=z();return r.jsx("div",{className:"min-h-screen bg-neutral-bg flex items-center justify-center p-4",children:r.jsxs("div",{className:"bg-surface rounded-2xl shadow-card border border-border-light max-w-md w-full p-8 text-center",children:[r.jsx("div",{className:"w-20 h-20 mx-auto mb-5 rounded-full bg-error/10 flex items-center justify-center",children:r.jsx(D,{className:"w-10 h-10 text-error"})}),r.jsx("h2",{className:"text-xl font-bold text-on-surface mb-2",children:s("页面发生异常")}),r.jsx("p",{className:"text-sm text-text-muted mb-6",children:s("很抱歉，页面遇到了意外错误。请尝试刷新或返回。")}),!1,r.jsxs("div",{className:"flex flex-col gap-3",children:[r.jsxs("button",{onClick:e,className:"w-full py-3 px-4 rounded-xl bg-primary text-white font-medium text-sm hover:bg-primary-container transition-colors flex items-center justify-center gap-2",children:[r.jsx(J,{className:"w-4 h-4"}),s("重试")]}),r.jsxs("div",{className:"flex gap-3",children:[r.jsxs("button",{onClick:a,className:"flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2",children:[r.jsx(W,{className:"w-4 h-4"}),s("返回上一页")]}),r.jsxs("button",{onClick:A,className:"flex-1 py-3 px-4 rounded-xl border border-border-light text-on-surface font-medium text-sm hover:bg-slate-50 transition-colors flex items-center justify-center gap-2",children:[r.jsx($,{className:"w-4 h-4"}),s("回到首页")]})]})]}),r.jsx("p",{className:"text-xs text-text-muted mt-6",children:s("如果问题持续存在，请联系技术支持")})]})})}o.__docgenInfo={description:`React 错误边界组件\r
捕获子组件树中的 JavaScript 错误，显示友好的错误页面并提供重试功能`,methods:[{name:"handleRetry",docblock:null,modifiers:[],params:[],returns:{type:{name:"void"}}},{name:"handleGoHome",docblock:null,modifiers:[],params:[],returns:{type:{name:"void"}}},{name:"handleGoBack",docblock:null,modifiers:[],params:[],returns:{type:{name:"void"}}}],displayName:"ErrorBoundary",props:{children:{required:!0,tsType:{name:"ReactNode"},description:""},fallback:{required:!1,tsType:{name:"ReactNode"},description:"自定义 fallback UI（可选）"},onError:{required:!1,tsType:{name:"signature",type:"function",raw:"(error: Error, errorInfo: ErrorInfo) => void",signature:{arguments:[{type:{name:"Error"},name:"error"},{type:{name:"ErrorInfo"},name:"errorInfo"}],return:{name:"void"}}},description:"错误回调（用于日志上报）"}}};function m({shouldThrow:t=!1}){if(t)throw new Error("模拟渲染错误：组件发生未捕获异常！");return r.jsx("div",{className:"text-on-surface",children:"正常渲染的内容 ✅"})}const Y={title:"Components/ErrorBoundary",component:o,parameters:{layout:"centered",docs:{description:{component:"React 错误边界组件。捕获子组件树中的 JavaScript 错误，显示友好的错误页面并提供重试、返回等功能。"}}},argTypes:{fallback:{control:!1,description:"自定义错误回退 UI（ReactNode）"},onError:{action:"onError",description:"错误回调（用于日志上报）"}}},n={render:()=>r.jsx(o,{children:r.jsxs("div",{className:"p-6 bg-surface rounded-2xl border border-border-light max-w-md",children:[r.jsx("p",{className:"text-on-surface font-medium",children:"子组件正常工作"}),r.jsx("p",{className:"text-text-muted text-sm mt-1",children:"这里展示正常内容"})]})})},d={render:()=>r.jsx(o,{children:r.jsx(m,{shouldThrow:!0})})},l={render:()=>r.jsx(o,{fallback:r.jsxs("div",{className:"p-8 bg-amber-50 border border-amber-200 rounded-2xl max-w-md text-center",children:[r.jsx("div",{className:"text-3xl mb-2",children:"⚠️"}),r.jsx("h3",{className:"font-bold text-amber-800 mb-1",children:"自定义错误提示"}),r.jsx("p",{className:"text-sm text-amber-600",children:"发生了错误，但使用了自定义的 fallback UI"})]}),children:r.jsx(m,{shouldThrow:!0})})},c={render:()=>r.jsx(o,{onError:(t,e)=>{console.log("[Storybook] Error logged:",t.message,e)},children:r.jsx(m,{shouldThrow:!0})})},i={render:()=>r.jsxs("div",{className:"space-y-4 max-w-lg",children:[r.jsx(o,{children:r.jsxs("div",{className:"p-4 bg-surface rounded-xl border border-border-light",children:[r.jsx("p",{className:"text-sm font-medium text-emerald-600",children:"✅ 上方边界 - 正常"}),r.jsx("p",{className:"text-xs text-text-muted mt-1",children:"这个 ErrorBoundary 没有问题"})]})}),r.jsx(o,{children:r.jsx(m,{shouldThrow:!0})}),r.jsx(o,{children:r.jsxs("div",{className:"p-4 bg-surface rounded-xl border border-border-light",children:[r.jsx("p",{className:"text-sm font-medium text-emerald-600",children:"✅ 下方边界 - 正常"}),r.jsx("p",{className:"text-xs text-text-muted mt-1",children:"这个 ErrorBoundary 也没有问题"})]})})]})};var u,x,p,h,b;n.parameters={...n.parameters,docs:{...(u=n.parameters)==null?void 0:u.docs,source:{originalSource:`{
  render: () => <ErrorBoundary>\r
      <div className="p-6 bg-surface rounded-2xl border border-border-light max-w-md">\r
        <p className="text-on-surface font-medium">子组件正常工作</p>\r
        <p className="text-text-muted text-sm mt-1">这里展示正常内容</p>\r
      </div>\r
    </ErrorBoundary>
}`,...(p=(x=n.parameters)==null?void 0:x.docs)==null?void 0:p.source},description:{story:"正常状态 — 子组件正常渲染",...(b=(h=n.parameters)==null?void 0:h.docs)==null?void 0:b.description}}};var f,y,g,N,E;d.parameters={...d.parameters,docs:{...(f=d.parameters)==null?void 0:f.docs,source:{originalSource:`{
  render: () => <ErrorBoundary>\r
      <BuggyComponent shouldThrow={true} />\r
    </ErrorBoundary>
}`,...(g=(y=d.parameters)==null?void 0:y.docs)==null?void 0:g.source},description:{story:"触发错误 — 捕获异常并显示 Fallback",...(E=(N=d.parameters)==null?void 0:N.docs)==null?void 0:E.description}}};var j,v,w,k,B;l.parameters={...l.parameters,docs:{...(j=l.parameters)==null?void 0:j.docs,source:{originalSource:`{
  render: () => <ErrorBoundary fallback={<div className="p-8 bg-amber-50 border border-amber-200 rounded-2xl max-w-md text-center">\r
          <div className="text-3xl mb-2">⚠️</div>\r
          <h3 className="font-bold text-amber-800 mb-1">自定义错误提示</h3>\r
          <p className="text-sm text-amber-600">发生了错误，但使用了自定义的 fallback UI</p>\r
        </div>}>\r
      <BuggyComponent shouldThrow={true} />\r
    </ErrorBoundary>
}`,...(w=(v=l.parameters)==null?void 0:v.docs)==null?void 0:w.source},description:{story:"自定义 Fallback",...(B=(k=l.parameters)==null?void 0:k.docs)==null?void 0:B.description}}};var C,T,I,S,R;c.parameters={...c.parameters,docs:{...(C=c.parameters)==null?void 0:C.docs,source:{originalSource:`{
  render: () => <ErrorBoundary onError={(error, errorInfo) => {
    console.log('[Storybook] Error logged:', error.message, errorInfo);
  }}>\r
      <BuggyComponent shouldThrow={true} />\r
    </ErrorBoundary>
}`,...(I=(T=c.parameters)==null?void 0:T.docs)==null?void 0:I.source},description:{story:"错误日志回调",...(R=(S=c.parameters)==null?void 0:S.docs)==null?void 0:R.description}}};var G,_,H,F,U;i.parameters={...i.parameters,docs:{...(G=i.parameters)==null?void 0:G.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 max-w-lg">\r
      <ErrorBoundary>\r
        <div className="p-4 bg-surface rounded-xl border border-border-light">\r
          <p className="text-sm font-medium text-emerald-600">✅ 上方边界 - 正常</p>\r
          <p className="text-xs text-text-muted mt-1">这个 ErrorBoundary 没有问题</p>\r
        </div>\r
      </ErrorBoundary>\r
      <ErrorBoundary>\r
        <BuggyComponent shouldThrow={true} />\r
      </ErrorBoundary>\r
      <ErrorBoundary>\r
        <div className="p-4 bg-surface rounded-xl border border-border-light">\r
          <p className="text-sm font-medium text-emerald-600">✅ 下方边界 - 正常</p>\r
          <p className="text-xs text-text-muted mt-1">这个 ErrorBoundary 也没有问题</p>\r
        </div>\r
      </ErrorBoundary>\r
    </div>
}`,...(H=(_=i.parameters)==null?void 0:_.docs)==null?void 0:H.source},description:{story:"嵌套错误边界",...(U=(F=i.parameters)==null?void 0:F.docs)==null?void 0:U.description}}};const Z=["Normal","CaughtError","CustomFallback","WithErrorCallback","NestedBoundaries"];export{d as CaughtError,l as CustomFallback,i as NestedBoundaries,n as Normal,c as WithErrorCallback,Z as __namedExportsOrder,Y as default};
