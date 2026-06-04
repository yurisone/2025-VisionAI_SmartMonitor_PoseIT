from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685
import spidev
import threading
import requests
from collections import deque

# SPI (MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel=0):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

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

def get_pitch_from_server():
    try:
        response = requests.get("http://18.204.77.217:5000/get_pitch", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return int(data.get("pitch_angle", 90))
        else:
            print("⚠️ 서버 수신 오류:", response.status_code)
            return 90
    except Exception as e:
        print("❌ 서버 수신 실패:", e)
        return 90

def move_monitor_forward():
    print("🔧 [모터1] 앞으로 이동 (모니터 사용자 쪽으로)")

def move_monitor_backward():
    print("🔧 [모터1] 뒤로 이동 (모니터 사용자로부터 멀리)")

# 초기값
motor35_channel = 1
motor150_channel = 0
current_angle35 = 90
current_angle150 = 90

update_interval = 1.0
send_interval = 3.0
last_update = time.time()
last_sent_time = time.time()

turtle_neck_start = None
TURTLE_DURATION = 5
angle_buffer = deque(maxlen=10)

# 시작할 때 초기 위치로 세팅
current_angle150 = move_servo_smooth(motor150_channel, current_angle150, 90)

try:
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
            distance_cm = int(27.86 / (ir_voltage + 0.1))

            if now - last_sent_time >= send_interval:
                send_distance_to_server_async(distance_cm)
                last_sent_time = now

            # [2] 목각도 받아오기
            angle150 = get_pitch_from_server()
            angle_buffer.append(angle150)

            # ✅ 받은 각도 그대로 사용
            reversed_angle150 = angle150

            # [3] 거북목 판단 및 타이머 처리
            print(f"\n▶︎ [입력값] 목각도: {angle150}°, 거리: {distance_cm}cm")
            print("📊 최근 목각도값들:", list(angle_buffer))
            print(f"🎯 목표 M2 각도: {reversed_angle150}°")

            if angle150 <= 53:
                if turtle_neck_start is None:
                    turtle_neck_start = now
                duration = now - turtle_neck_start
                print(f"📍 거북목 상태 유지 시간: {duration:.1f}초")

                if duration >= TURTLE_DURATION:
                    print("✅ 5초 이상 지속 → 모터 제어 실행")
                    if current_angle150 != reversed_angle150:
                        current_angle150 = move_servo_smooth(motor150_channel, current_angle150, reversed_angle150)
                    else:
                        print("↪️ 현재 위치와 같음 → 모터 이동 생략")
                    if distance_cm < 50:
                        move_monitor_backward()
                    else:
                        move_monitor_forward()
                else:
                    print("⏳ 아직 지속시간 부족 → 대기 중")
            else:
                print("📌 정상 자세 → 타이머 리셋")
                turtle_neck_start = None

            print(f"[M3] 거리: {distance_cm}cm   모터 각도: {angle35}°")
            print(f"[M2] 목각도: {angle150}°     모터 각도: {current_angle150}°")

            last_update = now

except KeyboardInterrupt:
    print("⛔ 종료됨")

finally:
    pca.deinit()
    spi.close()
