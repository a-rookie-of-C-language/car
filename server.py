import datetime

import cv2
import numpy as np
from flask import Flask, Response, render_template, request, jsonify
from flask_cors import CORS
import time
import torch
from ultralytics import YOLO
import warnings
import os

# 忽略特定的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.cuda.amp.autocast")

# 尝试修补torch.cuda.amp.autocast
try:
    import torch.cuda.amp as amp
    original_autocast = amp.autocast
    
    def patched_autocast(*args, **kwargs):
        if not args and 'enabled' in kwargs and 'device_type' not in kwargs:
            return torch.amp.autocast('cuda', enabled=kwargs['enabled'])
        elif args and isinstance(args[0], bool) and len(args) == 1:
            return torch.amp.autocast('cuda', enabled=args[0])
        return original_autocast(*args, **kwargs)
    
    amp.autocast = patched_autocast
    print("已应用torch.cuda.amp.autocast补丁")
except Exception as e:
    print(f"应用补丁失败: {e}")

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
# 修改为你的实际视频流地址
url = "rtsp://admin:admin@192.168.118.10:8554/live"
url1 = "rtsp://admin:admin@10.243.71.168:8554/live"
# 全局变量，用于存储点击坐标
click_coordinates = {'x': 0, 'y': 0}
# 全局变量，控制是否启用YOLO检测
yolo_detection_enabled = True

# 检查是否有可用的GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"使用设备: {device}")

# 加载YOLOv8模型
try:
    model = YOLO("yolo11n.pt")
    model.to(device)  # 确保模型在正确的设备上
    print("YOLOv8模型加载成功")
except Exception as e:
    print(f"YOLOv8模型加载失败: {e}")
    model = None

# 创建保存图像的目录
save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_frames')
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
    print(f"创建图像保存目录: {save_dir}")


