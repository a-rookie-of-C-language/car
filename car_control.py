#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小车控制程序
这个程序用于直接控制小车移动，无需键盘输入
"""

import sys
import time
import threading

# 导入ROS相关模块
try:
    import roslib

    roslib.load_manifest('car_control_pkg')  # 修改这里的包名
    import rospy
    from geometry_msgs.msg import Twist
    from geometry_msgs.msg import TwistStamped
except ImportError as e:
    print(f"导入ROS模块失败: {e}")
    sys.exit(1)

# 定义消息类型
TwistMsg = Twist


# 重写PublishThread类，专为直接控制设计
class PublishThread(threading.Thread):
    def __init__(self, rate):
        super(PublishThread, self).__init__()
        # 修改话题名称，确保与底盘控制器一致
        self.publisher = rospy.Publisher('/cmd_vel', TwistMsg, queue_size=1)
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.speed = 0.0
        self.turn = 0.0
        self.condition = threading.Condition()
        self.done = False

        # 设置超时
        if rate != 0.0:
            self.timeout = 1.0 / rate
        else:
            self.timeout = None

        self.start()

    def wait_for_subscribers(self):
        # 注释掉等待订阅者的代码，直接返回
        return

        # 原代码
        # i = 0
        # while not rospy.is_shutdown() and self.publisher.get_num_connections() == 0:
        #    if i == 4:
        #        print("等待订阅者连接到 {}".format(self.publisher.name))
        #    rospy.sleep(0.5)
        #    i += 1
        #    i = i % 5
        # if rospy.is_shutdown():
        #    raise Exception("在订阅者连接前收到关闭请求")

    def update(self, x, y, z, th, speed, turn):
        self.condition.acquire()
        self.x = x
        self.y = y
        self.z = z
        self.th = th
        self.speed = speed
        self.turn = turn
        # 通知发布线程有新消息
        self.condition.notify()
        self.condition.release()

    def stop(self):
        self.done = True
        self.update(0, 0, 0, 0, 0, 0)
        self.join()

    def run(self):
        twist_msg = TwistMsg()
        twist = twist_msg  # 简化版本，不使用stamped

        while not self.done:
            self.condition.acquire()
            # 等待新消息或超时
            self.condition.wait(self.timeout)

            # 将状态复制到twist消息中
            twist.linear.x = self.x * self.speed
            twist.linear.y = self.y * self.speed
            twist.linear.z = self.z * self.speed
            twist.angular.x = 0
            twist.angular.y = 0
            twist.angular.z = self.th * self.turn

            self.condition.release()

            # 发布
            self.publisher.publish(twist_msg)

        # 线程退出时发布停止消息
        twist.linear.x = 0
        twist.linear.y = 0
        twist.linear.z = 0
        twist.angular.x = 0
        twist.angular.y = 0
        twist.angular.z = 0
        self.publisher.publish(twist_msg)


def run(direction, duration=2.0, speed_value=0.5, turn_value=1.0):
    """
    直接控制小车移动，无需键盘输入

    参数:
        direction: 移动方向，可选值：'forward', 'back', 'left', 'right', 'stop'
        duration: 移动持续时间(秒)
        speed_value: 线速度值
        turn_value: 角速度值
    """
    # 初始化ROS节点（如果尚未初始化）
    if not rospy.core.is_initialized():
        rospy.init_node('teleop_direct_control')

    # 设置速度参数
    speed = speed_value
    turn = turn_value

    # 创建发布线程
    pub_thread = PublishThread(0.0)
    pub_thread.wait_for_subscribers()

    # 根据方向设置移动参数，增加速度值
    if direction == 'forward':
        x, y, z, th = 2, 0, 0, 0  # 前进速度加大
    elif direction == 'back':
        x, y, z, th = -2, 0, 0, 0  # 后退速度加大
    elif direction == 'left':
        x, y, z, th = 0, 0, 0, 2  # 左转速度加大
    elif direction == 'right':
        x, y, z, th = 0, 0, 0, -2  # 右转速度加大
    else:  # 默认停止
        x, y, z, th = 0, 0, 0, 0

    try:
        # 更新移动参数
        pub_thread.update(x, y, z, th, speed, turn)
        print("小车正在执行 {} 动作，持续 {} 秒".format(direction, duration))

        # 使用循环来确保持续时间准确
        start_time = time.time()
        while time.time() - start_time < duration and not rospy.is_shutdown():
            rospy.sleep(0.1)  # 小间隔检查时间

        # 停止小车
        pub_thread.update(0, 0, 0, 0, 0, 0)
        print("小车已停止")

    except Exception as e:
        print("操作过程中出现错误: {}".format(e))

    finally:
        # 确保线程停止
        pub_thread.stop()


def ros_main():
    """
    ROS节点主函数，从ROS参数服务器获取参数
    """
    rospy.init_node('car_control')

    # 增加默认速度值
    default_speed = rospy.get_param('~speed', 1.0)  # 默认速度改为1.0
    default_turn = rospy.get_param('~turn', 2.0)  # 默认转向速度改为2.0

    try:
        rospy.loginfo("小车控制节点启动...")

        # 增加每个动作之间的间隔
        run('forward', 3.0, default_speed, default_turn)
        rospy.sleep(2.0)  # 增加等待时间

        run('back', 3.0, default_speed, default_turn)
        rospy.sleep(2.0)

        run('left', 2.0, default_speed, default_turn)
        rospy.sleep(2.0)

        run('right', 2.0, default_speed, default_turn)
        rospy.sleep(2.0)

        run('stop')

        rospy.loginfo("小车控制演示完成")
        rospy.spin()

    except rospy.ROSInterruptException:
        rospy.loginfo("节点被中断")
    except Exception as e:
        rospy.logerr("发生错误: {}".format(e))


def main():
    """
    主函数，演示如何使用run函数控制小车
    """
    print("小车控制程序启动...")

    try:
        # 演示不同的移动命令
        print("\n1. 小车前进")
        run('forward', 3.0)  # 前进3秒
        time.sleep(1)  # 等待1秒

        print("\n2. 小车后退")
        run('back', 3.0)  # 后退3秒
        time.sleep(1)  # 等待1秒

        print("\n3. 小车左转")
        run('left', 2.0)  # 左转2秒
        time.sleep(1)  # 等待1秒

        print("\n4. 小车右转")
        run('right', 2.0)  # 右转2秒
        time.sleep(1)  # 等待1秒

        print("\n5. 小车高速前进")
        run('forward', 2.0, 0.8)  # 高速前进2秒
        time.sleep(1)  # 等待1秒

        print("\n6. 小车停止")
        run('stop')  # 停止

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        # 修改f-string为format方法
        print("\n程序执行出错: {}".format(e))

    print("\n小车控制程序结束")


if __name__ == "__main__":
    # 如果是通过ROS launch启动的，使用ros_main函数
    if len(sys.argv) > 1 and sys.argv[1] == '__name:=car_control':
        ros_main()
    else:
        # 否则使用普通main函数
        main()