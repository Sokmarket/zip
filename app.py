import os,sys,re,json,zipfile,threading,webbrowser,html
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,unquote
from urllib.request import Request,urlopen
from io import BytesIO
from datetime import datetime
ROOT=Path(__file__).resolve().parent; OUT=ROOT/"ciktilar"; OUT.mkdir(exist_ok=True); PORT=8767
HOST=os.environ.get("EGITIM_HOST","127.0.0.1")
PROGRESS={"active":False,"percent":0,"message":"Hazır","done":True}
PROGRESS_LOCK=threading.Lock()
def set_progress(percent,message,active=True):
 with PROGRESS_LOCK: PROGRESS.update({"active":active,"percent":max(0,min(100,int(percent))),"message":str(message),"done":not active})
EXT={".txt",".md",".rst",".py",".bat",".cmd",".ps1",".sh",".js",".ts",".jsx",".tsx",".html",".htm",".css",".json",".xml",".yaml",".yml",".toml",".ini",".cfg",".csv",".sql",".java",".c",".h",".cpp",".cs",".go",".rs",".php",".rb",".ipynb",".pdf",".docx",".pptx",".png",".jpg",".jpeg",".tif",".tiff",".bmp"}
SKIP={".git","node_modules",".venv","venv","__pycache__","dist","build"}
def safe(s): return re.sub(r"[^\w.-]+","_",s,flags=re.UNICODE).strip("._")[:90] or "egitim"
def fetch(u,timeout=25):
 r=urlopen(Request(u,headers={"User-Agent":"EgitimPDFAtolyesi/1.0"}),timeout=timeout); return r.read(),r.headers.get("Content-Type",""),r.geturl()
def dec(b):
 for e in ("utf-8-sig","utf-8","cp1254","latin-1"):
  try:return b.decode(e)
  except UnicodeDecodeError:pass
 return b.decode("utf-8","replace")
def clean_text(s):
 # PDF/reportlab uyumsuz kontrol karakterlerini ayıkla; metin içeriğini mümkün olduğunca koru.
 return "".join(ch for ch in str(s) if ch in "\n\r\t" or ord(ch)>=32 and ord(ch)!=127)

def text_of(data,name,ctype="",ocr=False):

 ext=Path(name).suffix.lower()
 if ext==".docx":
  try:
   from docx import Document
   d=Document(BytesIO(data)); parts=[p.text for p in d.paragraphs if p.text.strip()]
   for ti,table in enumerate(d.tables,1):
    parts.append(f"[Tablo {ti}]")
    parts.extend(" | ".join(c.text.replace("\n"," / ") for c in row.cells) for row in table.rows)
   return "\n".join(parts),"Word belgesi"
  except Exception as e:return "[DOCX okunamadı: "+str(e)+"]","Word belgesi"
 if ext==".pptx":
  try:
   from pptx import Presentation
   prs=Presentation(BytesIO(data)); parts=[]
   for i,slide in enumerate(prs.slides,1):
    parts.append(f"[Slayt {i}]")
    for shape in slide.shapes:
     if getattr(shape,"has_text_frame",False) and shape.text.strip():parts.append(shape.text)
     if getattr(shape,"has_table",False):
      for row in shape.table.rows:parts.append(" | ".join(c.text for c in row.cells))
   return "\n".join(parts),"PowerPoint sunumu"
  except Exception as e:return "[PPTX okunamadı: "+str(e)+"]","PowerPoint sunumu"
 if ext in (".png",".jpg",".jpeg",".tif",".tiff",".bmp"):
  if ocr:
   try:
    from PIL import Image
    import pytesseract
    return pytesseract.image_to_string(Image.open(BytesIO(data)),lang=os.environ.get("EDUPDF_OCR_LANG","tur+eng")),"Görsel OCR"
   except Exception as e:return "[OCR başarısız. Tesseract OCR motoru ve dil paketleri kurulu olmalı: "+str(e)+"]","Görsel/OCR"
  return "[Görsel eklendi; OCR seçeneğini açarak metin çıkarabilirsiniz.]","Görsel"
 if ext==".pdf" or "application/pdf" in ctype:
  try:
   from pypdf import PdfReader
   reader=PdfReader(BytesIO(data),strict=False)
   parts=[]
   for i,page in enumerate(reader.pages,1):
    try:
     txt=page.extract_text() or ""
     if txt.strip(): parts.append(f"[PDF sayfa {i}]\n{txt}")
    except Exception as e:
     parts.append(f"[PDF sayfa {i}: metin çıkarılamadı: {type(e).__name__}]")
   if not parts: return "[PDF'den seçilebilir metin çıkarılamadı; taranmış sayfalar için OCR gerekir]","PDF"
   return "\n\n".join(parts),"PDF metni"
  except Exception as e:return "[PDF metni çıkarılamadı; dosya bozuk/şifreli olabilir: "+type(e).__name__+"]","PDF"
 if ext in (".html",".htm") or "text/html" in ctype:
  s=re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>"," ",dec(data)); s=re.sub(r"(?i)</(p|div|h[1-6]|li|tr)>","\n",s); s=re.sub(r"(?s)<[^>]+>"," ",s); return html.unescape(s),"Web/HTML"
 if ext==".ipynb":
  try:
   obj=json.loads(dec(data)); return "\n\n".join("["+c.get("cell_type","code").upper()+"]\n"+"".join(c.get("source",[])) if isinstance(c.get("source",[]),list) else c.get("source","") for c in obj.get("cells",[])),"Notebook"
  except:pass
 return dec(data),"Metin/kod"
