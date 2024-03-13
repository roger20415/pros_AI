from std_msgs.msg import Float32MultiArray
from collections import defaultdict
from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path
from rclpy.qos import QoSProfile, ReliabilityPolicy

import json
from std_msgs.msg import String
from ROS_receive_and_data_processing.car_models import *
import sys
import math
from rclpy.node import Node
from ROS_receive_and_data_processing.UnityAdaptor import *
import orjson
import time
from ROS_receive_and_data_processing.config import ACTION_MAPPINGS, LIDAR_PER_SECTOR


class AI_node(Node):
    def __init__(self):
        super().__init__("aiNode")
        self.get_logger().info("Ai start")
        self.real_car_data = {}
        self.data_to_AI = ""

        self.latest_goal_position = None
        self.lastest_data = None
        """
        以下字典是用來定義這個node接收到最新的數值後傳送到UnityAdaptor.py內轉換
        最終轉換格式是UnityAdaptor.py決定 這邊只負責接收最新數值
        """
        self.real_car_data["ROS2CarPosition"] = []
        self.real_car_data["ROS2CarQuaternion"] = []
        self.real_car_data["ROS2TargetPosition"] = []

        #  讀取四輪電壓
        self.real_car_data["ROS2WheelAngularVelocityLeftBack"] = 0.01
        self.real_car_data["ROS2WheelAngularVelocityLeftFront"] = 0.01
        self.real_car_data["ROS2WheelAngularVelocityRightBack"] = 0.01
        self.real_car_data["ROS2WheelAngularVelocityRightFront"] = 0.01

        #  lidar的射線
        self.real_car_data["ROS2Range"] = []
        # lidar每條射線的vector
        self.real_car_data["ROS2RangePosition"] = []

        #  navigation資料
        self.real_car_data["twist_msg"] = Twist()
        self.real_car_data["path_msg"] = Path()
        self.real_car_data["path_position_msg"] = []
        self.real_car_data["path_orientation_msg"] = []

        """
        確定以下資料都有收到 才會在 check_and_get_lastest_data() 更新最新資料
        amcl 追蹤車體目前位置
        goal 目標位置
        lidar lidar資料
        """
        self.data_updated = {
            "amcl": False,
            "goal": False,
            "lidar": False,
        }

        """
        接收目標, 車體目前位置, 輪子轉速, lidar的距離和vector
        """
        self.subscriber_amcl = self.create_subscription(
            PoseWithCovarianceStamped, "/amcl_pose", self.subscribe_callback_amcl, 1
        )
        """
        目標座標
        """
        self.subscriber_goal = self.create_subscription(
            PoseStamped, "/goal_pose", self.subscribe_callback_goal, 1
        )
        """
        lidar掃描
        """
        self.subscriber_lidar = self.create_subscription(
            LaserScan, "/scan", self.laser_scan_callback, 1
        )
        """
        車體後輪電壓
        """
        self.subscriber_rear = self.create_subscription(
            String, DeviceDataTypeEnum.car_C_state, self.rear_wheel_callback, 1
        )
        """
        車體前輪電壓
        """
        self.subscriber_forward = self.create_subscription(
            String, DeviceDataTypeEnum.car_C_state_front, self.forward_wheel_callback, 1
        )

        """
        publish給前後的esp32驅動車輪
        """
        self.publisher = self.create_publisher(
            String, DeviceDataTypeEnum.car_C_control, 10
        )  # 後輪esp32

        self.publisher_forward = self.create_publisher(String, "test", 10)  # 後輪esp32

        """
        回傳經過路徑規劃時物體該用多少速度去移動
        return linear x y z & angular x y z
        """
        self.subscriber_navigation = self.create_subscription(
            Twist, "/cmd_vel_nav", self.navigation_callback, 1
        )

        """
        路徑位置和四位數轉角
        """
        self.subscriber_navigation_plan = self.create_subscription(
            Path, "/plan", self.navigation_plan_callback, 1
        )

    """
    檢查所有數據是否更新
    如果amcl lidar goal都收到就傳入UnityAdaptor.py內的transfer_obs()並更新資料
    goal只會在點擊目標的一瞬間更新 所以下面恢復成false的部分沒有goal
    """

    def check_and_get_lastest_data(self):
        if all(self.data_updated.values()):
            # 確認所有的數據都更新並publish
            self.data_updated["amcl"] = False
            self.data_updated["lidar"] = False
            self.lastest_data = transfer_obs(self.real_car_data)

    """
    給其他有引入AI_node的程式碼取得最新資料
    """

    def get_latest_data(self):
        return self.lastest_data

    """
    輸出給車子驅動用的電壓
    """

    def publish_to_unity(self, action_code):

        # _vel1, _vel3是左側 _vel2, _vel4是右側

        action = ACTION_MAPPINGS.get(action_code, "invalid")
        _vel1, _vel2, _vel3, _vel4 = action[0], action[1], action[2], action[3]

        control_signal = {
            "type": str(DeviceDataTypeEnum.car_C_control),
            "data": dict(CarCControl(target_vel=[_vel1, _vel2])),
        }

        control_msg = String()
        control_msg.data = orjson.dumps(control_signal).decode()
        self.publisher.publish(control_msg)
        control_signal_forward = {
            "type": str(DeviceDataTypeEnum.car_C_control),
            "data": dict(CarCControl(target_vel=[_vel3, _vel4])),
        }
        control_msg_forward = String()
        control_msg_forward.data = orjson.dumps(control_signal_forward).decode()

        self.publisher_forward.publish(control_msg_forward)

        #  lidar轉一圈需要0.1多秒, 確保lidar更新到最新data
        # time.sleep(0.2)

    """
    這個func目前還在考慮要不要用
    """

    def publish_to_unity_nav(self, action):
        """
        _vel1, _vel3是左側
        _vel2, _vel4是右側
        """
        _vel1, _vel2, _vel3, _vel4 = action[0], action[1], action[2], action[3]

        control_signal = {
            "type": str(DeviceDataTypeEnum.car_C_control),
            "data": dict(CarCControl(target_vel=[_vel1, _vel2])),
        }

        control_msg = String()
        control_msg.data = orjson.dumps(control_signal).decode()
        self.publisher.publish(control_msg)
        # print("DeviceDataTypeEnum.car_C_control : ", DeviceDataTypeEnum.car_C_control)
        control_signal_forward = {
            "type": str(DeviceDataTypeEnum.car_C_control),
            "data": dict(CarCControl(target_vel=[_vel3, _vel4])),
        }
        control_msg_forward = String()
        control_msg_forward.data = orjson.dumps(control_signal_forward).decode()

        # Publish the control signal
        self.publisher_forward.publish(control_msg_forward)

    """
    給車子四個輪子停止的電壓
    """

    def publish_to_unity_RESET(self):
        self.publish_to_unity(6)

    """
    重製lastest_data
    """

    def reset(self):
        self.lastest_data = None

    """
    確定amcl goal lidar其中一個有收到訊號
    並更新目前是否有接收到的狀態
    """

    def update_and_check_data(self, data_type):
        self.data_updated[data_type] = True
        self.check_and_get_lastest_data()

    """
    amcl的subscribe function
    """

    def subscribe_callback_amcl(self, message):
        pose = self.transfer_car_pose(message)[0]
        quaternion = self.transfer_car_pose(message)[1]
        self.real_car_data["ROS2CarPosition"] = pose
        self.real_car_data["ROS2CarQuaternion"] = quaternion
        self.update_and_check_data("amcl")

    """
    給 subscribe_callback_amcl 做轉換使用
    """

    def transfer_car_pose(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        return [position.x, position.y, position.z], [
            orientation.x,
            orientation.y,
            orientation.z,
            orientation.w,
        ]

    """
    goal 的 subscribe function
    """

    def subscribe_callback_goal(self, message):
        target = self.transfer_target_pos(message)
        if target:
            self.real_car_data["ROS2TargetPosition"] = target
            self.update_and_check_data("goal")

    """
    給 subscribe_callback_goal 轉換用
    """

    def transfer_target_pos(self, msg):
        position = msg.pose.position
        return [position.x, position.y, position.z]

    """
    lidar 的 subscriber function
    """

    def laser_scan_callback(self, msg):
        """
        普通lidar 預設輸出1800個數值
        高級lidar 預設輸出3240個數值
        可以透過print(len(msg.ranges))去觀察
        """
        angle_min = msg.angle_min
        angle_max = msg.angle_max
        angle_increment = msg.angle_increment
        ranges_180 = []
        direction_180 = []
        all_ranges = msg.ranges
        for i in range(len(all_ranges)):
            if i % LIDAR_PER_SECTOR == 0:  # handle the amount of lidar.
                angle_tmp = angle_min + i * angle_increment
                ranges_180.append(all_ranges[i])
                direction_180.append([math.cos(angle_tmp), math.sin(angle_tmp), 0])
        self.real_car_data["ROS2Range"] = ranges_180
        self.real_car_data["ROS2RangePosition"] = direction_180
        self.update_and_check_data("lidar")

    """
    navigation輸出路徑所需速度及轉角的subscribe function
    """

    def navigation_callback(self, msg):
        self.real_car_data["twist_msg"] = msg

    """
    navigation輸出路徑位置及四位數轉角的subscribe function
    """

    def navigation_plan_callback(self, msg):
        if msg.poses:
            self.real_car_data["path_msg"] = msg.poses[0]
            # self.real_car_data["path_msg"] = msg.poses[-1].pose

    """
    接收後輪的電壓 subscribe function
    """

    def rear_wheel_callback(self, message):
        try:
            json_str = message.data
            data = json.loads(json_str)
            if "data" in data and "vels" in data["data"]:
                vels = data["data"]["vels"]
                self.real_car_data["ROS2WheelAngularVelocityLeftBack"] = vels[0]
                self.real_car_data["ROS2WheelAngularVelocityRightBack"] = vels[1]
            else:
                print("Invalid message format. Missing 'vels' key.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    """
    接收前輪的電壓 subscribe function
    """

    def forward_wheel_callback(self, message):
        try:
            json_str = message.data
            data = json.loads(json_str)
            if "data" in data and "vels" in data["data"]:
                vels = data["data"]["vels"]
                self.real_car_data["ROS2WheelAngularVelocityLeftFront"] = vels[0]
                self.real_car_data["ROS2WheelAngularVelocityRightFront"] = vels[1]
            else:
                print("Invalid message format. Missing 'vels' key.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
