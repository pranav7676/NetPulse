import streamlit as st
import pandas as pd
import plotly.express as px
import psutil
import time
import threading
from scapy.all import sniff, IP
from datetime import datetime
import os
import traceback


packets_data = []
capture_running = False
capture_thread = None


def packet_callback(packet):
    try:
        if IP in packet:
            packets_data.append({
                'timestamp': datetime.now(),
                'src': packet[IP].src,
                'dst': packet[IP].dst,
                'proto': packet[IP].proto,
                'len': len(packet)
            })
    except Exception as e:
        print(f"Error processing packet: {str(e)}")

def start_sniffing():
    global capture_running
    try:
        while capture_running:
            try:
                sniff(prn=packet_callback, store=False, count=10)
                time.sleep(1)
            except Exception as e:
                print(f"Error in sniffing: {str(e)}")
                time.sleep(5)  # Wait before retrying
    except KeyboardInterrupt:
        print("Sniffing stopped by user")
    except Exception as e:
        print(f"Fatal error in sniffing: {str(e)}")
        capture_running = False


st.set_page_config(
    page_title="NetPulse – Network Dashboard",
    layout="wide",
    page_icon="🌐"
)


def show_loading_animation():
    loading_placeholder = st.empty()
    
    loading_placeholder.markdown("""
        <style>
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes oldScreen {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
        @keyframes progress {
            0% { width: 0%; }
            100% { width: 100%; }
        }
        .loading-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(0,25,25,0.9) 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .scanline {
            position: absolute;
            width: 100%;
            height: 4px;
            background: linear-gradient(to right,
                transparent 0%,
                rgba(0, 255, 255, 0.2) 10%,
                rgba(0, 255, 255, 0.6) 50%,
                rgba(0, 255, 255, 0.2) 90%,
                transparent 100%);
            animation: scanline 4s linear infinite;
        }
        .content-wrapper {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
        }
        .loading-circle {
            position: relative;
            width: 80px;
            height: 80px;
        }
        .rotating-circle {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: 3px solid rgba(0, 255, 255, 0.5);
            border-top-color: #00FFFF;
            border-radius: 50%;
            animation: rotate 1.5s linear infinite;
        }
        .inner-circle {
            position: absolute;
            top: 15px;
            left: 15px;
            right: 15px;
            bottom: 15px;
            border: 2px solid #00FFFF;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .progress-container {
            width: 200px;
            height: 2px;
            background: rgba(0, 255, 255, 0.1);
            overflow: hidden;
            border-radius: 2px;
        }
        .progress-bar {
            width: 0%;
            height: 100%;
            background: #00FFFF;
            animation: progress 3s ease-in-out;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        .loading-text {
            color: #00FFFF;
            font-family: monospace;
            font-size: 18px;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            letter-spacing: 2px;
        }
        </style>
        <div class="loading-container">
            <div class="scanline"></div>
            <div class="content-wrapper">
                <div class="loading-circle">
                    <div class="rotating-circle"></div>
                    <div class="inner-circle"></div>
                </div>
                <div class="loading-text">INITIALIZING NETPULSE</div>
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    return loading_placeholder


loading_screen = show_loading_animation()


time.sleep(3)


loading_screen.empty()


st.markdown("""
<style>
/* Make Streamlit elements transparent */
.css-18e3th9, .css-1d391kg, .css-1y4p8pa, .css-1r6slb0, [data-testid="stVerticalBlock"] { 
    background: transparent !important; 
}
.css-1y4p8pa {
    padding: 2rem 1rem;
}
/* Fullscreen canvas for particles */
#bgCanvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    pointer-events: none;
    opacity: 0.8;
}
/* Ensure content is readable */
.stMarkdown, .stButton, .stDataFrame {
    position: relative;
    z-index: 1;
}
</style>

