# 🖥️ 2025 Vision AI Smart Monitor PoseIT (2024.09 ~ 2025.12)

식물이 자라는 최적의 환경을 유지하기 위해 온습도, 조도, 토양 수분 상태를 모니터링하고 자동으로 환경을 제어하고 

**ESP32 기반의 센서 데이터 수집 및 자동 제어 기능을 구현한 IoT 스마트 온실 시스템입니다.**

온도, 습도, 조도, 토양 수분 데이터를 실시간으로 수집하고,
설정된 조건에 따라 워터펌프, 팬 모터, LED를 자동 제어하도록 구현했습니다.

또한 MQTT 브로커를 통해 데이터를 전송하고,
InfluxDB 및 Grafana를 활용하여 실시간 환경 데이터를 시각화했습니다.

---


## 🔧 Tech Stack

### Hardware
- ESP32
- TFT Display
- 조도센서(BH1750)
- 온습도센서(DHT22)
- 팬모터(EZ Motor R300)
- 릴레이모듈(4 relay module)
- LED(8-bit 2812 RGB)
- 토양 습도 센서 모듈(SZH-EK106)
- A/D 컨버터 모듈
- DC 워터 펌프(FIT0910)


### Software
- Arduino IDE / C++
- MQTT
- InfluxDB
- Grafana

---

## 🖥 시스템 아키텍처

센서 데이터 수집 →
ESP32 실시간 처리 →
MQTT 브로커 전송 →
InfluxDB 저장 →
Grafana 시각화 →
조건 기반 자동 제어

<img width="1858" height="1502" alt="image" src="https://github.com/user-attachments/assets/e6b4b43f-61e6-47d5-8551-c91ab154ea4b" />


---

## 🚀 주요 기능

### Real-time Environment Monitoring
- 온도 / 습도 / 조도 / 토양 수분 데이터 수집
- TFT 및 Web Dashboard 실시간 출력

### Automatic Water Pump Control
- 토양 수분 값이 임계값 이하일 경우 워터펌프 자동 동작

### Fan Motor Control
- 온도 및 습도 조건 기반 팬 제어

### LED Brightness Control
- 조도 센서 값을 기반으로 LED 자동 제어

### MQTT-based Data Communication
- MQTT 브로커를 통한 센서 데이터 송수신

### Data Visualization
- InfluxDB 및 Grafana를 활용한 실시간 데이터 시각화

---

## 👨‍💻 My Role

- ESP32 기반 센서 데이터 수집 및 TFT 상태 출력 구현
- MQTT 기반 센서 데이터 송수신 구조 구현
- 토양 수분 / 온습도 / 조도 조건 기반 자동 제어 로직 설계
- InfluxDB 및 Grafana 기반 환경 데이터 시각화 구성

---

## 🛠 Troubleshooting

### 센서 노이즈 필터링
센서 값이 순간적으로 튀는 문제가 발생하여
주기 기반 평균 처리 로직을 적용해 데이터 안정성을 개선했습니다.

### 조건 기반 채터링 완화
임계값 근처에서 워터펌프가 반복 동작하는 문제가 발생하여
상태 유지 조건 기반 제어 로직을 추가해 채터링을 완화했습니다.

---

## 🎥 Demo Video

https://youtu.be/CeD-fb0U9y4

---

## 📈 Result

- ESP32 기반 IoT 환경 자동 제어 시스템 구현
- MQTT 기반 실시간 데이터 통신 구조 구축
- InfluxDB/Grafana 기반 센서 데이터 시각화 구현


---

<br>
<br>




**[📂 Additional Demo]**

