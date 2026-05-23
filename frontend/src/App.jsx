import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState("entry");
  const [mode, setMode] = useState("login");
  const [toast, setToast] = useState("");
  const [login, setLogin] = useState({ email: "admin@example.com", password: "admin1234" });
  const [register, setRegister] = useState({ full_name: "", department: "", position: "", email: "", password: "", requested_role: "Viewer", reason: "" });

  const [summary, setSummary] = useState(null);
  const [pm, setPm] = useState(null);
  const [eligibility, setEligibility] = useState([]);
  const [projects, setProjects] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [requests, setRequests] = useState([]);

  const [projectForm, setProjectForm] = useState({ project_name: "", customer_name: "", project_manager: "", contract_value: "", status: "Active" });
  const [contractForm, setContractForm] = useState({ project_id: "", po_number: "", contract_name: "", contract_value: "", payment_term: "", status: "Active" });
  const [milestoneForm, setMilestoneForm] = useState({ project_id: "", contract_id: "", milestone_name: "", milestone_percent: "", milestone_amount: "", planned_billing_date: "", status: "Planned", remark: "" });
  const [invoiceForm, setInvoiceForm] = useState({ milestone_id: "", invoice_number: "", invoice_amount: "", due_date: "", remark: "" });
  const [paymentInputs, setPaymentInputs] = useState({});
  const [tgText, setTgText] = useState("/status Cloud 11");
  const [tgReply, setTgReply] = useState("");

  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const notify = (m) => { setToast(m); setTimeout(() => setToast(""), 2500); };
  const n = (v) => v === "" || v === null || v === undefined ? 0 : Number(String(v).replace(/,/g, ""));

  const doLogin = async () => {
    try {
      const res = await axios.post(`${API}/auth/login`, login);
      if (!res.data.access_token) return notify(res.data.message || "Login failed");
      localStorage.setItem("token", res.data.access_token);
      setToken(res.data.access_token);
      setUser(res.data.user);
    } catch (e) { notify("Login failed"); }
  };

  const doRegister = async () => {
    await axios.post(`${API}/auth/register`, register);
    setMode("login");
    notify("Registration submitted.");
  };

  const loadAll = async () => {
    if (!token) return;
    try {
      const [me, s, p, e, pr, co, ms, inv, doc] = await Promise.all([
        axios.get(`${API}/auth/me`, { headers }),
        axios.get(`${API}/dashboard/summary`, { headers }),
        axios.get(`${API}/dashboard/pm-summary`, { headers }),
        axios.get(`${API}/dashboard/billing-eligibility`, { headers }),
        axios.get(`${API}/projects/`, { headers }),
        axios.get(`${API}/contracts/`, { headers }),
        axios.get(`${API}/milestones/`, { headers }),
        axios.get(`${API}/invoices/`, { headers }),
        axios.get(`${API}/documents/`, { headers }),
      ]);
      setUser(me.data);
      setSummary(s.data);
      setPm(p.data);
      setEligibility(e.data);
      setProjects(pr.data);
      setContracts(co.data);
      setMilestones(ms.data);
      setInvoices(inv.data);
      setDocuments(doc.data);
      if (me.data.role === "Admin") {
        const r = await axios.get(`${API}/auth/requests`, { headers });
        setRequests(r.data);
      }
    } catch (e) { notify("Cannot load data. Check backend."); }
  };

  useEffect(() => { loadAll(); }, [token]);

  const saveProject = async () => {
    if (!projectForm.project_name) return notify("กรอก Project Name");
    await axios.post(`${API}/projects/`, { ...projectForm, contract_value: n(projectForm.contract_value) }, { headers });
    setProjectForm({ project_name: "", customer_name: "", project_manager: "", contract_value: "", status: "Active" });
    await loadAll();
    notify("Saved Project");
  };

  const saveContract = async () => {
    if (!contractForm.project_id || !contractForm.po_number) return notify("เลือก Project และกรอก PO");
    await axios.post(`${API}/contracts/`, { ...contractForm, project_id: n(contractForm.project_id), contract_value: n(contractForm.contract_value) }, { headers });
    setContractForm({ project_id: "", po_number: "", contract_name: "", contract_value: "", payment_term: "", status: "Active" });
    await loadAll();
    notify("Saved Contract / PO");
  };

  const saveMilestone = async () => {
    if (!milestoneForm.project_id || !milestoneForm.contract_id || !milestoneForm.milestone_name) return notify("กรอกงวดงานให้ครบ");
    await axios.post(`${API}/milestones/`, { ...milestoneForm, project_id: n(milestoneForm.project_id), contract_id: n(milestoneForm.contract_id), milestone_percent: n(milestoneForm.milestone_percent), milestone_amount: n(milestoneForm.milestone_amount) }, { headers });
    setMilestoneForm({ project_id: "", contract_id: "", milestone_name: "", milestone_percent: "", milestone_amount: "", planned_billing_date: "", status: "Planned", remark: "" });
    await loadAll();
    notify("Saved Milestone");
  };

  const saveInvoice = async () => {
    if (!invoiceForm.invoice_number || !invoiceForm.invoice_amount) return notify("กรอก Invoice ให้ครบ");
    await axios.post(`${API}/invoices/`, { ...invoiceForm, milestone_id: invoiceForm.milestone_id ? n(invoiceForm.milestone_id) : null, invoice_amount: n(invoiceForm.invoice_amount) }, { headers });
    setInvoiceForm({ milestone_id: "", invoice_number: "", invoice_amount: "", due_date: "", remark: "" });
    await loadAll();
    notify("Saved Invoice");
  };

  const updatePayment = async (invoice) => {
    const paid = n(paymentInputs[invoice.id]);
    if (paid <= 0) return notify("กรอกยอดรับเงิน");
    await axios.patch(`${API}/invoices/${invoice.id}/payment`, { paid_amount: paid, remark: "Updated from UI" }, { headers });
    setPaymentInputs({ ...paymentInputs, [invoice.id]: "" });
    await loadAll();
    notify("Payment Updated");
  };

  const approve = async (id, role) => {
    await axios.post(`${API}/auth/approve/${id}`, { role }, { headers });
    await loadAll();
    notify("Approved");
  };

  const reject = async (id) => {
    await axios.post(`${API}/auth/reject/${id}`, {}, { headers });
    await loadAll();
    notify("Rejected");
  };

  const deleteByApi = async (path) => {
    if (!confirm("Confirm delete?")) return;
    await axios.delete(`${API}${path}`, { headers });
    await loadAll();
    notify("Deleted");
  };

  const sendTelegramCommand = async () => {
    const res = await axios.post(`${API}/telegram/command`, { text: tgText, actor: user?.email || "web-user" });
    setTgReply(res.data.reply);
  };

  if (!token) return <div className="auth-page">{toast && <div className="toast">{toast}</div>}<div className="auth-card">
    <h1>Project Billing Agent</h1>
    <div className="tabs"><button className={mode==="login"?"active":""} onClick={()=>setMode("login")}>Login</button><button className={mode==="register"?"active":""} onClick={()=>setMode("register")}>Register</button></div>
    {mode==="login" ? <>
      <input placeholder="Email" value={login.email} onChange={e=>setLogin({...login,email:e.target.value})}/>
      <input placeholder="Password" type="password" value={login.password} onChange={e=>setLogin({...login,password:e.target.value})}/>
      <button onClick={doLogin}>Login</button>
      <p className="hint">Default: admin@example.com / admin1234</p>
    </> : <>
      <input placeholder="Full Name" value={register.full_name} onChange={e=>setRegister({...register,full_name:e.target.value})}/>
      <input placeholder="Department" value={register.department} onChange={e=>setRegister({...register,department:e.target.value})}/>
      <input placeholder="Position" value={register.position} onChange={e=>setRegister({...register,position:e.target.value})}/>
      <input placeholder="Email" value={register.email} onChange={e=>setRegister({...register,email:e.target.value})}/>
      <input placeholder="Password" type="password" value={register.password} onChange={e=>setRegister({...register,password:e.target.value})}/>
      <select value={register.requested_role} onChange={e=>setRegister({...register,requested_role:e.target.value})}><option>Viewer</option><option>PM</option><option>Finance</option><option>Director</option><option>Admin</option></select>
      <textarea placeholder="Reason" value={register.reason} onChange={e=>setRegister({...register,reason:e.target.value})}/>
      <button onClick={doRegister}>Submit Access Request</button>
    </>}
  </div></div>;

  if (!summary || !pm) return <div className="app">Loading...</div>;

  return <div className="app">{toast && <div className="toast">{toast}</div>}
    <header><div><h1>Project Billing Agent v1.9</h1><p>{user?.full_name} | {user?.role}</p></div><button onClick={()=>{localStorage.removeItem("token");setToken("");}}>Logout</button></header>

    <div className="tabs">
      <button className={tab==="entry"?"active":""} onClick={()=>setTab("entry")}>Data Entry</button>
      <button className={tab==="manage"?"active":""} onClick={()=>setTab("manage")}>Manage Data</button>
      <button className={tab==="dashboard"?"active":""} onClick={()=>setTab("dashboard")}>PM Dashboard</button>
      <button className={tab==="billing"?"active":""} onClick={()=>setTab("billing")}>Billing Eligibility</button>
      <button className={tab==="telegram"?"active":""} onClick={()=>setTab("telegram")}>Telegram / Inquiry</button>
      {user?.role==="Admin" && <button className={tab==="admin"?"active":""} onClick={()=>setTab("admin")}>Admin</button>}
    </div>

    <div className="grid"><Card title="Projects" value={summary.total_projects}/><Card title="Contract Value" value={`${summary.total_contract_value.toLocaleString()} ฿`}/><Card title="Invoice" value={`${summary.total_invoice_amount.toLocaleString()} ฿`}/><Card title="Paid" value={`${summary.total_paid_amount.toLocaleString()} ฿`} good/><Card title="Outstanding" value={`${summary.total_outstanding.toLocaleString()} ฿`} danger/><Card title="Billing Progress" value={`${pm.billing_progress}%`} warn/><Card title="Collection Rate" value={`${pm.collection_rate}%`}/><Card title="Documents" value={summary.document_count}/></div>

    {tab==="entry" && <section className="forms">
      <Box title="Add Project"><input placeholder="Project Name" value={projectForm.project_name} onChange={e=>setProjectForm({...projectForm,project_name:e.target.value})}/><input placeholder="Customer" value={projectForm.customer_name} onChange={e=>setProjectForm({...projectForm,customer_name:e.target.value})}/><input placeholder="Project Manager" value={projectForm.project_manager} onChange={e=>setProjectForm({...projectForm,project_manager:e.target.value})}/><input inputMode="decimal" placeholder="Contract Value" value={projectForm.contract_value} onChange={e=>setProjectForm({...projectForm,contract_value:e.target.value})}/><button onClick={saveProject}>Save Project</button></Box>
      <Box title="Add Contract / PO"><ProjectSelect projects={projects} value={contractForm.project_id} onChange={v=>setContractForm({...contractForm,project_id:v})}/><input placeholder="PO Number" value={contractForm.po_number} onChange={e=>setContractForm({...contractForm,po_number:e.target.value})}/><input placeholder="Contract Name" value={contractForm.contract_name} onChange={e=>setContractForm({...contractForm,contract_name:e.target.value})}/><input inputMode="decimal" placeholder="Contract Value" value={contractForm.contract_value} onChange={e=>setContractForm({...contractForm,contract_value:e.target.value})}/><input placeholder="Payment Term" value={contractForm.payment_term} onChange={e=>setContractForm({...contractForm,payment_term:e.target.value})}/><button onClick={saveContract}>Save Contract</button></Box>
      <Box title="Add Milestone"><ProjectSelect projects={projects} value={milestoneForm.project_id} onChange={v=>setMilestoneForm({...milestoneForm,project_id:v})}/><select value={milestoneForm.contract_id} onChange={e=>setMilestoneForm({...milestoneForm,contract_id:e.target.value})}><option value="">Select Contract</option>{contracts.map(x=><option key={x.id} value={x.id}>{x.po_number} - {x.contract_name}</option>)}</select><input placeholder="Milestone Name" value={milestoneForm.milestone_name} onChange={e=>setMilestoneForm({...milestoneForm,milestone_name:e.target.value})}/><input inputMode="decimal" placeholder="Milestone %" value={milestoneForm.milestone_percent} onChange={e=>setMilestoneForm({...milestoneForm,milestone_percent:e.target.value})}/><input inputMode="decimal" placeholder="Milestone Amount" value={milestoneForm.milestone_amount} onChange={e=>setMilestoneForm({...milestoneForm,milestone_amount:e.target.value})}/><button onClick={saveMilestone}>Save Milestone</button></Box>
      <Box title="Add Invoice"><select value={invoiceForm.milestone_id} onChange={e=>setInvoiceForm({...invoiceForm,milestone_id:e.target.value})}><option value="">Select Milestone Optional</option>{milestones.map(x=><option key={x.id} value={x.id}>{x.milestone_name}</option>)}</select><input placeholder="Invoice No." value={invoiceForm.invoice_number} onChange={e=>setInvoiceForm({...invoiceForm,invoice_number:e.target.value})}/><input inputMode="decimal" placeholder="Invoice Amount" value={invoiceForm.invoice_amount} onChange={e=>setInvoiceForm({...invoiceForm,invoice_amount:e.target.value})}/><input placeholder="Due Date YYYY-MM-DD" value={invoiceForm.due_date} onChange={e=>setInvoiceForm({...invoiceForm,due_date:e.target.value})}/><button onClick={saveInvoice}>Save Invoice</button></Box>
    </section>}

    {tab==="manage" && <section><Table title="Projects" heads={["ID","Project","Customer","PM","Value","Status","Action"]} rows={projects.map(x=>[x.id,x.project_name,x.customer_name,x.project_manager,`${(x.contract_value||0).toLocaleString()} ฿`,x.status,<button className="danger-btn" onClick={()=>deleteByApi(`/projects/${x.id}`)}>Delete</button>])}/><Table title="Contracts / PO" heads={["ID","PO","Contract","Project ID","Value","Total","Action"]} rows={contracts.map(x=>[x.id,x.po_number,x.contract_name,x.project_id,`${(x.contract_value||0).toLocaleString()} ฿`,`${(x.total_value||0).toLocaleString()} ฿`,<button className="danger-btn" onClick={()=>deleteByApi(`/contracts/${x.id}`)}>Delete</button>])}/><Table title="Milestones" heads={["ID","Milestone","%","Amount","Status","Action"]} rows={milestones.map(x=>[x.id,x.milestone_name,`${x.milestone_percent}%`,`${(x.milestone_amount||0).toLocaleString()} ฿`,x.status,<button className="danger-btn" onClick={()=>deleteByApi(`/milestones/${x.id}`)}>Delete</button>])}/><section className="panel"><h2>Invoices / Payment Update</h2><table><thead><tr><th>Invoice</th><th>Amount</th><th>Paid</th><th>Outstanding</th><th>Status</th><th>Update Paid</th><th>Action</th></tr></thead><tbody>{invoices.map(x=><tr key={x.id}><td>{x.invoice_number}</td><td>{(x.invoice_amount||0).toLocaleString()} ฿</td><td className="good">{(x.paid_amount||0).toLocaleString()} ฿</td><td className="danger">{(x.outstanding_amount||0).toLocaleString()} ฿</td><td><span className="pill">{x.payment_status}</span></td><td><input className="pay" inputMode="decimal" value={paymentInputs[x.id]||""} onChange={e=>setPaymentInputs({...paymentInputs,[x.id]:e.target.value})}/><button onClick={()=>updatePayment(x)}>Save</button></td><td><button className="danger-btn" onClick={()=>deleteByApi(`/invoices/${x.id}`)}>Delete</button></td></tr>)}</tbody></table></section></section>}

    {tab==="dashboard" && <Table title="PM Project Summary" heads={["Project","Customer","Status","Contract","Milestones","Invoiced","Collected","Outstanding"]} rows={pm.projects.map(p=>[p.project_name,p.customer_name,p.status,`${p.contract_value.toLocaleString()} ฿`,`${p.milestone_billed}/${p.milestone_total}`,`${p.invoice_total.toLocaleString()} ฿`,`${p.paid_total.toLocaleString()} ฿`,`${p.outstanding_total.toLocaleString()} ฿`])}/>}
    {tab==="billing" && <Billing eligibility={eligibility}/>}
    {tab==="telegram" && <section className="panel"><h2>Telegram Command / Inquiry</h2><textarea value={tgText} onChange={e=>setTgText(e.target.value)}/><button onClick={sendTelegramCommand}>Send Command</button>{tgReply && <pre>{tgReply}</pre>}</section>}
    {tab==="admin" && <section className="panel"><h2>Access Requests</h2><table><thead><tr><th>Name</th><th>Dept</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>{requests.map(r=><tr key={r.id}><td>{r.full_name}</td><td>{r.department}</td><td>{r.email}</td><td>{r.requested_role}</td><td><span className="pill">{r.status}</span></td><td><button onClick={()=>approve(r.id,r.requested_role)}>Approve</button><button className="secondary" onClick={()=>reject(r.id)}>Reject</button></td></tr>)}</tbody></table></section>}
  </div>;
}

