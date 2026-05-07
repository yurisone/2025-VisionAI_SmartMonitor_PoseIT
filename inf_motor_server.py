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

# I2C (PCA9685)
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# PWM 변환 함수
def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000
    return int(pulse / 1000000 * 50 * 65535)

# 부드럽게 모터 움직이기
def move_servo_smooth(channel, current_angle, target_angle, delay=0.015):
    step = 1 if target_angle > current_angle else -1
    for angle in range(current_angle, target_angle + step, step):
        pca.channels[channel].duty_cycle = angle_to_pwm(angle)
        time.sleep(delay)
    return target_angle

# 📤 서버 전송 함수 (비동기)
def send_distance_to_server_async(distance_cm):
    def send():
        try:
            data = {"distance_cm": float(distance_cm)}
            response = requests.post("http://18.204.77.217:5000/save_distance", json=data, timeout=5)
            print(f"✅ 서버 전송 성공: {response.json()}")
        except Exception as e:
            print("❌ 서버 보내기 실패:", e)
    threading.Thread(target=send, daemon=True).start()
# 📥 서버에서 pitch 각도 받아오기 (비동기 아님 – 1초마다 실행)
def get_pitch_from_server():
    try:
        response = requests.get("http://18.204.77.217:5000/get_pitch", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return int(data.get("pitch_angle", 90))  # ← pitch_angle 키로 받아야 정확
        else:
            print("⚠️ 서버 응답 오류:", response.status_code)
            return 90
    except Exception as e:
        print("❌ 서버 받이오기 실패:", e)
        return 90
    
# 나중에 모터1 연결되면 여기에 실제 제어 코드 작성
def move_monitor_forward():
    print("🔧 [모터1] 앞으로 cm이동 (모니터 사용자 쪽으로)")

def move_monitor_backward():
    print("🔧 [모터1] 뒤로 cm이동 (모니터 사용자로부터 멀리)")



# 초기값
motor35_channel = 1  # 35kg (IR 센서)
motor150_channel = 0  # 150kg (가변저항)
current_angle35 = 90
current_angle150 = 90

update_interval = 1.0     # 센서 읽기 주기
send_interval = 3.0      # 서버 전송 주기
last_update = time.time()
last_sent_time = time.time()

try:
    while True:
        now = time.time()
        if now - last_update >= update_interval:
            # [1] IR 센서 (35kg 서보 제어용)
            ir_adc = read_adc(1)
            ir_voltage = (ir_adc / 1023) * 3.3

            if ir_voltage < 0.4:
                angle35 = 180
            elif ir_voltage > 2.5:
                angle35 = 0
            else:
                angle35 = int((2.5 - ir_voltage) / 2.1 * 180)

            current_angle35 = move_servo_smooth(motor35_channel, current_angle35, angle35)
            # 예시: 간단한 역수 기반 모델 (가까워질수록 거리 작아짐)
            distance_cm = int(27.86 / (ir_voltage + 0.1))  # +0.1은 0으로 나누는 걸 방지

            print(f"[35kg] 전압: {ir_voltage:.2f}V → 거리: {distance_cm}cm, 각도: {angle35}°")

            if now - last_sent_time >= send_interval:
                send_distance_to_server_async(distance_cm)
                last_sent_time = now

            # [2] 가변저항 (150kg 서보 제어용)
            #pot_adc = read_adc(0)
            #pot_voltage = (pot_adc / 1023) * 3.3
            #angle150 = int((pot_voltage / 3.3) * 180)
            #print(f"[150kg] 전압: {pot_voltage:.2f}V → 각도: {angle3}°")
            #current_angle150 = move_servo_smooth(motor150_channel, current_angle150, angle150)
            angle150 = get_pitch_from_server()
            current_angle150 = move_servo_smooth(motor150_channel, current_angle150, angle150)
            print(f"[150kg] 각도: {angle150}°")
            last_update = now

except KeyboardInterrupt:
    print("⛔ 종료됨")

finally:
    pca.deinit()
    spi.close()
