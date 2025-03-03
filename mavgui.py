import sys
import numpy as np
from pymavlink import mavutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsTextItem
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
        self.setGeometry(100, 100, 500, 420)
        self.setStyleSheet("background-color: black;")

        self.scene = QGraphicsScene(-250, -190, 500, 380)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(10, 10, 480, 360)
        self.view.setStyleSheet("background: black; border: 2px solid gray;")
        self.view.setSceneRect(-150, -150, 300, 300)
        self.setCentralWidget(self.view)

        self.instrument_bg = QGraphicsEllipseItem(-150, -150, 300, 300)
        self.instrument_bg.setBrush(QBrush(Qt.black))
        self.scene.addItem(self.instrument_bg)

        self.horizon_group = self.scene.createItemGroup([])

        self.sky = QGraphicsRectItem(-200, -200, 400, 200)
        self.sky.setBrush(QBrush(QColor(100, 149, 237)))  
        self.horizon_group.addToGroup(self.sky)

        self.ground = QGraphicsRectItem(-200, 0, 400, 200)
        self.ground.setBrush(QBrush(QColor(139, 69, 19)))  
        self.horizon_group.addToGroup(self.ground)

        self.horizon_line = QGraphicsLineItem(-100, 0, 100, 0)
        self.horizon_line.setPen(QPen(Qt.white, 3))
        self.scene.addItem(self.horizon_line)

        for i in range(-30, 40, 5):  
            width = 15 if i % 10 == 0 else 7  
            mark = QGraphicsLineItem(-width, -i * 2, width, -i * 2)
            mark.setPen(QPen(Qt.white, 2))
            self.horizon_group.addToGroup(mark)

        self.left_wing = QGraphicsRectItem(-80, -5, 30, 5)
        self.left_wing.setBrush(QBrush(Qt.yellow))
        self.horizon_group.addToGroup(self.left_wing)

        self.right_wing = QGraphicsRectItem(50, -5, 30, 5)
        self.right_wing.setBrush(QBrush(Qt.yellow))
        self.horizon_group.addToGroup(self.right_wing)

        self.roll_scale = QGraphicsEllipseItem(-120, -120, 240, 240)
        self.roll_scale.setPen(QPen(Qt.white, 2))
        self.scene.addItem(self.roll_scale)

        self.roll_text = QGraphicsTextItem("Roll: 0.0°")
        self.roll_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.roll_text.setDefaultTextColor(Qt.white)
        self.roll_text.setPos(-130, 150)

        self.pitch_text = QGraphicsTextItem("Pitch: 0.0°")
        self.pitch_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.pitch_text.setDefaultTextColor(Qt.white)
        self.pitch_text.setPos(-40, 150)

        self.yaw_text = QGraphicsTextItem("Yaw: 0.0°")
        self.yaw_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.yaw_text.setDefaultTextColor(Qt.white)
        self.yaw_text.setPos(60, 150)

        self.scene.addItem(self.roll_text)
        self.scene.addItem(self.pitch_text)
        self.scene.addItem(self.yaw_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_horizon)
        self.timer.start(100)  

    def update_horizon(self):
        try:
            msg = connection.recv_match(type='ATTITUDE', blocking=True, timeout=1)
            if msg:
                pitch = np.degrees(msg.pitch)  
                roll = np.degrees(msg.roll)  
                yaw = np.degrees(msg.yaw)

                transform = QTransform()
                transform.rotate(-roll, Qt.ZAxis)
                transform.translate(0, max(-30, min(30, pitch * 2)))  
                self.horizon_group.setTransform(transform)

                self.left_wing.setTransform(QTransform().rotate(-roll))
                self.right_wing.setTransform(QTransform().rotate(-roll))

                self.roll_text.setPlainText(f"Roll: {roll:.1f}°")
                self.pitch_text.setPlainText(f"Pitch: {pitch:.1f}°")
                self.yaw_text.setPlainText(f"Yaw: {yaw:.1f}°")

                self.setWindowTitle(f"Virtual Horizon - Pitch: {pitch:.1f}°, Roll: {roll:.1f}°, Yaw: {yaw:.1f}°")

        except Exception as e:
            self.setWindowTitle(f"Error: {e}")

app = QApplication(sys.argv)
horizon = VirtualHorizon()
horizon.show()
sys.exit(app.exec_())
