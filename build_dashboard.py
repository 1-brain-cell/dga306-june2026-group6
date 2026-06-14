"""
build_dashboard.py
สร้างไฟล์ output/integrated_dashboard.html
รวมแผนภาพจากโน้ตบุ๊ก A, B, C พร้อมกล่องหมายเหตุและเรื่องราวการเล่าเรื่อง (Storytelling)
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pathlib, json

# ── พาธ ──────────────────────────────────────────────────────────────────────
BASE   = pathlib.Path(__file__).parent
OUT    = BASE / "output" / "integrated_dashboard.html"
DATA   = BASE / "data" / "processed"

TEMPLATE    = "plotly_white"
FONT_FAMILY = "Sarabun, IBM Plex Sans Thai, sans-serif"
UNIT_FUEL   = "พันลิตรต่อเดือน"

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 1  โหลดข้อมูลเชื้อเพลิง (Notebook A & C)
# ═════════════════════════════════════════════════════════════════════════════
print("โหลดข้อมูลน้ำมัน …")
try:
    df_fuel_raw = pd.read_csv(DATA / "doeb_ado_b7_combined.csv", encoding="utf-8", low_memory=False)
except UnicodeDecodeError:
    df_fuel_raw = pd.read_csv(DATA / "doeb_ado_b7_combined.csv", encoding="cp874", low_memory=False)

df_fuel = df_fuel_raw.dropna(subset=["OIL_NAME_ENG"]).copy()
df_fuel["year_ce"] = df_fuel["YEAR_ID"] - 543
df_fuel["date"] = pd.to_datetime(
    df_fuel["year_ce"].astype(str) + "-" + df_fuel["MONTH_ID"].astype(str).str.zfill(2) + "-01"
)

df_monthly = (
    df_fuel.groupby(["date", "YEAR_ID", "year_ce", "MONTH_ID", "OIL_NAME_ENG", "OIL_NAME_THAI"], as_index=False)
    ["QTY"].sum().sort_values("date")
)

df_monthly_total = df_monthly.groupby("date")["QTY"].transform("sum")
df_monthly = df_monthly.copy()
df_monthly["share_pct"] = (df_monthly["QTY"] / df_monthly_total * 100).round(2)

MONTH_ABBR = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

df_heat = df_fuel.groupby(["YEAR_ID","MONTH_ID"], as_index=False)["QTY"].sum()
pivot = df_heat.pivot(index="YEAR_ID", columns="MONTH_ID", values="QTY")
pivot.index = pivot.index.astype(str)
pivot.columns = [MONTH_ABBR[m] for m in pivot.columns]
month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
pivot = pivot[[c for c in month_order if c in pivot.columns]]

COLOR_MAP = {"ADO B7": "#1f77b4", "ADO": "#ff7f0e"}

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 2  โหลดข้อมูลคุมประพฤติ (Notebook B)
# ═════════════════════════════════════════════════════════════════════════════
print("โหลดข้อมูลคุมประพฤติ …")
try:
    df_prob = pd.read_csv(DATA / "probation_adult_combined.csv", encoding="utf-8")
except UnicodeDecodeError:
    df_prob = pd.read_csv(DATA / "probation_adult_combined.csv", encoding="cp874")

try:
    df_guilty = pd.read_csv(DATA / "probation_adult_2565_guilty_clean.csv", encoding="utf-8")
except UnicodeDecodeError:
    df_guilty = pd.read_csv(DATA / "probation_adult_2565_guilty_clean.csv", encoding="cp874")

def extract_province(name):
    name = str(name).replace("สำนักงานคุมประพฤติ", "").replace("จังหวัด", "").strip()
    return name.split(" ")[0]

df_prob["Province"] = df_prob["สำนักงานคุมประพฤติ"].apply(extract_province)

month_map = {
    "ม.ค.":"01","ก.พ.":"02","มี.ค.":"03","เม.ย.":"04","พ.ค.":"05","มิ.ย.":"06",
    "ก.ค.":"07","ส.ค.":"08","ก.ย.":"09","ต.ค.":"10","พ.ย.":"11","ธ.ค.":"12"
}

def parse_date(my):
    parts = str(my).split(" ")
    if len(parts) >= 2:
        m_y = parts[1]
        for th, en in month_map.items():
            if th in m_y:
                y = m_y.replace(th, "")
                try:
                    return f"{int(y)-543}-{en}-01"
                except ValueError:
                    return None
    return None

id_vars = ["สำนักงานคุมประพฤติ", "Province", "year_be"]
month_cols = [c for c in df_prob.columns if c not in id_vars]
df_long = df_prob.melt(id_vars=id_vars, value_vars=month_cols, var_name="Month_Year", value_name="Cases")
df_long["Cases"] = df_long["Cases"].fillna(0).astype(int)
df_long["Date"] = pd.to_datetime(df_long["Month_Year"].apply(parse_date), errors="coerce")
df_long = df_long.dropna(subset=["Date"]).sort_values("Date")

id_vars_g = ["ฐานความผิด", "year_be"]
month_cols_g = [c for c in df_guilty.columns if c not in id_vars_g]
df_g_long = df_guilty.melt(id_vars=id_vars_g, value_vars=month_cols_g, var_name="Month_Year", value_name="Cases")
df_g_long["Cases"] = df_g_long["Cases"].fillna(0).astype(int)
df_g_long["Date"] = pd.to_datetime(df_g_long["Month_Year"].apply(parse_date), errors="coerce")
df_g_long = df_g_long.dropna(subset=["Date"]).sort_values("Date")

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 3  เตรียมข้อมูล ML (Notebook C)
# ═════════════════════════════════════════════════════════════════════════════
print("เตรียม ML …")
df_b7 = df_fuel[df_fuel["OIL_NAME_ENG"] == "ADO B7"].copy()
df_ml = (
    df_b7.groupby(["date","MONTH_ID"], as_index=False)["QTY"].sum()
    .sort_values("date").reset_index(drop=True)
)
df_ml["trend"] = np.arange(len(df_ml))
month_dummies = pd.get_dummies(df_ml["MONTH_ID"], prefix="month", drop_first=True).astype(int)
df_feat = pd.concat([df_ml[["date","QTY","trend"]], month_dummies], axis=1)
FEATURE_COLS = [c for c in df_feat.columns if c not in ["date","QTY"]]

N_TEST = 20
X = df_feat[FEATURE_COLS].values.astype(float)
y = df_feat["QTY"].values.astype(float)
dates_all = df_feat["date"].values

X_train, X_test = X[:-N_TEST], X[-N_TEST:]
y_train, y_test = y[:-N_TEST], y[-N_TEST:]
dates_train = dates_all[:-N_TEST]
dates_test  = dates_all[-N_TEST:]

model = LinearRegression()
model.fit(X_train, y_train)
y_pred_train = model.predict(X_train)
y_pred_test  = model.predict(X_test)

rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
rmse_test  = np.sqrt(mean_squared_error(y_test, y_pred_test))
r2_train   = r2_score(y_train, y_pred_train)
r2_test    = r2_score(y_test, y_pred_test)
mae_test   = float(np.mean(np.abs(y_test - y_pred_test)))

residuals_test = y_test - y_pred_test
dates_train_ts = [pd.Timestamp(d) for d in dates_train]
dates_test_ts  = [pd.Timestamp(d) for d in dates_test]

# KMeans (Notebook B)
df_kmeans = df_long.groupby("สำนักงานคุมประพฤติ").agg(
    Total_Cases=("Cases","sum"),
    Mean_Cases=("Cases","mean"),
    Std_Cases=("Cases","std")
).fillna(0).reset_index()
X_km = df_kmeans[["Total_Cases","Mean_Cases","Std_Cases"]].values
scaler = StandardScaler()
X_km_scaled = scaler.fit_transform(X_km)
km = KMeans(n_clusters=3, random_state=42, n_init=10)
df_kmeans["Cluster"] = km.fit_predict(X_km_scaled).astype(str)

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 4  สร้างแผนภาพทั้งหมด
# ═════════════════════════════════════════════════════════════════════════════
print("สร้างแผนภาพ …")

def make_fig(fig):
    fig.update_layout(font=dict(family=FONT_FAMILY, size=13))
    return fig

# ── A1: Multi-line chart ──────────────────────────────────────────────────
figA1 = make_fig(px.line(
    df_monthly, x="date", y="QTY", color="OIL_NAME_ENG",
    color_discrete_map=COLOR_MAP,
    labels={"date":"Month (CE)","QTY":f"Sales Volume ({UNIT_FUEL})","OIL_NAME_ENG":"Fuel Type"},
    title="A1 — Monthly Diesel Sales Volume by Fuel Type (ADO B7 vs ADO) 2017–2025",
    template=TEMPLATE, markers=False, line_shape="spline"
))
figA1.update_traces(line=dict(width=2.2))
figA1.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified", yaxis=dict(tickformat=",.0f"),
    margin=dict(t=80, b=40)
)

# ── A2: Stacked area chart ────────────────────────────────────────────────
fuel_order = ["ADO","ADO B7"]
df_area = df_monthly[df_monthly["OIL_NAME_ENG"].isin(fuel_order)].copy()
figA2 = make_fig(px.area(
    df_area, x="date", y="share_pct", color="OIL_NAME_ENG",
    color_discrete_map=COLOR_MAP,
    category_orders={"OIL_NAME_ENG": fuel_order},
    groupnorm="percent",
    labels={"date":"Month (CE)","share_pct":"Market Share (%)","OIL_NAME_ENG":"Fuel Type"},
    title="A2 — Monthly Market Share of Diesel Sales by Fuel Type (%) 2017–2025",
    template=TEMPLATE, line_shape="spline"
))
figA2.update_traces(line=dict(width=1.5))
figA2.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    yaxis=dict(ticksuffix="%", range=[0,100]),
    margin=dict(t=80, b=40)
)

# ── A3: Seasonal heatmap ──────────────────────────────────────────────────
figA3 = make_fig(go.Figure(go.Heatmap(
    z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
    colorscale="Blues",
    colorbar=dict(title=dict(text=f"Sales<br>({UNIT_FUEL})", side="right"), tickformat=",.0f"),
    hoverongaps=False,
    hovertemplate="Year (BE): %{y}<br>Month: %{x}<br>Sales: %{z:,.0f} " + UNIT_FUEL + "<extra></extra>",
    xgap=2, ygap=2
)))
figA3.update_layout(
    title="A3 — Seasonal Heatmap: Total Diesel Sales (ADO B7 + ADO) by Month and Year (BE)",
    xaxis=dict(title="Month", categoryorder="array", categoryarray=month_order),
    yaxis=dict(title="Year (BE)", autorange="reversed"),
    template=TEMPLATE, margin=dict(t=80, b=40)
)

# ── B1: Top 10 provinces bar ──────────────────────────────────────────────
df_prov = (
    df_long.groupby("Province")["Cases"].sum()
    .reset_index().sort_values("Cases", ascending=False).head(10)
)
figB1 = make_fig(px.bar(
    df_prov, x="Province", y="Cases", text_auto=True,
    title="B1 — Top 10 Provinces by Total Probation Cases (FY 2565–2566)",
    labels={"Province":"Province","Cases":"Total Cases"},
    template=TEMPLATE
))
figB1.update_layout(margin=dict(t=80, b=40))

# ── B2: Stacked bar by offense type ──────────────────────────────────────
df_g_agg = df_g_long.groupby(["Date","ฐานความผิด"])["Cases"].sum().reset_index()
df_g_agg["Date_Str"] = df_g_agg["Date"].dt.strftime("%Y-%m")
figB2 = make_fig(px.bar(
    df_g_agg, x="Date_Str", y="Cases", color="ฐานความผิด",
    title="B2 — Probation Cases by Offense Type over Time (FY 2565)",
    labels={"Date_Str":"Time (Fiscal Year Oct–Sep)","Cases":"Total Cases","ฐานความผิด":"Offense Type"},
    barmode="stack", template=TEMPLATE
))
figB2.update_layout(
    xaxis_title='Time (Note: Data represents Fiscal Year Oct-Sep)',
    margin=dict(t=100, b=40)
)

# ── B2_1: Top 5 Offenses Line Chart ──────────────────────────────────────
top_5_offenses = df_g_agg.groupby('ฐานความผิด')["Cases"].sum().nlargest(5).index
df_top5 = df_g_agg[df_g_agg['ฐานความผิด'].isin(top_5_offenses)]

figB2_1 = make_fig(px.line(
    df_top5, x="Date_Str", y="Cases", color="ฐานความผิด", markers=True,
    title="B2_1 — Top 5 Probation Cases by Type of Offense over Time (FY 2565)",
    labels={"Date_Str":"Time (Fiscal Year Oct–Sep)","Cases":"Total Cases","ฐานความผิด":"Offense Type"},
    template=TEMPLATE
))
figB2_1.update_layout(
    xaxis_title='Time (Note: Data represents Fiscal Year Oct-Sep)',
    margin=dict(t=100, b=40)
)

# ── B3: Time series total cases ───────────────────────────────────────────
df_time = df_long.groupby("Date")["Cases"].sum().reset_index()
figB3 = make_fig(px.line(
    df_time, x="Date", y="Cases", markers=True,
    title="B3 — Total Probation Cases Trend (FY 2565–2566)",
    labels={"Date":"Time (Fiscal Year Oct–Sep)","Cases":"Total Cases"},
    template=TEMPLATE
))
figB3.update_layout(margin=dict(t=80, b=40))

# ── B4: KMeans scatter ────────────────────────────────────────────────────
figB4 = make_fig(px.scatter(
    df_kmeans, x="Total_Cases", y="Std_Cases", color="Cluster",
    hover_name="สำนักงานคุมประพฤติ",
    title="B4 — KMeans Clustering of Probation Offices (k=3)",
    labels={"Total_Cases":"Total Cases","Std_Cases":"Std Dev of Cases"},
    template=TEMPLATE
))
figB4.update_layout(margin=dict(t=80, b=40))

# ── C1: Actual vs Predicted ───────────────────────────────────────────────
figC1 = go.Figure()
figC1.add_trace(go.Scatter(x=dates_train_ts, y=y_train, mode="lines",
    name="Actual (Train)", line=dict(color="#1f77b4", width=1.8)))
figC1.add_trace(go.Scatter(x=dates_test_ts, y=y_test, mode="lines+markers",
    name="Actual (Test)", line=dict(color="#d62728", width=2.2), marker=dict(size=6)))
figC1.add_trace(go.Scatter(x=dates_train_ts, y=y_pred_train, mode="lines",
    name="Predicted (Train)", line=dict(color="#17becf", width=1.8, dash="dash")))
figC1.add_trace(go.Scatter(x=dates_test_ts, y=y_pred_test, mode="lines+markers",
    name="Predicted (Test)", line=dict(color="#ff7f0e", width=2.2, dash="dash"),
    marker=dict(size=6, symbol="x")))
figC1.add_vrect(
    x0=dates_test_ts[0], x1=dates_test_ts[-1],
    fillcolor="rgba(255,127,14,0.08)", layer="below", line_width=0,
    annotation_text=f"Test Period (n={N_TEST})",
    annotation_position="top left",
    annotation_font=dict(size=11, color="#ff7f0e")
)
figC1.update_layout(
    title=(
        f"C1 — Linear Regression: Actual vs Predicted — Monthly ADO B7 Sales<br>"
        f"<sup>Train RMSE={rmse_train:,.0f} | Test RMSE={rmse_test:,.0f} | "
        f"Train R²={r2_train:.4f} | Test R²={r2_test:.4f} ({UNIT_FUEL})</sup>"
    ),
    xaxis_title="Month (CE)",
    yaxis_title=f"Sales Volume ({UNIT_FUEL})",
    template=TEMPLATE,
    font=dict(family=FONT_FAMILY, size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    yaxis=dict(tickformat=",.0f"),
    margin=dict(t=100, b=40)
)

# ── C2: Residuals bar ─────────────────────────────────────────────────────
date_labels = [pd.Timestamp(d).strftime("%Y-%m") for d in dates_test]
bar_colors  = ["#2ca02c" if r >= 0 else "#d62728" for r in residuals_test]
figC2 = go.Figure(go.Bar(
    x=date_labels, y=residuals_test,
    marker_color=bar_colors,
    hovertemplate="Month: %{x}<br>Residual: %{y:,.0f}<extra></extra>"
))
figC2.add_hline(y=0, line_width=1.5, line_dash="dash", line_color="#555555")
figC2.update_layout(
    title=(
        f"C2 — Residuals on Test Set — Linear Regression (ADO B7 Monthly Sales)<br>"
        f"<sup>Test RMSE={rmse_test:,.0f} | Test R²={r2_test:.4f} | MAE={mae_test:,.0f} ({UNIT_FUEL})</sup>"
    ),
    xaxis_title="Month (CE)",
    yaxis_title=f"Residual: Actual − Predicted ({UNIT_FUEL})",
    template=TEMPLATE,
    font=dict(family=FONT_FAMILY, size=13),
    showlegend=False,
    hovermode="x unified",
    yaxis=dict(tickformat=",.0f"),
    margin=dict(t=100, b=40)
)

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 5  แปลงแผนภาพเป็น HTML div
# ═════════════════════════════════════════════════════════════════════════════
print("แปลงเป็น HTML …")
config = dict(responsive=True)

def fig_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=config)

divs = {
    "A1": fig_div(figA1),
    "A2": fig_div(figA2),
    "A3": fig_div(figA3),
    "B1": fig_div(figB1),
    "B2": fig_div(figB2),
    "B2_1": fig_div(figB2_1),
    "B3": fig_div(figB3),
    "B4": fig_div(figB4),
    "C1": fig_div(figC1),
    "C2": fig_div(figC2),
}

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 6  ข้อมูลเนื้อหาสำหรับการเล่าเรื่อง (Storytelling) และหมายเหตุทางเทคนิค
# ═════════════════════════════════════════════════════════════════════════════

stories = {}

stories["A"] = {
    "context": "สถานการณ์การเปลี่ยนผ่านนโยบายพลังงานของประเทศไทย ส่งผลให้มีการผลักดันน้ำมันดีเซลหมุนเร็ว บี 7 (ADO B7) ขึ้นเป็นน้ำมันดีเซลพื้นฐานของประเทศ เพื่อช่วยเหลือเกษตรกรผู้ปลูกปาล์มน้ำมันและลดมลพิษทางอากาศ",
    "insights": "จากข้อมูลพบว่าส่วนแบ่งการตลาดของ B7 ขยายตัวอย่างต่อเนื่องและทดแทนดีเซลหมุนเร็วธรรมดา (ADO) เกือบทั้งหมด นอกจากนี้ปริมาณการจำหน่ายยังมีความผันผวนตามฤดูกาล (Seasonality) อย่างชัดเจน โดยมักมียอดขายพุ่งสูงในช่วงฤดูเก็บเกี่ยวผลผลิตทางการเกษตรหรือเทศกาลที่มีการเดินทางข้ามจังหวัดหนาแน่น",
    "use_cases": "ข้อมูลนี้สามารถนำไปใช้ในการวางแผนโลจิสติกส์การกระจายน้ำมันของสถานีบริการให้สอดคล้องกับความต้องการตามฤดูกาล รวมถึงเป็นข้อมูลพื้นฐานในการประเมินความคุ้มค่าของนโยบายส่งเสริมพลังงานทดแทนของภาครัฐ"
}

stories["B"] = {
    "context": "กรมคุมประพฤติมีภารกิจหลักในการติดตามและฟื้นฟูพฤติกรรมของผู้กระทำผิด โดยเฉพาะกลุ่มคดีที่ส่งผลกระทบต่อความปลอดภัยสาธารณะ เช่น คดีขับรถขณะเมาสุราและคดียาเสพติด ซึ่งเป็นปัญหาสังคมที่เรื้อรัง",
    "insights": "ข้อมูลชี้ให้เห็นถึงความหนาแน่นของคดีในแต่ละพื้นที่ โดยมีบางจังหวัดที่แบกรับภาระคดีสูงอย่างมีนัยสำคัญ เมื่อพิจารณาแนวโน้มรายเดือนจะพบยอดคดีพุ่งสูงแบบฉับพลัน (Spike) ในช่วงหลังเทศกาลสำคัญ (เช่น ปีใหม่และสงกรานต์) ซึ่งสอดคล้องกับการตั้งด่านตรวจเข้มงวด",
    "use_cases": "สามารถใช้เพื่อจัดสรรทรัพยากรบุคคล (พนักงานคุมประพฤติ) และงบประมาณไปยังพื้นที่เสี่ยงหรือจังหวัดที่มีปริมาณคดีสูงล่วงหน้า (Proactive Resource Allocation) ตลอดจนช่วยในการออกแบบแคมเปญรณรงค์ความปลอดภัยทางถนนให้ตรงจุดและตรงเวลามากยิ่งขึ้น"
}

stories["C"] = {
    "context": "การบริหารจัดการคลังน้ำมันเชื้อเพลิงระดับประเทศต้องการการพยากรณ์อุปสงค์ล่วงหน้าที่มีความแม่นยำ เพื่อรักษาเสถียรภาพและความมั่นคงทางพลังงาน (Energy Security)",
    "insights": "โมเดล Linear Regression ขั้นพื้นฐานที่ใช้ตัวแปรปัจจัยฤดูกาล (Seasonality Dummies) และแนวโน้ม (Trend) สามารถจับทิศทางหลักของความต้องการใช้น้ำมัน ADO B7 ได้ อย่างไรก็ตาม โมเดลเกิดความคลาดเคลื่อนสูงในสภาวะที่เกิดวิกฤตการณ์ที่ไม่คาดฝัน (เช่น การระบาดของ COVID-19) ซึ่งทำให้รูปแบบการใช้น้ำมันเปลี่ยนแปลงแบบกะทันหัน",
    "use_cases": "แสดงให้เห็นถึงศักยภาพของการนำ Machine Learning มาใช้ประกอบการตัดสินใจของภาครัฐ (Data-Driven Policy) อย่างไรก็ดี ชี้ให้เห็นว่าระบบพยากรณ์ที่ใช้ในระดับประเทศจำเป็นต้องพัฒนาให้ซับซ้อนขึ้น โดยการบูรณาการปัจจัยภายนอก (เช่น ราคาน้ำมันโลก, GDP, นโยบายรัฐ) เพื่อรับมือกับวิกฤตเศรษฐกิจรูปแบบใหม่"
}


def note_box(rows):
    """rows = list of (label, value) tuples"""
    trs = "".join(
        f"<tr><td class='nl'>{lab}</td><td class='nv'>{val}</td></tr>"
        for lab, val in rows
    )
    return f"<table class='note-box'>{trs}</table>"

notes = {}

notes["A1"] = note_box([
    ("ชุดข้อมูล", "ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 รายจังหวัด พ.ศ. 2560–2568 — กรมธุรกิจพลังงาน"),
    ("คอลัมน์ที่ใช้", "OIL_NAME_ENG (ประเภทน้ำมัน), QTY (ปริมาณ), YEAR_ID, MONTH_ID"),
    ("การแปลงข้อมูล", "กรองแถวที่มี OIL_NAME_ENG ไม่เป็น NaN; รวม QTY (aggregate sum) ระดับประเทศรายเดือน แยกตามประเภทน้ำมัน"),
    ("หน่วย", "พันลิตรต่อเดือน"),
])

notes["A2"] = note_box([
    ("ชุดข้อมูล", "ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 รายจังหวัด พ.ศ. 2560–2568 — กรมธุรกิจพลังงาน"),
    ("คอลัมน์ที่ใช้", "OIL_NAME_ENG, QTY, YEAR_ID, MONTH_ID"),
    ("การแปลงข้อมูล", "คำนวณ share_pct = QTY รายประเภท ÷ ผลรวม QTY ทุกประเภทรายเดือน × 100; แสดงแบบ Stacked Area 100%"),
    ("หน่วย", "ร้อยละ (%)"),
])

notes["A3"] = note_box([
    ("ชุดข้อมูล", "ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 รายจังหวัด พ.ศ. 2560–2568 — กรมธุรกิจพลังงาน"),
    ("คอลัมน์ที่ใช้", "QTY (ADO B7 + ADO รวม), YEAR_ID (พ.ศ.), MONTH_ID"),
    ("การแปลงข้อมูล", "รวม QTY ทุกประเภทน้ำมันระดับประเทศ จัดเป็นตาราง Pivot (แถว = ปี พ.ศ., คอลัมน์ = เดือน) เพื่อแสดง Heatmap"),
    ("หน่วย", "พันลิตรต่อเดือน (ค่าสีเข้มขึ้น = ปริมาณมากขึ้น); แกน Y แสดงปี พ.ศ. (Buddhist Era)"),
])

notes["B1"] = note_box([
    ("ชุดข้อมูล", "การรับคดีคุมความประพฤติผู้ใหญ่ ปีงบประมาณ 2565–2566 — กรมคุมประพฤติ กระทรวงยุติธรรม"),
    ("คอลัมน์ที่ใช้", "สำนักงานคุมประพฤติ (สกัดชื่อจังหวัด), คอลัมน์เดือน (Melt → Cases)"),
    ("การแปลงข้อมูล", "สกัดชื่อจังหวัดออกจากชื่อสำนักงาน; Melt Wide→Long; รวม Cases ทั้งหมดต่อจังหวัด; เรียงลำดับและคัด 10 อันดับแรก"),
    ("หน่วย", "คดี (จำนวนราย)"),
])

notes["B2"] = note_box([
    ("ชุดข้อมูล", "การรับคดีสอดส่องผู้ใหญ่จำแนกตามฐานความผิด ปีงบประมาณ 2565 — กรมคุมประพฤติ"),
    ("คอลัมน์ที่ใช้", "ฐานความผิด, คอลัมน์เดือน (Melt → Cases, Date)"),
    ("การแปลงข้อมูล", "Melt Wide→Long; แปลงชื่อเดือนภาษาไทย → datetime; รวม Cases รายเดือนต่อฐานความผิด"),
    ("หน่วย", "คดี (จำนวนราย); แกน X แสดงปีงบประมาณ (ต.ค.–ก.ย.)"),
])

notes["B2_1"] = note_box([
    ("ชุดข้อมูล", "การรับคดีสอดส่องผู้ใหญ่จำแนกตามฐานความผิด ปีงบประมาณ 2565 — กรมคุมประพฤติ"),
    ("คอลัมน์ที่ใช้", "เดือน (แปลงเป็นวันที่), ฐานความผิด, Cases"),
    ("การแปลงข้อมูล", "คัดกรองเฉพาะ 5 ฐานความผิดสูงสุด และหาผลรวมรายเดือน เพื่อแสดงเป็นกราฟเส้นแยกประเภทความผิด"),
    ("หน่วย", "คดี (จำนวนราย); แกน X แสดงปีงบประมาณ (ต.ค.–ก.ย.)"),
])

notes["B3"] = note_box([
    ("ชุดข้อมูล", "การรับคดีคุมความประพฤติผู้ใหญ่ ปีงบประมาณ 2565–2566 — กรมคุมประพฤติ"),
    ("คอลัมน์ที่ใช้", "คอลัมน์เดือน (Melt → Cases, Date), สำนักงานคุมประพฤติ"),
    ("การแปลงข้อมูล", "Melt Wide→Long; รวม Cases ทุกสำนักงานรายเดือน; แสดงเป็น Time Series"),
    ("หน่วย", "คดี (จำนวนราย); แกน X แสดงปีงบประมาณ (ต.ค.–ก.ย.)"),
])

notes["B4"] = note_box([
    ("ชุดข้อมูล", "การรับคดีคุมความประพฤติผู้ใหญ่ ปีงบประมาณ 2565–2566 — กรมคุมประพฤติ"),
    ("คอลัมน์ที่ใช้", "สำนักงานคุมประพฤติ, Cases (รวมและสถิติ)"),
    ("การแปลงข้อมูล", "Aggregate: Total_Cases, Mean_Cases, Std_Cases ต่อสำนักงาน; StandardScaler; KMeans k=3"),
    ("หน่วย", "แกน X = จำนวนคดีรวม (คดี), แกน Y = ส่วนเบี่ยงเบนมาตรฐาน (คดี)"),
    ("แบบจำลอง / ฟีเจอร์", "KMeans Clustering (Unsupervised) — ฟีเจอร์: Total_Cases, Mean_Cases, Std_Cases"),
    ("Train/Test Split", "ไม่มี (Unsupervised Learning ใช้ข้อมูลรวม 100%)"),
    ("เมตริก", "Euclidean Distance within-cluster (ไม่มี RMSE/R² — เป็น Clustering ไม่ใช่ Regression)"),
    ("ข้อจำกัด", "ข้อมูล Aggregate ระดับสำนักงาน ครอบคลุมเฉพาะปีงบประมาณ 2565–2566; จำนวน Cluster (k=3) เลือกโดยผู้วิเคราะห์ ไม่ได้หาค่าเหมาะสมด้วย Elbow Method"),
])

notes["C1"] = note_box([
    ("ชุดข้อมูล", "ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 (ADO B7) รายจังหวัด พ.ศ. 2560–2566 — กรมธุรกิจพลังงาน"),
    ("คอลัมน์ที่ใช้", "QTY (ADO B7 เท่านั้น), YEAR_ID, MONTH_ID"),
    ("การแปลงข้อมูล", "กรอง OIL_NAME_ENG = 'ADO B7'; Aggregate QTY ระดับประเทศรายเดือน; สร้าง trend (0…N-1) + One-Hot Month Dummies เดือน 2–12"),
    ("หน่วย", "พันลิตรต่อเดือน"),
    ("ฟีเจอร์ (Features)", "trend (Trend Term เชิงเส้น) + month_2 … month_12 (One-Hot Encoding, Base = มกราคม) รวม 12 ตัวแปร"),
    ("Train/Test Split", f"Time-based split: Train 64 เดือน (ม.ค. 2560 – เม.ย. 2565), Test {N_TEST} เดือน (พ.ค. 2565 – ธ.ค. 2566)"),
    ("RMSE / R²", f"Train RMSE = {rmse_train:,.0f} | Test RMSE = {rmse_test:,.0f} | Train R² = {r2_train:.4f} | Test R² = {r2_test:.4f}"),
    ("ข้อจำกัด", "ข้อมูล Aggregate ระดับประเทศ; ขอบเขตเฉพาะผู้ค้าน้ำมันตามมาตรา 7; โมเดลเชิงเส้นไม่รองรับ Structural Break (เช่น COVID-19); ไม่มีตัวแปรภายนอก (ราคาน้ำมัน, GDP, นโยบายพลังงาน)"),
])

notes["C2"] = note_box([
    ("ชุดข้อมูล", "ปริมาณการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 (ADO B7) — กรมธุรกิจพลังงาน"),
    ("คอลัมน์ที่ใช้", "QTY (ADO B7), MONTH_ID (แปลงเป็น One-Hot Dummies)"),
    ("การแปลงข้อมูล", f"Residual = QTY จริง − QTY พยากรณ์ บนชุดทดสอบ {N_TEST} เดือน; สีเขียว = โมเดลต่ำกว่าจริง, สีแดง = โมเดลสูงกว่าจริง"),
    ("หน่วย", "พันลิตรต่อเดือน"),
    ("ฟีเจอร์ (Features)", "trend + One-Hot Month Dummies เดือน 2–12 (12 ตัวแปร)"),
    ("Train/Test Split", f"Time-based split: Test {N_TEST} เดือน (พ.ค. 2565 – ธ.ค. 2566)"),
    ("RMSE / R²", f"Test RMSE = {rmse_test:,.0f} | Test R² = {r2_test:.4f} | MAE = {mae_test:,.0f}"),
    ("ข้อจำกัด", "ข้อมูล Aggregate ระดับประเทศ; ขอบเขตเฉพาะผู้ค้าน้ำมันตามมาตรา 7; โมเดลเชิงเส้นไม่รองรับ Non-linear Patterns"),
])

# ═════════════════════════════════════════════════════════════════════════════
# ส่วนที่ 7  ประกอบ HTML สมบูรณ์
# ═════════════════════════════════════════════════════════════════════════════
print("ประกอบ HTML …")

import plotly
PLOTLY_JS = plotly.offline.get_plotlyjs()

def section(tag, title_th, note_key):
    return f"""
    <section class="chart-block">
      <h3 class="chart-label">{tag}</h3>
      <p class="chart-title-th">{title_th}</p>
      <div class="chart-wrap">{divs[tag]}</div>
      <div class="note-wrap">{notes[note_key]}</div>
    </section>