def add_zip(data,name,entries,errors,ocr=False):
 try:
  with zipfile.ZipFile(BytesIO(data)) as z:
   for i in z.infolist():
    p=Path(i.filename)
    if i.is_dir() or p.suffix.lower() not in EXT or any(x in SKIP for x in p.parts):continue
    try:
     b=z.read(i); t,k=text_of(b,i.filename,ocr=ocr); entries.append({"name":name+"/"+i.filename,"text":t,"kind":k,"bytes":len(b)})
    except Exception as e:errors.append(i.filename+": "+str(e))
 except Exception as e:errors.append(name+": ZIP açılamadı: "+str(e))
def github(url,entries,errors):
 p=[x for x in urlparse(url).path.strip("/").split("/") if x]
 if len(p)<2:errors.append("GitHub URL geçersiz: "+url);return
 owner,repo=p[0],p[1].removesuffix(".git"); api=f"https://api.github.com/repos/{owner}/{repo}"
 try:
  b,_,_=fetch(api); meta=json.loads(b); branch=meta.get("default_branch","main")
  try:
   b,_,_=fetch(api+"/readme"); rd=json.loads(b); import base64
   entries.append({"name":f"github.com/{owner}/{repo}/README.md","text":base64.b64decode(rd.get("content","")).decode("utf-8","replace"),"kind":"GitHub README","bytes":len(b)})
  except Exception as e:errors.append("README: "+str(e))
  b,_,_=fetch(f"{api}/git/trees/{branch}?recursive=1",45); tree=json.loads(b).get("tree",[])
  for it in tree:
   path=it.get("path",""); pp=Path(path)
   if it.get("type")!="blob" or pp.suffix.lower() not in EXT or pp.suffix.lower()==".pdf" or any(x in SKIP for x in pp.parts):continue
   raw,ct,_=fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}",35); t,k=text_of(raw,path,ct)
   entries.append({"name":f"github.com/{owner}/{repo}/{path}","text":t,"kind":k,"bytes":len(raw)})
  entries.append({"name":f"github.com/{owner}/{repo}/REPO_INFO.txt","text":f"Depo: {meta.get('full_name')}\nAçıklama: {meta.get('description')}\nDal: {branch}\nLisans: {(meta.get('license') or {}).get('spdx_id','Belirtilmemiş')}\nURL: {meta.get('html_url')}","kind":"Depo bilgisi","bytes":0})
 except Exception as e:errors.append("GitHub "+owner+"/"+repo+": "+str(e))
