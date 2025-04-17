# 巡航小车控制系统

这是一个基于Python和Flask的巡航小车控制系统，集成了YOLOv5目标检测、路径规划和Web界面控制功能。

## 系统组件

系统由以下几个主要组件组成：

- **模型检测模块** (`model.py`): 加载YOLOv5模型用于目标检测
- **Web服务器** (`server.py`): 提供Web界面和视频流服务
- **路径规划算法** (`dfs.py`): 使用深度优先搜索算法进行路径规划
- **路径跟随控制** (`path_follower.py`): 将规划路径转换为小车控制命令
- **Web前端界面** (`templates/index.html`): 用户交互界面

## 安装依赖

在使用系统前，请确保安装以下依赖：

```bash
   pip install flask flask-cors opencv-python numpy torch torchvision
```

如果需要使用YOLOv5进行目标检测，系统会自动下载预训练模型。

## 使用方法
### 1. 启动服务器
运行以下命令启动Web服务器：

```bash
  python server.py
```

服务器默认在 http://localhost:5000 上运行。

### 2. 访问Web界面
在浏览器中打开 index.html 访问控制界面。

### 3. API接口说明
系统提供以下API接口：
 视频流接口
- URL : /video_feed
- 方法 : GET
- 描述 : 提供实时视频流
- 使用示例 : 在HTML中使用 `http://localhost:5000/video_feed` 坐标发送接口
- URL : /send_coordinates
- 方法 : POST
- 参数 : JSON格式 {"x": 数值, "y": 数值}
- 描述 : 发送点击坐标到服务器，用于控制小车移动
- 使用示例 :
  ```javascript
  fetch('http://localhost:5000/send_coordinates', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({x: 100, y: 200})
  })
   ```
- URL : /toggle_detection
- 方法 : POST
- 参数 : JSON格式 {"enabled": true/false}
- 描述 : 启用或禁用YOLOv5目标检测
- 使用示例 :
  ```javascript
  fetch('http://localhost:5000/toggle_detection', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({enabled: true})
  })
   ```
- URL : /save_frame
- 方法 : POST
- 描述 : 保存当前视频帧，包括检测结果和点击位置标记
- 返回 : JSON格式 {"status": "success", "message": "图像已保存", "filename": "文件名", "coordinates": {"x": 数值, "y": 数值}}
- 使用示例 :
  ```javascript
  fetch('http://localhost:5000/save_frame', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({})
  })
   ```
### 4. 路径规划API
dfs.py 提供了深度优先搜索算法用于路径规划：

```python
from dfs import dfs

# 示例地图：0表示通道，1表示障碍物
map_matrix = [
    [0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1],
    [0, 0, 0, 1, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0]
]

# 寻找从(0,0)到(4,4)的路径
path = dfs(map_matrix, 0, 0, 4, 4)

# 输出路径
if path:
    print("找到路径:")
    for point in path:
        print(f"({point[0]}, {point[1]})")
else:
    print("没有找到路径")
 ```

### 5. 路径跟随控制API
path_follower.py 提供了将路径转换为小车控制命令的功能：

```python
from Scripts.path_follower import follow_path

# 示例地图
map_matrix = [
    [0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1],
    [0, 0, 0, 1, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0]
]

# 设置起点和终点
start_x, start_y = 0, 0
end_x, end_y = 4, 4

# 执行路径跟随
follow_path(map_matrix, start_x, start_y, end_x, end_y,
            speed=0.5, turn_speed=1.0, move_time=1.0)
 ```

## 系统功能
1. 实时视频流 ：显示摄像头捕获的画面或模拟视频
2. 目标检测 ：使用YOLOv5识别视频中的物体
3. 点击控制 ：通过点击视频画面控制小车移动
4. 路径规划 ：使用DFS算法规划从起点到终点的路径
5. 图像保存 ：保存当前视频帧，包括检测结果
## 注意事项
1. 如果无法连接到实际摄像头，系统会自动使用模拟视频
2. YOLOv5模型首次加载时需要下载，请确保网络连接正常
3. 系统默认使用CPU进行推理，如有GPU可自动切换
4. 保存的图像存储在项目目录下的 saved_frames 文件夹中
## 故障排除
1. 如果视频流无法显示，请检查服务器是否正常运行
2. 如果YOLOv5模型加载失败，请检查网络连接或手动下载模型
3. 如果点击坐标发送失败，请检查浏览器控制台是否有错误信息