from flask import Flask, request, Response, render_template, send_file
import os
import glob
from PIL import Image, ExifTags
from werkzeug.utils import secure_filename
from datetime import date 
import datetime
import uuid
import requests
import base64
import config
from generate_citation import draw_pic
from redis_tool import r
from get_rank import get_rank_data


app = Flask(__name__)  # 实例Flask应用

ALLOW_EXTENSIONS = ['png', 'jpg', 'jpeg']
 
# 设置图片保存文件夹
app.config['UPLOAD_FOLDER'] = './static/images/'
image_c = 1000
image_url = "http://127.0.0.1:8002/images/"

target = [
    [0, "自主规划大师"],
    [5, "高级自主规划大师"],       
    [10, "特级自主规划大师"],
    [15, "冠军自主规划大师"],
    [21, "自主规划大师终生成就奖"],
]

# pip install python-docx


# 首页
@app.route('/')
def hello_world():
    data = get_rank_data()
    return render_template('submit.html', **data)

# 首页
@app.route('/test')
def hello_test():
    data = get_rank_data()
    return render_template('submit_test.html', **data)

# 判断文件后缀是否在列表中
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1] in ALLOW_EXTENSIONS


@app.route("/get_image",  methods=['GET'])
def get_image():
    # 图片上传保存的路径
    try:
        day = request.args.get('day')
        name = request.args.get('name')
        
        files = glob.glob(r'./static/images/{}/{}*'.format(day, name))
        print(r'./static/images/{}/{}*'.format(day, name))
        if files:
            ima = files[0]
        else:
            return "未找到文件!"
        with open(ima, 'rb') as f:
            image = f.read()
            result = Response(image, mimetype="image/jpg")
            return result
    except BaseException as e:
        return {"code": '503', "data": str(e), "message": "图片不存在"}

def keep(d1, d2):
    d1 = datetime.datetime.strptime(d1 , '%Y%m%d')
    d2 = datetime.datetime.strptime(d2 , '%Y%m%d')        
    diff = d2 - d1
    return diff.days <= 1


# 上传图片
@app.route("/upload_image_v2", methods=['POST', "GET"])
def uploads_v2():
    if request.method == 'POST':
        # 获取文件
        file = request.form['photo']
        name = request.form['username']
        # print(f"{name=}")
        # print(f"{file=}")
        if not name:
            return "请填入正确的姓名!"
        if name not in config.students:
            return "此姓名不在云朵之家名单, 请检查姓名输入!"
        # 检测文件格式
        if 1:
            # 文件夹不存在则创建
            day = date.today().strftime("%Y%m%d")
            if not os.path.exists("./static/images/{}".format(day)):
                os.makedirs("./static/images/{}".format(day))

            # 生成base64 转义的图片

            with open(os.path.join(app.config['UPLOAD_FOLDER'], day, name + ".png"), "wb") as fh:
                fh.write(base64.decodebytes(file.split(",")[1].encode()))


            # save to redis
            ky = f"clock_{name}"
            if not r.lindex(ky, -1) or day > r.lindex(ky, -1).decode('utf-8'):
                r.rpush(ky, day)
            
            # 判断连续打卡几天
            today = date.today().strftime("%Y%m%d")
            history = r.lrange(ky, -30, -1)
            print("his", history)
            history.sort()

            # 连续打卡天数
            d = 1
            for i in range(len(history) - 2, -1, -1):
                if keep(history[i].decode('utf-8'), history[i + 1].decode('utf-8')):
                    d += 1
                else:
                    break
            print(f"{name=} 连续打卡 {d=} 天")
            suggest = f'{name}小云朵, 你已连续打卡<span class="label label-danger">{d}</span>天,'
            hit = False
            
            level = "自主规划大师终生成就奖"
            for i, (nd, title) in enumerate(target):
                if d < nd:
                    suggest += f'当前荣获<span class="label label-success">{target[i - 1][1]}</span> 称号, 再坚持{nd - d}天可获得{title}称号!'
                    level = target[i - 1][1]
                    hit = True
                    break
            if not hit:
                suggest += "你已荣获自主规划大师终生成就奖称号!"
            print(suggest)

            # 请求识别ocr内容
            # ocr = get_ocr(app.config['UPLOAD_FOLDER'] + file_name_min)

            # 画奖状
            citation = draw_pic(name, level)
            print(f"{citation=}")
            return render_template('result.html', picname = citation, suggest = suggest)
            return send_file(citation, mimetype='image/gif')

            # 返回原本和缩略图的 完整浏览链接
            return {"code": '200', "image_url_min": image_url + file_name_min,
                    "message": "上传成功", "ocr": ocr}

        else:
            return "格式错误，仅支持jpg、png、jpeg格式文件"
    return {"code": '503', "data": "", "message": "仅支持post方法"}


