import React, { useState, useEffect } from 'react';
import { Link } from 'react-router'; // Updated import
import Sidebar from "../components/layout/Sidebar";
import { FiAlertTriangle, FiVideo, FiUsers, FiShield, FiArrowRightCircle } from 'react-icons/fi';
import { getAlerts, getCamerasList, getAllEmployees, getAllSecurity } from '../services/MainService';



// Helper to format timestamp
const formatTimestamp = (isoString) => {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleString();
    } catch (e) {
        return isoString; // Return original if parsing fails
    }
};

// Reusable Card Component - Updated Styling
const DashboardCard = ({ icon, title, value, linkTo, linkText = "View Details", bgColor = 'bg-neutral-700', iconBgColor = 'bg-cyan-600' }) => (
    <div className={`${bgColor} p-6 rounded-lg shadow-md text-white flex flex-col justify-between hover:brightness-110 transition-all duration-200`}>
        <div className="flex items-start justify-between mb-4">
            {/* Icon in a square */}
            <div className={`p-3 rounded-md ${iconBgColor}`}>
                 <div className="text-2xl">{icon}</div>
            </div>
            <h3 className="text-lg font-semibold text-right ml-2">{title}</h3>
        </div>
        <div className="text-3xl font-bold mb-4 text-right">{value}</div>
        <Link to={linkTo} className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center self-start mt-auto">
            {linkText} <FiArrowRightCircle className="ml-1" />
        </Link>
    </div>
);