"""

def story_html(story_data):
    return f"""
    <div class="story-block">
      <h3>📖 บริบทและข้อค้นพบสำคัญ (Context & Insights)</h3>
      <p><strong>บริบท:</strong> {story_data['context']}</p>
      <p><strong>ข้อค้นพบสำคัญ:</strong> {story_data['insights']}</p>
      <hr style="border:0; border-top:1px solid #e2e8f0; margin: 16px 0;">
      <span class="use-case-badge">💡 Use Cases</span>
      <p>{story_data['use_cases']}</p>
    </div>
    """

html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>แดชบอร์ดบูรณาการ — DGA306 กลุ่ม 6</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet" />
  <script>{PLOTLY_JS}</script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Sarabun', sans-serif;
      font-size: 15px;
      background: #f5f6fa;
      color: #222;
      line-height: 1.6;
    }}
    header {{
      background: #0d3a6e;
      color: #fff;
      padding: 28px 40px 24px;
    }}
    header h1 {{ font-size: 1.55rem; font-weight: 700; margin-bottom: 4px; }}
    header p  {{ font-size: 0.92rem; opacity: 0.82; }}
    .toc {{
      background: #e9eff7;
      border-left: 4px solid #1a6bbf;
      margin: 24px 40px;
      padding: 16px 24px;
      border-radius: 4px;
    }}
    .toc h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 10px; color: #0d3a6e; }}
    .toc ul {{ list-style: none; columns: 2; gap: 24px; }}
    .toc li {{ margin-bottom: 4px; }}
    .toc a  {{ color: #1a6bbf; text-decoration: none; font-size: 0.88rem; }}
    .toc a:hover {{ text-decoration: underline; }}
    .notebook-header {{
      background: #1a6bbf;
      color: #fff;
      margin: 32px 40px 0;
      padding: 10px 20px;
      border-radius: 4px 4px 0 0;
      font-weight: 600;
      font-size: 0.95rem;
    }}
    .story-block {{
      background: #fff;
      margin: 0 40px 24px;
      padding: 24px;
      border-radius: 0 0 6px 6px;
      box-shadow: 0 1px 4px rgba(0,0,0,.10);
      border-left: 5px solid #28a745;
    }}
    .story-block h3 {{ font-size: 1.1rem; color: #1a6bbf; margin-bottom: 12px; }}
    .story-block p {{ font-size: 0.95rem; color: #444; margin-bottom: 8px; line-height: 1.7; }}
    .use-case-badge {{
      display: inline-block;
      background: #e8f5e9;
      color: #2e7d32;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .chart-block {{
      background: #fff;
      margin: 0 40px 24px;
      border-radius: 6px;
      box-shadow: 0 1px 4px rgba(0,0,0,.10);
      overflow: hidden;
    }}
    .chart-label {{
      background: #f0f4fb;
      border-bottom: 1px solid #d8e3f0;
      padding: 8px 20px;
      font-size: 0.80rem;
      font-weight: 600;
      color: #0d3a6e;
      letter-spacing: .04em;
    }}
    .chart-title-th {{
      padding: 6px 20px 0;
      font-size: 0.90rem;
      color: #444;
    }}
    .chart-wrap {{
      padding: 8px 16px 4px;
      min-height: 400px;
    }}
    .note-wrap {{
      padding: 4px 16px 14px;
    }}
    table.note-box {{
      width: 100%;
      border-collapse: collapse;
      background: #f8faff;
      border: 1px solid #d0ddf0;
      border-radius: 4px;
      font-size: 0.82rem;
    }}
    table.note-box td {{ padding: 4px 10px; vertical-align: top; border-bottom: 1px solid #e3ebf8; }}
    table.note-box tr:last-child td {{ border-bottom: none; }}
    td.nl {{
      white-space: nowrap;
      font-weight: 600;
      color: #0d3a6e;
      width: 200px;
      min-width: 160px;
    }}
    td.nv {{ color: #333; }}
    footer {{
      text-align: center;
      padding: 20px;
      font-size: 0.80rem;
      color: #888;
      margin-top: 16px;
    }}
    @media (max-width: 700px) {{
      header, .toc, .notebook-header, .chart-block, .story-block {{ margin-left: 12px; margin-right: 12px; }}
      .toc ul {{ columns: 1; }}
      td.nl {{ width: 120px; min-width: 100px; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>แดชบอร์ดบูรณาการ — ข้อมูลรัฐบาล DGA306 กลุ่ม 6</h1>
  <p>รวมแผนภาพจากโน้ตบุ๊ก A (แนวโน้มเชื้อเพลิง), B (คดีคุมประพฤติ), C (พยากรณ์ด้วย ML) &nbsp;|&nbsp; สร้างด้วย Python Plotly &nbsp;|&nbsp; เปิดได้โดยไม่ต้องรัน Python</p>
</header>

<nav class="toc">
  <h2>สารบัญแผนภาพ</h2>
  <ul>
    <li><a href="#A1">A1 — แนวโน้มปริมาณน้ำมัน (Multi-line)</a></li>
    <li><a href="#A2">A2 — สัดส่วนน้ำมันรายเดือน (Stacked Area)</a></li>
    <li><a href="#A3">A3 — Heatmap ฤดูกาล (Seasonal Heatmap)</a></li>
    <li><a href="#B1">B1 — 10 จังหวัดคดีคุมประพฤติสูงสุด</a></li>
    <li><a href="#B2">B2 — คดีจำแนกตามฐานความผิด (Stacked Bar)</a></li>
    <li><a href="#B2_1">B2_1 — คดีจำแนกตามฐานความผิด 5 อันดับแรก (Line Chart)</a></li>
    <li><a href="#B3">B3 — แนวโน้มคดีรายเดือน (Time Series)</a></li>
    <li><a href="#B4">B4 — จัดกลุ่มสำนักงาน KMeans</a></li>
    <li><a href="#C1">C1 — Actual vs Predicted (Linear Regression)</a></li>
    <li><a href="#C2">C2 — Residuals ชุดทดสอบ</a></li>
  </ul>
</nav>

<!-- ══ โน้ตบุ๊ก A ══════════════════════════════════════════════════════════ -->
<div class="notebook-header">หมวด A — แนวโน้มการจำหน่ายน้ำมันดีเซลหมุนเร็ว บี 7 (กรมธุรกิจพลังงาน)</div>
{story_html(stories["A"])}

<div id="A1">
{section("A1",
  "แผนภาพที่ A1: แนวโน้มปริมาณการจำหน่ายน้ำมันรายเดือน แยกตามประเภท (Multi-line Chart)",
  "A1")}
</div>

<div id="A2">
{section("A2",
  "แผนภาพที่ A2: สัดส่วนปริมาณการจำหน่ายน้ำมันรายเดือน (Stacked Area 100%)",
  "A2")}
</div>

<div id="A3">
{section("A3",
  "แผนภาพที่ A3: รูปแบบตามฤดูกาล — ปริมาณดีเซลรวมต่อเดือนและปี (Seasonal Heatmap)",
  "A3")}
</div>

<!-- ══ โน้ตบุ๊ก B ══════════════════════════════════════════════════════════ -->
<div class="notebook-header">หมวด B — คดีคุมความประพฤติผู้ใหญ่ (กรมคุมประพฤติ กระทรวงยุติธรรม)</div>
{story_html(stories["B"])}

<div id="B1">
{section("B1",
  "แผนภาพที่ B1: 10 จังหวัดที่มีคดีคุมความประพฤติรวมสูงสุด (Bar Chart)",
  "B1")}
</div>

<div id="B2">
{section("B2",
  "แผนภาพที่ B2: สัดส่วนคดีจำแนกตามฐานความผิดตามเวลา (Stacked Bar)",
  "B2")}
</div>

<div id="B2_1">
{section("B2_1",
  "แผนภาพที่ B2_1: แนวโน้มคดีจำแนกตามฐานความผิด 5 อันดับแรก (Line Chart)",
  "B2_1")}
</div>

<div id="B3">
{section("B3",
  "แผนภาพที่ B3: แนวโน้มจำนวนคดีคุมความประพฤติรายเดือน (Time Series)",
  "B3")}
</div>

<div id="B4">
{section("B4",
  "แผนภาพที่ B4: การจัดกลุ่มสำนักงานคุมประพฤติด้วย KMeans Clustering (k=3)",
  "B4")}
</div>

<!-- ══ โน้ตบุ๊ก C ══════════════════════════════════════════════════════════ -->
<div class="notebook-header">หมวด C — การพยากรณ์ปริมาณน้ำมัน ADO B7 ด้วย Linear Regression (กรมธุรกิจพลังงาน)</div>
{story_html(stories["C"])}

<div id="C1">
{section("C1",
  "แผนภาพที่ C1: เปรียบเทียบค่าจริงกับค่าพยากรณ์ (Actual vs Predicted)",
  "C1")}
</div>

<div id="C2">
{section("C2",
  "แผนภาพที่ C2: ค่าความคลาดเคลื่อนบนชุดทดสอบ (Residuals on Test Set)",
  "C2")}
</div>

<footer>
  สร้างโดย Python Plotly &nbsp;|&nbsp; DGA306 Day 4 — กลุ่ม 6 &nbsp;|&nbsp; ข้อมูลจาก gdcatalog.go.th, data.doeb.go.th, gdcatalog.go.th (กรมคุมประพฤติ)
</footer>

</body>
</html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"\nเขียนไฟล์สำเร็จ: {OUT}")
print(f"ขนาดไฟล์: {OUT.stat().st_size / 1_048_576:.2f} MB")
