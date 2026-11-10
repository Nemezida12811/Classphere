import "./forms.css";
import BigButton from "./BigButton";
import Select from "react-select";
import { useState } from "react";


function FormEditRoom({ room, onSave }: any) {
    // Standard Sensor Config States
    const [roomName, setRoomName] = useState(room.name || "");
    const [units, setUnits] = useState("standard");
    const [ntpHost, setNtpHost] = useState("pool.ntp.org");
    const [broker, setBroker] = useState("mqtt.eclipseprojects.io");
    const [ssid, setSsid] = useState("login");
    const [password, setPassword] = useState("password");
    const [interval, setInterval] = useState(10000);

    const unitOptions = [
        { value: "standard", label: "Standard" },
        { value: "metric", label: "Metric" },
        { value: "imperial", label: "Imperial" }
    ];

    const handleSubmit = () => {
        onSave({
            deviceName: roomName,
            measurementUnits: units,
            ntpHost,
            brokerAddress: broker,
            wifi: { ssid, password },
            updateIntervalMs: interval
        });
    };

    return (
        <div className="page">
            <div className="login-card edit-card">
                <h2 className="title-sensor">Sensor Configuration</h2>
                <h3 className="subtitle">Configuring: {room.id}</h3>

                <div className="input-group">
                    <label>Display Name</label>
                    <input type="text" className="input" value={roomName} onChange={(e) => setRoomName(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>Measurement Units</label>
                    <Select
                        options={unitOptions}
                        defaultValue={unitOptions[0]}
                        onChange={(opt) => setUnits(opt?.value || "standard")}
                        className="my-select"
                        classNamePrefix="my-select"
                    />
                </div>

                <div className="input-group">
                    <label>NTP Host (Time Sync)</label>
                    <input type="text" className="input" value={ntpHost} onChange={(e) => setNtpHost(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>MQTT Broker Address</label>
                    <input type="text" className="input" value={broker} onChange={(e) => setBroker(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>WiFi SSID</label>
                    <input type="text" className="input" placeholder="Network Name" value={ssid} onChange={(e) => setSsid(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>WiFi Password</label>
                    <input type="password" className="input" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
                </div>

                <div className="input-group">
                    <label>Update Interval (ms)</label>
                    <input type="number" className="input" value={interval} onChange={(e) => setInterval(Number(e.target.value))} />
                </div>

                <BigButton text="Save Configuration" onClick={handleSubmit} />
            </div>
        </div>
    );
}

export default FormEditRoom;