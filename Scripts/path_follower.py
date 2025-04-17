#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
路径跟随程序
将DFS算法生成的路径转换为小车控制命令
"""

import time
from dfs import dfs
from car_control import run
import math

def follow_path(matrix, start_x, start_y, end_x, end_y, speed=0.5, turn_speed=1.0, move_time=1.0):
    """
    让小车按照DFS算法找到的路径移动
    
    参数:
        matrix: 地图矩阵，0表示通道，1表示障碍物
        start_x, start_y: 起点坐标
        end_x, end_y: 终点坐标
        speed: 移动速度
        turn_speed: 转弯速度
        move_time: 每步移动的时间(秒)
    
    返回:
        是否成功到达终点
    """
    # 使用DFS算法找到路径
    path = dfs(matrix, start_x, start_y, end_x, end_y)
    
    if not path:
        print("无法找到从({},{})到({},{})的路径".format(start_x, start_y, end_x, end_y))
        return False
    
    print("找到路径，共{}步:".format(len(path)))
    for i, point in enumerate(path):
        print("步骤 {}: ({}, {})".format(i+1, point[0], point[1]))
    
    # 如果路径只有一个点（起点和终点相同），直接返回成功
    if len(path) <= 1:
        print("起点和终点相同，无需移动")
        return True
    
    # 遍历路径点，转换为移动指令
    current_direction = None  # 当前朝向，初始为None
    
    for i in range(1, len(path)):
        prev_point = path[i-1]
        current_point = path[i]
        
        # 计算移动方向
        dx = current_point[0] - prev_point[0]
        dy = current_point[1] - prev_point[1]
        
        # 确定移动方向
        if dx == 1 and dy == 0:  # 向下移动
            direction = 'down'
        elif dx == -1 and dy == 0:  # 向上移动
            direction = 'up'
        elif dx == 0 and dy == 1:  # 向右移动
            direction = 'right'
        elif dx == 0 and dy == -1:  # 向左移动
            direction = 'left'
        else:
            print("错误：路径中存在非相邻点")
            return False
        
        # 将地图方向转换为小车控制命令
        # 假设小车初始朝向为"向前"(forward)，对应地图的"向下"(down)
        if current_direction is None:
            # 第一步，根据初始方向设置
            if direction == 'down':
                move_cmd = 'forward'
            elif direction == 'up':
                move_cmd = 'back'
            elif direction == 'right':
                move_cmd = 'right'
                # 先转向
                print("小车右转")
                run('right', turn_time, speed, turn_speed)
                time.sleep(0.5)
                # 然后前进
                move_cmd = 'forward'
            elif direction == 'left':
                move_cmd = 'left'
                # 先转向
                print("小车左转")
                run('left', turn_time, speed, turn_speed)
                time.sleep(0.5)
                # 然后前进
                move_cmd = 'forward'
            
            current_direction = direction
        else:
            # 后续步骤，需要根据当前朝向和目标方向确定转向
            if current_direction == direction:
                # 方向相同，继续前进
                move_cmd = 'forward'
            elif (current_direction == 'down' and direction == 'up') or \
                 (current_direction == 'up' and direction == 'down') or \
                 (current_direction == 'left' and direction == 'right') or \
                 (current_direction == 'right' and direction == 'left'):
                # 需要掉头（180度转向）
                print("小车掉头")
                run('right', turn_time * 2, speed, turn_speed)  # 转两倍时间实现掉头
                time.sleep(0.5)
                move_cmd = 'forward'
            elif (current_direction == 'down' and direction == 'right') or \
                 (current_direction == 'right' and direction == 'up') or \
                 (current_direction == 'up' and direction == 'left') or \
                 (current_direction == 'left' and direction == 'down'):
                # 需要右转
                print("小车右转")
                run('right', turn_time, speed, turn_speed)
                time.sleep(0.5)
                move_cmd = 'forward'
            else:
                # 需要左转
                print("小车左转")
                run('left', turn_time, speed, turn_speed)
                time.sleep(0.5)
                move_cmd = 'forward'
            
            current_direction = direction
        
        # 执行移动命令
        print("小车从({},{})移动到({},{})，执行: {}".format(
            prev_point[0], prev_point[1], current_point[0], current_point[1], move_cmd))
        run(move_cmd, move_time, speed, turn_speed)
        time.sleep(0.5)  # 每步之间稍作停顿
    
    print("路径执行完成，小车已到达目标位置({},{})".format(end_x, end_y))
    return True

def direct_path(start_x, start_y, end_x, end_y, speed=0.5, turn_speed=1.0, move_time=1.0):
    """
    让小车直接从起点移动到终点，不考虑障碍物
    
    参数:
        start_x, start_y: 起点坐标
        end_x, end_y: 终点坐标
        speed: 移动速度
        turn_speed: 转弯速度
        move_time: 移动时间(秒)
    
    返回:
        是否成功到达终点
    """
    print("开始直接从({},{})导航到({},{})".format(start_x, start_y, end_x, end_y))
    
    # 计算起点到终点的距离
    distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
    print(f"直线距离: {distance:.2f}")
    
    # 计算方向角度（相对于水平轴）
    if end_x == start_x and end_y == start_y:
        print("起点和终点相同，无需移动")
        return True
    
    # 计算角度（弧度）
    angle_rad = math.atan2(end_y - start_y, end_x - start_x)
    # 转换为角度
    angle_deg = math.degrees(angle_rad)
    
    # 将角度映射到小车控制方向
    # 假设0度是向右，90度是向上，180度是向左，270度是向下
    print(f"目标方向角度: {angle_deg:.2f}度")
    
    # 根据角度确定转向命令
    if -45 <= angle_deg <= 45:  # 向右
        direction = 'right'
    elif 45 < angle_deg <= 135:  # 向上
        direction = 'up'
    elif 135 < angle_deg <= 180 or -180 <= angle_deg < -135:  # 向左
        direction = 'left'
    else:  # 向下
        direction = 'down'
    
    print(f"移动方向: {direction}")
    
    # 转换为小车控制命令
    if direction == 'right':
        print("小车右转")
        run('right', turn_time, speed, turn_speed)
        time.sleep(0.5)
        move_cmd = 'forward'
    elif direction == 'left':
        print("小车左转")
        run('left', turn_time, speed, turn_speed)
        time.sleep(0.5)
        move_cmd = 'forward'
    elif direction == 'up':
        move_cmd = 'back'
    elif direction == 'down':
        move_cmd = 'forward'
    
    # 计算移动时间（根据距离调整）
    adjusted_move_time = move_time * distance
    
    # 执行移动命令
    print(f"小车执行: {move_cmd}，时间: {adjusted_move_time:.2f}秒")
    run(move_cmd, adjusted_move_time, speed, turn_speed)
    
    print("导航完成，小车已到达目标位置({},{})".format(end_x, end_y))
    return True

# 设置转向和移动的时间参数
turn_time = 0.8  # 转向时间
move_time = 1.0  # 每步移动时间

if __name__ == "__main__":
    # 测试直接路径
    start_x, start_y = 0, 0
    end_x, end_y = 4, 4
    
    print("测试直接路径导航:")
    direct_path(start_x, start_y, end_x, end_y, 0.5, 1.0, 1.0)