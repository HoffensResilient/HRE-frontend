# Visualization using plotly
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------- CONFIG ----------
# DB_PATH = "database/sensor_data_mock.csv"
# TABLE_NAME = "sensor_data_mock"  # Replace with actual table name
# DB_PATH = "database/ideal_rocket_launch.csv"
# TABLE_NAME = "ideal_rocket_launch"  # Replace with actual table name

DATA_SOURCES = {
    "Ideal Launch": "database/ideal_rocket_launch.csv",
    "Sensor Data": "database/sensor_data_mock.csv"
    
}
# ----------------------------


st.set_page_config(page_title="Rocket Telemetry", layout="wide")
st.title("🚀 Rocket Telemetry Dashboard")

# Sidebar Dataset selector and File uploader
st.sidebar.header("Flight Data Filters")

# 1. Select existing dataset
selected_dataset = st.sidebar.selectbox("Select existing dataset", options=list(DATA_SOURCES.keys()))

# 2. Upload your own data
uploaded_file = st.sidebar.file_uploader("Or upload your CSV data", type=["csv"])

@st.cache_data
def load_data(db_path):
    return pd.read_csv(db_path)

# Load data conditionally
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    dataset_name = "Uploaded Data"
else:
    DB_PATH = DATA_SOURCES[selected_dataset]
    df = load_data(DB_PATH)
    dataset_name = selected_dataset

# Show dataset name right under the title
st.markdown(f"### Currently loaded dataset: **{dataset_name}**")

# Sidebar info
st.sidebar.write(f"Dataset: {dataset_name}")
st.sidebar.write(f"Total Records: {len(df)}")

if df.empty:
    st.warning("No data found in dataset.")
    st.stop()



# Process time column
# Convert date + time for sorting/plotting
# Fix the malformed time format
df['time'] = df['time'].str.replace(r':(?=\d{3}$)', '.', regex=True)

# Merge and parse datetime
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')

# Optional: show parsing issues
if df['datetime'].isnull().any():
    st.warning("Some datetime values could not be parsed.")
    st.dataframe(df[df['datetime'].isnull()])




# Rocket Simulation
# --- 3D Rocket Trajectory with time slider animation --- #

# Create ground surface
ground_plane = go.Surface(
    z=[[df.gps_alt.min() - 10] * 2] * 2,
    x=[[df.lon.min(), df.lon.max()], [df.lon.min(), df.lon.max()]],
    y=[[df.lat.min(), df.lat.min()], [df.lat.max(), df.lat.max()]],
    showscale=False,
    opacity=0.3,
    colorscale=[[0, 'green'], [1, 'darkgreen']],
    name='Ground'
)

# Animation frames
frames = [
    go.Frame(
        data=[
            ground_plane,
            go.Scatter3d(
                x=df.lon[:k],
                y=df.lat[:k],
                z=df.gps_alt[:k],
                mode='lines',
                line=dict(color='blue', width=4),
                name='Rocket Path'
            ),
            go.Scatter3d(
                x=[df.lon[k - 1]],
                y=[df.lat[k - 1]],
                z=[df.gps_alt[k - 1]],
                # mode='text',
                mode='text+markers',
                marker=dict(size=4, color='red', symbol='circle'),
                text=['🚀'],
                textposition='middle center',
                # textposition='top center',
                name='🚀 Rocket'
            )
        ],
        name=str(k)
    )
    for k in range(10, len(df), 5)
]

# Slider steps
slider_steps = [
    dict(
        method="animate",
        args=[[str(k)], {
            "frame": {"duration": 0, "redraw": True},
            "mode": "immediate"
        }],
        label=f"{k * 50} ms"
    )
    for k in range(10, len(df), 5)
]

# Initial figure data (with rocket visible)
fig = go.Figure(
    data=[
        ground_plane,
        go.Scatter3d(
            x=df.lon[:10],
            y=df.lat[:10],
            z=df.gps_alt[:10],
            mode='lines',
            line=dict(color='blue', width=4),
            name='Rocket Path'
        ),
        go.Scatter3d(
            x=[df.lon[9]],
            y=[df.lat[9]],
            z=[df.gps_alt[9]],
            # mode='text',
            mode='text+markers',
            marker=dict(size=4, color='red', symbol='circle'),
            text=['🚀'],
            textposition='middle center',
            # textposition='top center',
            name='🚀 Rocket'
        )
    ],
    layout=go.Layout(
        title="🛰️ Live Rocket Trajectory with Time Slider",
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Altitude (m)',
            camera=dict(
                up=dict(x=0, y=0, z=1),
                eye=dict(x=3, y=0.3, z=0.3)
            )
        ),
        dragmode='turntable',
        updatemenus=[dict(
            type="buttons",
            showactive=True,
            x=0.1, y=1.1,
            direction="left",
            buttons=[
                dict(
                    label="▶️ Play",
                    method="animate",
                    args=[None, {
                        "frame": {"duration": 50, "redraw": True},
                        "fromcurrent": True,
                        "mode": "immediate"
                    }]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate"
                    }]
                )
            ]
        )],
        sliders=[{
            "active": 0,
            "pad": {"t": 50},
            "steps": slider_steps,
            "x": 0.05,
            "len": 0.9
        }]
    ),
    frames=frames
)

