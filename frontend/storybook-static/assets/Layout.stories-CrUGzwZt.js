import{j as e}from"./iframe-BgyFVukn.js";import{S as v}from"./Sidebar-BKi5iY1w.js";import{H as y}from"./Header-BwIVaQu5.js";import"./preload-helper-Dp1pzeXC.js";import"./sparkles-CXOrxNE2.js";import"./createLucideIcon-C5yOfbJT.js";import"./chevron-right-Dp1TRzSI.js";import"./settings-BcukFMc5.js";import"./user-kvdGHbHj.js";function j({children:t}){return e.jsxs("div",{className:"flex min-h-screen bg-neutral-bg",children:[e.jsx(v,{}),e.jsxs("main",{className:"flex-1 flex flex-col min-w-0",children:[e.jsx(y,{}),e.jsx("div",{className:"flex-1 max-w-5xl mx-auto w-full px-6 py-6",children:t})]})]})}j.__docgenInfo={description:"",methods:[],displayName:"Layout",props:{children:{required:!0,tsType:{name:"ReactNode"},description:""}}};const k={title:"Components/Layout",component:j,parameters:{layout:"fullscreen",docs:{description:{component:"应用布局组件。包含左侧导航栏、顶部栏和主内容区。所有页面均使用此布局。"}}},argTypes:{children:{control:!1,description:"主内容区域子元素"}}},r={args:{children:e.jsx("div",{className:"text-center py-12",children:e.jsx("p",{className:"text-text-muted",children:"选择左侧菜单开始使用"})})}},s={args:{children:e.jsx("div",{className:"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",children:["总访客","今日新增","匹配度"].map(t=>e.jsxs("div",{className:"bg-surface rounded-2xl border border-border-light p-5",children:[e.jsx("div",{className:"text-sm text-text-muted",children:t}),e.jsx("div",{className:"text-2xl font-bold text-on-surface mt-2",children:Math.floor(Math.random()*1e4)})]},t))})}},a={args:{children:e.jsx("div",{className:"bg-surface rounded-2xl border border-border-light overflow-hidden",children:e.jsxs("table",{className:"w-full text-sm",children:[e.jsx("thead",{children:e.jsxs("tr",{className:"border-b border-border-light bg-slate-50",children:[e.jsx("th",{className:"text-left p-4 text-text-muted font-medium",children:"姓名"}),e.jsx("th",{className:"text-left p-4 text-text-muted font-medium",children:"职位"}),e.jsx("th",{className:"text-left p-4 text-text-muted font-medium",children:"状态"})]})}),e.jsx("tbody",{children:[{name:"张明",role:"工程师",status:"在线"},{name:"李华",role:"设计师",status:"离线"},{name:"王芳",role:"产品经理",status:"在线"}].map(t=>e.jsxs("tr",{className:"border-b border-border-light last:border-0",children:[e.jsx("td",{className:"p-4 text-on-surface",children:t.name}),e.jsx("td",{className:"p-4 text-text-muted",children:t.role}),e.jsx("td",{className:"p-4",children:e.jsx("span",{className:`px-2 py-0.5 rounded-full text-xs font-medium ${t.status==="在线"?"bg-emerald-50 text-emerald-700":"bg-slate-50 text-slate-500"}`,children:t.status})})]},t.name))})]})})}};var d,l,o,m,c;r.parameters={...r.parameters,docs:{...(d=r.parameters)==null?void 0:d.docs,source:{originalSource:`{
  args: {
    children: <div className="text-center py-12">\r
        <p className="text-text-muted">选择左侧菜单开始使用</p>\r
      </div>
  }
}`,...(o=(l=r.parameters)==null?void 0:l.docs)==null?void 0:o.source},description:{story:"空白内容区",...(c=(m=r.parameters)==null?void 0:m.docs)==null?void 0:c.description}}};var i,n,x,p,u;s.parameters={...s.parameters,docs:{...(i=s.parameters)==null?void 0:i.docs,source:{originalSource:`{
  args: {
    children: <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">\r
        {['总访客', '今日新增', '匹配度'].map(title => <div key={title} className="bg-surface rounded-2xl border border-border-light p-5">\r
            <div className="text-sm text-text-muted">{title}</div>\r
            <div className="text-2xl font-bold text-on-surface mt-2">\r
              {Math.floor(Math.random() * 10000)}\r
            </div>\r
          </div>)}\r
      </div>
  }
}`,...(x=(n=s.parameters)==null?void 0:n.docs)==null?void 0:x.source},description:{story:"带卡片内容",...(u=(p=s.parameters)==null?void 0:p.docs)==null?void 0:u.description}}};var h,b,f,g,N;a.parameters={...a.parameters,docs:{...(h=a.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    children: <div className="bg-surface rounded-2xl border border-border-light overflow-hidden">\r
        <table className="w-full text-sm">\r
          <thead>\r
            <tr className="border-b border-border-light bg-slate-50">\r
              <th className="text-left p-4 text-text-muted font-medium">姓名</th>\r
              <th className="text-left p-4 text-text-muted font-medium">职位</th>\r
              <th className="text-left p-4 text-text-muted font-medium">状态</th>\r
            </tr>\r
          </thead>\r
          <tbody>\r
            {[{
            name: '张明',
            role: '工程师',
            status: '在线'
          }, {
            name: '李华',
            role: '设计师',
            status: '离线'
          }, {
            name: '王芳',
            role: '产品经理',
            status: '在线'
          }].map(row => <tr key={row.name} className="border-b border-border-light last:border-0">\r
                <td className="p-4 text-on-surface">{row.name}</td>\r
                <td className="p-4 text-text-muted">{row.role}</td>\r
                <td className="p-4">\r
                  <span className={\`px-2 py-0.5 rounded-full text-xs font-medium \${row.status === '在线' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-500'}\`}>\r
                    {row.status}\r
                  </span>\r
                </td>\r
              </tr>)}\r
          </tbody>\r
        </table>\r
      </div>
  }
}`,...(f=(b=a.parameters)==null?void 0:b.docs)==null?void 0:f.source},description:{story:"带表格内容",...(N=(g=a.parameters)==null?void 0:g.docs)==null?void 0:N.description}}};const H=["Empty","WithCards","WithTable"];export{r as Empty,s as WithCards,a as WithTable,H as __namedExportsOrder,k as default};
