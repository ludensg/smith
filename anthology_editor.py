#!/usr/bin/env python3
"""
Anthology Track Editor
Run with:   python3 anthology_editor.py
Requires:   Python 3.8+  +  tkinter
"""

import copy, json, os, tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_TITLE    = "Anthology Track Editor"
DEFAULT_JSON = "tracks.json"
VOLUMES      = {"I": "Ballads", "II": "Social Music", "III": "Songs"}

SIMPLE_FIELDS = [
    ("v",              "Volume",               "volume"),
    ("o",              "Order in volume",       "int"),
    ("t",              "Title",                 "text"),
    ("labelInfo",      "Info on original label","text"),
    ("a",              "Artist",                "text"),
    ("instrumentation","Instrumentation",       "text"),
    ("y",              "Recording date",        "text"),
    ("issueNumber",    "Issue / master number", "text"),
    ("g",              "Genre / tag",           "text"),
]

def blank_track():
    return {"n":"","v":"I","o":1,"t":"","labelInfo":"","a":"","instrumentation":"",
            "y":"","issueNumber":"","g":"","h":"","notes":"",
            "discography":[],"bibliography":[],"spotifyLinks":[],
            "imgsTop":[],"imgsBottom":[]}

def make_n(v,o): return f"{v}·{o}"


# ── helper: get colors from any widget ancestor ──────────────────
def _colors(widget):
    w = widget
    while w and not hasattr(w,'colors'):
        w = getattr(w,'master',None)
    return w.colors if w else {"bg":"#161310","fg":"#EEE4C8","panel":"#1E1A14","accent":"#C8860A","sel":"#3A2D18"}


# ── single-line string prompt ─────────────────────────────────────
def _ask_string(parent, prompt, initial=""):
    top = tk.Toplevel(parent); top.title(prompt)
    top.geometry("500x120"); top.resizable(True,False); top.grab_set()
    C = _colors(parent); top.configure(bg=C["bg"])
    result=[None]
    frm=tk.Frame(top,bg=C["bg"],padx=14,pady=14)
    frm.pack(fill="both",expand=True); frm.columnconfigure(0,weight=1)
    var=tk.StringVar(value=initial)
    e=ttk.Entry(frm,textvariable=var,width=62)
    e.grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,10)); e.focus_set(); e.select_range(0,"end")
    def ok(): result[0]=var.get(); top.destroy()
    tk.Button(frm,text="OK",command=ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=10,pady=4).grid(row=1,column=1,sticky="e")
    tk.Button(frm,text="Cancel",command=top.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).grid(row=1,column=0,sticky="e",padx=(0,8))
    frm.bind_all("<Return>",lambda _:ok()); top.wait_window(top); return result[0]


