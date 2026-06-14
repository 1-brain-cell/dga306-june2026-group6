# แหล่งข้อมูล (Sources)

บันทึกชุดข้อมูลที่ใช้ในโครงการ DGA306 Day 4 — ตามกฎใน AGENTS.md
ทุกรายการตรวจสอบจากหน้าเว็บจริง ณ วันที่ 14 มิถุนายน 2569

---

## ชุดข้อมูลที่ 1 — กรมธุรกิจพลังงาน (DOEB)

| ฟิลด์ | ค่า |
|---|---|
| **ชื่อชุดข้อมูล (ไทย)** | ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 |
| **หน่วยงาน** | กรมธุรกิจพลังงาน — กองบริการธุรกิจและการสำรองน้ำมันเชื้อเพลิง (กบส.) — กลุ่มประมวลข้อมูล (ปข.) |
| **gdcatalog URL** | https://gdcatalog.go.th/dataset/gdpublish-ado-b7 |
| **Origin catalog URL** | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7 |
| **ลงทะเบียนใน GD-Catalog วันที่** | 25 มิถุนายน 2567 |
| **ปรับปรุงครั้งล่าสุดในระบบเมื่อ** | 21 ธันวาคม 2568 |
| **ปีข้อมูลที่ครอบคลุม** | 2560 – 2568 |
| **หมายเหตุขอบเขต** | เฉพาะผู้ค้าน้ำมันตามมาตรา 7 — ข้อมูลปริมาณการจำหน่ายรายจังหวัด |
| **รูปแบบไฟล์** | CSV (2560–2567), XLSX (2568) |
| **ติดต่อ** | data@doeb.go.th |

### URL ดาวน์โหลดทุกปี (ยืนยันจาก data.doeb.go.th)

| ปี | รูปแบบ | URL ดาวน์โหลดโดยตรง |
|---|---|---|
| 2560 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/d7520cce-65f5-465a-828a-669f2e1d72aa/download/002_diesel_ado_b7_60.csv |
| 2561 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/c9a7b9d2-39cd-4648-977c-bb28304f2c2d/download/002_diesel_ado_b7_61.csv |
| 2562 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/fafaafec-c273-48d3-a695-37931f164452/download/002_diesel_ado_b7_62.csv |
| 2563 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/8643d629-ac9a-45f4-be23-268972cc6dcd/download/002_diesel_ado_b7_63.csv |
| 2564 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/03df90d9-8f61-4a59-802f-a45588cc0ceb/download/002_diesel_ado_b7_64.csv |
| 2565 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/791c4223-ed5a-475e-8fd2-d1fb03176c42/download/002_diesel_ado_b7_65.csv |
| 2566 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/6a2db7c3-e9fa-430e-a3fc-e5687ffe97f5/download/002_diesel_ado_b7_66.csv |
| 2567 | CSV | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/a0f2fbfc-abf8-4f72-8832-585bcadaeccf/download/2567.csv |
| 2568 | XLSX | https://data.doeb.go.th/dataset/ce709041-d37a-401f-b855-99493816e7b7/resource/0c2c573d-57b9-4865-b56f-aa841d9c8043/download/untitled.xlsx |

> หมายเหตุ: ไฟล์ปี 2568 เป็นรูปแบบ XLSX ให้ใช้ engine='xlrd' หรือ openpyxl และตรวจสอบ
> header หลายแถวก่อนประมวลผล ตามกฎใน AGENTS.md

---

## ชุดข้อมูลที่ 2 — กรมคุมประพฤติ (Probation)

