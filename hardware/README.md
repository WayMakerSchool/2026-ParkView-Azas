# ParkView Raspberry Pi

IP CCTV 영상을 라즈베리파이에서 분석하고, 주차면 상태만 ParkView 앱에 제공하는 엣지 서버입니다. ESP32 펌웨어는 이 프로젝트에 포함하지 않습니다.

## 처리 흐름

1. IP CCTV의 RTSP 스트림에서 30초마다 프레임을 가져옵니다.
2. YOLO가 자동차 계열 객체만 탐지합니다.
3. 탐지 중심점을 설치 시 등록한 주차면 폴리곤과 매칭합니다.
4. 두 번 연속 빈 상태가 확인된 뒤에만 `empty`로 변경합니다.
5. `/api/result`와 선택적인 Firebase 전송으로 결과를 제공합니다.

## Mac에서 먼저 확인

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python server.py --host 0.0.0.0 --port 5180
```

`.env`에서 `PARKVIEW_CAMERA_URL`을 실제 CCTV RTSP 주소로 바꿔야 분석이 시작됩니다.

```text
http://라즈베리파이주소:5180/api/health
http://라즈베리파이주소:5180/api/result
http://라즈베리파이주소:5180/calibrate.html
```

## 실제 설치

라즈베리파이에서 프로젝트 폴더로 이동한 다음 실행합니다.

```bash
sudo ./deploy/install-raspberry-pi.sh
sudo nano /opt/parkview/.env
sudo systemctl start parkview-edge
sudo journalctl -u parkview-edge -f
```

주차면 등록은 설치 중에만 `PARKVIEW_CALIBRATION_MODE=true`로 켜고 진행합니다. 등록이 끝나면 다시 `false`로 바꿉니다.

## 앱 연결

`Parkview-Web/config.js`의 `edgeApiBaseUrl`에 라즈베리파이 주소를 입력합니다.

```js
window.PARKVIEW_CONFIG = {
  edgeApiBaseUrl: "http://raspberrypi.local:5180"
};
```

웹앱과 라즈베리파이가 같은 주소에서 서비스되면 빈 문자열을 유지합니다.