# Render in Streamlit
st.plotly_chart(fig, use_container_width=True)


# --- Helper function for 2D plots with time slider animation ---
def create_time_slider_frames(df, y_cols, y_label):
    frames = []
    slider_steps = []
    n_points = len(df)
    step_size = max(1, n_points // 30)  # max 30 frames

    for k in range(step_size, n_points + 1, step_size):
        frame_data = []
        for col in y_cols:
            frame_data.append(go.Scatter(x=df['datetime'][:k], y=df[col][:k], mode='lines', name=col))
        
        frames.append(go.Frame(data=frame_data, name=str(k)))

        slider_steps.append(dict(
            method="animate",
            args=[[str(k)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
            label=str(df['datetime'].iloc[k-1].strftime("%H:%M:%S"))
        ))

    initial_data = []
    for col in y_cols:
        initial_data.append(go.Scatter(x=df['datetime'][:step_size], y=df[col][:step_size], mode='lines', name=col))

    layout = go.Layout(
        title=f"{y_label} over Time with Time Slider",
        xaxis_title="Time",
        yaxis_title=y_label,
        updatemenus=[dict(
            type="buttons",
            showactive=True,
            y=1.15,
            x=0,
            xanchor="left",
            yanchor="top",
            buttons=[
                dict(label="▶️ Play", method="animate", args=[None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True, "mode": "immediate"}]),
                dict(label="⏸ Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]),
            ]
        )],
        sliders=[dict(
            active=0,
            steps=slider_steps,
            x=0,
            len=1,
            xanchor="left",
            y=-0.1,
            yanchor="top",
            pad={"b": 10},
            currentvalue={"prefix": "Time: ", "visible": True, "xanchor": "right"}
        )]
    )

    fig = go.Figure(data=initial_data, layout=layout, frames=frames)
    return fig

st.subheader("📈 Live Graphs Streaming data")

# --- Altitude over Time ---
st.subheader("📈 Altitude over Time")
fig2 = create_time_slider_frames(df, ['alt'], 'Altitude')
st.plotly_chart(fig2, use_container_width=True)

# --- Acceleration over Time ---
st.subheader("🎯 Accelerometer Data")
fig3 = create_time_slider_frames(df, ['acc_x', 'acc_y', 'acc_z'], 'Acceleration')
st.plotly_chart(fig3, use_container_width=True)

# --- Euler Angles over Time ---
st.subheader("🛰️ Orientation (Euler Angles)")
fig4 = create_time_slider_frames(df, ['eu_x', 'eu_y', 'eu_z'], 'Orientation')
st.plotly_chart(fig4, use_container_width=True)

# --- Valve State Timeline ---
st.subheader("💡 Valve State Over Time")
fig5 = create_time_slider_frames(df, ['valve_state'], 'Valve State')
st.plotly_chart(fig5, use_container_width=True)

st.subheader("📈 Static Graphs all data")

# Altitude vs Time
st.subheader("📈 Altitude over Time")
fig2 = px.line(df, x='datetime', y='alt', title="Altitude vs Time")
st.plotly_chart(fig2, use_container_width=True)

# Acceleration over Time
st.subheader("🎯 Accelerometer Data")
fig3 = px.line(df, x='datetime', y=['acc_x', 'acc_y', 'acc_z'], title="Acceleration over Time")
st.plotly_chart(fig3, use_container_width=True)

# Euler Angles over Time
st.subheader("🛰️ Orientation (Euler Angles)")
fig4 = px.line(df, x='datetime', y=['eu_x', 'eu_y', 'eu_z'], title="Orientation over Time")
st.plotly_chart(fig4, use_container_width=True)

# Valve State Timeline
st.subheader("💡 Valve State Over Time")
fig5 = px.scatter(df, x='datetime', y='valve_state', title="Valve State")
st.plotly_chart(fig5, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit and Plotly, HAHAHAHA")

