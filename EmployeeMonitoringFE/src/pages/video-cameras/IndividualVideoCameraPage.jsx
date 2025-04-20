import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router';
import Sidebar from "../../components/layout/Sidebar";
import { getCamera } from '../../services/MainService';
import { useUser } from '../../context/UserContext';
import { SERVER_URL } from '../../utils/constants';
import { 
    FiEdit, 
    FiSave, 
    FiPlus, 
    FiTrash, 
    FiSquare, 
    FiGrid, 
    FiArrowLeft, 
    FiMapPin, 
    FiServer,
    FiLink,
    FiLock,
    FiWifi,
    FiTag,
    FiAlertCircle, 
    FiInfo,
    FiRefreshCw
} from 'react-icons/fi';
import axios from 'axios';

const IndividualVideoCameraPage = () => {
    const { cameraId } = useParams();
    const navigate = useNavigate();
    const [camera, setCamera] = useState(null);
    const [zones, setZones] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [currentZone, setCurrentZone] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [streamUrl, setStreamUrl] = useState('');
    const [isStreamActive, setIsStreamActive] = useState(false);
    const [isFaceRecognitionEnabled, setIsFaceRecognitionEnabled] = useState(false);
    const { token } = useUser();
    
    const faceRecognitionSliderRef = useRef(null);
    const videoContainerRef = useRef(null);
    const streamRef = useRef(null);
    const refreshTimerRef = useRef(null);

    const buildStreamUrl = (cameraObj, tokenVal, faceRecEnabled) => {
        if (!cameraObj?.name || !tokenVal) return '';
        let url = `${SERVER_URL}/video-cameras/${cameraObj.name}/stream?token=${tokenVal}`;
        if (faceRecEnabled) url += '&face_recognition=true';
        return url;
    };

    const fetchCameraData = async () => {
        setRefreshing(true);
        setIsStreamActive(false);
        setError(null);
        try {
            const response = await getCamera(cameraId);
            const cam = response.data.camera;
            setCamera(cam);
            console.log(cam)
            const faceRec = cam?.filters?.face_recognition;
            setIsFaceRecognitionEnabled(faceRec);

            setStreamUrl(buildStreamUrl(cam, token, faceRec));
        } catch (err) {
            console.error("Failed to fetch camera details:", err);
            setError("Failed to load camera details. Please try again later.");
            setStreamUrl('');
        } finally {
            setRefreshing(false);
            setLoading(false);
        }
    };

    useEffect(() => {
        if (cameraId && token) {
            fetchCameraData();
            
            refreshTimerRef.current = setInterval(() => {
                if (camera && camera.name) {
                    setIsStreamActive(false);
                    setError(null);
                }
            }, 120000);
            
            return () => {
                if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
            };
        } else {
            setError("Missing camera ID or authentication.");
            setLoading(false);
            setIsStreamActive(false);
            setStreamUrl('');
        }
    }, [cameraId, token]);

    useEffect(() => {
        if (camera && token) {
            setStreamUrl(buildStreamUrl(camera, token, isFaceRecognitionEnabled));
            setIsStreamActive(false);
            setError(null);
        }
    }, [camera, token, isFaceRecognitionEnabled]);

    const handleManualRefresh = () => {
        setLoading(true);
        setIsStreamActive(false);
        setError(null);
        fetchCameraData();
    };

    const handleStreamLoad = () => {
        if (streamRef.current) {
            streamRef.current.style.display = 'block';
        }
        setIsStreamActive(true);
        setError(null);
    };
    
    const handleStreamError = () => {
        setError("Stream unavailable or failed to load. Please check camera status or refresh.");
        setIsStreamActive(false);
        if (streamRef.current) {
            streamRef.current.style.display = 'none';
        }
    };

    const startDrawZone = () => {
        setEditMode(true);
        setIsDrawing(true);
        setCurrentZone({
            id: `temp-${Date.now()}`,
            name: `Zone ${zones.length + 1}`,
            points: []
        });
    };

    const cancelDrawZone = () => {
        setEditMode(false);
        setIsDrawing(false);
        setCurrentZone(null);
    };

    const saveZone = async () => {
        if (currentZone && currentZone.points.length >= 3) {
            try {
                setLoading(true);
                
                const zoneData = {
                    name: currentZone.name,
                    video_camera_id: cameraId,
                    points: currentZone.points
                };
                
                const response = await axios.post(
                    `${SERVER_URL}/zone`,
                    zoneData,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                
                setZones([...zones, {
                    ...currentZone,
                    id: response.data.id || currentZone.id
                }]);
                
                setEditMode(false);
                setIsDrawing(false);
                setCurrentZone(null);
                
            } catch (err) {
                console.error("Failed to save zone:", err);
                setError("Failed to save zone. Please try again.");
            } finally {
                setLoading(false);
            }
        } else {
            setError("A valid zone must have at least 3 points.");
        }
    };

    const deleteZone = async (zoneId) => {
        try {
            setLoading(true);
            
            await axios.delete(
                `${SERVER_URL}/zone/${zoneId}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            
            setZones(zones.filter(zone => zone.id !== zoneId));
            
        } catch (err) {
            console.error("Failed to delete zone:", err);
            setError("Failed to delete zone. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleCanvasClick = (e) => {
        if (!isDrawing || !editMode) return;
        
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        setCurrentZone(prev => ({
            ...prev,
            points: [...prev.points, {x, y}]
        }));
    };

    const polygonPoints = (points) => {
        return points.map(point => `${point.x},${point.y}`).join(' ');
    };

    const handleToggleFaceRecognition = (event) => {
        const newFaceRecognitionState = event.target.checked;
        setIsFaceRecognitionEnabled(newFaceRecognitionState);
    };    

    return (
        <div className="flex h-screen bg-neutral-900 text-white">
            <Sidebar />
            <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto">
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center">
                        <button 
                            onClick={() => navigate('/video-cameras')}
                            className="mr-4 p-2 rounded hover:bg-neutral-800"
                        >
                            <FiArrowLeft size={20} />
                        </button>
                        <h1 className="text-3xl font-semibold">
                            {loading ? 'Loading Camera...' : camera?.name || 'Camera Details'}
                        </h1>
                    </div>
                    
                    {!editMode ? (
                        <div className="flex space-x-2">
                            <button
                                onClick={handleManualRefresh}
                                className="bg-neutral-700 hover:bg-neutral-600 text-white font-bold py-2 px-4 rounded inline-flex items-center transition-colors duration-200"
                            >
                                <FiRefreshCw className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                                Refresh
                            </button>
                            <button
                                onClick={startDrawZone}
                                className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-4 rounded inline-flex items-center transition-colors duration-200"
                            >
                                <FiPlus className="mr-2" />
                                Add Zone
                            </button>
                        </div>
                    ) : (
                        <div className="flex space-x-2">
                            <button
                                onClick={cancelDrawZone}
                                className="bg-neutral-700 hover:bg-neutral-600 text-white font-bold py-2 px-4 rounded inline-flex items-center transition-colors duration-200"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={saveZone}
                                disabled={!currentZone || currentZone.points.length < 3}
                                className={`${
                                    !currentZone || currentZone.points.length < 3 
                                    ? 'bg-cyan-800 cursor-not-allowed' 
                                    : 'bg-cyan-600 hover:bg-cyan-500'
                                } text-white font-bold py-2 px-4 rounded inline-flex items-center transition-colors duration-200`}
                            >
                                <FiSave className="mr-2" />
                                Save Zone
                            </button>
                        </div>
                    )}
                </div>

                {loading && !camera ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="text-xl text-neutral-400">Loading camera data...</div>
                    </div>
                ) : error && !isStreamActive ? (
                    <div className="bg-red-800 border border-red-600 text-red-100 px-4 py-3 rounded relative mb-6" role="alert">
                        <strong className="font-bold">Error:</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                ) : !camera ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="text-xl text-neutral-400">Could not load camera data.</div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 bg-neutral-800 rounded-lg shadow-md p-4">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold">Live Feed with Zones</h2>
                                <div className={`
                                    px-3 py-1 rounded-full text-sm font-medium flex items-center
                                    ${isStreamActive && !error ? 'bg-green-500 text-green-900' : 'bg-red-500 text-red-900'}
                                `}>
                                    <span className={`mr-1 w-2 h-2 rounded-full ${isStreamActive && !error ? 'bg-green-900 animate-pulse' : 'bg-red-900'}`}></span>
                                    {isStreamActive && !error ? 'LIVE' : 'OFFLINE'}
                                </div>
                            </div>
                            
                            <div className="relative aspect-video bg-black" ref={videoContainerRef} onClick={handleCanvasClick}>
                                {streamUrl && camera?.name ? (
                                    <>
                                        <img
                                            ref={streamRef}
                                            key={`stream-${isFaceRecognitionEnabled}-${streamUrl}`}
                                            src={streamUrl}
                                            alt={`Stream from ${camera.name}`}
                                            className="w-full h-full object-cover"
                                            style={{ display: isStreamActive ? 'block' : 'none' }} 
                                            onLoad={handleStreamLoad}
                                            onError={handleStreamError}
                                        />
                                        {!isStreamActive && (
                                            <div className="absolute inset-0 flex items-center justify-center text-neutral-500 bg-black">
                                                {refreshing || (loading && !isStreamActive) ? "Connecting to stream..." : error ? "Stream unavailable" : "Initializing stream..."}
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-neutral-500">
                                        {loading ? "Loading camera data..." : !camera?.name ? "Camera name missing." : "Stream URL not available."}
                                    </div>
                                )}
                                
                                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                                    {zones.map((zone) => (
                                        <polygon
                                            key={zone.id}
                                            points={polygonPoints(zone.points)}
                                            className="fill-cyan-500 fill-opacity-20 stroke-cyan-500 stroke-2"
                                        />
                                    ))}
                                    
                                    {currentZone && currentZone.points.length > 0 && (
                                        <polygon
                                            points={polygonPoints(currentZone.points)}
                                            className="fill-yellow-500 fill-opacity-20 stroke-yellow-500 stroke-2"
                                        />
                                    )}
                                </svg>
                            </div>
                            {editMode && (
                                    <div className="absolute inset-x-0 bottom-4 flex justify-center">
                                        <div className="bg-black bg-opacity-70 text-white px-4 py-2 rounded">
                                            Click to add points. Minimum 3 points needed.
                                        </div>
                                    </div>
                                )}
                            <div className="mt-4">
                                <label className="inline-flex items-center cursor-pointer">
                                    <input 
                                        type="checkbox" 
                                        className="sr-only peer" 
                                        checked={isFaceRecognitionEnabled}
                                        ref={faceRecognitionSliderRef}
                                        onChange={handleToggleFaceRecognition}
                                    />
                                    <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 dark:peer-focus:ring-cyan-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-cyan-600"></div>
                                    <span className="ms-3 text-sm font-medium text-neutral-300">Face Recognition</span>
                                </label>
                            </div>
                        </div>
                        
                        <div className="bg-neutral-800 rounded-lg shadow-md p-4 flex flex-col">
                            <h2 className="text-xl font-semibold mb-4 flex items-center">
                                <FiInfo className="mr-2" />
                                Camera Information
                            </h2>
                            
                            <div className="mb-6 space-y-2">
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiTag className="mr-2" />Name:</span>
                                    <span>{camera?.name}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiMapPin className="mr-2" />Location:</span>
                                    <span>{camera?.location || 'N/A'}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiServer className="mr-2" />IP Address:</span>
                                    <span className="font-mono">{camera?.ip || 'N/A'}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiLink className="mr-2" />Port:</span>
                                    <span className="font-mono">{camera?.port || 'N/A'}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiWifi className="mr-2" />Username:</span>
                                    <span className="font-mono">{camera?.username || 'N/A'}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiLock className="mr-2" />Password:</span>
                                    <span className="font-mono">{camera?.password}</span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiAlertCircle className="mr-2" />Status:</span>
                                    <span className={isStreamActive && !error ? 'text-green-400' : 'text-red-400'}>
                                        {isStreamActive && !error ? 'Active' : error ? 'Error' : 'Inactive'}
                                    </span>
                                </p>
                                <p className="flex justify-between py-2 border-b border-neutral-700">
                                    <span className="text-neutral-400 flex items-center"><FiGrid className="mr-2" />RTSP URL:</span>
                                    <span className="font-mono text-xs">rtsp://{camera?.username}:{camera?.password}@{camera?.ip}:{camera?.port}/stream2</span>
                                </p>
                            </div>
                            
                            <h3 className="text-lg font-semibold mb-2 flex items-center">
                                <FiGrid className="mr-2" />
                                Defined Zones ({zones.length})
                            </h3>
                            
                            {zones.length === 0 ? (
                                <div className="text-center py-4 text-neutral-500 bg-neutral-700/30 rounded">
                                    No zones defined. Click "Add Zone" to create one.
                                </div>
                            ) : (
                                <div className="overflow-y-auto flex-grow">
                                    {zones.map((zone) => (
                                        <div key={zone.id} className="flex items-center justify-between p-3 bg-neutral-700/30 mb-2 rounded">
                                            <div>
                                                <p className="font-medium">{zone.name}</p>
                                                <p className="text-xs text-neutral-400">{zone.points.length} points</p>
                                            </div>
                                            <div className="flex space-x-2">
                                                <button
                                                    className="p-1 text-neutral-400 hover:text-white"
                                                    onClick={() => {/* Edit zone functionality */}}
                                                >
                                                    <FiEdit size={16} />
                                                </button>
                                                <button
                                                    className="p-1 text-neutral-400 hover:text-red-500"
                                                    onClick={() => deleteZone(zone.id)}
                                                >
                                                    <FiTrash size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default IndividualVideoCameraPage;