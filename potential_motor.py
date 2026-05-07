from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685
import spidev

# SPI 초기화 (MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel=0):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

# PCA9685 초기화
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# PWM 변환 함수
def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000
    duty = int(pulse / 1000000 * 50 * 65535)
    return duty

motor150_channel = 0  # 150kg 모터
#motor35_channel = 1  # 35kg 모터

try:
    # 이전 각도와 비교해서 변화 크기 클 때만 업데이트
    prev_angle = -1

    while True:
        adc_val = read_adc(0)
        angle = (adc_val / 1023) * 180
        if abs(angle - prev_angle) > 1:  # 변화가 1도 이상일 때만 갱신
            pwm = angle_to_pwm(angle)
            pca.channels[motor150_channel].duty_cycle = pwm
            #pca.channels[motor35_channel].duty_cycle = pwm
            prev_angle = angle

        print(f"ADC: {adc_val}, 각도: {int(angle)}")
        time.sleep(0.008)

except KeyboardInterrupt:
    print("종료됨")

finally:
    pca.deinit()
    spi.close()
