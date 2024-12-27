import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import pickle  # Import pickle for loading the model

# Load the model with error handling
def load_model(model_path):
    try:
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        return model
    except FileNotFoundError:
        st.error("Model file not found. Please check the path.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the model: {e}")
        return None

# Function to predict rainfall condition
def Prediksi_Curah_Hujan(model, Temperature, Humidity, Rain_Sensor, LDR_Sensor):
    fitur = pd.DataFrame({
        'Temperature': [Temperature],
        'Humidity': [Humidity],
        'Rain_Sensor': [Rain_Sensor],
        'LDR_Sensor': [LDR_Sensor]
    })

    try:
        prediksi = model.predict(fitur)
        if prediksi[0] == 0:
            return "Gelap"
        elif prediksi[0] == 1:
            return "Hujan"
        elif prediksi[0] == 2:
            return "Mendung"
        elif prediksi[0] == 3:
            return "Cerah"
        else:
            return "Hasil prediksi tidak dikenali."
    except Exception as e:
        return f"Kesalahan pada prediksi: {e}"

# Function to create styled markdown
def create_styled_markdown(label, value):
    return f"""
    <div class="parameter-label">{label}</div>
    <div class="current-value">{value}</div>
    """

# Set up basic configuration
st.set_page_config(
    page_title="Sistem Prediksi Cuaca",
    page_icon="https://psikologi.unj.ac.id/wp-content/uploads/2020/10/Logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header Title
st.title("Sistem Prediksi Cuaca")

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("sistem-prediksi-cuaca-cfe9c4990f25.json", scope)
client = gspread.authorize(creds)

# Read the first 100 rows from the worksheet
@st.cache_data(ttl=16000)
def load_data(sheet):
    sheet = client.open("Monitoring Data prediksi Hujan").worksheet(sheet)
    data = sheet.get_all_records()
    return data

# Load data
data_list_1 = load_data("Monitoring data")
df = pd.DataFrame(data_list_1)

# Convert 'Timestamp' column to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Load the model
model = load_model('models/nby_model.pkl')  # Update with your model path
if model is None:
    st.stop()  # Stop the app if the model cannot be loaded

# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.selectbox("Select an option", ["Home", "Current Data", "Select Date"])

if option == "Home":
    st.write("## Selamat Datang di Sistem Prediksi Cuaca")
    st.write("""
        Sistem ini dirancang untuk memprediksi kondisi cuaca berdasarkan data yang dikumpulkan dari sensor.
        Anda dapat melihat data cuaca saat ini, memprediksi kondisi cuaca berdasarkan data terbaru, 
        dan juga melihat data historis berdasarkan tanggal yang dipilih.
        
        ### Fitur Utama:
        - **Prediksi Cuaca**: Menggunakan model machine learning untuk memprediksi kondisi cuaca.
        - **Visualisasi Data**: Menampilkan grafik untuk memudahkan pemahaman data cuaca.
        - **Data Historis**: Memungkinkan pengguna untuk melihat data cuaca pada tanggal tertentu.
        
        Terima kasih telah menggunakan sistem ini!
    """)

elif option == "Current Data":
    # Display current weather data
    current_values = data_list_1[-1]  # Get the latest data
    st.write("----")
    st.write("### Kondisi Cuaca Saat Ini")
    columns = st.columns(5, gap='large')

    columns[0].markdown(create_styled_markdown("Suhu (°C)", current_values['Temperature (°C)']), unsafe_allow_html =True)
    columns[1].markdown(create_styled_markdown("Kelembaban (%)", current_values['Humidity (%)']), unsafe_allow_html=True)
    columns[2].markdown(create_styled_markdown("Rain Sensor", current_values['Rain Sensor']), unsafe_allow_html=True)
    columns[3].markdown(create_styled_markdown("LDR Sensor", current_values['LDR Sensor']), unsafe_allow_html=True)

    # Prepare input features for prediction
    Temperature = current_values['Temperature (°C)']
    Humidity = current_values['Humidity (%)']
    Rain_Sensor = current_values['Rain Sensor']
    LDR_Sensor = current_values['LDR Sensor']

    # Predict the weather condition using the integrated function
    predicted_condition = Prediksi_Curah_Hujan(model, Temperature, Humidity, Rain_Sensor, LDR_Sensor)
    columns[4].markdown(create_styled_markdown("Prediksi Kondisi", predicted_condition), unsafe_allow_html=True)

    # Visualize current data
    timestamps = [row['Timestamp'] for row in data_list_1]
    temperatures = [row['Temperature (°C)'] for row in data_list_1]
    humidity = [row['Humidity (%)'] for row in data_list_1]
    rain_sensor = [row['Rain Sensor'] for row in data_list_1]
    ldr_sensor = [row['LDR Sensor'] for row in data_list_1]

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Temperature (°C)', 'Humidity (%)',
            'Rain Sensor', 'LDR Sensor',
            None
        ),
        shared_xaxes=False
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=temperatures, name='Suhu (°C)', mode='lines', line=dict(color='red')),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=humidity, name='Kelembaban (%)', mode='lines', line=dict(color='green')),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=rain_sensor, name='Rain Sensor', mode='lines', line=dict(color='blue')),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=ldr_sensor, name='LDR Sensor', mode='lines', line=dict(color='orange')),
        row=2, col=2
    )

    fig.update_layout(
        height=1600,
        title_text="Parameter Monitoring Cuaca",
        showlegend=False,
        xaxis_title='Waktu',
        xaxis2_title='Waktu',
        xaxis3_title='Waktu',
        xaxis4_title='Waktu',
    )

    st.plotly_chart(fig)

    

