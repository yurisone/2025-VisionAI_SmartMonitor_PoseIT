import spidev
import time

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)              # bus 0, device 0 (CE0 사용)
spi.max_speed_hz = 1350000  # SPI 통신 속도

# ADC 읽기 함수 (MCP3008)
def read_adc(channel=1):  # CH1에 센서 연결됨
    if not 0 <= channel <= 7:
        return -1
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((r[1] & 3) << 8) + r[2]
    return value

try:
    while True:
        adc_val = read_adc(1)  # CH1 사용
        voltage = (adc_val / 1023) * 3.3  # 전압으로 변환
        print(f"ADC 값: {adc_val} / 전압: {voltage:.2f} V")
        time.sleep(0.3)

except KeyboardInterrupt:
    print("종료됨")

finally:
    spi.close()
