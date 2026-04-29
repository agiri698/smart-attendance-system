import { useRef, useState } from "react";

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [cameraStarted, setCameraStarted] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [matchedStudent, setMatchedStudent] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [attendanceList, setAttendanceList] = useState([]);

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
    });

    videoRef.current.srcObject = stream;
    setCameraStarted(true);
    setMatchedStudent(null);
    setErrorMessage("");
  };

  const stopCamera = () => {
    const stream = videoRef.current.srcObject;

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }

    videoRef.current.srcObject = null;
    setCameraStarted(false);
    setIsScanning(false);
    setMatchedStudent(null);
    setErrorMessage("");
  };

  const scanFace = async () => {
  setIsScanning(true);
  setMatchedStudent(null);
  setErrorMessage("");

  try {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("image", blob, "captured_face.jpg");

      const response = await fetch("http://127.0.0.1:8000/mark-attendance", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      setTimeout(() => {
        if (data.status === "Present") {
          const student = {
            ...data,
            time: new Date().toLocaleTimeString(),
          };

          setMatchedStudent(student);
          setAttendanceList((prev) => [...prev, student]);
        } else {
          setErrorMessage(data.message || "Face not recognized. Please try again.");
        }

        setIsScanning(false);
      }, 1500);
    }, "image/jpeg");
  } catch (error) {
    setIsScanning(false);
    setErrorMessage("Backend not connected. Please start Python server.");
  }
};

  return (
    <div style={{ textAlign: "center", marginTop: "30px" }}>
      <h1>Smart Attendance System</h1>
      <p>CNN Based Face Recognition Project</p>

      {!cameraStarted && (
        <button onClick={startCamera} style={btn("green")}>
          Mark Attendance
        </button>
      )}

      {cameraStarted && (
        <>
          <button onClick={scanFace} style={btn("blue")}>
            Capture & Scan Face
          </button>

          <button
            onClick={stopCamera}
            style={{ ...btn("crimson"), marginLeft: "10px" }}
          >
            Cancel Camera
          </button>
        </>
      )}

      <br /><br />

      <video
        ref={videoRef}
        autoPlay
        style={{
          width: "400px",
          display: cameraStarted ? "inline-block" : "none",
          border: "3px solid green",
          borderRadius: "10px",
        }}
      />
      <canvas
        ref={canvasRef}
        style={{ display: "none" }}
      />

      {isScanning && <h2> CNN scanning face...</h2>}

      {errorMessage && (
  <h2 style={{ color: "crimson" }}>
    ❌ {errorMessage}
  </h2>
)}

      {matchedStudent && (
  <div style={{ color: "green" }}>
    <h2>✅ Face Matched Successfully</h2>
    <p><b>Name:</b> {matchedStudent.name}</p>
    <p><b>Roll No:</b> {matchedStudent.rollNo}</p>
    <p><b>Confidence:</b> {matchedStudent.confidence}</p>
    <p><b>Status:</b> {matchedStudent.status}</p>
  </div>
)}

      <hr />

      <h2>Attendance Report</h2>

      <table
        border="1"
        style={{
          margin: "auto",
          width: "80%",
          borderCollapse: "collapse",
        }}
      >
        <thead>
          <tr>
            <th>Name</th>
            <th>Roll No</th>
            <th>Status</th>
            <th>Time</th>
          </tr>
        </thead>

        <tbody>
          {attendanceList.map((item, index) => (
            <tr key={index}>
              <td>{item.name}</td>
              <td>{item.rollNo}</td>
              <td>{item.status}</td>
              <td>{item.time}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function btn(color) {
  return {
    padding: "12px 20px",
    fontSize: "16px",
    backgroundColor: color,
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  };
}

export default App;