const HomePage = () => {
    const [unresolvedAlerts, setUnresolvedAlerts] = useState(0);
    const [cameraCounts, setCameraCounts] = useState({ active: 0, inactive: 0 });
    const [employeeCount, setEmployeeCount] = useState(0);
    const [securityCount, setSecurityCount] = useState(0);
    const [latestAlerts, setLatestAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            setError(null); // Reset error on new load
            try {
                // Fetch unresolved alerts count
                const alertsResponse = await getAlerts({ status: 'active' });
                setUnresolvedAlerts(alertsResponse.data.alerts?.length || 0);

                // Fetch camera status
                const camerasResponse = await getCamerasList();
                // Assuming response format is { cameras: [{ status: 'active'/'inactive', ... }] }
                // Adjust based on actual API response structure
                const cams = camerasResponse.data.cameras || [];
                const activeCams = cams.filter(cam => cam.status === 'active').length; // Adjust property name if needed
                const inactiveCams = cams.length - activeCams;
                setCameraCounts({ active: activeCams, inactive: inactiveCams });

                // Fetch employee count
                const employeesResponse = await getAllEmployees();
                setEmployeeCount(employeesResponse.data.employees?.length || 0);

                // Fetch security count
                const securityResponse = await getAllSecurity();
                setSecurityCount(securityResponse.data.length || 0);

                // Fetch latest alerts (e.g., last 5, assuming default sort is latest first or add sort param)
                const latestAlertsResponse = await getAlerts({ /* Add limit/sort if available */ });
                // Ensure alerts is an array before slicing
                const alertsData = latestAlertsResponse.data.alerts || [];
                setLatestAlerts(alertsData.slice(0, 5));

            } catch (err) {
                console.error("Failed to fetch dashboard data:", err);
                setError("Failed to load dashboard data. Please try again later.");
                // Set default/empty states on error?
                setUnresolvedAlerts(0);
                setCameraCounts({ active: 0, inactive: 0 });
                setEmployeeCount(0);
                setSecurityCount(0);
                setLatestAlerts([]);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    return (
        <div className="flex h-screen bg-neutral-900 text-white">
            <Sidebar />
            <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto">
                <h1 className="text-3xl font-semibold mb-8">Dashboard Overview</h1>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="text-xl text-neutral-400">Loading dashboard data...</div>
                        {/* Optional: Add a spinner here */}
                    </div>
                ) : error ? (
                     <div className="bg-red-800 border border-red-600 text-red-100 px-4 py-3 rounded relative mb-6" role="alert">
                        <strong className="font-bold">Error:</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                ) : (
                    <>
                        {/* Cards Section - Added different background colors */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <DashboardCard
                                icon={<FiAlertTriangle />}
                                title="Unresolved Alerts"
                                value={unresolvedAlerts}
                                linkTo="/alerts"
                                linkText="View Alerts"
                                bgColor="bg-red-800" // Example color
                                iconBgColor="bg-red-600"
                            />
                            <DashboardCard
                                icon={<FiVideo />}
                                title="Camera Status"
                                value={
                                    <div className="text-lg text-right"> {/* Smaller text, right aligned */}
                                        <p>Active: <span className="font-bold">{cameraCounts.active}</span></p>
                                        <p>Inactive: <span className="font-bold">{cameraCounts.inactive}</span></p>
                                    </div>
                                }
                                linkTo="/video-cameras"
                                linkText="Manage Cameras"
                                bgColor="bg-blue-800" // Example color
                                iconBgColor="bg-blue-600"
                            />
                            <DashboardCard
                                icon={<FiUsers />}
                                title="Total Employees"
                                value={employeeCount}
                                linkTo="/employees"
                                linkText="View Employees"
                                bgColor="bg-green-800" // Example color
                                iconBgColor="bg-green-600"
                            />
                            <DashboardCard
                                icon={<FiShield />}
                                title="Security Personnel"
                                value={securityCount}
                                linkTo="/security" // Link might need adjustment
                                linkText="View Security"
                                bgColor="bg-yellow-800" // Example color
                                iconBgColor="bg-yellow-600"
                            />
                        </div>

                        {/* Latest Alerts Table - Removed Actions column */}
                        <div className="bg-neutral-800 p-6 rounded-lg shadow-md">
                            <h2 className="text-xl font-semibold mb-4">Latest Alerts</h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left table-auto">
                                    <thead className="border-b border-neutral-600">
                                        <tr>
                                            <th className="px-4 py-2">Timestamp</th>
                                            <th className="px-4 py-2">Type</th>
                                            <th className="px-4 py-2">Level</th>
                                            <th className="px-4 py-2">Zone ID</th> {/* Assuming zone_id is available */}
                                            <th className="px-4 py-2">Status</th>
                                            <th className="px-4 py-2 text-right">Details</th> {/* Header for details link */}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {latestAlerts.length > 0 ? (
                                            latestAlerts.map((alert) => (
                                                <tr key={alert.id} className="border-b border-neutral-700 hover:bg-neutral-700/50 transition-colors">
                                                    <td className="px-4 py-2">{formatTimestamp(alert.timestamp)}</td>
                                                    <td className="px-4 py-2 whitespace-nowrap">{alert.type}</td>
                                                    <td className="px-4 py-2 capitalize">{alert.level}</td> {/* Use actual level */}
                                                    <td className="px-4 py-2">{alert.zone_id ?? 'N/A'}</td> {/* Use actual zone_id */}
                                                    <td className={`px-4 py-2 capitalize ${alert.status === 'active' ? 'text-red-400' : 'text-green-400'}`}>
                                                        {alert.status}
                                                    </td>
                                                    <td className="px-4 py-2 text-right"> {/* Cell for details link */}
                                                        <Link to={`/alerts/${alert.id}`} className="text-cyan-400 hover:text-cyan-300 text-sm">
                                                            View
                                                        </Link>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="6" className="text-center py-4 text-neutral-500">No recent alerts found.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                             {/* Link to view all alerts - check if total count > displayed count if possible */}
                             <div className="mt-4 text-right">
                                <Link to="/alerts" className="text-cyan-400 hover:text-cyan-300 text-sm flex items-center justify-end">
                                    View All Alerts <FiArrowRightCircle className="ml-1" />
                                </Link>
                            </div>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
export default HomePage;