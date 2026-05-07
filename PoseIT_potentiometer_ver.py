from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685
import spidev
import threading
import requests

# SPI (MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel=0):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

# 가변저항 값 → 각도로 변환
def read_neck_angle_from_potentiometer(channel=0):
    adc_val = read_adc(channel)
    angle = int((adc_val / 1023) * 40+30)
    return angle

# I2C (PCA9685)
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000
    return int(pulse / 1000000 * 50 * 65535)

def move_servo_smooth(channel, current_angle, target_angle, delay=0.015):
    step = 1 if target_angle > current_angle else -1
    for angle in range(current_angle, target_angle + step, step):
        pca.channels[channel].duty_cycle = angle_to_pwm(angle)
        time.sleep(delay)
    return target_angle

def send_distance_to_server_async(distance_cm):
    def send():
        try:
            data = {"distance_cm": float(distance_cm)}
            response = requests.post("http://18.204.77.217:5000/save_distance", json=data, timeout=5)
            print(f"✅ 서버 송신 성공: {response.json()}")
        except Exception as e:
            print("❌ 서버 송신 실패")
    threading.Thread(target=send, daemon=True).start()

# 필수 모터1 동작 함수
def move_monitor_forward():
    print("🔧 [모터1] 아래으로 이동 (모니터 사용자 쪽으로)")

def move_monitor_backward():
    print("🔧 [모터1] 위로 이동 (모니터 사용자에서 멀리)")

# 초기값 설정
motor35_channel = 1  # IR 센서 모터
motor150_channel = 0  # 서버에서 받은 각도 모터
current_angle35 = 90
current_angle150 = 90

update_interval = 1.0
send_interval = 3.0
last_update = time.time()
last_sent_time = time.time()

try:
    # 🔄 시작 시 모터2(M2)를 원점으로 이동
    current_angle150 = move_servo_smooth(motor150_channel, current_angle150, 90)
    while True:
        now = time.time()
        if now - last_update >= update_interval:
            # [1] 거리 계산
            ir_adc = read_adc(1)
            ir_voltage = (ir_adc / 1023) * 3.3
            if ir_voltage < 0.4:
                angle35 = 180
            elif ir_voltage > 2.5:
                angle35 = 0
            else:
                angle35 = int((2.5 - ir_voltage) / 2.1 * 180)

            current_angle35 = move_servo_smooth(motor35_channel, current_angle35, angle35)
            distance_cm = int(27.86 / (ir_voltage + 0.1))  # 간단한 역수 모델
            if now - last_sent_time >= send_interval:
                send_distance_to_server_async(distance_cm)
                last_sent_time = now

            # [2] 건너받은 각도 검사 (channel 0)
            angle150 = read_neck_angle_from_potentiometer(channel=0)
            # 반전
            reversed_angle150 = 180 - angle150

            # [3] 조건 분기 처리
            print(f"\n▶︎ [입력값] 목각도: {angle150}°, 거리: {distance_cm}cm")
            if angle150 < 53:
                print("📍 거북목 상태 감지됨")
                if distance_cm < 40:
                    print("📌 Case 1: 거북목 + 거리가 가까워질 때")
                    current_angle150 = move_servo_smooth(motor150_channel, current_angle150, reversed_angle150)
                    move_monitor_backward()
                else:
                    print("📌 Case 2: 거북목 + 거리가 멀 때")
                    current_angle150 = move_servo_smooth(motor150_channel, current_angle150, reversed_angle150)
                    move_monitor_forward()
            else:
                print("📌 Case 3: 정상자세 유지")

            print(f"[M3] 거리: {distance_cm}cm   모터 각도: {angle35}°")
            print(f"[M2] 목각도: {angle150}°     모터 각도: {current_angle150}°")

            last_update = now

except KeyboardInterrupt:
    print("⛔ 종료됨")

finally:
    pca.deinit()
    spi.close()
