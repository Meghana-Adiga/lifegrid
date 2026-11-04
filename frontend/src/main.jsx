import React,{useState} from 'react';
import{createRoot}
from'react-dom/client';
import'./style.css';

function App()
{const
  [token,setToken]=useState(localStorage.token||''),
  [email,E]=useState(''),
  [password,P]=useState(''),
  [data,D]=useState(null),
  [error,X]=useState('');
 
 async function api(path,opts={})
 {
   let r=await fetch((import.meta.env.VITE_API_URL||'http://localhost:8000')+path,
                     {...opts,
                      headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})}});
   let j=await r.json();
   if(!r.ok)
     throw Error(j.detail||'Request failed');
   return j
 }
 
 async function login(e)
 {
   e.preventDefault();
   try{
     let x=await api('/auth/login',
                       {method:'POST',
                        body:JSON.stringify({email,password})});
       localStorage.token=x.access_token;
       setToken(x.access_token);
       X('')}
   catch(e){X(e.message)}
 }
 
 async function load()
 {
   try{
     D(await api('/dashboard'));
     X('')}
   catch(e){X(e.message)}}
 return <main><header><div className="mark">L</div><div><b>LIFEGRID</b><small>Community resource coordination</small></div></header><section className="hero"><p className="eyebrow">PHASE 1 · CORE</p><h1>Connect what’s available<br/>with what’s needed.</h1><p>A simple workspace for listing resources, raising requests and coordinating matches.</p></section>{!token?<form onSubmit={login}><h2>Sign in</h2><input type="email" placeholder="Email" value={email} onChange={e=>E(e.target.value)} required/><input type="password" placeholder="Password" value={password} onChange={e=>P(e.target.value)} required/><button>Sign in</button><p className="hint">New users: register through <code>POST /auth/register</code> in the API docs.</p></form>:<section className="panel"><h2>Your overview</h2><p>Dashboard summary from the LIFEGRID API.</p><button onClick={load}>Refresh dashboard</button>{data&&<div className="stats">{Object.entries(data).map(([k,v])=><article><strong>{v}</strong><span>{k.replaceAll('_',' ')}</span></article>)}</div>}<nav><a href="http://localhost:8000/docs" target="_blank">Open API workspace →</a><button className="quiet" onClick={()=>{localStorage.removeItem('token');setToken('');D(null)}}>Sign out</button></nav></section>}{error&&<p className="error">{error}</p>}<footer>Phase 1 is a coordination foundation. Matching is manual; no automated allocation or live tracking.</footer></main>}
createRoot(document.getElementById('root')).render(<App/>);