class VideoCamera:
    def __init__(self):
        # 尝试打开摄像头或视频流
        try:
            # 可以尝试使用视频流URL
            self.video = cv2.VideoCapture(url)
            # 或者使用本地摄像头
            # self.video = cv2.VideoCapture(0)
            
            if not self.video.isOpened():
                raise Exception("无法打开视频源")
            
            self.use_mock = False
            print("成功连接到视频源")
        except Exception as e:
            print(f"视频源初始化失败: {e}")
            print("使用模拟视频代替")
            self.use_mock = True
            self.mock_frame_count = 0

    def __del__(self):
        if not self.use_mock and hasattr(self, 'video'):
            self.video.release()

    def get_frame(self):
        frame = self.get_current_frame()
        if frame is None:
            return None
            
        # 使用YOLOv8进行目标检测
        global yolo_detection_enabled, model
        
        if yolo_detection_enabled and model is not None:
            try:
                # 使用YOLOv8进行检测
                results = model(frame, verbose=False)  # 设置verbose=False减少输出
                
                # 在图像上绘制检测结果
                # YOLOv8的results对象可以直接用于绘制
                annotated_frame = results[0].plot()  # 获取带有检测框的图像
                
                # 显示检测到的对象数量
                num_objects = len(results[0].boxes)
                cv2.putText(annotated_frame, f"检测到 {num_objects} 个对象", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                frame = annotated_frame
                
            except Exception as e:
                print(f"YOLOv8检测错误: {e}")
                # 在视频上显示错误信息
                cv2.putText(frame, f"YOLOv8检测错误: {str(e)}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 在视频上显示当前点击坐标
        text = f"点击坐标: x={click_coordinates['x']}, y={click_coordinates['y']}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 在视频上显示用户点击的位置
        if click_coordinates['x'] > 0 or click_coordinates['y'] > 0:  # 只有当有效点击时才显示
            # 绘制十字准星
            x = int(click_coordinates['x'])
            y = int(click_coordinates['y'])
            cv2.line(frame, (x - 15, y), (x + 15, y), (255, 255, 0), 2)
            cv2.line(frame, (x, y - 15), (x, y + 15), (255, 255, 0), 2)
            # 绘制圆圈
            cv2.circle(frame, (x, y), 20, (255, 255, 0), 2)
        
        # 编码为JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
        
    def get_current_frame(self):
        """获取当前视频帧（不带JPEG编码）"""
        if not self.use_mock:
            success, frame = self.video.read()
            if not success:
                return None
            return frame
        else:
            # 创建模拟视频帧 - 更丰富的模拟场景
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # 添加网格背景
            for i in range(0, 640, 40):
                cv2.line(frame, (i, 0), (i, 480), (20, 20, 20), 1)
            for i in range(0, 480, 40):
                cv2.line(frame, (0, i), (640, i), (20, 20, 20), 1)

            # 添加移动的主要物体 - 红色小车
            car_x = int(320 + 200 * np.sin(self.mock_frame_count / 30))
            car_y = int(240 + 150 * np.cos(self.mock_frame_count / 20))

            # 绘制小车车身
            cv2.rectangle(frame, (car_x - 25, car_y - 15), (car_x + 25, car_y + 15), (0, 0, 255), -1)
            # 绘制小车轮子
            cv2.circle(frame, (car_x - 15, car_y + 15), 8, (30, 30, 30), -1)
            cv2.circle(frame, (car_x + 15, car_y + 15), 8, (30, 30, 30), -1)
            cv2.circle(frame, (car_x - 15, car_y - 15), 8, (30, 30, 30), -1)
            cv2.circle(frame, (car_x + 15, car_y - 15), 8, (30, 30, 30), -1)

            # 添加障碍物 - 绿色方块
            obstacle_x = int(100 + 50 * np.sin(self.mock_frame_count / 15))
            obstacle_y = int(100 + 50 * np.cos(self.mock_frame_count / 25))
            cv2.rectangle(frame, (obstacle_x - 20, obstacle_y - 20), (obstacle_x + 20, obstacle_y + 20), (0, 255, 0), -1)

            # 添加目标点 - 蓝色圆圈
            target_x = int(500 + 30 * np.cos(self.mock_frame_count / 10))
            target_y = int(400 + 30 * np.sin(self.mock_frame_count / 18))
            cv2.circle(frame, (target_x, target_y), 15, (255, 0, 0), -1)
            cv2.circle(frame, (target_x, target_y), 25, (255, 0, 0), 2)

            # 更新帧计数
            self.mock_frame_count += 1
            
            return frame


# 视频摄像头实例
camera = None


def gen_frames():
    global camera
    if camera is None:
        camera = VideoCamera()

    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # 限制帧率，约30fps


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/send_coordinates', methods=['POST'])
def receive_coordinates():
    global click_coordinates
    data = request.get_json()
    click_coordinates['x'] = data.get('x', 0)
    click_coordinates['y'] = data.get('y', 0)
    print(f"收到坐标: x={click_coordinates['x']}, y={click_coordinates['y']}")
    # 这里可以添加控制小车的逻辑
    return jsonify({'status': 'success'})


@app.route('/toggle_detection', methods=['POST'])
def toggle_detection():
    global yolo_detection_enabled
    data = request.get_json()
    yolo_detection_enabled = data.get('enabled', False)
    print(f"YOLOv8检测状态: {'启用' if yolo_detection_enabled else '禁用'}")
    return jsonify({'success': True})


@app.route('/save_frame', methods=['POST'])
def save_frame():
    """保存当前视频帧"""
    global camera, click_coordinates
    
    if camera is None:
        return jsonify({'status': 'error', 'message': '摄像头未初始化'}), 500
    
    try:
        # 获取当前帧
        frame = camera.get_current_frame()
        if frame is None:
            return jsonify({'status': 'error', 'message': '无法获取视频帧'}), 500
        
        # 在图像上标记点击位置
        x = int(click_coordinates['x'])
        y = int(click_coordinates['y'])
        if x > 0 or y > 0:  # 只有当有效点击时才显示
            cv2.line(frame, (x - 15, y), (x + 15, y), (255, 255, 0), 2)
            cv2.line(frame, (x, y - 15), (x, y + 15), (255, 255, 0), 2)
            cv2.circle(frame, (x, y), 20, (255, 255, 0), 2)
        
        # 使用YOLOv8进行目标检测并在图像上标注
        if yolo_detection_enabled and model is not None:
            try:
                results = model(frame, verbose=False)
                # 使用YOLOv8的绘制功能
                frame = results[0].plot()
                
                # 显示检测到的对象数量
                num_objects = len(results[0].boxes)
                cv2.putText(frame, f"检测到 {num_objects} 个对象", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            except Exception as e:
                print(f"保存帧时YOLOv8检测错误: {e}")
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"frame_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        # 保存图像
        cv2.imwrite(filepath, frame)
        
        return jsonify({
            'status': 'success', 
            'message': f'图像已保存', 
            'filename': filename,
            'coordinates': {'x': x, 'y': y}
        })
    
    except Exception as e:
        print(f"保存图像时出错: {e}")
        return jsonify({'status': 'error', 'message': f'保存图像失败: {str(e)}'}), 500


# 添加一个直接使用YOLOv8处理视频流的路由
@app.route('/start_video_detection', methods=['POST'])
def start_video_detection():
    """启动YOLOv8直接处理视频流"""
    try:
        # 获取请求中的视频源
        data = request.get_json()
        video_source = data.get('source', 0)  # 默认使用摄像头
        
        if model is None:
            return jsonify({'status': 'error', 'message': 'YOLOv8模型未加载'}), 500
        
        # 使用YOLOv8的predict方法处理视频
        # 注意：这是一个异步操作，会在后台运行
        model.predict(source=video_source, show=True, conf=0.25, save=True, 
                     project=save_dir, name='yolov8_detections')
        
        return jsonify({
            'status': 'success',
            'message': f'已启动YOLOv8视频检测，结果将保存到{save_dir}/yolov8_detections'
        })
    
    except Exception as e:
        print(f"启动视频检测时出错: {e}")
        return jsonify({'status': 'error', 'message': f'启动视频检测失败: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)