const $=s=>document.querySelector(s);let chosen=[];const input=$("#files"),list=$("#list"),drop=$("#drop");
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function size(n){return n<1024?n+" B":n<1048576?(n/1024).toFixed(1)+" KB":n<1073741824?(n/1048576).toFixed(1)+" MB":(n/1073741824).toFixed(2)+" GB"}
function render(){list.innerHTML="";chosen.forEach((f,i)=>{let d=document.createElement("div");d.className="file";d.innerHTML=`<span class="ext">${esc((f.name.split(".").pop()||"FILE").slice(0,4).toUpperCase())}</span><span class="fmeta"><b>${esc(f.name)}</b><small>${size(f.size)}</small></span><button type="button" class="remove" data-i="${i}" aria-label="Dosyayı kaldır">×</button>`;list.append(d)});$("#count").textContent=chosen.length+" dosya";list.querySelectorAll("button").forEach(b=>b.onclick=()=>{chosen.splice(+b.dataset.i,1);render()})}
function add(fs){for(const f of fs)if(!chosen.some(x=>x.name===f.name&&x.size===f.size&&x.lastModified===f.lastModified))chosen.push(f);render()}
input.onchange=()=>{add(input.files);input.value=""};
["dragover","dragenter"].forEach(x=>drop.addEventListener(x,e=>{e.preventDefault();drop.classList.add("drag")}));
["drop","dragleave"].forEach(x=>drop.addEventListener(x,e=>{e.preventDefault();drop.classList.remove("drag")}));
drop.addEventListener("drop",e=>add(e.dataTransfer.files));
$("#theme").onclick=()=>document.body.classList.toggle("dark");
let deferred;window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferred=e;$("#install").hidden=false});
$("#install").onclick=async()=>{if(deferred){deferred.prompt();await deferred.userChoice;deferred=null;$("#install").hidden=true}};
if("serviceWorker"in navigator)navigator.serviceWorker.register("/sw.js").catch(()=>{});
function showProgress(percent,message){$("#progress").hidden=false;$("#progressText").textContent=message||"Kaynaklar işleniyor…";$("#progressBar").value=percent||0;$("#progressPct").textContent=(percent||0)+"%"}
let polling=false;
async function pollProgress(){if(polling)return;polling=true;while(polling){try{let r=await fetch("/api/progress?_"+Date.now(),{cache:"no-store"});let p=await r.json();showProgress(p.percent,p.message);if(p.done&&p.percent===100)break}catch{}await new Promise(r=>setTimeout(r,900))}polling=false}
$("#form").onsubmit=async e=>{e.preventDefault();$("#result").hidden=true;$("#submit").disabled=true;$("#result").innerHTML="";showProgress(1,"İşlem başlatılıyor…");polling=false;pollProgress();
try{let d=new FormData();d.append("title",$("#title").value);d.append("urls",$("#urls").value);d.append("pagesize",$("#pagesize").value);d.append("codesize",$("#codesize").value);d.append("questions",$("#questions").value);if($("#offline").checked)d.append("offline","1");if($("#crawl").checked)d.append("crawl","1");if($("#compact").checked)d.append("compact","1");if($("#includeoriginal").checked)d.append("includeoriginal","1");if($("#summaries").checked)d.append("summaries","1");if($("#chapters").checked)d.append("chapters","1");if($("#dedup").checked)d.append("dedup","1");if($("#ocr").checked)d.append("ocr","1");if($("#translate").value!=="none")d.append("translate",$("#translate").value);chosen.forEach(f=>d.append("files",f,f.name));
let r=await fetch("/api/create",{method:"POST",body:d}),o=await r.json();if(!r.ok||!o.ok)throw Error(o.error||"İşlem başarısız");
polling=false;showProgress(100,"İşlem tamamlandı.");$("#result").hidden=false;
$("#result").innerHTML=`<h3>✓ Eğitim paketi hazır</h3><p>${o.count} kaynak öğesi işlendi.</p><p>ZIP paketi otomatik indirilmeye başlandı; PDF'yi ayrıca aşağıdaki bağlantıdan alabilirsin.</p><a id="pdfLink" href="${o.pdf}">PDF'yi indir ↓</a><a id="zipLink" href="${o.zip}">ZIP paketini indir ↓</a>${o.warnings?.length?`<p>${o.warnings.length} uyarı; ayrıntılar raporda.</p>`:""}`;
const a=document.createElement("a");a.href=o.zip;a.download="";document.body.appendChild(a);a.click();a.remove();
$("#result").scrollIntoView({behavior:"smooth",block:"nearest"});
}catch(err){polling=false;$("#progressText").textContent="İşlem durdu.";$("#result").hidden=false;$("#result").innerHTML=`<h3>İşlem tamamlanamadı</h3><p>${esc(err.message)}</p><p>Komut penceresindeki son hata satırlarını kontrol edin.</p>`}
finally{polling=false;$("#submit").disabled=false}
};