elif option == "Select Date":
    # Date selection for historical data
    selected_date = st.date_input("Select a date", datetime.today())
    filtered_data = df[df['Timestamp'].dt.date == selected_date]

    if not filtered_data.empty:
        st.write("### Data for", selected_date)

        # Get the most recent data for the selected date
        latest_data = filtered_data.iloc[-1]    

        # Prepare input features for prediction
        Temperature = latest_data['Temperature (°C)']
        Humidity = latest_data['Humidity (%)']
        Rain_Sensor = latest_data['Rain Sensor']
        LDR_Sensor = latest_data['LDR Sensor']

        # Predict the weather condition using the integrated function
        predicted_condition = Prediksi_Curah_Hujan(model, Temperature, Humidity, Rain_Sensor, LDR_Sensor)
        st.markdown(create_styled_markdown("Prediksi Kondisi", predicted_condition), unsafe_allow_html=True)

        # Visualize historical data
        timestamps = filtered_data['Timestamp'].tolist()
        temperatures = filtered_data['Temperature (°C)'].tolist()
        humidity = filtered_data['Humidity (%)'].tolist()
        rain_sensor = filtered_data['Rain Sensor'].tolist()
        ldr_sensor = filtered_data['LDR Sensor'].tolist()

        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Temperature (°C)', 'Humidity (%)',
                'Rain Sensor', 'LDR Sensor',
                None
            ),
            shared_xaxes=False
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=temperatures, name='Suhu (°C)', mode='lines', line=dict(color='red')),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=humidity, name='Kelembaban (%)', mode='lines', line=dict(color='green')),
            row=1, col=2
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=rain_sensor, name='Rain Sensor', mode='lines', line=dict(color='blue')),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=ldr_sensor, name='LDR Sensor', mode='lines', line=dict(color='orange')),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            title_text="Parameter Monitoring Cuaca for " + str(selected_date),
            showlegend=False,
            xaxis_title='Waktu',
            xaxis2_title='Waktu',
            xaxis3_title='Waktu',
            xaxis4_title='Waktu',
        )

        st.plotly_chart(fig)

        # Display the filtered data for the selected date
        st.write("### Data untuk Tanggal", selected_date)
        st.dataframe(filtered_data)  # Show the filtered data for the selected date
    else:
        st.write("No data available for the selected date.")