# 上传图片
@app.route("/upload_image", methods=['POST', "GET"])
def uploads():
    if request.method == 'POST':
        # 获取文件
        file = request.files['photo']
        name = request.form['username']
        print(f"{name=}")
        if not name:
            return "请填入正确的姓名!"
        if name not in config.students:
            return "此姓名不在云朵之家名单, 请检查姓名输入!"
        # 检测文件格式
        if file and allowed_file(file.filename):
            # 文件夹不存在则创建
            day = date.today().strftime("%Y%m%d")
            if not os.path.exists("./static/images/{}".format(day)):
                os.makedirs("./static/images/{}".format(day))
            # secure_filename方法会去掉文件名中的中文，获取文件的后缀名
            file_name_hz = secure_filename(file.filename).split('.')[-1]
            # 使用uuid生成唯一图片名
            #first_name = str(uuid.uuid4())
            first_name = name 
            # 将 uuid和后缀拼接为 完整的文件名
            file_name = first_name + '.' + file_name_hz
            # # 保存原图
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], day, file_name))

            # save to redis
            ky = f"clock_{name}"
            if not r.lindex(ky, -1) or day > r.lindex(ky, -1).decode('utf-8'):
                r.rpush(ky, day)
 
            ## 以下是压缩图片的过程，在原图的基础上
            #file_min = Image.open(file)
            ## exif读取原始方位信息 防止图片压缩后发生旋转
            #try:
            #    for orientation in ExifTags.TAGS.keys():
            #        if ExifTags.TAGS[orientation] == 'Orientation': break
            #    exif = dict(file_min._getexif().items())
            #    if exif[orientation] == 3:
            #        file_min = file_min.rotate(180, expand=True)
            #    elif exif[orientation] == 6:
            #        file_min = file_min.rotate(270, expand=True)
            #    elif exif[orientation] == 8:
            #        file_min = file_min.rotate(90, expand=True)
            #except:
            #    pass
            ## 获取原图尺寸
            #w, h = file_min.size
            ## 计算压缩比
            #bili = max(1, int(w / image_c))
            ## 按比例对宽高压缩
            #file_min.thumbnail((w // bili, h // bili))
            ## 生成缩略图的完整文件名
            #file_name_min = first_name + '_min.' + file_name_hz
            ## 保存缩略图
            #file_min.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name_min))

            # 请求识别ocr内容
            # ocr = get_ocr(app.config['UPLOAD_FOLDER'] + file_name_min)

            # 画奖状
            citation = draw_pic(name)
            print(f"{citation=}")
            return render_template('result.html', picname = citation)
            return send_file(citation, mimetype='image/gif')

            # 返回原本和缩略图的 完整浏览链接
            return {"code": '200', "image_url_min": image_url + file_name_min,
                    "message": "上传成功", "ocr": ocr}

        else:
            return "格式错误，仅支持jpg、png、jpeg格式文件"
    return {"code": '503', "data": "", "message": "仅支持post方法"}

def get_token():
	# host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=【官网获取的AK】&client_secret=【官网获取的SK】'
	# response = requests.get(host)

	return "24.68e0085d39ffc21fdfef322c4e18ff2d.2592000.1655726936.282335-26286203"

def get_ocr(path):
	print(f"{path=}")
	request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
	f = open(path, 'rb')
	img = base64.b64encode(f.read())
	params = {"image":img}
	access_token = get_token()
	request_url = request_url + "?access_token=" + access_token
	headers = {'content-type': 'application/x-www-form-urlencoded'}
	response = requests.post(request_url, data=params, headers=headers)
	if response:
	    print (response.json())
	    return response.json()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=True)  # 项目入口
