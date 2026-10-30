# 🪙 GoldSense Research

ต้นแบบวิจัยทิศทางราคาทองล่วงหน้า (GC=F) ด้วย Python + Streamlit
UI ภาษาไทย ธีมกรมท่า–ทอง ออกแบบให้ใช้บนมือถือ

> ต้นแบบวิจัยเท่านั้น ไม่ใช่ราคาทองไทย ไม่ใช่ระบบ production
> เปอร์เซ็นต์ยังไม่ได้สอบเทียบ และไม่ใช่คำแนะนำลงทุน

## เปิดเป็นแอปบนหน้าจอโทรศัพท์ (ฟรี ไม่ต้องใช้คอม)

### 1) Deploy บน Streamlit Community Cloud
1. เปิด https://share.streamlit.io แล้วเข้าสู่ระบบด้วย GitHub
2. กด **Create app** → **Deploy a public app from GitHub**
3. Repository: `mengnattawitmarin/goldsense` · Branch: `main` · Main file: `app.py`
4. (ไม่บังคับ) ตั้ง App URL เช่น `goldsense` → ได้ `https://goldsense.streamlit.app`
5. Advanced settings → Python 3.12 → กด **Deploy** รอ 2–5 นาที

### 2) เพิ่มลงหน้าจอโฮม
- **Android (Chrome):** เปิดลิงก์แอป → เมนู ⋮ → **เพิ่มลงในหน้าจอหลัก / Add to Home screen**
- **iPhone (Safari):** เปิดลิงก์แอป → ปุ่มแชร์ □↑ → **เพิ่มไปยังหน้าจอโฮม**

### หมายเหตุ
- แอปบน Streamlit Cloud จะ "หลับ" ถ้าไม่มีคนเปิดนาน เปิดครั้งแรกอาจต้องกดปุ่มปลุกและรอ ~1 นาที
- ข้อมูลอัปเดตทุกชั่วโมงขณะเปิดแอป หรือกด 🔄 ตรวจข้อมูลใหม่
- ข้อมูลมาจาก Yahoo Finance ผ่าน yfinance บางครั้งโดนจำกัดการเรียก ให้ลองใหม่ภายหลัง

## รันบนคอมพิวเตอร์
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## ทดสอบ
```bash
pip install -r requirements-dev.txt
pytest -q
```
ทดสอบด้วยข้อมูลจำลอง: ปัจจัยไม่ใช้ราคาของแถวตัวเอง, งดทำนายเมื่อข้อมูลไม่ครบ,
ตัดแท่งของวันปัจจุบัน และข้อมูลไม่พอ 500 แถวต้องหยุด

## ไฟล์
| ไฟล์ | หน้าที่ |
|---|---|
| `app.py` | หน้าแอป Streamlit (mobile-first) |
| `goldsense_core.py` | โหลดข้อมูล สร้างปัจจัย โมเดล บทวิเคราะห์ (ไม่พึ่ง Streamlit) |
| `tests/test_core.py` | unit tests |
| `.streamlit/config.toml` | ธีมสี |
| `ALGORITHM.md` | นิยามโมเดลและการทดสอบ |
| `AI_HANDOFF.md` | ข้อกำหนดสำหรับพัฒนาต่อ |

## ข้อจำกัด
- GC=F เป็นทองล่วงหน้า ไม่ใช่ Gold Spot และอาจกระโดดตอนเปลี่ยนสัญญา
- ทดสอบแบบ holdout 80/20 ครั้งเดียว ยังไม่ใช่ walk-forward ไม่มี calibration
- ยังไม่มีข่าว Real Yield ราคาทองไทย ฐานข้อมูล หรือ scheduler เบื้องหลัง
- requirements เป็นช่วงรุ่น ควรล็อกรุ่นหลังรันบน Cloud สำเร็จ
