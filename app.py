import os
import av
import threading
import streamlit as st
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer
 
from audio_handling import AudioFrameHandler
from drowsy_detection import VideoFrameHandler
 
# Define the audio file to use.
alarm_file_path = os.path.join("audio", "wake_up.wav")
 
# Streamlit Components
st.set_page_config(
    page_title="Drowsiness Detection | LearnOpenCV",
    page_icon="https://learnopencv.com/wp-content/uploads/2017/12/favicon.png",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "### Visit www.learnopencv.com for more exciting tutorials!!!",
    },
)
 
st.title("Drowsiness Detection!")
 
col1, col2 = st.columns(spec=[1, 1])
 
with col1:
    # Lowest valid value of Eye Aspect Ratio. Ideal values [0.15, 0.2].
    EAR_THRESH = st.slider("Eye Aspect Ratio threshold:", 0.0, 0.4, 0.18, 0.01)
 
with col2:
    # The amount of time (in seconds) to wait before sounding the alarm.
    WAIT_TIME = st.slider("Seconds to wait before sounding alarm:", 0.0, 5.0, 1.0, 0.25)
 
thresholds = {
    "EAR_THRESH": EAR_THRESH,
    "WAIT_TIME": WAIT_TIME,
}
 
# For streamlit-webrtc
video_handler = VideoFrameHandler()
audio_handler = AudioFrameHandler(sound_file_path=alarm_file_path)
 
# For thread-safe access & to prevent race-condition.
lock = threading.Lock()  
 
shared_state = {"play_alarm": False}
 
def video_frame_callback(frame: av.VideoFrame):
    frame = frame.to_ndarray(format="bgr24")  # Decode and convert frame to RGB
 
    frame, play_alarm = video_handler.process(frame, thresholds)  # Process frame
    with lock:
        shared_state["play_alarm"] = play_alarm  # Update shared state
     
    # Encode and return BGR frame
    return av.VideoFrame.from_ndarray(frame, format="bgr24")  
 
def audio_frame_callback(frame: av.AudioFrame):
    with lock:  # access the current “play_alarm” state
        play_alarm = shared_state["play_alarm"]
 
    new_frame: av.AudioFrame = audio_handler.process(frame,
                                                     play_sound=play_alarm)
    return new_frame
 
ctx = webrtc_streamer(
    key="driver-drowsiness-detection",
    video_frame_callback=video_frame_callback,
    audio_frame_callback=audio_frame_callback,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": {"width": True, "audio": True}},
    video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=False),
)