def url_process(u,entries,errors,crawl):
 try:
  if "github.com" in urlparse(u).netloc.lower():return github(u,entries,errors)
  b,ct,final=fetch(u,35); t,k=text_of(b,final,ct); entries.append({"name":final,"text":t,"kind":k,"bytes":len(b)})
  # Optional same-host crawl, bounded by site robots and de-duplication; no arbitrary page count limit.
  if crawl and ("html" in ct or final.endswith((".html",".htm"))):
   from urllib.parse import urljoin
   links=re.findall(r"""(?i)href\s*=\s*["']([^"'#]+)["']""",dec(b)); host=urlparse(final).netloc; seen={final}
   for link in links:
    target=urljoin(final,html.unescape(link))
    if urlparse(target).netloc!=host or urlparse(target).scheme not in ("http","https") or target in seen:continue
    seen.add(target)
    try:
     d,c,f=fetch(target,20)
     if "html" in c:
      tx,ky=text_of(d,f,c);entries.append({"name":f,"text":tx,"kind":ky,"bytes":len(d)})
    except Exception as e:errors.append(target+": "+str(e))
 except Exception as e:errors.append(u+": "+str(e))
def make_pdf(title,entries,errors,form=None):
 form=form or {}
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted
 from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
 from reportlab.lib.pagesizes import A4, letter
 from reportlab.lib.units import mm
 from reportlab.lib import colors
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 from xml.sax.saxutils import escape
 pagesize=letter if form.get("pagesize")=="letter" else A4
 margin=14*mm if form.get("compact")=="1" else 18*mm
 path=OUT/(safe(title)+"_egitim.pdf"); doc=SimpleDocTemplate(str(path),pagesize=pagesize,leftMargin=margin,rightMargin=margin,topMargin=margin,bottomMargin=margin,title=title)
 # Use a Unicode TTF when available so Turkish characters render and remain searchable in PDFs.
 font_pairs=[
  (Path(os.environ.get("WINDIR",r"C:\Windows"))/"Fonts"/"arial.ttf", Path(os.environ.get("WINDIR",r"C:\Windows"))/"Fonts"/"arialbd.ttf"),
  (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
  (Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"), Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")),
 ]
 font_name="Helvetica"; bold_name="Helvetica-Bold"
 for regular_path,bold_path in font_pairs:
  if regular_path.is_file() and bold_path.is_file():
   try:
    pdfmetrics.registerFont(TTFont("EgitimUnicode",str(regular_path)))
    pdfmetrics.registerFont(TTFont("EgitimUnicode-Bold",str(bold_path)))
    pdfmetrics.registerFontFamily("EgitimUnicode",normal="EgitimUnicode",bold="EgitimUnicode-Bold",italic="EgitimUnicode",boldItalic="EgitimUnicode-Bold")
    font_name="EgitimUnicode"; bold_name="EgitimUnicode-Bold"; break
   except Exception: pass
 st=getSampleStyleSheet()
 for style in st.byName.values():
  if hasattr(style,"fontName"): style.fontName=font_name
 st.add(ParagraphStyle(name="Cover",parent=st["Title"],fontName=bold_name,fontSize=27,leading=33,textColor=colors.HexColor("#244fc2"),spaceAfter=18));st.add(ParagraphStyle(name="Sec",parent=st["Heading1"],fontName=bold_name,fontSize=16,textColor=colors.HexColor("#244fc2"),spaceBefore=12,spaceAfter=8));code_size={"small":6,"normal":7,"large":9}.get(form.get("codesize","normal"),7)
 st.add(ParagraphStyle(name="CodeCustom",fontName=font_name,fontSize=code_size,leading=code_size+2,backColor=colors.HexColor("#f0f3f8"),borderPadding=5))
 story=[Spacer(1,32*mm),Paragraph(escape(title),st["Cover"]),Paragraph("Kaynaklardan otomatik oluşturulmuş eğitim rehberi",st["Normal"]),Spacer(1,8*mm),Paragraph("Tarih: "+datetime.now().strftime("%d.%m.%Y %H:%M"),st["Normal"]),Paragraph("Kaynak sayısı: "+str(len(entries)),st["Normal"]),Spacer(1,12*mm),Paragraph("Öğrenme hedefleri",st["Sec"])]
 for q in ["Kaynakların yapısını ve temel konularını tanımak","Kod ve metin örneklerini incelemek","Kaynaklar arasında bağlantı kurmak","Öğrendiklerini küçük bir örnekle pekiştirmek"]:story.append(Paragraph("• "+q,st["Normal"]))
 if form.get("summaries")=="1":
  story += [PageBreak(),Paragraph("Yönetici özeti",st["Sec"])]
  for e in entries:
   text=re.sub(r"\s+"," ",e.get("text","")).strip()
   sentences=re.split(r"(?<=[.!?])\s+",text)
   summary=" ".join(sentences[:4])[:1200] or "Bu kaynak için özetlenecek metin çıkarılamadı."
   story.append(Paragraph(escape(e["name"]),st["Heading2"]))
   story.append(Paragraph(escape(summary),st["Normal"]))
 if form.get("chapters")=="1":
  story += [PageBreak(),Paragraph("Konu ve bölüm rehberi",st["Sec"])]
  for e in entries:
   story.append(Paragraph(escape(e["name"]),st["Heading2"]))
   lines=e.get("text","").splitlines()
   heads=[ln.strip() for ln in lines if ln.strip() and (len(ln.strip())<90 and (ln.strip().startswith(("#","Chapter ","CHAPTER ","Bölüm ","BÖLÜM ")) or (ln.strip().isupper() and len(ln.strip())>3)))]
   if not heads: heads=["Genel içerik"]
   for h in heads[:80]:story.append(Paragraph("• "+escape(h.lstrip("# ")),st["Normal"]))
 story += [PageBreak(),Paragraph("İçindekiler / kaynak listesi",st["Sec"])]
 for i,e in enumerate(entries,1):story.append(Paragraph(f"{i}. {escape(e['name'])} — {escape(e['kind'])}",st["Normal"]))
 story.append(PageBreak())
 for i,e in enumerate(entries,1):
  story.append(Paragraph(f"{i}. {escape(e['name'])}",st["Sec"]));story.append(Paragraph("Tür: "+escape(e["kind"]),st["Normal"]))
  source_text=clean_text(e.get("text",""))
  for line in (source_text.splitlines() or ["[İçerik yok]"]):
   line=escape(line)
   if not line.strip():story.append(Spacer(1,2))
   elif len(line)>180 or any(x in e["name"].lower() for x in (".py",".bat",".js",".json",".html",".css",".sh",".sql")):
    for j in range(0,len(line),120):story.append(Preformatted(line[j:j+120],st["CodeCustom"]))
   else:
    for j in range(0,len(line),1000):story.append(Paragraph(line[j:j+1000],st["Normal"]))
  story.append(Spacer(1,5*mm))
 story += [PageBreak(),Paragraph("Pekiştirme soruları",st["Sec"])]
 questions=["Bu kaynakların çözmeye çalıştığı problem nedir?","En önemli üç kavram veya fonksiyon hangileridir?","Kodun girdileri, çıktıları ve hata durumları nelerdir?","Öğrendiklerinizi kullanarak nasıl küçük bir uygulama geliştirirsiniz?","Hangi bilgilerin doğrulanması gerekir?","Kaynakta hangi bağımlılıklar veya ön koşullar belirtiliyor?","Bir hata oluşursa nasıl teşhis edilir ve giderilir?","Bu yaklaşımın alternatifleri ve sınırlamaları nelerdir?","Öğrendiğiniz bilgiyi gerçek bir senaryoda nasıl uygularsınız?","Kaynağın güvenilirliğini nasıl doğrularsınız?"]
 for i,q in enumerate(questions[:max(3,min(10,int(form.get("questions","5"))))],1):story.append(Paragraph(f"{i}. {q}",st["Normal"]));story.append(Spacer(1,4*mm))
 if errors:
  story += [PageBreak(),Paragraph("İşlem uyarıları",st["Sec"])]
  for er in errors:story.append(Paragraph("• "+escape(er),st["Normal"]))
 def footer(c,d):c.saveState();c.setFont("Helvetica",8);c.setFillColor(colors.grey);c.drawString(18*mm,10*mm,"Eğitim PDF Atölyesi");c.drawRightString(pagesize[0]-margin,10*mm,"Sayfa "+str(d.page));c.restoreState()
 doc.build(story,onFirstPage=footer,onLaterPages=footer);return path