<canvas id="bgCanvas"></canvas>
<script>
    // Load Three.js from multiple CDNs with fallback
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = () => reject(new Error(`Failed to load ${src}`));
            document.head.appendChild(script);
        });
    }

    // Try primary CDN, fallback to alternatives
    loadScript('https://unpkg.com/three@0.157.0/build/three.min.js')
        .catch(() => loadScript('https://cdn.skypack.dev/three'))
        .catch(() => loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'))
        .then(() => {
            try {
                // Initialize Three.js scene
                const canvas = document.getElementById('bgCanvas');
                if (!canvas) throw new Error('Canvas element not found');

                const scene = new THREE.Scene();
                scene.fog = new THREE.Fog(0x000000, 50, 150);
                
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                camera.position.z = 30;
                
                const renderer = new THREE.WebGLRenderer({
                    canvas: canvas,
                    alpha: true,
                    antialias: true,
                    powerPreference: "high-performance"
                });
                
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.setClearColor(0x000000, 0);

                // PARTICLES AND CONNECTIONS
                const particleCount = 150; // Reduced for better performance with lines
                const positions = new Float32Array(particleCount*3);
                const velocities = new Float32Array(particleCount*3);
                for(let i=0; i<particleCount*3; i++){
                    positions[i] = (Math.random()-0.5)*50;
                    velocities[i] = 0.01 + Math.random()*0.02;
                }

                // Create particles with enhanced visibility
                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.BufferAttribute(positions,3));
                const material = new THREE.PointsMaterial({
                    color: 0x00ffff,
                    size: 0.4,
                    opacity: 0.9,
                    transparent: true,
                    sizeAttenuation: true
                });
                const particles = new THREE.Points(geometry, material);

                // Create lines for connections with improved visibility
                const linesMaterial = new THREE.LineBasicMaterial({
                    color: 0x00ffff,
                    opacity: 0.4,
                    transparent: true,
                    blending: THREE.AdditiveBlending
                });
                const linesGeometry = new THREE.BufferGeometry();
                const connections = new THREE.LineSegments(linesGeometry, linesMaterial);

                scene.add(particles);
                scene.add(connections);

                camera.position.z = 30;

                // Track mouse
                let mouse = {x:0, y:0};
                document.addEventListener('mousemove', (e) => {
                    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
                    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
                });

                // Animate particles and connections
                function animate() {
                    requestAnimationFrame(animate);
                    const positions = geometry.attributes.position.array;
                    
                    // Update particle positions
                    for(let i=0; i<particleCount*3; i+=3){
                        // particles move slowly based on velocity
                        positions[i+0] += velocities[i+0] * 0.5 * (mouse.x || 0.1);
                        positions[i+1] += velocities[i+1] * 0.5 * (mouse.y || 0.1);
                        // wrap around
                        if(positions[i+0] > 25) positions[i+0] = -25;
                        if(positions[i+0] < -25) positions[i+0] = 25;
                        if(positions[i+1] > 25) positions[i+1] = -25;
                        if(positions[i+1] < -25) positions[i+1] = 25;
                    }
                    
                    // Create connections between nearby particles
                    const linePositions = [];
                    const maxDistance = 10; // Maximum distance for connection
                    
                    for(let i=0; i<particleCount; i++) {
                        const x1 = positions[i*3];
                        const y1 = positions[i*3+1];
                        const z1 = positions[i*3+2];
                        
                        for(let j=i+1; j<particleCount; j++) {
                            const x2 = positions[j*3];
                            const y2 = positions[j*3+1];
                            const z2 = positions[j*3+2];
                            
                            const dx = x2-x1;
                            const dy = y2-y1;
                            const dz = z2-z1;
                            const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                            
                            if(dist < maxDistance) {
                                // Add line vertices
                                linePositions.push(x1,y1,z1);
                                linePositions.push(x2,y2,z2);
                            }
                        }
                    }
                    
                    // Update geometries
                    linesGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
                    geometry.attributes.position.needsUpdate = true;
                    
                    // Rotate scene slightly
                    particles.rotation.y += 0.001;
                    connections.rotation.y += 0.001;
                    
                    renderer.render(scene, camera);
                }
                animate();

                // Responsive
                window.addEventListener('resize', () => {
                    camera.aspect = window.innerWidth/window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                });
            } catch (error) {
                console.error('Three.js initialization error:', error);
            }
        })
        .catch(error => {
            console.error('Failed to load Three.js library:', error);
        });
</script>
""", unsafe_allow_html=True)

# ----------------------------
# CUSTOM CSS
# ----------------------------
st.markdown("""
<style>
.stImage {
    display: block !important;
    margin: 0 auto !important;
    filter: drop-shadow(0 0 10px rgba(0,255,255,0.5));
    animation: logoGlow 3s ease-in-out infinite;
}
.stImage img {
    max-width: 100% !important;
    height: auto !important;
}
.big-title { 
    font-size: 36px; 
    font-weight: 700; 
    color: #00FFFF; 
    text-shadow: 0px 0px 10px #00FFFF; 
    text-align: center;
    margin-top: 1rem;
}
.metric-box { 
    background: rgba(0, 255, 255, 0.1); 
    border: 1px solid #00FFFF; 
    padding: 20px; 
    border-radius: 15px; 
    text-align: center; 
}
.subtitle { 
    text-align: center; 
    display: block; 
}
.glow { animation: glow 2.5s ease-in-out infinite; }
.pulse { animation: pulse 2s ease-in-out infinite; }
.fade-in { animation: fadeIn 1s ease-in-out both; }

@keyframes logoGlow {
    0% { filter: drop-shadow(0 0 10px rgba(0,255,255,0.5)); }
    50% { filter: drop-shadow(0 0 20px rgba(0,255,255,0.8)); }
    100% { filter: drop-shadow(0 0 10px rgba(0,255,255,0.5)); }
}

@keyframes progress {
    0% { width: 0%; opacity: 1; }
    50% { width: 100%; opacity: 0.5; }
    100% { width: 0%; opacity: 1; }
}

