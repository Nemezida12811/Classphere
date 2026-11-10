import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import LocationDetailsPage from "./LocationDetailsPage.tsx";
import type { User, Location } from "../components/types.tsx";
import {comfortApi, locationApi} from "../newRestApiService.tsx";

function LocationDetailsWrapper({ user, onLogout }: { user: User | null, onLogout: () => void }) {
    const { locationId } = useParams();
    const navigate = useNavigate();
    const [location, setLocation] = useState<Location | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchFullData = async () => {
            const token = localStorage.getItem('token') || "";
            if (!locationId) return;

            try {
                setIsLoading(true);

                const locData = await locationApi.get(locationId, token);

                const roomPromises = locData.deviceIds.map(async (deviceId: string) => {
                    try {
                        const sensorData = await comfortApi.getLatestSensors(deviceId, token);
                        const comfortData = await comfortApi.getComfortLevel(deviceId, token);

                        return {
                            id: deviceId,
                            name: sensorData.name || `Room ${deviceId.substring(0, 5)}`,
                            metrics: {
                                comfortIndex: comfortData.comfortPercentage,
                            },
                            hideRoom: sensorData.hidden || false
                        };
                    } catch (err) {
                        console.error(`Failed to fetch room ${deviceId}`, err);
                        return null;
                    }
                });

                const resolvedRooms = (await Promise.all(roomPromises)).filter((r): r is any => r !== null);

                setLocation({
                    ...locData,
                    rooms: resolvedRooms
                });

            } catch (err: any) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchFullData();
    }, [locationId]);

    if (isLoading) return <div className="loading-screen">Loading location details...</div>;

    if (error || !location) {
        return (
            <div className="error-screen">
                <h2>{"Location not found"}</h2>
                <button onClick={() => navigate('/locations')}>Back to Locations</button>
            </div>
        );
    }

    return <LocationDetailsPage user={user} location={location} onLogout={onLogout} />;
}

export default LocationDetailsWrapper;