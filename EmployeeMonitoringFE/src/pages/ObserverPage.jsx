import React, { useState, useEffect } from 'react';
import Sidebar from '../components/layout/Sidebar';
import { getCamerasList } from '../services/MainService';
import { useUser } from '../context/UserContext';
import { FiGrid, FiMaximize, FiMinimize } from 'react-icons/fi';
import VideoCameraFeed from '../components/video/VideoCameraFeed';

const ObserverPage = () => {
    const [cameras, setCameras] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [gridSize, setGridSize] = useState('md'); // 'sm', 'md', 'lg' or 'xl'
    const [focusedCamera, setFocusedCamera] = useState(null);
    const { token } = useUser();

    useEffect(() => {
        const fetchCameras = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await getCamerasList();
                setCameras(response.data.cameras || []);
            } catch (err) {
                console.error("Failed to fetch cameras:", err);
                setError("Failed to load camera list. Please try again later.");
                setCameras([]);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchCameras();
        } else {
            setError("Authentication token not found. Please log in.");
            setLoading(false);
        }
    }, [token]);

    const handleGridChange = (size) => {
        setGridSize(size);
        // Reset focused camera when changing grid
        setFocusedCamera(null);
    };

    const handleCameraClick = (camera) => {
        // Toggle focused state
        if (focusedCamera && focusedCamera.id === camera.id) {
            setFocusedCamera(null);
        } else {
            setFocusedCamera(camera);
        }
    };

    // Define grid columns based on grid size
    const getGridClass = () => {
        if (focusedCamera) {
            return "grid grid-cols-1 lg:grid-cols-2 gap-4";
        }
        
        switch (gridSize) {
            case 'sm':
                return "grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4";
            case 'md':
                return "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-4";
            case 'lg':
                return "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2";
            case 'xl':
                return "grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2";
            default:
                return "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-4";
        }
    };

    return (
        <div className="flex h-screen bg-neutral-900 text-white">
            <Sidebar />
            <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-semibold">Observer Mode</h1>
                    
                    {/* Grid Size Controls */}
                    <div className="flex space-x-2">
                        <button 
                            onClick={() => handleGridChange('sm')}
                            className={`p-2 rounded ${gridSize === 'sm' ? 'bg-cyan-600' : 'bg-neutral-700 hover:bg-neutral-600'}`}
                            title="Fewer cameras, larger views"
                        >
                            <FiMaximize />
                        </button>
                        <button 
                            onClick={() => handleGridChange('md')}
                            className={`p-2 rounded ${gridSize === 'md' ? 'bg-cyan-600' : 'bg-neutral-700 hover:bg-neutral-600'}`}
                            title="Medium grid"
                        >
                            <FiGrid />
                        </button>
                        <button 
                            onClick={() => handleGridChange('xl')}
                            className={`p-2 rounded ${gridSize === 'xl' ? 'bg-cyan-600' : 'bg-neutral-700 hover:bg-neutral-600'}`}
                            title="More cameras, smaller views"
                        >
                            <FiMinimize />
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="text-xl text-neutral-400">Loading cameras...</div>
                    </div>
                ) : error ? (
                    <div className="bg-red-800 border border-red-600 text-red-100 px-4 py-3 rounded relative mb-6" role="alert">
                        <strong className="font-bold">Error:</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                ) : cameras.length === 0 ? (
                     <div className="text-center py-10 text-neutral-500">
                        No cameras found or available.
                    </div>
                ) : (
                    <div className={getGridClass()}>
                        {focusedCamera ? (
                            // Focused camera gets more space
                            <>
                                <div className="lg:col-span-1 xl:col-span-1">
                                    <VideoCameraFeed 
                                        camera={focusedCamera} 
                                        detailed={true}
                                        onClickHandler={handleCameraClick}
                                    />
                                </div>
                                
                                {/* Other cameras */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 lg:col-span-1 xl:col-span-1">
                                    {cameras
                                        .filter(cam => cam.id !== focusedCamera.id)
                                        .map(camera => (
                                            <VideoCameraFeed 
                                                key={camera.id} 
                                                camera={camera} 
                                                detailed={false}
                                                onClickHandler={handleCameraClick}
                                            />
                                        ))
                                    }
                                </div>
                            </>
                        ) : (
                            // All cameras in grid
                            cameras.map(camera => (
                                <VideoCameraFeed 
                                    key={camera.id} 
                                    camera={camera} 
                                    detailed={gridSize === 'sm' || gridSize === 'md'}
                                    onClickHandler={handleCameraClick}
                                />
                            ))
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

export default ObserverPage;