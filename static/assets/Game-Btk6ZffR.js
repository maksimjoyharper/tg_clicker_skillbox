import{j as e,r as l}from"./index-GtC7LnaD.js";const D="_falling_letters_container_16a21_1",k="_img_open_box_16a21_21",M="_title_logo_16a21_33",$="_canv_16a21_47",p={falling_letters_container:D,img_open_box:k,title_logo:M,canv:$},E="/assets/S-white-DJHRycHD.png",L=({x:t,duration:n,id:a,onClick:s})=>e.jsxs("button",{className:"btn",onTouchStart:()=>s(a),id:a,style:{left:`${t}%`,animationDuration:`${n}s`},children:[" ",e.jsx("img",{src:E,className:"falling_letter_white"})]}),i=[];for(let t=0;t<256;++t)i.push((t+256).toString(16).slice(1));function U(t,n=0){return(i[t[n+0]]+i[t[n+1]]+i[t[n+2]]+i[t[n+3]]+"-"+i[t[n+4]]+i[t[n+5]]+"-"+i[t[n+6]]+i[t[n+7]]+"-"+i[t[n+8]]+i[t[n+9]]+"-"+i[t[n+10]]+i[t[n+11]]+i[t[n+12]]+i[t[n+13]]+i[t[n+14]]+i[t[n+15]]).toLowerCase()}let f;const C=new Uint8Array(16);function T(){if(!f){if(typeof crypto>"u"||!crypto.getRandomValues)throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");f=crypto.getRandomValues.bind(crypto)}return f(C)}const R=typeof crypto<"u"&&crypto.randomUUID&&crypto.randomUUID.bind(crypto),y={randomUUID:R};function u(t,n,a){if(y.randomUUID&&!n&&!t)return y.randomUUID();t=t||{};const s=t.random||(t.rng||T)();return s[6]=s[6]&15|64,s[8]=s[8]&63|128,U(s)}const V="_timer_container_1kjre_1",F="_time_1kjre_1",S={timer_container:V,time:F},A=t=>{const n=Math.floor(t%3600/60),a=t%60;return`${n.toString().padStart(2,"0")}:${a.toString().padStart(2,"0")}`};function H({setIsVision:t,time:n,setTimer:a}){return l.useEffect(()=>{const s=setInterval(()=>{a(o=>o-1)},1e3);return()=>clearInterval(s)},[n]),l.useEffect(()=>{n===0&&t(!1)},[n]),e.jsx("div",{className:S.timer_container,children:e.jsx("div",{className:S.time,children:A(n)})})}const P="/assets/S-blue-Dh_q71fZ.png",q=[{id:u(),duration:3,x:33},{id:u(),duration:1,x:58}],J=({setCount:t,blueLetter:n,setBlueLetter:a})=>{const s=o=>{a(r=>r.filter(c=>c.id!==o)),t(r=>r-3)};return l.useEffect(()=>{const o=setInterval(()=>{a(r=>{const c=q.map(d=>({...d,id:u(),duration:Math.random()+2}));return[...r,...c]})},2e3);return()=>clearInterval(o)},[]),e.jsx(e.Fragment,{children:n.map(o=>e.jsxs("button",{className:"btn_blue",onTouchStart:()=>s(o.id),id:o.id,style:{left:`${o.x}%`,animationDuration:`${o.duration}s`},children:[" ",e.jsx("img",{className:"falling_letter_blue",src:P})]},o.id))})},W="_counter_container_119w0_1",G="_counter_119w0_1",I={counter_container:W,counter:G};function K({count:t}){return e.jsx("div",{className:I.counter_container,children:e.jsx("div",{className:I.counter,children:t})})}const O="/assets/bomb-DeoDqckm.png";function N(){return Math.floor(Math.random()*81)+10}function Z({setCount:t,setWhiteLetter:n,setBlueLetter:a,setFlask:s,count:o}){const[r,c]=l.useState([]),d=m=>{c(x=>x.filter(g=>g.id!==m)),n([]),a([]),s([]),o<=10?t(0):t(x=>x-10)};return l.useEffect(()=>{const x=setInterval(()=>{const g={x:N(),duration:Math.random()*3+2,id:u().toString()};c(v=>[...v,g])},4e3);return()=>clearInterval(x)},[]),e.jsx(e.Fragment,{children:r.map(m=>e.jsxs("button",{className:"btn_bomb",onTouchStart:()=>d(m.id),id:m.id,style:{left:`${m.x}%`,animationDuration:`${m.duration}s`},children:[" ",e.jsx("img",{src:O,className:"falling_bomb"})]}))})}const z="/assets/flask-0VLBKfJP.png";function Q({setCount:t,flasks:n,setFlask:a}){const s=o=>{a(r=>r.filter(c=>c.id!==o)),t(r=>r+5)};return l.useEffect(()=>{const r=setInterval(()=>{const c={x:N(),duration:Math.random()*3+2,id:u().toString()};a(d=>d.length===3?[...d.slice(1),c]:[...d,c])},4200);return()=>clearInterval(r)},[]),e.jsx(e.Fragment,{children:n.map(o=>e.jsxs("button",{className:"btn_flask",onTouchStart:()=>s(o.id),id:o.id,style:{left:`${o.x}%`,animationDuration:`${o.duration}s`},children:[" ",e.jsx("img",{src:z,className:"falling_flask"})]}))})}const X="/assets/open-box-BIBPcrIn.png",Y=[{id:u(),duration:Math.random()*3+2,x:10},{id:u(),duration:Math.random()*3+2,x:30},{id:u(),duration:Math.random()*3+2,x:50},{id:u(),duration:Math.random()*3+2,x:70},{id:u(),duration:Math.random()*3+2,x:85}],tt="_modal_7v2vv_1",nt="_overlay_7v2vv_14",et="_content_7v2vv_20",j={modal:tt,overlay:nt,content:et};function ot({children:t}){return e.jsx("div",{className:j.modal,children:e.jsx("div",{className:j.overlay,children:e.jsx("div",{className:j.content,children:t})})})}function at(){const[t,n]=l.useState(!0),[a,s]=l.useState(15),[o,r]=l.useState(0),[c,d]=l.useState([]),[m,x]=l.useState([]),[g,v]=l.useState([]);l.useEffect(()=>{const _=setInterval(()=>{d(h=>{const b=Y.map(w=>({...w,id:u(),duration:Math.random()+3}));return[...h,...b]})},1e3);return()=>clearInterval(_)},[]);const B=_=>{d(h=>h.filter(b=>b.id!==_)),r(h=>h+1)};return e.jsx(ot,{children:t&&e.jsxs("div",{className:p.falling_letters_container,children:[e.jsx(H,{time:a,setTimer:s,setIsVision:n}),e.jsx("p",{className:p.title_logo,children:"Skillbox"}),e.jsx(K,{count:o}),c.map(_=>e.jsx(L,{onClick:()=>B(_.id),id:_.id,x:_.x,duration:_.duration},_.id)),e.jsx(J,{setCount:r,blueLetter:m,setBlueLetter:x}),e.jsx(Q,{setCount:s,flasks:g,setFlask:v}),e.jsx(Z,{count:o,setCount:r,setWhiteLetter:d,setBlueLetter:x,setFlask:v}),e.jsx("img",{src:X,className:p.img_open_box})]})})}export{at as default};