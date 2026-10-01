import pygame
import math
import sys

pygame.init()

LEBAR=1100
TINGGI=720
FPS=85

# Warna Tema Ungu Sci-Fi
BG_DARK=(15,5,30)
UNGU_GELAP=(40,20,60)
UNGU_CARD=(30,15,55)
UNGU_SEDANG=(80,50,120)
UNGU_TERANG=(130,90,180)
UNGU_NEON=(180,100,255)
UNGU_GLOW=(120,60,200)
CYAN_ACCENT=(100,220,255)
MAGENTA_ACCENT=(220,80,255)
PUTIH=(255,255,255)
ABU=(180,180,180)
HIJAU=(80,255,150)
MERAH=(255,80,80)

layar=pygame.display.set_mode((LEBAR,TINGGI))
pygame.display.set_caption("Calculator Advanced 2D")
clock=pygame.time.Clock()

font_judul=pygame.font.Font(None,80)
font_besar=pygame.font.Font(None,44)
font_sedang=pygame.font.Font(None,32)
font_kecil=pygame.font.Font(None,24)
font_micro=pygame.font.Font(None,20)

def draw_bg(surface):
    surface.fill(BG_DARK)
    for y in range(0,TINGGI,30):
        pygame.draw.line(surface,(25,10,45),(0,y),(LEBAR,y),1)
    for x in range(0,LEBAR,40):
        pygame.draw.line(surface,(25,10,45),(x,0),(x,TINGGI),1)

def draw_watermark(surface):
    wm=font_micro.render("Made By: Dyles Enserval Verbox",True,(90,60,130))
    surface.blit(wm,(LEBAR-wm.get_width()-15,TINGGI-wm.get_height()-8))

