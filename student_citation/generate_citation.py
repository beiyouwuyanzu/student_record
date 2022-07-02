from docx.shared import Pt, RGBColor
from PIL import Image,ImageDraw,ImageFont 
import datetime





def draw_pic(name, level):
    old_img = Image.open(r"citation.jpeg")#导入证书模板
    draw = ImageDraw.Draw(old_img)
    newcolor = RGBColor(184,134,11) #通过RGB设置学生名字的颜色
    black = RGBColor(205, 170, 125)
    newfont=ImageFont.truetype('panda.ttf',120)
    
    sfont = ImageFont.truetype('panda.ttf', 40)
    draw.text((200, 400), name, font=newfont, fill = newcolor)
    draw.text((100, 500), level, font=newfont, fill = newcolor)
    draw.text((400, 650), datetime.datetime.now().strftime("%m月%d日 %H:%M"), font=sfont, fill = black)
    draw.text((490, 700), "云朵之家", font = sfont, fill = black)
    save_adress = "static/images" + '/' + name + '.jpg'
    old_img.save(save_adress)
    print("荣誉证书制作完成")
    return save_adress