| ฟิลด์ | ค่า |
|---|---|
| **ชื่อชุดข้อมูล (ไทย)** | การรับคดีคุมความประพฤติผู้กระทำผิดที่เป็นผู้ใหญ่ |
| **หน่วยงาน** | กรมคุมประพฤติ — กระทรวงยุติธรรม |
| **gdcatalog URL** | https://gdcatalog.go.th/dataset/gdpublish-probation-21-01 |
| **Origin catalog URL** | https://probation.gdcatalog.go.th/dataset/aca2c825-c0df-4e30-94e4-2fe84851014c |
| **data.go.th URL** | https://data.go.th/dataset/aca2c825-c0df-4e30-94e4-2fe84851014c |
| **ลงทะเบียนใน GD-Catalog วันที่** | 7 เมษายน 2569 |
| **ปรับปรุงครั้งล่าสุดในระบบเมื่อ** | 7 พฤษภาคม 2569 |
| **ปีข้อมูลที่เริ่มต้นจัดทำ** | 2565 |
| **ปีข้อมูลล่าสุดที่เผยแพร่** | 2566 |
| **ปีข้อมูลที่ครอบคลุม** | 2565 – 2566 |
| **ขอบเขตเชิงภูมิศาสตร์** | จังหวัด (ยืนยันจากฟิลด์ "ขอบเขตเชิงภูมิศาสตร์หรือเชิงพื้นที่" = จังหวัด) |
| **การจัดจำแนก** | ขอบเขตเชิงภูมิศาสตร์หรือเชิงพื้นที่ + ฐานความผิด |
| **หมายเหตุขอบเขต** | คุมประพฤติผู้กระทำผิดที่มีอายุตั้งแต่ 18 ปีบริบูรณ์ขึ้นไป ในวันที่การกระทำผิดเกิดขึ้น |
| **หน่วยวัด** | คดี |
| **รูปแบบไฟล์** | CSV, XLSX |
| **ความถี่การปรับปรุง** | ทุกเดือน |
| **ฝ่ายงานสำหรับติดต่อ** | กองอำนวยการบังคับใช้กฎหมายเพื่อการคุมประพฤติ |
| **อีเมลสำหรับติดต่อ** | ict_gdcatalog@probation.mail.go.th |
| **URL ข้อมูลเพิ่มเติม** | https://www.probation.go.th/contentmenu.php?id=158 |

### URL ดาวน์โหลดทุกปี (ยืนยันจาก gdcatalog.go.th/dataset/gdpublish-probation-21-01)

| ปี | รูปแบบ | ชื่อทรัพยากร | URL ดาวน์โหลดโดยตรง |
|---|---|---|---|
| 2565 | CSV | จำนวนคดีสอดส่องผู้ใหญ่ (สอดส่องปอ.56) | https://probation.gdcatalog.go.th/dataset/aca2c825-c0df-4e30-94e4-2fe84851014c/resource/53f52643-8ca7-4481-8e04-9a07556d7428/download/1.probation_21_01_2565.csv |
| 2566 | CSV | จำนวนคดีสอดส่องผู้ใหญ่ (สอดส่องปอ.56) | https://probation.gdcatalog.go.th/dataset/aca2c825-c0df-4e30-94e4-2fe84851014c/resource/297f2bf4-e429-4444-809d-e98f3878564c/download/1.probation_21_01_2566.csv |
| 2565 | CSV | คดีสอดส่อง (ผู้ใหญ่) จำแนกตามฐานความผิด | https://probation.gdcatalog.go.th/dataset/aca2c825-c0df-4e30-94e4-2fe84851014c/resource/db84f111-3770-476f-8abb-14b500be4de2/download/1.probation_21_01_2565_guilty.csv |

> หมายเหตุ: ชุดข้อมูลนี้ครอบคลุม "การรับคดีคุมความประพฤติผู้กระทำผิดที่เป็นผู้ใหญ่"
> จำแนกตามจังหวัด และฐานความผิด ซึ่งสอดคล้องกับที่ต้องการ (จำแนกจังหวัด/ปีงบประมาณ)
> ข้อมูลปีงบประมาณ: ปีงบประมาณ 2565 และ 2566 (ตุลาคม – กันยายน)


