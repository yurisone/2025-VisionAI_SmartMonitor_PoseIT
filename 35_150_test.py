from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685

# I2C 초기화
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 서보는 50Hz

# 각도를 PWM으로 변환하는 함수
def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000  # 0~180도 → 500~2500us
    duty = int(pulse / 1000000 * 50 * 65535)
    return duty

# 제어할 채널 번호
motor2_channel = 0  # 35kg 모터
motor3_channel = 1  # 150kg 모터

try:
    for angle in [0, 90, 180, 90, 0]:
        print(f"모터2 (채널 {motor2_channel}) 각도: {angle}")
        print(f"모터3 (채널 {motor3_channel}) 각도: {180 - angle}")  # 반대 방향으로 예시
        pca.channels[motor2_channel].duty_cycle = angle_to_pwm(angle)
        pca.channels[motor3_channel].duty_cycle = angle_to_pwm(180 - angle)
        time.sleep(1)

except KeyboardInterrupt:
    print("사용자 종료")

finally:
    pca.deinit()
