import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from collections import deque
import RPi.GPIO as GPIO
import spidev
import requests

# [1] M1 제어부 (리니어 액추에이터) - 모니터를 사용자 쪽으로 전진 / 후진
PUL = 17
DIR = 27
ENA = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)

def rotate_step(direction, delay=0.0005, steps=1500):
    GPIO.output(DIR, GPIO.HIGH if direction == 'a' else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(delay)b       
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(delay)

def move_monitor_forward():
    print("[M1] 모니터 전진")
    rotate_step('d', 0.0005, 1500)

def move_monitor_backward():
    print("[M1] 모니터 후진")
    rotate_step('a', 0.0005, 1500)

# [2] M2, M3 제어부 I2C & PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000
    return int(pulse / 1_000_000 * 50 * 65535)

def move_servo_smooth(channel, current_angle, target_angle, delay=0.02):
    step = 1 if target_angle > current_angle else -1
    for angle in range(current_angle, target_angle + step, step):
        pwm = angle_to_pwm(angle)
        pca.channels[channel].duty_cycle = pwm
        time.sleep(delay)
    return target_angle

# [3] SPI (IR 센서 거리 측정부) GP2Y0A21YK0F / MCP3008을 통해 SPI 통신으로 읽음
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel=1):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

def adc_to_distance(adc_val):
    # ADC 값 → 전압 → 거리(cm)
    voltage = (adc_val / 1023) * 3.3
    if voltage <= 0.4:
        return 80
    distance = 27.86 / (voltage + 0.1)
    return round(min(max(distance, 10), 80), 1)

# 거리값 서버로 전송

def send_distance_to_server(distance_cm):
    url = "http://18.204.77.217:5000/save_distance"
    data = {"distance_cm": distance_cm}
    try:
        res = requests.post(url, json=data, timeout=3)
        if res.status_code == 200:
            print("✅ 서버에 거리값 전송 성공")
        else:
            print(f"❗서버 전송 실패: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"❌ 서버 전송 예외: {e}")

# 서버로부터 pitch 값 받아오기
def get_pitch_from_server():
    try:
        res = requests.get("http://18.204.77.217:5000/get_pitch", timeout=5)
        if res.status_code == 200:
            data = res.json()
            pitch = int(data.get("pitch_angle", 90))
            print(f"✅ 서버 응답 성공: 목각도 = {pitch}")
            return pitch
        else:
            print(f"⚠️ 서버 응답 실패, 상태코드: {res.status_code}")
            return 90
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return 90

# [5] 상태 변수 초기화
motor150_channel = 0
motor35_channel = 1
m1_status = "neutral"
m1_last_action_time = 0
m1_ready_time = 0
M1_REST_DURATION = 5

m2_original = 130
m2_raised = 115
current_angle_m2 = m2_original
m2_active = False
m2_last_action_time = 0

m3_original = 80
m3_lowered = 95
current_angle_m3 = m3_original
m3_active = False
m3_action_time = 0
M3_HOLD_DURATION = 5

m3_triggered_by_m2 = False


distance_buffer = deque(maxlen=5)

is_forward_head = False
forward_head_start_time = 0

# 초기 서보 위치 설정
current_angle_m2 = move_servo_smooth(motor150_channel, current_angle_m2, m2_original)
current_angle_m3 = move_servo_smooth(motor35_channel, current_angle_m3, m3_original)

try:
    while True:
        now = time.time()

        adc_val = read_adc(1)
        distance_cm = adc_to_distance(adc_val)

        send_distance_to_server(distance_cm)

        ##################################
        pitch = get_pitch_from_server()
        #pitch = 45  # 🎯 임의 고정 테스트

        if pitch < 50:
            if not is_forward_head:
                is_forward_head = True
                forward_head_start_time = now
        else:
            is_forward_head = False
            forward_head_start_time = 0

        distance_buffer.append(distance_cm)

        # M3 동작 - 2초 후 하강, 5초 후 복귀
        if m3_triggered_by_m2 and not m3_active and (now - m2_last_action_time >= 2):
            print("[M3] M2 이후 2초 경과 → M3 아래로")
            current_angle_m3 = move_servo_smooth(motor35_channel, current_angle_m3, m3_lowered)
            m3_active = True
            m3_action_time = now

        if m3_active and now - m3_action_time >= M3_HOLD_DURATION:
            print("[M3] 복귀")
            current_angle_m3 = move_servo_smooth(motor35_channel, current_angle_m3, m3_original)
            m3_active = False
            m3_triggered_by_m2 = False

        if m2_active and now - m2_last_action_time >= 5:
            print("[M2] 복귀")
            current_angle_m2 = move_servo_smooth(motor150_channel, current_angle_m2, m2_original)
            m2_active = False
            m1_ready_time = now

        if (
            not m2_active
            and now - m1_ready_time >= M1_REST_DURATION
            and is_forward_head
            and now - forward_head_start_time >= 5
        ):
            if distance_cm <= 40:
                print("[CASE 1] 거북목 + 가까움 → M1 후진 + M2 상승")
                move_monitor_backward()
                m1_status = "backward"
                current_angle_m2 = move_servo_smooth(motor150_channel, current_angle_m2, m2_raised)
                m2_active = True
                m2_last_action_time = now
                m1_ready_time = now
                m3_triggered_by_m2 = True
            elif 40 < distance_cm <= 45:
                print("[CASE 2] 거북목 + 중간 → M2 상승")
                current_angle_m2 = move_servo_smooth(motor150_channel, current_angle_m2, m2_raised)
                m2_active = True
                m2_last_action_time = now
                m1_ready_time = now
                m3_triggered_by_m2 = True
            elif distance_cm > 45:
                print("[CASE 3] 거북목 + 멀음 → M1 전진")
                move_monitor_forward()
                m1_status = "forward"
                m1_ready_time = now

        print(f"[IR] {distance_cm:.1f}cm (ADC: {adc_val}), [M2] 각도: {current_angle_m2}°, [M3] tilt각: {current_angle_m3}°")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n⛔ 종료됨")
finally:
    pca.deinit()
    spi.close()
    GPIO.cleanup()