function Billing({eligibility}){return <section className="panel"><h2>Billing Eligibility</h2>{eligibility.map(p=><div className="project-block" key={p.project_id}><h3>{p.project_name}</h3><p>Ready to Bill: {p.ready_to_bill_count} | Paid: {p.paid_milestone_count} | Outstanding: {p.total_outstanding_amount.toLocaleString()} ฿</p><table><thead><tr><th>Milestone</th><th>Amount</th><th>Invoice</th><th>Paid</th><th>Outstanding</th><th>Status</th><th>Recommendation</th></tr></thead><tbody>{p.milestones.map(m=><tr key={m.milestone_id}><td>{m.milestone_name}</td><td>{m.milestone_amount.toLocaleString()} ฿</td><td>{m.invoice_numbers.length?m.invoice_numbers.join(", "):"-"}</td><td className="good">{m.paid_amount.toLocaleString()} ฿</td><td className="danger">{m.outstanding_amount.toLocaleString()} ฿</td><td><span className="pill">{m.eligibility_status}</span></td><td>{m.recommendation}</td></tr>)}</tbody></table></div>)}</section>}
function Card({title,value,good,warn,danger}){let cls=good?"good":warn?"warn":danger?"danger":"";return <div className="card"><h2>{title}</h2><p className={cls}>{value}</p></div>}
function Box({title,children}){return <div className="box"><h2>{title}</h2>{children}</div>}
function ProjectSelect({projects,value,onChange}){return <select value={value} onChange={e=>onChange(e.target.value)}><option value="">Select Project</option>{projects.map(x=><option key={x.id} value={x.id}>{x.project_name}</option>)}</select>}
function Table({title,heads,rows}){return <section className="panel"><h2>{title}</h2><table><thead><tr>{heads.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{r.map((c,j)=><td key={j}>{c||"-"}</td>)}</tr>)}</tbody></table></section>}
export default App;
