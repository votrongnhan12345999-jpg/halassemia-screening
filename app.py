import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("Công cụ Sàng lọc Thalassemia & Phân tích Huyết học")
st.markdown("Đề tài NCKH Tin sinh học | Khoa Công nghệ Sinh học - ĐH Đồng Tháp")

# 1. Khu vực tải file lên
uploaded_file = st.file_uploader("Tải lên tập dữ liệu của bạn (CSV hoặc Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Đọc file CSV hoặc Excel
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

   # Tự động làm sạch tên cột (xóa khoảng trắng thừa, chuyển thành chữ hoa)
    df.columns = [str(col).strip().upper() for col in df.columns]

    # Tìm chính xác tên cột MCV và RBC hoặc các biến thể tương đương
    mcv_col = next((col for col in df.columns if 'MCV' in col), None)
    rbc_col = next((col for col in df.columns if 'RBC' in col), None)

    if mcv_col and rbc_col:
        # Tính chỉ số Mentzer Index dựa trên tên cột tìm được
        df['MENTZER_INDEX'] = df[mcv_col] / df[rbc_col]
        
        def classify_screening(row):
            if pd.isna(row['MENTZER_INDEX']):
                return 'Chưa đủ dữ liệu'
            elif row['MENTZER_INDEX'] < 13:
                return '🔴 Nghi ngờ Thalassemia (Hồng cầu nhỏ)'
            else:
                return '🟡 Nghi ngờ Thiếu máu thiếu sắt'

        df['GỢI Ý SÀNG LỌC'] = df.apply(classify_screening, axis=1)

    # 2. Hiển thị bảng kết quả sàng lọc
    st.subheader("📋 Kết quả Sàng lọc Tự động & Mentzer Index")
    st.dataframe(df)
    
    # Thống kê cảnh báo số ca nghi ngờ
    if 'MENTZER_INDEX' in df.columns:
        num_thal = len(df[df['MENTZER_INDEX'] < 13])
        st.warning(f"⚠️ Phát hiện **{num_thal}** trường hợp có chỉ số Mentzer < 13 cần lưu ý sàng lọc Thalassemia chuyên sâu!")
    else:
        st.error(f"Hệ thống tìm thấy cột MCV là '{mcv_col}' nhưng chưa tìm thấy cột RBC phù hợp trong file của bạn!")

  # 3. Trực quan hóa Biểu đồ hộp (Boxplot)
    st.subheader("📊 Trực quan hóa Biểu đồ Hộp (Boxplot) Huyết học")
    
    if 'MCV' in df.columns:
        fig, ax = plt.subplots(figsize=(10, 5))
        if 'MUTATION_GROUP' in df.columns:
            sns.boxplot(x='MUTATION_GROUP', y='MCV', data=df, palette='Set2', ax=ax)
            # Giữ chữ nằm thẳng ngang, canh giữa tuyệt đối với từng cột hộp
            plt.xticks(rotation=0, ha='center', fontsize=10)
        else:
            sns.boxplot(y=df['MCV'], color='skyblue', ax=ax)
            
        ax.set_title("Phân bố thể tích hồng cầu trung bình (MCV) theo nhóm", fontsize=14, pad=15)
        ax.set_xlabel("Nhóm đột biến / Phân loại", fontsize=11, labelpad=10)
        ax.set_ylabel("MCV (fl)", fontsize=11)
        
        plt.tight_layout()
        st.pyplot(fig)