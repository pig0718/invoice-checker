import streamlit as st
import easyocr
from PIL import Image
import re

# ✅ 自訂檢查條件
EXPECTED_TITLES = [
    "伸太田工業股份有限公司",
    "伸太田工業(股)公司"
]
EXPECTED_TAX_ID = "55854972"

st.set_page_config(page_title="發票檢查工具", layout="centered")
st.title("📄 發票檢查工具（easyocr 版）")
st.markdown("上傳發票圖片，系統將自動檢查抬頭、統編、金額大小寫與稅額是否一致。")

uploaded_file = st.file_uploader("請上傳發票圖片（JPG / PNG）", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="上傳的發票", use_container_width=True)

    with st.spinner("正在擷取文字..."):
        reader = easyocr.Reader(['ch_tra', 'en'])
        results = reader.readtext(image)
        text = "\n".join([res[1] for res in results])

    st.subheader("📋 擷取文字內容")
    st.text(text)

    errors = []

    # 抬頭檢查
    if not any(title in text for title in EXPECTED_TITLES):
        errors.append("❌ 抬頭錯誤：未找到合法公司名稱")

    # 統編檢查
    tax_id_match = re.search(r"\d{8}", text)
    if not tax_id_match or tax_id_match.group() != EXPECTED_TAX_ID:
        errors.append(f"❌ 統一編號錯誤：應為「{EXPECTED_TAX_ID}」")

    # 金額檢查（數字與大寫）
    num_match = re.search(r"NT\$[\d,]+", text)
    chinese_match = re.search(r"[壹貳參肆伍陸柒捌玖拾佰仟萬億]+元", text)
    if not num_match or not chinese_match:
        errors.append("❌ 金額格式錯誤：未找到數字或大寫金額")

    # 稅額檢查
    amount_match = re.search(r"應稅金額[:：]?\s*NT\$([\d,]+)", text)
    tax_match = re.search(r"稅額[:：]?\s*NT\$([\d,]+)", text)
    total_match = re.search(r"總金額[:：]?\s*NT\$([\d,]+)", text)

    if amount_match and tax_match and total_match:
        amount = int(amount_match.group(1).replace(",", ""))
        tax = int(tax_match.group(1).replace(",", ""))
        total = int(total_match.group(1).replace(",", ""))

        expected_tax = round(amount * 0.05)
        if tax != expected_tax:
            errors.append(f"❌ 稅額錯誤：應為 NT${expected_tax}，實際為 NT${tax}")

        if total != amount + tax:
            errors.append(f"❌ 總金額錯誤：應為 NT${amount + tax}，實際為 NT${total}")
    else:
        errors.append("❌ 未找到完整稅額資訊（應稅金額 / 稅額 / 總金額）")

    st.subheader("✅ 檢查結果")
    if errors:
        for err in errors:
            st.error(err)
    else:
        st.success("全部正確 ✅")
