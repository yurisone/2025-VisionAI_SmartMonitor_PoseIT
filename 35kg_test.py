from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685

# I2C 초기화
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 서보는 50Hz로 고정

# 각도를 PWM으로 변환하는 함수
def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000  # 0~180도 → 500~2500us
    duty = int(pulse / 1000000 * 50 * 65535)
    return duty

# 0° → 90° → 180° → 90° 순서로 테스트
try:
    for angle in [0, 90, 180, 90, 0]:
        print(f"서보 각도: {angle}")
        pca.channels[0].duty_cycle = angle_to_pwm(angle)
        time.sleep(1)

except KeyboardInterrupt:
    print("종료합니다.")

finally:
    pca.deinit()