# ── generic list-of-strings dialog ───────────────────────────────
class StringListDialog(tk.Toplevel):
    def __init__(self,parent,title,items):
        super().__init__(parent); self.title(title)
        self.geometry("580x320"); self.resizable(True,True); self.grab_set()
        self.result=None; self._items=list(items or [])
        C=parent.colors; self.configure(bg=C["bg"])
        tb=tk.Frame(self,bg=C["bg"]); tb.pack(fill="x",padx=10,pady=(10,4))
        tk.Label(tb,text=title,bg=C["bg"],fg=C["accent"],font=("Georgia",12,"bold")).pack(side="left")
        tk.Button(tb,text="+ Add",command=self._add,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).pack(side="right")
        lf=tk.Frame(self,bg=C["bg"]); lf.pack(fill="both",expand=True,padx=10,pady=4)
        self._lb=tk.Listbox(lf,bg=C["panel"],fg=C["fg"],selectbackground=C["sel"],selectforeground="#FFF4DC",font=("Courier",9),activestyle="none",borderwidth=0,highlightthickness=0)
        sb=ttk.Scrollbar(lf,orient="vertical",command=self._lb.yview); self._lb.configure(yscrollcommand=sb.set)
        self._lb.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._lb.bind("<Double-Button-1>",lambda _:self._edit())
        rb=tk.Frame(self,bg=C["bg"]); rb.pack(fill="x",padx=10,pady=4)
        for lbl,cmd in [("Edit",self._edit),("Delete",self._delete),("↑",self._up),("↓",self._dn)]:
            tk.Button(rb,text=lbl,command=cmd,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=3).pack(side="left",padx=(0,6))
        bb=tk.Frame(self,bg=C["bg"]); bb.pack(fill="x",padx=10,pady=(4,10))
        tk.Button(bb,text="OK",command=self._ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=12,pady=5).pack(side="right")
        tk.Button(bb,text="Cancel",command=self.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=10,pady=5).pack(side="right",padx=(0,8))
        self._refresh(); self.wait_window(self)
    def _refresh(self):
        self._lb.delete(0,"end")
        for item in self._items: self._lb.insert("end",f"  {(item[:72]+'…') if len(item)>72 else item}")
    def _sel(self): s=self._lb.curselection(); return s[0] if s else None
    def _add(self):
        v=_ask_string(self,"Add entry","")
        if v is not None: self._items.append(v); self._refresh(); self._lb.selection_set(len(self._items)-1)
    def _edit(self):
        idx=self._sel()
        if idx is None: return
        v=_ask_string(self,"Edit entry",self._items[idx])
        if v is not None: self._items[idx]=v; self._refresh(); self._lb.selection_set(idx)
    def _delete(self):
        idx=self._sel()
        if idx is None: return
        if messagebox.askyesno("Delete","Remove this entry?",parent=self): del self._items[idx]; self._refresh()
    def _up(self):
        idx=self._sel()
        if idx is None or idx==0: return
        self._items[idx-1],self._items[idx]=self._items[idx],self._items[idx-1]; self._refresh(); self._lb.selection_set(idx-1)
    def _dn(self):
        idx=self._sel()
        if idx is None or idx>=len(self._items)-1: return
        self._items[idx],self._items[idx+1]=self._items[idx+1],self._items[idx]; self._refresh(); self._lb.selection_set(idx+1)
    def _ok(self): self.result=self._items; self.destroy()


# ── spotify links dialog ──────────────────────────────────────────
class SpotifyLinksDialog(tk.Toplevel):
    def __init__(self,parent,links):
        super().__init__(parent); self.title("Spotify links")
        self.geometry("640x340"); self.resizable(True,True); self.grab_set()
        self.result=None; self._links=copy.deepcopy(links or [])
        C=parent.colors; self.configure(bg=C["bg"])
        tb=tk.Frame(self,bg=C["bg"]); tb.pack(fill="x",padx=10,pady=(10,4))
        tk.Label(tb,text="Spotify links",bg=C["bg"],fg=C["accent"],font=("Georgia",12,"bold")).pack(side="left")
        tk.Label(tb,text="  ·  ID = part after open.spotify.com/track/",bg=C["bg"],fg="#7A6A50",font=("Georgia",8,"italic")).pack(side="left")
        tk.Button(tb,text="+ Add",command=self._add,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).pack(side="right")
        lf=tk.Frame(self,bg=C["bg"]); lf.pack(fill="both",expand=True,padx=10,pady=4)
        self._lb=tk.Listbox(lf,bg=C["panel"],fg=C["fg"],selectbackground=C["sel"],selectforeground="#FFF4DC",font=("Courier",9),activestyle="none",borderwidth=0,highlightthickness=0)
        sb=ttk.Scrollbar(lf,orient="vertical",command=self._lb.yview); self._lb.configure(yscrollcommand=sb.set)
        self._lb.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._lb.bind("<Double-Button-1>",lambda _:self._edit())
        rb=tk.Frame(self,bg=C["bg"]); rb.pack(fill="x",padx=10,pady=4)
        for lbl,cmd in [("Edit",self._edit),("Delete",self._delete),("↑",self._up),("↓",self._dn)]:
            tk.Button(rb,text=lbl,command=cmd,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=3).pack(side="left",padx=(0,6))
        bb=tk.Frame(self,bg=C["bg"]); bb.pack(fill="x",padx=10,pady=(4,10))
        tk.Button(bb,text="OK",command=self._ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=12,pady=5).pack(side="right")
        tk.Button(bb,text="Cancel",command=self.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=10,pady=5).pack(side="right",padx=(0,8))
        self._refresh(); self.wait_window(self)
    def _refresh(self):
        self._lb.delete(0,"end")
        for lk in self._links: self._lb.insert("end",f"  {(lk.get('label') or '—'):<28}  {lk.get('id','—')}")
    def _sel(self): s=self._lb.curselection(); return s[0] if s else None
    def _add(self):
        dlg=_SpotifyEntryDialog(self,{})
        if dlg.result: self._links.append(dlg.result); self._refresh(); self._lb.selection_set(len(self._links)-1)
    def _edit(self):
        idx=self._sel()
        if idx is None: return
        dlg=_SpotifyEntryDialog(self,self._links[idx])
        if dlg.result: self._links[idx]=dlg.result; self._refresh(); self._lb.selection_set(idx)
    def _delete(self):
        idx=self._sel()
        if idx is None: return
        if messagebox.askyesno("Delete","Remove this Spotify link?",parent=self): del self._links[idx]; self._refresh()
    def _up(self):
        idx=self._sel()
        if idx is None or idx==0: return
        self._links[idx-1],self._links[idx]=self._links[idx],self._links[idx-1]; self._refresh(); self._lb.selection_set(idx-1)
    def _dn(self):
        idx=self._sel()
        if idx is None or idx>=len(self._links)-1: return
        self._links[idx],self._links[idx+1]=self._links[idx+1],self._links[idx]; self._refresh(); self._lb.selection_set(idx+1)
    def _ok(self): self.result=self._links; self.destroy()

