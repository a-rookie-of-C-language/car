from ultralytics import YOLO

if __name__ == "__main__":
    # 加载YOLOv8模型
    model = YOLO('yolov8s.pt')  # 加载预训练的YOLOv8s模型
    # 设置为评估模式
    model.eval()
