import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged.tsx";
import FormEditRoom from "../components/FormEditRoom.tsx";
import {useNavigate} from "react-router-dom";


function EditRoom({ room, user, onLogout }: any) {
    const navigate = useNavigate();

    const handleSave = async (configData: any) => {
        console.log("SENDING REMOTE CONFIG TO SENSOR:", configData);

        // PREVIEW MODE: Simulate a 1.5s delay for the sensor to acknowledge config
        const saveSimulation = new Promise((resolve) => setTimeout(resolve, 1500));

        try {
            await saveSimulation;
            alert("Configuration sent to sensor successfully!");
            navigate(`/locations/${room.location.id}/${room.id}`);
        } catch (error) {
            alert("Failed to reach sensor.");
        }
    };

    return (
        <div className="content">
            <HeaderLogged username={user.username} onLogout={onLogout} onLogoClick={() => navigate('/locations')} />
            <BackButton text="Back" transparent onClick={() => navigate(-1)} />
            <FormEditRoom room={room} onSave={handleSave} />
            <Footer/>
        </div>
    );
}

export default EditRoom;