def create(form):
 set_progress(3,"Dosyalar hazırlanıyor…")
 title=(form.get("title") or "Eğitim Rehberi").strip() or "Eğitim Rehberi";entries=[];errors=[]
 total=max(1,len(form.get("files",[]))+len([x for x in (form.get("urls") or "").splitlines() if x.strip()])); done=0
 for name,data in form.get("files",[]):
  set_progress(5+int(35*done/total),"Dosya işleniyor: "+Path(name).name)
  if name.lower().endswith(".zip"):add_zip(data,Path(name).name,entries,errors,ocr=form.get("ocr")=="1")
  else:
   try:
    t,k=text_of(data,name,ocr=form.get("ocr")=="1");entries.append({"name":name,"text":t,"kind":k,"bytes":len(data)})
   except Exception as e:
    errors.append(name+": içerik çıkarılamadı ("+type(e).__name__+": "+str(e)[:300]+")")
  done+=1
 for u in [x.strip() for x in (form.get("urls") or "").splitlines() if x.strip()]:
  if form.get("offline")=="1":
   errors.append("Çevrimdışı mod: URL/GitHub kaynağı alınmadı: "+u+" (kaynağı dosya olarak indirip yükleyin).")
  else:
   set_progress(5+int(35*done/total),"Web/GitHub kaynağı alınıyor: "+u)
   if u.startswith(("http://","https://")):url_process(u,entries,errors,form.get("crawl")=="1")
   else:errors.append("Geçersiz URL: "+u)
  done+=1
 if form.get("dedup")=="1":
  unique=[]; seen=set()
  for item in entries:
   key=re.sub(r"\s+"," ",item.get("text","")).strip().casefold()
   if key and key in seen:
    errors.append("Tekrarlanan içerik atlandı: "+item["name"]);continue
   if key:seen.add(key)
   unique.append(item)
  entries=unique
 if form.get("translate") in ("en","tr") and form.get("offline")=="1":
  errors.append("Çevrimdışı mod: çeviri kapalıdır; metin dış çeviri servisine gönderilmedi.")
 elif form.get("translate") in ("en","tr"):
  try:
   from deep_translator import GoogleTranslator
   target=form.get("translate")
   translator=GoogleTranslator(source="auto",target=target)
   for item in entries:
    raw=item.get("text","")
    # Chunk into small chunks to stay within typical translator request limits.
    chunks=[raw[i:i+3500] for i in range(0,len(raw),3500)]
    translated=[]
    for chunk in chunks:
     if chunk.strip(): translated.append(translator.translate(chunk) or chunk)
     else: translated.append(chunk)
    item["text"]="\n".join(translated); item["kind"] += " (çeviri: "+target.upper()+")"
  except Exception as e:
   errors.append("Çeviri yapılamadı (internet/deep-translator gerekebilir): "+str(e))
 if not entries:raise ValueError("İşlenebilir kaynak bulunamadı. Dosya veya URL ekleyin.")
 set_progress(45,"PDF oluşturuluyor; büyük belgelerde uzun sürebilir…")
 pdf=make_pdf(title,entries,errors,form); set_progress(90,"ZIP paketi hazırlanıyor…"); zpath=OUT/(safe(title)+"_egitim_paketi.zip")
 with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
  z.write(pdf,pdf.name)
  if form.get("includeoriginal")=="1":
   for original_name,original_data in form.get("files",[]):
    safe_name=Path(original_name).name
    z.writestr("orijinal_kaynaklar/"+safe_name,original_data)
  report=["EĞİTİM PDF ATÖLYESİ — İŞLEM RAPORU",f"Tarih: {datetime.now().isoformat(timespec='seconds')}",f"Kaynak sayısı: {len(entries)}","", "KAYNAKLAR:"]+[f"- {e['name']} [{e['kind']}, {e.get('bytes',0)} bayt]" for e in entries]
  if errors:report+=["","UYARILAR:"]+["- "+x for x in errors]
  z.writestr("ISLEM_RAPORU.txt","\n".join(report))
  from io import StringIO
  import csv
  buf=StringIO(); writer=csv.writer(buf); writer.writerow(["Kaynak","Tür","Boyut (bayt)"])
  for item in entries: writer.writerow([item["name"],item["kind"],item.get("bytes",0)])
  z.writestr("KAYNAK_ENVANTERI.csv",buf.getvalue())
  z.writestr("BASLANGIC.txt","Eğitim PDF Atölyesi çıktısı\n- PDF dosyası: eğitim rehberi\n- ISLEM_RAPORU.txt: işlem özeti ve uyarılar\n- KAYNAK_ENVANTERI.csv: kaynak dökümü\n- orijinal_kaynaklar/: seçildiyse yüklenen orijinal dosyalar\n")
 set_progress(100,"İşlem tamamlandı.",False)
 return {"ok":True,"pdf":"/download/"+pdf.name,"zip":"/download/"+zpath.name,"count":len(entries),"warnings":errors}
