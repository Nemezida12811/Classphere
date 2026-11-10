import "./Log.css";
import Footer from "../components/Footer";
import BackButton from "../components/BackButton";
import HeaderLogged from "../components/HeaderLogged.tsx";
import FormAddRoom from "../components/FormAddRoom.tsx";
import {Navigate, useNavigate} from "react-router-dom";
import type {Location, User} from "../components/types.tsx";
import {locationApi} from "../newRestApiService.tsx";

type AddRoomProps = {
    currentLocationId?: string;
    availableLocations: Location[];
    user: User | null;
    onLogout: () => void;
};

function AddRoom({ currentLocationId, availableLocations, user, onLogout }: AddRoomProps) {
    const navigate = useNavigate();

    if (!user || !localStorage.getItem('token')) return <Navigate to="/login" replace />;

    const handleCreate = async (formData: any) => {
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            // Use the locationId chosen from the dropdown
            await locationApi.addDevice(
                formData.locationId,
                formData.deviceId,
                formData.name,
                token
            );

            if (formData.hideRoom) {
                await locationApi.hideDevice(formData.locationId, formData.deviceId, token);
            }

            alert("Room added successfully!");
            navigate(`/locations/${formData.locationId}`);
        } catch (error: any) {
            alert(error.message || "Failed to add room.");
        }
    };

    return (
        <div className="content">
            <HeaderLogged
                username={user.username}
                onLogout={onLogout}
                onLogoClick={() => navigate('/locations')}
            />
            <BackButton text="Back" transparent onClick={() => navigate(-1)} />
            <FormAddRoom
                locations={availableLocations}
                defaultLocationId={currentLocationId}
                onSave={handleCreate}
            />
            <Footer />
        </div>
    );
}

export default AddRoom;