/* Center button container */
.stButton {
    display: flex;
    justify-content: center;
    margin: 1rem 0;
}

/* Button hover animation */
.stButton > button {
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    background: rgba(0, 255, 255, 0.1) !important;
    border: 1px solid #00FFFF !important;
    color: #00FFFF !important;
    font-weight: bold !important;
    padding: 0.6em 1.2em !important;
    border-radius: 8px !important;
}

.stButton > button:hover {
    background: rgba(0, 255, 255, 0.2) !important;
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
    transform: translateY(-2px);
}

.stButton > button:hover::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 30px;
    height: 30px;
    border: 2px solid transparent;
    border-top-color: #00FFFF;
    border-radius: 50%;
    animation: button-loading-spinner 1s ease infinite;
}

@keyframes button-loading-spinner {
    from {
        transform: translate(-50%, -50%) rotate(0turn);
    }
    to {
        transform: translate(-50%, -50%) rotate(1turn);
    }
}

@keyframes glow { 0% { text-shadow: 0 0 6px rgba(0,255,255,0.8); } 50% { text-shadow: 0 0 18px rgba(0,255,255,1); } 100% { text-shadow: 0 0 6px rgba(0,255,255,0.8); } }
@keyframes pulse { 0% { transform: scale(1); box-shadow: 0 0 0 rgba(0,255,255,0.0); } 50% { transform: scale(1.02); box-shadow: 0 0 12px rgba(0,255,255,0.08); } 100% { transform: scale(1); box-shadow: 0 0 0 rgba(0,255,255,0.0); } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)


try:
    import os
    logo_path = os.path.join(os.path.dirname(__file__), "unnamed-removebg-preview (1).png")
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([2,1,2])
        with col2:
            st.image(logo_path, width=180, use_container_width=False)
    else:
        st.warning("Logo file not found. Please ensure 'unnamed-removebg-preview (1).png' exists in the same directory.")
except Exception as e:
    st.error(f"Could not load logo: {str(e)}")
    import traceback
    st.error(f"Error details: {traceback.format_exc()}")

st.markdown("""
<h1 class='big-title glow'>NetPulse: Real-Time Network Traffic Monitor</h1>
<p class='subtitle fade-in'>Visualize your network in real-time with protocol insights, packet sizes, and live bandwidth stats.</p>
""", unsafe_allow_html=True)


st.markdown("<div style='display: flex; justify-content: center; gap: 2rem; margin: 2rem 0;'>", unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])

if col_btn1.button("🚀 Start Capture"):
    if not capture_running:
        capture_running = True
        capture_thread = threading.Thread(target=start_sniffing, daemon=True)
        capture_thread.start()
        st.success("✅ Packet capture started!")
    else:
        st.warning("⚠️ Capture already running!")

if col_btn2.button("⏹️ Stop Capture"):
    capture_running = False
    st.info("🛑 Capture stopped! You can still view captured data.")

if col_btn3.button("🧹 Clear Data"):
    packets_data.clear()
    st.warning("🧹 Data cleared successfully!")

st.markdown("</div>", unsafe_allow_html=True)

st.divider()


net_io = psutil.net_io_counters()
col1, col2, col3 = st.columns(3)
col1.markdown(f"<div class='metric-box pulse'><h3>📤 Bytes Sent</h3><p>{net_io.bytes_sent / 1024**2:.2f} MB</p></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box pulse'><h3>📥 Bytes Received</h3><p>{net_io.bytes_recv / 1024**2:.2f} MB</p></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-box pulse'><h3>🔌 Active Connections</h3><p>{len(psutil.net_connections())}</p></div>", unsafe_allow_html=True)

st.divider()

# Auto-refresh functionality
if 'refresh_key' not in st.session_state:
    st.session_state['refresh_key'] = 0

# Display packets and visualizations
if packets_data:
    df = pd.DataFrame(packets_data)
    df['proto'] = df['proto'].astype(str)

    st.subheader("📡 Latest Captured Packets")
    st.dataframe(
        df.tail(10),
        hide_index=False,
        use_container_width=True
    )

    fig1 = px.line(df.tail(100), x='timestamp', y='len', color='proto',
                   title="📈 Live Packet Size Over Time",
                   color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig1, use_container_width=True)

    proto_counts = df['proto'].value_counts().reset_index()
    proto_counts.columns = ['Protocol', 'Count']
    fig2 = px.pie(proto_counts, names='Protocol', values='Count',
                  title="📊 Protocol Usage Distribution",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("💬 Top Communicating IPs")
    top_ips = df['src'].value_counts().reset_index()
    top_ips.columns = ['Source IP','Packets']
    st.bar_chart(top_ips.head(5).set_index('Source IP'))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Save Captured Data as CSV", csv, "network_capture.csv", "text/csv")
else:
    st.info("🔍 No packets captured yet. Click **Start Capture** to begin.")

st.divider()
st.caption("✨ Built with Streamlit • Plotly • Scapy • psutil | Designed by Pranav 💫")