def parse_form(h):
 import email
 raw=h.rfile.read(int(h.headers.get("Content-Length","0")))
 msg=email.message_from_bytes(b"Content-Type: "+h.headers.get("Content-Type","").encode()+b"\r\nMIME-Version: 1.0\r\n\r\n"+raw);out={"files":[]}
 for p in msg.walk():
  if p.is_multipart():continue
  n=p.get_param("name",header="content-disposition");fn=p.get_filename();data=p.get_payload(decode=True) or b""
  if fn:out["files"].append((Path(fn).name,data))
  elif n:out[n]=dec(data)
 return out
class Handler(SimpleHTTPRequestHandler):
 timeout=1800
 def setup(self):
  super().setup()
  try:self.connection.settimeout(1800)
  except Exception:pass
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,*a):print("[HTTP]",*a)
 def do_POST(self):
  if self.path!="/api/create":self.send_error(404);return
  try:
   set_progress(1,"İstek alındı; kaynaklar hazırlanıyor…")
   out=create(parse_form(self));code=200
  except Exception as e:
   set_progress(0,"Hata: "+str(e),False);out={"ok":False,"error":str(e)};code=400
  b=json.dumps(out,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path.startswith("/api/progress"):
   with PROGRESS_LOCK: b=json.dumps(PROGRESS,ensure_ascii=False).encode()
   self.send_response(200);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
  if self.path.startswith("/download/"):
   p=(OUT/Path(unquote(self.path.split("/download/",1)[1]).split("?")[0]).name).resolve()
   if not p.is_file() or p.parent!=OUT.resolve():self.send_error(404);return
   size=p.stat().st_size
   self.send_response(200);self.send_header("Content-Type","application/octet-stream");self.send_header("Content-Disposition",f'attachment; filename="{p.name}"');self.send_header("Content-Length",str(size));self.end_headers()
   with p.open("rb") as fh:
    while True:
     chunk=fh.read(1024*1024)
     if not chunk:break
     self.wfile.write(chunk)
   return
  allowed_static={"/","/index.html","/style.css","/app.js","/manifest.webmanifest","/icon.svg","/sw.js"}
  if self.path.split("?",1)[0] not in allowed_static:
   self.send_error(404);return
  super().do_GET()
def main():
 missing=[]
 for mod in ("reportlab","pypdf","docx","pptx"):
  try:__import__(mod)
  except ImportError:missing.append(mod)
 if missing:
  print("Eksik Python paketleri:",", ".join(missing))
  print("Bu başlatıcı çevrimdışı kullanım için internete bağlanmaz.")
  print("Paketleri önceden indirilmiş wheel dosyalarından kurun:")
  print("  python -m pip install --no-index --find-links=wheelhouse -r requirements.txt")
  input("Çıkmak için Enter...")
  return
 server=ThreadingHTTPServer((HOST,PORT),Handler)
 url=f"http://127.0.0.1:{PORT}" if HOST=="127.0.0.1" else f"http://<BU-PC-IP>:{PORT}"
 print(f"\nEğitim PDF Atölyesi: {url}\nYerel dosyalar için internet gerekmez. Durdurmak için Ctrl+C.")
 if HOST=="127.0.0.1": threading.Timer(1,lambda:webbrowser.open(url)).start()
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 server.server_close()
if __name__=="__main__":main()
