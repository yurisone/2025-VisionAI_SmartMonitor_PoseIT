# 🖥️ 2025 Vision AI Smart Monitor PoseIT (2024.09 ~ 2025.10)

사용자의 목각도와 모니터 간 거리를 실시간으로 모니터링하고 거북목이나 부적절한 시청 거리가 감지될 경우 모니터의 위치를 자동 제어하는 

**Vision AI 기반 하드웨어 통합 제어 시스템입니다.**

카메라와 IR 센서를 통해 자세 데이터를 수집하고 설정된 임계값과 유지 조건(State Machine)에 따라 3-DOF(전후, 상하, 틸트) 모터를 동기 제어하여 사용자에게 최적의 시청 환경을 물리적으로 제공하도록 구현했습니다.

---


## 🔧 Tech Stack

### Hardware & MCU
- Raspberry Pi 4B, NVIDIA Jetson Nano
- IR 거리 센서 (GP2Y0A21YK0F), 웹캠
- ADC 모듈 (MCP3008)
- 16채널 PWM 서보 드라이버 (PCA9685)
- 스텝모터 드라이버 (DM542)
- 리니어 레일 슬라이드 스텝모터 (57SFD04)
- 150kg 서보 모터 (RDS51150)
- 35kg 서보 모터 (DS3235-7.4)


### Software & Protocols
- Python, Kotlin
- Hardware Interface: SPI, I2C, GPIO, PWM
- AI & Vision: OpenCV, MediaPipe (목각도 연산)
- Network: HTTP / REST API (Flask 연동)

---

## 🖥 시스템 아키텍처

카메라/IR 센서 데이터 수집 → SPI 통신(ADC 변환) → Jetson/RPi 실시간 연산 → 조건 기반 상태 판단(5초 유지) → I2C/GPIO 통신 제어 → 3축 모터 자동 구동
<img width="1544" height="638" alt="image" src="https://github.com/user-attachments/assets/9d7c0f04-0ee7-4f99-95f7-61818148f17e" />


---

## 🚀 주요 기능

### Real-time Posture & Distance Monitoring
- MediaPipe 기반 귀-어깨-코 랜드마크 추출 및 목각도(Pitch) 연산
- MCP3008(ADC)과 SPI 통신을 연동하여 아날로그 IR 센서의 실시간 거리 데이터 수집

### 3축 모터 제어 (전후/상하/틸트 제어)
- M1 (리니어 레일 슬라이드 + 스텝모터): GPIO 핀을 이용해 스텝모터 드라이버(DM542) 제어, 모니터 전후 거리 조절
- M2, M3 (서보모터): PCA9685 PWM 모듈과 I2C 통신을 통해 모니터 높이 및 화면 틸트 각도 미세 동기 제어

### State Machine 기반 안전 제어 로직
- 일시적인 움직임에 의한 오작동을 막기 위해 5초 이상 거북목 상태가 유지될 때만 제어 명령을 인가하는 상태 전이 로직 구현
- 5초간 정상 자세 복귀 시 모니터를 원래 위치로 복원하는 자동화 루틴 적용
---

## 👨‍💻 My Role

- SPI/I2C 통신 기반 다중 하드웨어 제어망 구축: MCP3008(SPI)을 통한 센서 수집 및 PCA9685(I2C) 기반 다중 모터 동기 제어 로직 구현
- IR 센서 비선형 오차 보정 알고리즘 설계: 데이터 기반 다항식 곡선 피팅 보정 모델 적용
- 하드웨어 보호를 위한 제어 로직 설계: 채터링(잦은 구동) 방지를 위한 State Machine(상태 유지) 알고리즘 설계
<img width="1351" height="821" alt="image" src="https://github.com/user-attachments/assets/6dfbf20a-0a51-4641-a11d-3f0252aad63c" />

---

## 🛠 Troubleshooting

### 비선형 센서 오차 극복을 위한 곡선 피팅 보정 (오차 3% 이하)
**문제**: 예산 제약으로 라이다(LiDAR) 대신 IR 센서를 적용했으나, 출력 전압과 거리 간의 비선형 특성으로 인해 측정값이 튀어 제어 안정성이 떨어졌습니다. 
<br><br>
**해결**: 10cm 단위로 거리별 전압 데이터를 30회 이상 반복 수집한 후 이를 기반으로 2차 다항식 곡선 피팅 보정 모델을 도출하여 적용했습니다.
그 결과 물리적 하드웨어의 제약을 소프트웨어 로직으로 보완하여 거리 측정 오차를 3% 이하로 낮추는 데 성공했습니다.

### 채터링(기계적 마모) 방지를 위한 State Machine 유지 로직 적용
**문제**: 센서 보정 후에도 사용자가 잠깐 물건을 줍는 등의 일시적 움직임에 모터가 민감하게 반응하여 불필요한 구동(채터링)과 기계적 마모가 발생했습니다.
<br><br>
**해결**: 단순한 Delay 처리가 아닌, 매 루프마다 자세 조건을 재판단해 특정 상태(목각도 50도 이하 등)가 5초 이상 연속 지속될 때만 PWM 제어 명령을 인가하는 상태 유지(State Machine) 시간 필터링 로직을 구현했습니다.
---

## 🎥 Demo Video

https://youtu.be/CeD-fb0U9y4

---

## 📈 Result

- I2C/SPI 기반 3축 모터 통합 제어 시스템 성공적 구축
- 센서 노이즈 및 일시적 오작동을 줄이기 위한 임베디드 제어 안정화 로직 설계
- 물리적 장비의 상태 전이(State Machine) 구조 적용을 통한 하드웨어 제어 안정성 최적화


---

<br>
<br>