class _SpotifyEntryDialog(tk.Toplevel):
    def __init__(self,parent,link):
        super().__init__(parent); self.title("Spotify entry")
        self.geometry("520x160"); self.resizable(True,False); self.grab_set()
        self.result=None; C=_colors(parent); self.configure(bg=C["bg"])
        frm=tk.Frame(self,bg=C["bg"],padx=16,pady=14); frm.pack(fill="both",expand=True); frm.columnconfigure(1,weight=1)
        self._vars={}
        for row,(lbl,key) in enumerate([("Track ID","id"),("Label","label")]):
            tk.Label(frm,text=lbl,bg=C["bg"],fg=C["fg"],font=("Georgia",10)).grid(row=row,column=0,sticky="w",padx=(0,12),pady=6)
            var=tk.StringVar(value=link.get(key) or "")
            e=ttk.Entry(frm,textvariable=var,width=50); e.grid(row=row,column=1,sticky="ew",pady=6)
            if row==0: e.focus_set()
            self._vars[key]=var
        bb=tk.Frame(frm,bg=C["bg"]); bb.grid(row=2,column=0,columnspan=2,sticky="e",pady=(8,0))
        tk.Button(bb,text="OK",command=self._ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=10,pady=4).pack(side="right")
        tk.Button(bb,text="Cancel",command=self.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).pack(side="right",padx=(0,8))
        self.bind("<Return>",lambda _:self._ok()); self.bind("<Escape>",lambda _:self.destroy()); self.wait_window(self)
    def _ok(self):
        id_=self._vars["id"].get().strip()
        if not id_: messagebox.showwarning("Missing ID","Track ID cannot be empty.",parent=self); return
        self.result={"id":id_,"label":self._vars["label"].get().strip()}; self.destroy()


