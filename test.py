from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
import time

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

def set_pulse(pulse):
    duty = int(pulse / 1000000 * 50 * 65535)
    pca.channels[0].duty_cycle = duty

try:
    while True:
        print("0도")
        set_pulse(600)    # 0도 근처
        time.sleep(1)

        print("90도")
        set_pulse(1500)   # 중립
        time.sleep(1)

        print("180도")
        set_pulse(2400)   # 180도 근처
        time.sleep(1)

except KeyboardInterrupt:
    print("종료합니다.")
    pca.deinit()
