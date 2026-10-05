from PIL import Image, ImageDraw, ImageFont
import math, os
os.makedirs('/mnt/data/hoqa_build/images', exist_ok=True)
W,H=1200,700
font_paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
def font(sz,bold=True): return ImageFont.truetype(font_paths[0 if bold else 1],sz)
def base(title):
    im=Image.new('RGB',(W,H),(8,15,28)); d=ImageDraw.Draw(im)
    for y in range(H):
        c=(8,15+int(y*0.03),28+int(y*0.08)); d.line((0,y,W,y),fill=c)
    # glow
    for r in range(260,30,-12):
        a=(30,100,170)
        d.ellipse((600-r,390-r,600+r,390+r),outline=a,width=3)
    d.rounded_rectangle((270,35,930,115),25,outline=(0,210,255),width=4,fill=(12,25,43))
    d.text((W/2,75),title,font=font(52),anchor='mm',fill=(245,250,255))
    # watermark
    wm=font(42)
    for y in range(140,680,70):
        for x in range(-80,1200,260): d.text((x,y),'hoqabot',font=wm,fill=(18,34,55))
    # original heroine/mascot
    d.ellipse((485,190,715,420),fill=(32,175,230),outline=(0,235,255),width=8)
    d.polygon([(520,210),(600,165),(680,210),(655,300),(545,300)],fill=(22,25,40))
    # Чубрик в очках
    d.ellipse((535,250,575,295),fill='white'); d.ellipse((625,250,665,295),fill='white')
    d.ellipse((550,265,565,282),fill=(20,25,40)); d.ellipse((640,265,655,282),fill=(20,25,40))
    # очки
    d.rounded_rectangle((525,242,585,302),12,outline=(20,20,25),width=8)
    d.rounded_rectangle((615,242,675,302),12,outline=(20,20,25),width=8)
    d.line((585,270,615,270),fill=(20,20,25),width=8)
    d.line((525,255,500,245),fill=(20,20,25),width=7)
    d.line((675,255,700,245),fill=(20,20,25),width=7)
    d.polygon([(595,290),(600,305),(605,290)],fill=(240,150,120))
    d.line((550,325,650,325),fill=(245,80,100),width=8)
    d.rounded_rectangle((520,420,680,540),25,fill=(235,70,90),outline=(255,150,170),width=5)
    d.line((520,450,430,390),fill=(32,175,230),width=30); d.line((680,450,770,390),fill=(32,175,230),width=30)
    d.line((555,535,520,620),fill=(32,175,230),width=35); d.line((645,535,680,620),fill=(32,175,230),width=35)
    return im

def add_ball(im,xy,color):
    d=ImageDraw.Draw(im); x,y=xy; d.ellipse((x-55,y-55,x+55,y+55),fill=color,outline=(255,180,80),width=5); d.arc((x-55,y-55,x+55,y+55),0,180,fill=(30,30,30),width=4); d.arc((x-55,y-55,x+55,y+55),180,360,fill=(30,30,30),width=4); d.line((x-50,y,x+50,y),fill=(30,30,30),width=4)

im=base('Испытайте удачу!'); add_ball(im,(180,260),(230,230,230)); add_ball(im,(1020,220),(245,125,35)); im.save('/mnt/data/hoqa_build/images/start.jpg',quality=92)
for title,name,win in [('Вы попали!','hit.jpg',True),('Вы промахнулись','miss.jpg',False)]:
    im=base(title); d=ImageDraw.Draw(im); add_ball(im,(900,340),(245,125,35)); d.rounded_rectangle((120,555,1080,640),20,fill=(12,25,43),outline=(0,210,255),width=3); d.text((600,598),'HOQABOT  •  '+('Переходим к призу' if win else 'Но приз можно получить за задания'),font=font(30),anchor='mm',fill='white'); im.save('/mnt/data/hoqa_build/images/'+name,quality=92)

for title,name in [('Вы получили NFT!','nft.jpg'),('Оставьте комментарии','comments.jpg'),('Подпишитесь на каналы','tasks.jpg')]:
    im=base(title); d=ImageDraw.Draw(im); d.rounded_rectangle((120,555,1080,640),20,fill=(12,25,43),outline=(0,210,255),width=3); im.save('/mnt/data/hoqa_build/images/'+name,quality=92)

# simple ball animations
from PIL import ImageSequence
for sport,fn,color in [('basketball','basketball.gif',(245,125,35)),('football','football.gif',(235,235,235))]:
    frames=[]
    for i in range(14):
        im=Image.new('RGB',(700,400),(8,15,28)); d=ImageDraw.Draw(im)
        d.text((350,35),'HOQABOT',font=font(38),anchor='mm',fill=(0,220,255))
        # goal/rim
        if sport=='basketball':
            d.rectangle((520,120,540,300),fill=(190,200,210)); d.ellipse((455,105,555,135),outline=(240,70,80),width=8); d.line((465,135,545,135),fill='white',width=3)
        else:
            d.rectangle((500,110,650,300),outline='white',width=8); d.line((575,110,575,300),fill='white',width=3)
        x=90+i*32; y=270-110*math.sin(math.pi*i/13)
        d.ellipse((x-35,y-35,x+35,y+35),fill=color,outline=(255,255,255),width=3)
        frames.append(im)
    frames[0].save('/mnt/data/hoqa_build/images/'+fn,save_all=True,append_images=frames[1:],duration=70,loop=0)