# ── image slot dialog ─────────────────────────────────────────────
class ImageSlotDialog(tk.Toplevel):
    def __init__(self,parent,title,images):
        super().__init__(parent); self.title(title)
        self.geometry("680x400"); self.resizable(True,True); self.grab_set()
        self.result=None; self._imgs=copy.deepcopy(images or [])
        C=parent.colors; self.configure(bg=C["bg"])
        tb=tk.Frame(self,bg=C["bg"]); tb.pack(fill="x",padx=10,pady=(10,4))
        tk.Label(tb,text=title,bg=C["bg"],fg=C["accent"],font=("Georgia",12,"bold")).pack(side="left")
        tk.Button(tb,text="+ Add image",command=self._add,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).pack(side="right")
        lf=tk.Frame(self,bg=C["bg"]); lf.pack(fill="both",expand=True,padx=10,pady=4)
        self._lb=tk.Listbox(lf,bg=C["panel"],fg=C["fg"],selectbackground=C["sel"],selectforeground="#FFF4DC",font=("Courier",9),activestyle="none",borderwidth=0,highlightthickness=0)
        sb=ttk.Scrollbar(lf,orient="vertical",command=self._lb.yview); self._lb.configure(yscrollcommand=sb.set)
        self._lb.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._lb.bind("<Double-Button-1>",lambda _:self._edit())
        rb=tk.Frame(self,bg=C["bg"]); rb.pack(fill="x",padx=10,pady=4)
        for lbl,cmd in [("Edit",self._edit),("Delete",self._delete),("↑",self._up),("↓",self._dn)]:
            tk.Button(rb,text=lbl,command=cmd,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=3).pack(side="left",padx=(0,6))
        bb=tk.Frame(self,bg=C["bg"]); bb.pack(fill="x",padx=10,pady=(4,10))
        tk.Button(bb,text="OK",command=self._ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=12,pady=5).pack(side="right")
        tk.Button(bb,text="Cancel",command=self.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=10,pady=5).pack(side="right",padx=(0,8))
        self._refresh(); self.wait_window(self)
    def _refresh(self):
        self._lb.delete(0,"end")
        for i,img in enumerate(self._imgs):
            url=img.get("url",""); short=(url[:60]+"…") if len(url)>60 else url
            self._lb.insert("end",f"  [{i+1}]  {short}   ·   {img.get('credit','—')}")
    def _sel(self): s=self._lb.curselection(); return s[0] if s else None
    def _add(self):
        dlg=_ImageEntryDialog(self,{})
        if dlg.result: self._imgs.append(dlg.result); self._refresh(); self._lb.selection_set(len(self._imgs)-1)
    def _edit(self):
        idx=self._sel()
        if idx is None: return
        dlg=_ImageEntryDialog(self,self._imgs[idx])
        if dlg.result: self._imgs[idx]=dlg.result; self._refresh(); self._lb.selection_set(idx)
    def _delete(self):
        idx=self._sel()
        if idx is None: return
        if messagebox.askyesno("Delete","Remove this image?",parent=self): del self._imgs[idx]; self._refresh()
    def _up(self):
        idx=self._sel()
        if idx is None or idx==0: return
        self._imgs[idx-1],self._imgs[idx]=self._imgs[idx],self._imgs[idx-1]; self._refresh(); self._lb.selection_set(idx-1)
    def _dn(self):
        idx=self._sel()
        if idx is None or idx>=len(self._imgs)-1: return
        self._imgs[idx],self._imgs[idx+1]=self._imgs[idx+1],self._imgs[idx]; self._refresh(); self._lb.selection_set(idx+1)
    def _ok(self): self.result=self._imgs; self.destroy()

class _ImageEntryDialog(tk.Toplevel):
    def __init__(self,parent,img):
        super().__init__(parent); self.title("Image entry")
        self.geometry("560x180"); self.resizable(True,False); self.grab_set()
        self.result=None; C=_colors(parent); self.configure(bg=C["bg"])
        frm=tk.Frame(self,bg=C["bg"],padx=16,pady=14); frm.pack(fill="both",expand=True); frm.columnconfigure(1,weight=1)
        self._vars={}
        for row,(lbl,key) in enumerate([("URL","url"),("Credit","credit")]):
            tk.Label(frm,text=lbl,bg=C["bg"],fg=C["fg"],font=("Georgia",10)).grid(row=row,column=0,sticky="w",padx=(0,12),pady=6)
            var=tk.StringVar(value=img.get(key) or "")
            e=ttk.Entry(frm,textvariable=var,width=56); e.grid(row=row,column=1,sticky="ew",pady=6)
            if row==0: e.focus_set()
            self._vars[key]=var
        bb=tk.Frame(frm,bg=C["bg"]); bb.grid(row=2,column=0,columnspan=2,sticky="e",pady=(8,0))
        tk.Button(bb,text="OK",command=self._ok,bg=C["accent"],fg="#1A1208",relief="flat",padx=10,pady=4).pack(side="right")
        tk.Button(bb,text="Cancel",command=self.destroy,bg=C["panel"],fg=C["fg"],relief="flat",padx=8,pady=4).pack(side="right",padx=(0,8))
        self.bind("<Return>",lambda _:self._ok()); self.bind("<Escape>",lambda _:self.destroy()); self.wait_window(self)
    def _ok(self):
        url=self._vars["url"].get().strip()
        if not url: messagebox.showwarning("Missing URL","URL cannot be empty.",parent=self); return
        self.result={"url":url,"credit":self._vars["credit"].get().strip()}; self.destroy()


