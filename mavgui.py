import sys
import numpy as np
from pymavlink import mavutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsItemGroup
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import QTransform, QBrush, QColor, QPen, QPolygonF, QFont

print("Connecting to MAVLink...")
connection = mavutil.mavlink_connection('udp:127.0.0.1:14550')
connection.wait_heartbeat()
print("Connected!")

class VirtualHorizon(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Virtual Horizon")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")

        self.scene = QGraphicsScene(-250, -190, 500, 400)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(10, 10, 480, 380)
        self.view.setStyleSheet("background: black; border: 2px solid gray;")
        self.view.setSceneRect(-150, -150, 300, 300)
        self.setCentralWidget(self.view)

        self.instrument_bg = QGraphicsEllipseItem(-150, -150, 200, 200)
        self.instrument_bg.setBrush(QBrush(Qt.black))
        self.scene.addItem(self.instrument_bg)

        self.horizon_group = self.scene.createItemGroup([])

        self.sky = QGraphicsRectItem(-400, -300, 800, 300)
        self.sky.setBrush(QBrush(QColor(100, 149, 237)))  
        self.horizon_group.addToGroup(self.sky)

        self.ground = QGraphicsRectItem(-400, 0, 800, 300)
        self.ground.setBrush(QBrush(QColor(139, 69, 19)))  
        self.horizon_group.addToGroup(self.ground)

        self.horizon_line = QGraphicsLineItem(-100, 0, 100, 0)
        self.horizon_line.setPen(QPen(Qt.white, 3))
        self.scene.addItem(self.horizon_line)

        self.roll_scale = QGraphicsEllipseItem(-120, -120, 240, 240)
        self.roll_scale.setPen(QPen(Qt.white, 2))
        self.scene.addItem(self.roll_scale)

        self.left_wing = QGraphicsRectItem(-80, -5, 30, 5)
        self.left_wing.setBrush(QBrush(Qt.yellow))
        self.horizon_group.addToGroup(self.left_wing)

        self.right_wing = QGraphicsRectItem(50, -5, 30, 5)
        self.right_wing.setBrush(QBrush(Qt.yellow))
        self.horizon_group.addToGroup(self.right_wing)

        self.pitch_group = QGraphicsItemGroup()
        self.scene.addItem(self.pitch_group)

        for i in range(-30, 35, 5):
            length = 30 if i % 10 == 0 else 15  
            line = QGraphicsLineItem(-length, -i * 2, length, -i * 2)
            line.setPen(QPen(Qt.white, 2))
            self.pitch_group.addToGroup(line)

            if i % 10 == 0 and i != 0:  
                text = QGraphicsTextItem(str(abs(i)))
                text.setFont(QFont("Arial", 10, QFont.Bold))
                text.setDefaultTextColor(Qt.white)
                text.setPos(-50, -i * 2 - 5)
                self.pitch_group.addToGroup(text)

        self.roll_text = QGraphicsTextItem("Roll: 0.0°")
        self.roll_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.roll_text.setDefaultTextColor(Qt.white)
        self.roll_text.setPos(-130, 220)

        self.pitch_text = QGraphicsTextItem("Pitch: 0.0°")
        self.pitch_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.pitch_text.setDefaultTextColor(Qt.white)
        self.pitch_text.setPos(-40, 220)

        self.yaw_text = QGraphicsTextItem("Yaw: 0.0°")
        self.yaw_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.yaw_text.setDefaultTextColor(Qt.white)
        self.yaw_text.setPos(60, 220)

        self.scene.addItem(self.roll_text)
        self.scene.addItem(self.pitch_text)
        self.scene.addItem(self.yaw_text)

        self.altitude_text = QGraphicsTextItem("Alt: 0 m")
        self.altitude_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.altitude_text.setDefaultTextColor(Qt.white)
        self.altitude_text.setPos(230, 220)
        self.scene.addItem(self.altitude_text)

        self.vspeed_text = QGraphicsTextItem("VS: 0 m/s")
        self.vspeed_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.vspeed_text.setDefaultTextColor(Qt.white)
        self.vspeed_text.setPos(-350, 220)
        self.scene.addItem(self.vspeed_text)

        self.heading_text = QGraphicsTextItem("HDG: 0°")
        self.heading_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.heading_text.setDefaultTextColor(Qt.white)
        self.heading_text.setPos(-350, -280)
        self.scene.addItem(self.heading_text)

        self.airspeed_text = QGraphicsTextItem("AIS: 0 m/s")
        self.airspeed_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.airspeed_text.setDefaultTextColor(Qt.white)
        self.airspeed_text.setPos(230, -280)
        self.scene.addItem(self.airspeed_text)

        self.armed_status_text = QGraphicsTextItem("DISARMED")
        self.armed_status_text.setFont(QFont("Arial", 14, QFont.Bold))
        self.armed_status_text.setDefaultTextColor(Qt.red)
        self.armed_status_text.setPos(-50, -280)
        self.scene.addItem(self.armed_status_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_horizon)
        self.timer.start(100)  

    def update_horizon(self):
        try:
            msg_attitude = connection.recv_match(type='ATTITUDE', blocking=False)
            if msg_attitude:
                pitch = np.degrees(msg_attitude.pitch)
                roll = np.degrees(msg_attitude.roll)
                yaw = np.degrees(msg_attitude.yaw)

                transform = QTransform()
                transform.rotate(-roll, Qt.ZAxis)
                transform.translate(0, max(-30, min(30, pitch * 2)))  
                self.horizon_group.setTransform(transform)

                self.pitch_group.setTransform(QTransform().translate(0, max(-30, min(30, pitch * 2))))  

                self.roll_text.setPlainText(f"Roll: {roll:.1f}°")
                self.pitch_text.setPlainText(f"Pitch: {pitch:.1f}°")
                self.yaw_text.setPlainText(f"Yaw: {yaw:.1f}°")
                self.heading_text.setPlainText(f"HDG: {yaw:.1f}°")

            msg_vfr = connection.recv_match(type='VFR_HUD', blocking=False)
            if msg_vfr:
                altitude = msg_vfr.alt
                vspeed = msg_vfr.climb
                airspeed = msg_vfr.airspeed

                self.altitude_text.setPlainText(f"Alt: {altitude:.1f} m")
                self.vspeed_text.setPlainText(f"VS: {vspeed:.1f} m/s")
                self.airspeed_text.setPlainText(f"AIS: {airspeed:.1f} m/s")
            
            msg_armed = connection.recv_match(type='HEARTBEAT', blocking=False)
            if msg_armed:
                armed = msg_armed.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                if armed:
                    self.armed_status_text.setPlainText("ARMED")
                    self.armed_status_text.setDefaultTextColor(Qt.green)
                else:
                    self.armed_status_text.setPlainText("DISARMED")
                    self.armed_status_text.setDefaultTextColor(Qt.red)

        except Exception as e:
            self.setWindowTitle(f"Error: {e}")

app = QApplication(sys.argv)
horizon = VirtualHorizon()
horizon.show()
sys.exit(app.exec_())