def draw_gradient_title(surface,text,x,y):
    shadow=font_judul.render(text,True,(60,20,100))
    surface.blit(shadow,(x-shadow.get_width()//2+3,y-shadow.get_height()//2+3))
    chars=list(text)
    total=len(chars)
    cx=x-font_judul.size(text)[0]//2
    for i,ch in enumerate(chars):
        ratio=i/(total-1) if total>1 else 0
        r=int(CYAN_ACCENT[0]*(1-ratio)+MAGENTA_ACCENT[0]*ratio)
        g=int(CYAN_ACCENT[1]*(1-ratio)+MAGENTA_ACCENT[1]*ratio)
        b=int(CYAN_ACCENT[2]*(1-ratio)+MAGENTA_ACCENT[2]*ratio)
        r=int(r*0.7+UNGU_NEON[0]*0.3)
        g=int(g*0.7+UNGU_NEON[1]*0.3)
        b=int(b*0.7+UNGU_NEON[2]*0.3)
        surf=font_judul.render(ch,True,(r,g,b))
        surface.blit(surf,(cx,y-surf.get_height()//2))
        cx+=surf.get_width()

def draw_scene_header(surface,title):
    pygame.draw.rect(surface,UNGU_CARD,(0,0,LEBAR,75))
    pygame.draw.rect(surface,UNGU_NEON,(0,73,LEBAR,2))
    sh=font_besar.render(title,True,(60,20,100))
    surface.blit(sh,(LEBAR//2-sh.get_width()//2+2,22))
    txt=font_besar.render(title,True,UNGU_NEON)
    surface.blit(txt,(LEBAR//2-txt.get_width()//2,20))
    draw_watermark(surface)

def render_text(text,font,color,x,y,center=False):
    surf=font.render(text,True,color)
    rect=surf.get_rect(center=(x,y)) if center else surf.get_rect(topleft=(x,y))
    layar.blit(surf,rect)

class Button:
    def __init__(self,x,y,w,h,text,color=(80,50,120),hover=(130,90,180)):
        self.rect=pygame.Rect(x,y,w,h)
        self.text=text
        self.color=color
        self.hover=hover
        self.hovered=False
    def draw(self,surface):
        c=self.hover if self.hovered else self.color
        pygame.draw.rect(surface,c,self.rect,border_radius=8)
        bc=CYAN_ACCENT if self.hovered else UNGU_NEON
        pygame.draw.rect(surface,bc,self.rect,2,border_radius=8)
        if self.hovered:
            pygame.draw.rect(surface,CYAN_ACCENT,pygame.Rect(self.rect.x+2,self.rect.y+1,self.rect.w-4,2),border_radius=2)
        txt=font_kecil.render(self.text,True,PUTIH)
        surface.blit(txt,(self.rect.centerx-txt.get_width()//2,self.rect.centery-txt.get_height()//2))
    def check_hover(self,pos):
        self.hovered=self.rect.collidepoint(pos)
    def clicked(self,pos,event):
        return event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(pos)

class InputBox:
    def __init__(self,x,y,w,h,label=""):
        self.rect=pygame.Rect(x,y,w,h)
        self.text=""
        self.active=False
        self.label=label
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            self.active=self.rect.collidepoint(event.pos)
        if event.type==pygame.KEYDOWN and self.active:
            if event.key==pygame.K_BACKSPACE: self.text=self.text[:-1]
            elif event.key==pygame.K_RETURN: return True
            elif len(self.text)<25: self.text+=event.unicode
        return False
    def draw(self,surface):
        if self.label:
            lbl=font_kecil.render(self.label,True,ABU)
            surface.blit(lbl,(self.rect.x,self.rect.y-22))
        bc=CYAN_ACCENT if self.active else UNGU_NEON
        pygame.draw.rect(surface,(20,10,40),self.rect,border_radius=6)
        pygame.draw.rect(surface,bc,self.rect,2,border_radius=6)
        txt=font_kecil.render(self.text,True,PUTIH)
        surface.blit(txt,(self.rect.x+8,self.rect.centery-txt.get_height()//2))
        if self.active:
            cx=self.rect.x+8+txt.get_width()+2
            pygame.draw.line(surface,CYAN_ACCENT,(cx,self.rect.centery-8),(cx,self.rect.centery+8),2)

class MenuCard:
    def __init__(self,x,y,w,h,num,label):
        self.rect=pygame.Rect(x,y,w,h)
        self.num=num
        self.label=label
        self.hovered=False
    def draw(self,surface):
        bg=UNGU_SEDANG if self.hovered else UNGU_CARD
        pygame.draw.rect(surface,bg,self.rect,border_radius=10)
        bc=CYAN_ACCENT if self.hovered else UNGU_GLOW
        pygame.draw.rect(surface,bc,self.rect,2,border_radius=10)
        if self.hovered:
            pygame.draw.rect(surface,CYAN_ACCENT,pygame.Rect(self.rect.x+3,self.rect.y+2,self.rect.w-6,3),border_radius=2)
        nc=CYAN_ACCENT if self.hovered else UNGU_NEON
        ns=font_sedang.render(self.num,True,nc)
        surface.blit(ns,(self.rect.x+18,self.rect.y+15))
        words=self.label.split()
        line1=" ".join(words[:2]) if len(words)>2 else self.label
        line2=" ".join(words[2:]) if len(words)>2 else ""
        l1=font_kecil.render(line1,True,PUTIH)
        surface.blit(l1,(self.rect.x+18,self.rect.y+50))
        if line2:
            l2=font_kecil.render(line2,True,PUTIH)
            surface.blit(l2,(self.rect.x+18,self.rect.y+70))
    def check_hover(self,pos):
        self.hovered=self.rect.collidepoint(pos)
    def clicked(self,pos,event):
        return event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(pos)

def draw_hasil_box(surface,hasil,y,is_list=False):
    if not hasil: return
    if is_list:
        bh=len(hasil)*32+20
        pygame.draw.rect(surface,(15,8,35),(50,y,LEBAR-100,bh),border_radius=10)
        pygame.draw.rect(surface,UNGU_NEON,(50,y,LEBAR-100,bh),2,border_radius=10)
        for i,h in enumerate(hasil):
            c=HIJAU if "ERROR" not in h else MERAH
            render_text(h,font_kecil,c,LEBAR//2,y+16+i*32,center=True)
    else:
        pygame.draw.rect(surface,(15,8,35),(50,y,LEBAR-100,60),border_radius=10)
        pygame.draw.rect(surface,UNGU_NEON,(50,y,LEBAR-100,60),2,border_radius=10)
        c=HIJAU if "ERROR" not in hasil else MERAH
        render_text(hasil,font_sedang,c,LEBAR//2,y+30,center=True)

def menu_utama():
    items=[
        ("01","Operasi Dasar"),("02","Pangkat & Akar"),
        ("03","Trigonometri"),("04","Logaritma"),
        ("05","Faktorial & Kombinasi"),("06","Persamaan Kuadrat"),
        ("07","Konversi Suhu"),("08","Konversi Panjang"),
        ("09","Konversi Berat"),("10","Sistem Bilangan"),
        ("11","Statistik"),("12","Matrix 2x2")
    ]
    cw,ch=230,105; gx,gy=18,18; cols=4
    tw=cols*cw+(cols-1)*gx
    sx=(LEBAR-tw)//2; sy=170
    cards=[MenuCard(sx+(i%cols)*(cw+gx),sy+(i//cols)*(ch+gy),cw,ch,num,lb) for i,(num,lb) in enumerate(items)]
    btn_keluar=Button(LEBAR//2-90,625,180,50,"[ KELUAR ]",(80,20,30),(140,40,40))
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            for i,card in enumerate(cards):
                if card.clicked(pos,event): return str(i+1)
            if btn_keluar.clicked(pos,event): return "keluar"
        draw_bg(layar)
        draw_gradient_title(layar,"CALCULATOR ADVANCED",LEBAR//2,75)
        pygame.draw.line(layar,UNGU_NEON,(60,125),(LEBAR-60,125),1)
        pygame.draw.line(layar,UNGU_GLOW,(60,127),(LEBAR-60,127),1)
        for card in cards:
            card.check_hover(pos)
            card.draw(layar)
        btn_keluar.check_hover(pos)
        btn_keluar.draw(layar)
        draw_watermark(layar)
        pygame.display.flip()
        clock.tick(FPS)

def scene_operasi_dasar():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Angka 1:"),InputBox(LEBAR//2-160,205,320,40,"Angka 2:")]
    btns=[Button(80+i*155,285,140,50,op) for i,op in enumerate(["+","-","x","÷","%","^"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a=float(inputs[0].text); b=float(inputs[1].text)
                        if i==0: hasil=f"{a} + {b} = {a+b}"
                        elif i==1: hasil=f"{a} - {b} = {a-b}"
                        elif i==2: hasil=f"{a} x {b} = {a*b}"
                        elif i==3: hasil="ERROR: Tidak bisa bagi 0" if b==0 else f"{a} / {b} = {a/b}"
                        elif i==4: hasil=f"{a} % {b} = {a%b}"
                        elif i==5: hasil=f"{a} ^ {b} = {a**b}"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"OPERASI DASAR")
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_pangkat_akar():
    input1=InputBox(LEBAR//2-160,130,320,40,"Angka:")
    input2=InputBox(LEBAR//2-160,205,320,40,"n (akar/pangkat n):")
    btns=[Button(100+i*195,285,180,50,lb) for i,lb in enumerate(["x²","x³","√x"," (n)√x","x^n"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event); input2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        x=float(input1.text)
                        if i==0: hasil=f"{x}² = {x**2}"
                        elif i==1: hasil=f"{x}³ = {x**3}"
                        elif i==2: hasil="ERROR: Tidak bisa akar negatif" if x<0 else f"√{x} = {math.sqrt(x):.6f}"
                        elif i==3:
                            n=int(input2.text)
                            hasil="ERROR: Pangkat tidak boleh 0" if n==0 else f"(n)√{x} (n={n}) = {x**(1/n):.6f}"
                        elif i==4: n=float(input2.text); hasil=f"{x}^{n} = {x**n}"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"PANGKAT & AKAR")
        input1.draw(layar); input2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,375)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_trigonometri():
    input1=InputBox(LEBAR//2-160,130,320,40,"Sudut (derajat):")
    btns=[Button(80+i*165,210,150,50,f) for i,f in enumerate(["sin","cos","tan","sec","csc","cot"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        deg=float(input1.text); rad=math.radians(deg)
                        if i==0: hasil=f"sin({deg}°) = {math.sin(rad):.6f}"
                        elif i==1: hasil=f"cos({deg}°) = {math.cos(rad):.6f}"
                        elif i==2: hasil=f"tan({deg}°) = {math.tan(rad):.6f}"
                        elif i==3: cv=math.cos(rad); hasil="ERROR: Sec undefined" if abs(cv)<1e-10 else f"sec({deg}°) = {1/cv:.6f}"
                        elif i==4: sv=math.sin(rad); hasil="ERROR: Csc undefined" if abs(sv)<1e-10 else f"csc({deg}°) = {1/sv:.6f}"
                        elif i==5: tv=math.tan(rad); hasil="ERROR: Cot undefined" if abs(tv)<1e-10 else f"cot({deg}°) = {1/tv:.6f}"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"TRIGONOMETRI")
        input1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,295)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_logaritma():
    input1=InputBox(LEBAR//2-160,130,320,40,"Angka:")
    input2=InputBox(LEBAR//2-160,205,320,40,"Base (untuk log_n):")
    btns=[Button(330,290,140,50,lb) for lb in ["log10","ln","log_n"]]
    for i,btn in enumerate(btns): btn.rect.x=330+i*160
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event); input2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        x=float(input1.text)
                        if x<=0: hasil="ERROR: Log hanya untuk x > 0"; continue
                        if i==0: hasil=f"log10({x}) = {math.log10(x):.6f}"
                        elif i==1: hasil=f"ln({x}) = {math.log(x):.6f}"
                        elif i==2:
                            base=float(input2.text)
                            hasil="ERROR: Base harus > 0 dan ≠ 1" if base<=0 or base==1 else f"log_{base}({x}) = {math.log(x,base):.6f}"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"LOGARITMA")
        input1.draw(layar); input2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,370)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_faktorial():
    input1=InputBox(LEBAR//2-160,130,320,40,"n:")
    input2=InputBox(LEBAR//2-160,205,320,40,"r (untuk nPr / nCr):")
    btns=[Button(330+i*160,290,140,50,lb) for i,lb in enumerate(["n!","nPr","nCr"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event); input2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        n=int(input1.text)
                        if n<0: hasil="ERROR: n harus >= 0"; continue
                        if i==0: hasil=f"{n}! = {math.factorial(n)}"
                        else:
                            r=int(input2.text)
                            if r<0: hasil="ERROR: r harus >= 0"; continue
                            if r>n: hasil="ERROR: r tidak boleh > n"; continue
                            hasil=f"P({n},{r}) = {math.perm(n,r)}" if i==1 else f"C({n},{r}) = {math.comb(n,r)}"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"FAKTORIAL & KOMBINASI")
        input1.draw(layar); input2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,370)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_persamaan_kuadrat():
    inputs=[InputBox(LEBAR//2-160,110,320,40,lb) for lb in ["a (koefisien x²):","b (koefisien x):","c (konstanta):"]]
    for i,inp in enumerate(inputs): inp.rect.y=110+i*75
    btn_hitung=Button(LEBAR//2-85,340,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=[]
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            for inp in inputs: inp.handle_event(event)
            if btn_hitung.clicked(pos,event):
                try:
                    a=float(inputs[0].text); b=float(inputs[1].text); c=float(inputs[2].text)
                    if a==0: hasil=["ERROR: Bukan persamaan kuadrat (a = 0)"]; continue
                    D=b**2-4*a*c
                    hasil=[f"Diskriminan  D = {D:.4f}"]
                    if D>0:
                        x1=(-b+math.sqrt(D))/(2*a); x2=(-b-math.sqrt(D))/(2*a)
                        hasil+=[f"x₁ = {x1:.6f}",f"x₂ = {x2:.6f}"]
                    elif D==0: hasil.append(f"x₁ = x₂ = {-b/(2*a):.6f}")
                    else:
                        real=-b/(2*a); imag=math.sqrt(abs(D))/(2*a)
                        hasil+=[f"x1 = {real:.4f} + {imag:.4f}i",f"x2 = {real:.4f} - {imag:.4f}i"]
                except: hasil=["ERROR: Input tidak valid"]
        draw_bg(layar); draw_scene_header(layar,"PERSAMAAN KUADRAT  (ax² + bx + c = 0)")
        for inp in inputs: inp.draw(layar)
        btn_hitung.check_hover(pos); btn_hitung.draw(layar)
        draw_hasil_box(layar,hasil,415,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_konversi_suhu():
    input1=InputBox(LEBAR//2-160,130,320,40,"Nilai:")
    btns=[Button(80+i*190,210,175,50,lb) for i,lb in enumerate(["C --> F","C --> K","C --> R","F --> C","K --> C"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        v=float(input1.text)
                        if i==0: hasil=f"{v}°C = {(v*9/5)+32:.4f}°F"
                        elif i==1: hasil=f"{v}°C = {v+273.15:.4f} K"
                        elif i==2: hasil=f"{v}°C = {v*4/5:.4f}°R"
                        elif i==3: hasil=f"{v}°F = {(v-32)*5/9:.4f}°C"
                        elif i==4: hasil=f"{v} K = {v-273.15:.4f}°C"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"KONVERSI SUHU")
        input1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,295)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_konversi_panjang():
    input1=InputBox(LEBAR//2-160,130,320,40,"Nilai:")
    labels=["m --> km","m --> cm","m --> mm","m --> ft","km --> mil","mil --> km"]
    btns=[Button(80+(i%3)*320,210+(i//3)*70,300,55,lb) for i,lb in enumerate(labels)]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        v=float(input1.text)
                        r=[f"{v} m = {v/1000:.6f} km",f"{v} m = {v*100:.2f} cm",f"{v} m = {v*1000:.2f} mm",
                           f"{v} m = {v*3.28084:.4f} ft",f"{v} km = {v*0.621371:.4f} mil",f"{v} mil = {v*1.60934:.4f} km"]
                        hasil=r[i]
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"KONVERSI PANJANG")
        input1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_konversi_berat():
    input1=InputBox(LEBAR//2-160,130,320,40,"Nilai:")
    labels=["kg --> g","kg --> lb","kg --> ton","kg --> ons","lb --> kg"]
    btns=[Button(80+(i%3)*320,210+(i//3)*70,300,55,lb) for i,lb in enumerate(labels)]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        v=float(input1.text)
                        r=[f"{v} kg = {v*1000:.2f} g",f"{v} kg = {v*2.20462:.4f} lb",f"{v} kg = {v/1000:.6f} ton",
                           f"{v} kg = {v*10:.2f} ons",f"{v} lb = {v/2.20462:.4f} kg"]
                        hasil=r[i]
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"KONVERSI BERAT")
        input1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_sistem_bilangan():
    input1=InputBox(LEBAR//2-160,130,320,40,"Nilai:")
    labels=["Dec --> Bin","Dec --> Oct","Dec --> Hex","Bin --> Dec","Oct --> Dec","Hex --> Dec"]
    btns=[Button(80+(i%3)*320,210+(i//3)*70,300,55,lb) for i,lb in enumerate(labels)]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=""
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        if i==0: v=int(input1.text); hasil=f"{v}(10) = {bin(v)[2:]}(2)"
                        elif i==1: v=int(input1.text); hasil=f"{v}(10) = {oct(v)[2:]}(8)"
                        elif i==2: v=int(input1.text); hasil=f"{v}(10) = {hex(v)[2:].upper()}(16)"
                        elif i==3: v=input1.text; hasil=f"{v}(2) = {int(v,2)}(10)"
                        elif i==4: v=input1.text; hasil=f"{v}(8) = {int(v,8)}(10)"
                        elif i==5: v=input1.text; hasil=f"{v}(16) = {int(v,16)}(10)"
                    except: hasil="ERROR: Input tidak valid"
        draw_bg(layar); draw_scene_header(layar,"SISTEM BILANGAN")
        input1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_statistik():
    input1=InputBox(60,130,LEBAR-120,40,"Data (pisahkan spasi):")
    btn_hitung=Button(LEBAR//2-85,195,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=[]
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            input1.handle_event(event)
            if btn_hitung.clicked(pos,event):
                try:
                    data=list(map(float,input1.text.split()))
                    if not data: hasil=["ERROR: Data kosong"]; continue
                    n=len(data); mean=sum(data)/n; ds=sorted(data)
                    median=(ds[n//2-1]+ds[n//2])/2 if n%2==0 else ds[n//2]
                    var=sum((x-mean)**2 for x in data)/n; std=math.sqrt(var)
                    hasil=[f"N = {n}   |   Mean = {mean:.4f}",
                           f"Median = {median:.4f}   |   Variance = {var:.4f}",
                           f"Std Dev = {std:.4f}   |   Min = {min(data):.2f}   |   Max = {max(data):.2f}"]
                except: hasil=["ERROR: Input tidak valid"]
        draw_bg(layar); draw_scene_header(layar,"STATISTIK")
        input1.draw(layar); btn_hitung.check_hover(pos); btn_hitung.draw(layar)
        draw_hasil_box(layar,hasil,270,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_matrix():
    ax,ay=200,100; bx,by=650,100
    ia=[InputBox(ax+(i%2)*130,ay+30+(i//2)*65,115,38,f"a{i//2+1}{i%2+1}:") for i in range(4)]
    ib=[InputBox(bx+(i%2)*130,by+30+(i//2)*65,115,38,f"b{i//2+1}{i%2+1}:") for i in range(4)]
    btns=[Button(250+i*200,270,180,50,lb) for i,lb in enumerate(["A + B","A x B","Det(A)"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    hasil=[]
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if btn_back.clicked(pos,event): return "menu"
            for inp in ia+ib: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a11=float(ia[0].text); a12=float(ia[1].text)
                        a21=float(ia[2].text); a22=float(ia[3].text)
                        if i==0:
                            b11=float(ib[0].text); b12=float(ib[1].text)
                            b21=float(ib[2].text); b22=float(ib[3].text)
                            hasil=["Hasil  A + B :",f"[ {a11+b11:.2f}    {a12+b12:.2f} ]",f"[ {a21+b21:.2f}    {a22+b22:.2f} ]"]
                        elif i==1:
                            b11=float(ib[0].text); b12=float(ib[1].text)
                            b21=float(ib[2].text); b22=float(ib[3].text)
                            c11=a11*b11+a12*b21; c12=a11*b12+a12*b22
                            c21=a21*b11+a22*b21; c22=a21*b12+a22*b22
                            hasil=["Hasil  A x B :",f"[ {c11:.2f}    {c12:.2f} ]",f"[ {c21:.2f}    {c22:.2f} ]"]
                        elif i==2: hasil=[f"Det(A) = {a11*a22-a12*a21:.6f}"]
                    except: hasil=["ERROR: Input tidak valid"]
        draw_bg(layar); draw_scene_header(layar,"MATRIX 2x2")
        render_text("Matrix A",font_kecil,CYAN_ACCENT,ax,ay-10)
        render_text("Matrix B",font_kecil,CYAN_ACCENT,bx,by-10)
        for inp in ia+ib: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        draw_hasil_box(layar,hasil,350,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def main():
    scene="menu"
    scenes={"1":scene_operasi_dasar,"2":scene_pangkat_akar,"3":scene_trigonometri,
            "4":scene_logaritma,"5":scene_faktorial,"6":scene_persamaan_kuadrat,
            "7":scene_konversi_suhu,"8":scene_konversi_panjang,"9":scene_konversi_berat,
            "10":scene_sistem_bilangan,"11":scene_statistik,"12":scene_matrix}
    while True:
        if scene=="menu": scene=menu_utama()
        elif scene in scenes: scene=scenes[scene]()
        elif scene=="keluar": break
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()