# ── main editor ───────────────────────────────────────────────────
class AnthologyEditor(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP_TITLE)
        self.geometry("1060x720"); self.minsize(900,560)
        self.json_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),DEFAULT_JSON)
        self.tracks=[]; self.current_index=None
        self.field_vars={}; self.field_widgets={}
        self._build_style(); self._build_layout(); self._load_initial()

    def _build_style(self):
        st=ttk.Style(self)
        try: st.theme_use("clam")
        except tk.TclError: pass
        bg,panel,fg,accent,sel="#161310","#1E1A14","#EEE4C8","#C8860A","#3A2D18"
        self.configure(bg=bg); self.colors=dict(bg=bg,panel=panel,fg=fg,accent=accent,sel=sel)
        st.configure(".",background=bg,foreground=fg,fieldbackground=panel,font=("Georgia",10))
        st.configure("Treeview",background=panel,fieldbackground=panel,foreground=fg,rowheight=24,borderwidth=0)
        st.configure("Treeview.Heading",background="#2A241C",foreground=accent,font=("Georgia",9,"bold"))
        st.map("Treeview",background=[("selected",sel)],foreground=[("selected","#FFF4DC")])
        for name,bg_,fg_ in [("TButton","#2A241C",fg),("Accent.TButton",accent,"#1A1208"),
                               ("Img.TButton","#2A3020","#B8D898"),("List.TButton","#20241A","#A8C898")]:
            st.configure(name,background=bg_,foreground=fg_,borderwidth=1,focusthickness=1,padding=5)
            st.map(name,background=[("active","#3A2D18")])
        st.configure("TLabel",background=bg,foreground=fg)
        st.configure("Header.TLabel",background=bg,foreground=accent,font=("Georgia",13,"bold"))
        st.configure("Sub.TLabel",background=bg,foreground="#8C7B60",font=("Georgia",9,"italic"))
        st.configure("TEntry",fieldbackground=panel,foreground=fg,insertcolor=fg)
        st.configure("TCombobox",fieldbackground=panel,foreground=fg)
        st.configure("TFrame",background=bg); st.configure("Panel.TFrame",background=panel)

    def _build_layout(self):
        root=ttk.Frame(self); root.pack(fill="both",expand=True,padx=12,pady=12)
        hdr=ttk.Frame(root); hdr.pack(fill="x",pady=(0,10))
        ttk.Label(hdr,text="Anthology Track Editor",style="Header.TLabel").pack(side="left")
        ttk.Label(hdr,text=f"  ·  {DEFAULT_JSON}",style="Sub.TLabel").pack(side="left")
        body=ttk.Frame(root); body.pack(fill="both",expand=True)
        body.columnconfigure(0,weight=0,minsize=300); body.columnconfigure(1,weight=1); body.rowconfigure(0,weight=1)

        # left
        left=ttk.Frame(body); left.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        left.rowconfigure(1,weight=1); left.columnconfigure(0,weight=1)
        lh=ttk.Frame(left); lh.grid(row=0,column=0,sticky="ew",pady=(0,6))
        ttk.Label(lh,text="Tracks").pack(side="left")
        ttk.Button(lh,text="+ New",command=self.add_track,width=8).pack(side="right")
        self.tree=ttk.Treeview(left,columns=("num","title","vol"),show="headings",selectmode="browse")
        for col,hd,w in [("num","#",48),("title","Title",200),("vol","Vol",40)]:
            self.tree.heading(col,text=hd); self.tree.column(col,width=w,anchor="w" if col=="title" else "center")
        self.tree.grid(row=1,column=0,sticky="nsew"); self.tree.bind("<<TreeviewSelect>>",self.on_select)
        lb2=ttk.Frame(left); lb2.grid(row=2,column=0,sticky="ew",pady=(6,0))
        ttk.Button(lb2,text="Duplicate",command=self.duplicate).pack(side="left",padx=(0,6))
        ttk.Button(lb2,text="Delete",command=self.delete).pack(side="left")
        ttk.Button(lb2,text="↑",width=3,command=lambda:self.move(-1)).pack(side="right",padx=(6,0))
        ttk.Button(lb2,text="↓",width=3,command=lambda:self.move(1)).pack(side="right")

        # right — scrollable canvas
        rf=ttk.Frame(body,style="Panel.TFrame"); rf.grid(row=0,column=1,sticky="nsew")
        rf.rowconfigure(0,weight=1); rf.columnconfigure(0,weight=1)
        canvas=tk.Canvas(rf,bg=self.colors["panel"],highlightthickness=0,borderwidth=0)
        vsb=ttk.Scrollbar(rf,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0,column=0,sticky="nsew"); vsb.grid(row=0,column=1,sticky="ns")
        self._ff=ttk.Frame(canvas,style="Panel.TFrame",padding=16)
        self._fw=canvas.create_window((0,0),window=self._ff,anchor="nw")
        self._ff.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfig(self._fw,width=e.width))
        canvas.bind_all("<MouseWheel>",lambda e:canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        right=self._ff; right.columnconfigure(1,weight=1)
        self.form_title=ttk.Label(right,text="No track selected",style="Header.TLabel",background=self.colors["panel"])
        self.form_title.grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,12))
        row=1

        for key,label,kind in SIMPLE_FIELDS:
            ttk.Label(right,text=label,background=self.colors["panel"]).grid(row=row,column=0,sticky="nw",pady=5,padx=(0,10))
            if kind=="volume":
                var=tk.StringVar()
                w=ttk.Combobox(right,textvariable=var,values=list(VOLUMES.keys()),state="readonly",width=8)
                w.grid(row=row,column=1,sticky="w",pady=5)
            else:
                var=tk.StringVar()
                w=ttk.Entry(right,textvariable=var,width=48); w.grid(row=row,column=1,sticky="ew",pady=5)
            self.field_vars[key]=var; self.field_widgets[key]=w; row+=1

        # headline
        ttk.Label(right,text="Headline synopsis",background=self.colors["panel"]).grid(row=row,column=0,sticky="nw",pady=5,padx=(0,10))
        self._h_text=tk.Text(right,height=3,width=46,wrap="word",bg=self.colors["panel"],fg=self.colors["fg"],insertbackground=self.colors["fg"],relief="solid",borderwidth=1)
        self._h_text.grid(row=row,column=1,sticky="ew",pady=5); row+=1

        # notes
        ttk.Label(right,text="General notes",background=self.colors["panel"]).grid(row=row,column=0,sticky="nw",pady=5,padx=(0,10))
        self._notes_text=tk.Text(right,height=4,width=46,wrap="word",bg=self.colors["panel"],fg=self.colors["fg"],insertbackground=self.colors["fg"],relief="solid",borderwidth=1)
        self._notes_text.grid(row=row,column=1,sticky="ew",pady=5); row+=1

        # list-type fields
        self._list_vars={}
        for key,label,kind,dlg_type in [
            ("discography", "Discography",        "list","StringList"),
            ("bibliography","Bibliography",        "list","StringList"),
            ("spotifyLinks","Spotify links",       "spotify","Spotify"),
            ("imgsTop",     "Images (above card)", "img","Img"),
            ("imgsBottom",  "Images (below card)", "img","Img"),
        ]:
            ttk.Label(right,text=label,background=self.colors["panel"]).grid(row=row,column=0,sticky="w",pady=5,padx=(0,10))
            frm=ttk.Frame(right,style="Panel.TFrame"); frm.grid(row=row,column=1,sticky="ew",pady=5)
            var=tk.StringVar(value="0 entries"); self._list_vars[key]=var
            ttk.Label(frm,textvariable=var,background=self.colors["panel"],foreground="#8C7B60").pack(side="left",padx=(0,10))
            btn_style="Img.TButton" if kind=="img" else "List.TButton"
            ttk.Button(frm,text="Edit…",command=lambda k=key,dt=dlg_type:self._open_slot(k,dt),style=btn_style).pack(side="left")
            row+=1

        act=ttk.Frame(right,style="Panel.TFrame"); act.grid(row=row,column=0,columnspan=2,sticky="ew",pady=(10,0))
        ttk.Button(act,text="Apply changes to this track",command=self.commit,style="Accent.TButton").pack(side="left")

        bot=ttk.Frame(root); bot.pack(fill="x",pady=(12,0))
        ttk.Button(bot,text="Load JSON…",command=self.load_dialog).pack(side="left")
        ttk.Button(bot,text="Save",command=self.save,style="Accent.TButton").pack(side="left",padx=(8,0))
        ttk.Button(bot,text="Save As…",command=self.save_as).pack(side="left",padx=(8,0))
        self.status=tk.StringVar(value="Ready.")
        ttk.Label(bot,textvariable=self.status,style="Sub.TLabel").pack(side="right")

    def _open_slot(self,key,dlg_type):
        if self.current_index is None: messagebox.showinfo("No track","Select a track first.",parent=self); return
        t=self.tracks[self.current_index]; data=t.get(key) or []
        if dlg_type=="StringList":
            dlg=StringListDialog(self,"Discography" if key=="discography" else "Bibliography",data)
        elif dlg_type=="Spotify":
            dlg=SpotifyLinksDialog(self,data)
        else:
            dlg=ImageSlotDialog(self,"Images above the card" if key=="imgsTop" else "Images below the card",data)
        if dlg.result is not None:
            t[key]=dlg.result; self._refresh_slot_label(key,t)
            self.status.set(f"Updated '{key}' for '{t.get('t')}' (not yet saved)")

    def _refresh_slot_label(self,key,t):
        n=len(t.get(key) or [])
        self._list_vars[key].set(f"{n} {'entry' if n==1 else 'entries'}")

    def _refresh_all_slot_labels(self,t):
        for key in self._list_vars: self._refresh_slot_label(key,t)

    def _load_initial(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path,encoding="utf-8") as f: self.tracks=json.load(f)
                self._migrate_all()
                self.status.set(f"Loaded {len(self.tracks)} tracks from {self.json_path}")
            except Exception as e:
                messagebox.showwarning("Load error",str(e),parent=self); self.tracks=[]
        else:
            self.tracks=[]; self.status.set("No tracks.json found — starting empty.")
        self.refresh_tree()

    def _migrate_all(self):
        for t in self.tracks:
            if "img" in t or "imgC" in t:
                oi=t.pop("img",None); oc=t.pop("imgC",None)
                if "imgsTop" not in t: t["imgsTop"]=[{"url":oi,"credit":oc or ""}] if oi else []
            if "spotify" in t:
                os_=t.pop("spotify")
                if "spotifyLinks" not in t: t["spotifyLinks"]=[{"id":os_,"label":"Primary recording"}] if os_ else []
            for key,default in [("imgsTop",[]),("imgsBottom",[]),("spotifyLinks",[]),
                                  ("labelInfo",""),("instrumentation",""),("issueNumber",""),
                                  ("notes",""),("discography",[]),("bibliography",[])]:
                t.setdefault(key,default)

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        vo={"I":0,"II":1,"III":2}
        for idx,t in sorted(enumerate(self.tracks),key=lambda p:(vo.get(p[1].get("v","I"),9),p[1].get("o",0))):
            self.tree.insert("","end",iid=str(idx),values=(t.get("n",""),t.get("t",""),t.get("v","")))

    def on_select(self,_=None):
        sel=self.tree.selection()
        if sel: self.load_form(int(sel[0]))

    def load_form(self,idx):
        self.current_index=idx; t=self.tracks[idx]
        self.form_title.config(text=f"Editing: {t.get('t') or '(untitled)'}")
        for key,_,kind in SIMPLE_FIELDS:
            val=t.get(key); self.field_vars[key].set(str(val) if val is not None else "")
        self._h_text.delete("1.0","end"); self._h_text.insert("1.0",t.get("h") or "")
        self._notes_text.delete("1.0","end"); self._notes_text.insert("1.0",t.get("notes") or "")
        self._refresh_all_slot_labels(t)

    def commit(self):
        if self.current_index is None: messagebox.showinfo("No track","Select or create a track first.",parent=self); return
        t=self.tracks[self.current_index]
        for key,label,kind in SIMPLE_FIELDS:
            raw=self.field_vars[key].get().strip()
            if kind=="int":
                try: t[key]=int(raw) if raw else 1
                except ValueError: messagebox.showerror("Bad number",f"'{label}' must be a whole number.",parent=self); return
            else: t[key]=raw if raw else ""
        t["h"]=self._h_text.get("1.0","end").strip()
        t["notes"]=self._notes_text.get("1.0","end").strip()
        t["n"]=make_n(t.get("v","I"),t.get("o",1))
        for key in ("discography","bibliography","spotifyLinks","imgsTop","imgsBottom"): t.setdefault(key,[])
        self.refresh_tree(); self.tree.selection_set(str(self.current_index))
        self.status.set(f"Updated '{t.get('t')}' (not yet saved)")

    def add_track(self):
        self.tracks.append(blank_track()); idx=len(self.tracks)-1
        self.refresh_tree(); self.tree.selection_set(str(idx)); self.load_form(idx)
        self.status.set("New blank track added.")

    def duplicate(self):
        if self.current_index is None: return
        nt=copy.deepcopy(self.tracks[self.current_index]); nt["t"]=(nt.get("t") or "")+" (copy)"
        self.tracks.append(nt); idx=len(self.tracks)-1
        self.refresh_tree(); self.tree.selection_set(str(idx)); self.load_form(idx)

    def delete(self):
        if self.current_index is None: return
        t=self.tracks[self.current_index]
        if not messagebox.askyesno("Delete",f"Delete '{t.get('t') or 'this track'}'?",parent=self): return
        del self.tracks[self.current_index]; self.current_index=None
        self.form_title.config(text="No track selected")
        for key,_,kind in SIMPLE_FIELDS: self.field_vars[key].set("")
        self._h_text.delete("1.0","end"); self._notes_text.delete("1.0","end")
        for key in self._list_vars: self._list_vars[key].set("0 entries")
        self.refresh_tree(); self.status.set("Track deleted (not yet saved).")

    def move(self,direction):
        if self.current_index is None: return
        t=self.tracks[self.current_index]; vol=t.get("v")
        sib=sorted([i for i,x in enumerate(self.tracks) if x.get("v")==vol],key=lambda i:self.tracks[i].get("o",0))
        pos=sib.index(self.current_index); np_=pos+direction
        if np_<0 or np_>=len(sib): return
        oi=sib[np_]
        self.tracks[self.current_index]["o"],self.tracks[oi]["o"]=self.tracks[oi]["o"],self.tracks[self.current_index]["o"]
        for i in (self.current_index,oi): self.tracks[i]["n"]=make_n(self.tracks[i]["v"],self.tracks[i]["o"])
        self.refresh_tree(); self.tree.selection_set(str(self.current_index))

    def load_dialog(self):
        path=filedialog.askopenfilename(parent=self,title="Open tracks JSON",filetypes=[("JSON","*.json"),("All","*.*")],initialdir=os.path.dirname(self.json_path))
        if not path: return
        try:
            with open(path,encoding="utf-8") as f: data=json.load(f)
            if not isinstance(data,list): raise ValueError("Root must be a JSON array.")
            self.tracks=data; self.json_path=path; self.current_index=None
            self._migrate_all(); self.refresh_tree()
            self.status.set(f"Loaded {len(self.tracks)} tracks from {path}")
        except Exception as e: messagebox.showerror("Load error",str(e),parent=self)

    def _validate(self):
        problems=[]
        for i,t in enumerate(self.tracks):
            if not t.get("t"): problems.append(f"Track #{i+1}: missing title")
            if t.get("v") not in VOLUMES: problems.append(f"Track '{t.get('t','?')}': bad volume '{t.get('v')}'")
            for slot in ("imgsTop","imgsBottom"):
                for j,img in enumerate(t.get(slot) or []):
                    if not img.get("url"): problems.append(f"Track '{t.get('t','?')}' {slot}[{j}]: missing URL")
            for j,lk in enumerate(t.get("spotifyLinks") or []):
                if not lk.get("id"): problems.append(f"Track '{t.get('t','?')}' spotifyLinks[{j}]: missing ID")
        return problems

    def save(self): self._write(self.json_path)
    def save_as(self):
        path=filedialog.asksaveasfilename(parent=self,title="Save tracks JSON as",defaultextension=".json",initialfile=os.path.basename(self.json_path),filetypes=[("JSON","*.json")])
        if not path: return
        self.json_path=path; self._write(path)

    def _write(self,path):
        probs=self._validate()
        if probs:
            msg="Validation issues:\n\n"+"\n".join(probs[:8])
            if len(probs)>8: msg+=f"\n…and {len(probs)-8} more."
            msg+="\n\nSave anyway?"
            if not messagebox.askyesno("Warnings",msg,parent=self): return
        try:
            with open(path,"w",encoding="utf-8") as f: json.dump(self.tracks,f,indent=2,ensure_ascii=False)
            self.status.set(f"Saved {len(self.tracks)} tracks to {path}")
        except Exception as e: messagebox.showerror("Save error",str(e),parent=self)


def main():
    app=AnthologyEditor(); app.mainloop()

if __name__=="__main__":
    main()
