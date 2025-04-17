import React, { useState, useEffect } from 'react';
import { Link } from 'react-router';
import Sidebar from "../../components/layout/Sidebar";
import { getAlerts } from '../../services/MainService';
import { useUser } from '../../context/UserContext';
import { FiAlertTriangle, FiCheckCircle, FiFilter, FiRefreshCw } from 'react-icons/fi';

const AlertsPage = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'active', 'resolved'
    const { token } = useUser();

    useEffect(() => {
        fetchAlerts();
    }, [token, filterStatus]);

    const fetchAlerts = async () => {
        setLoading(true);
        setError(null);
        try {
            // Add status filter if not 'all'
            const params = filterStatus !== 'all' ? { status: filterStatus } : {};
            const response = await getAlerts(params);
            setAlerts(response.data.alerts || []);
        } catch (err) {
            console.error("Failed to fetch alerts:", err);
            setError("Failed to load alerts. Please try again later.");
            setAlerts([]);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (status) => {
        setFilterStatus(status);
    };

    // Format timestamp to readable date/time
    const formatTimestamp = (isoString) => {
        if (!isoString) return 'N/A';
        try {
            return new Date(isoString).toLocaleString();
        } catch (e) {
            return isoString;
        }
    };

    // Calculate alert statistics
    const alertStats = {
        total: alerts.length,
        active: alerts.filter(alert => alert.status === 'active').length,
        resolved: alerts.filter(alert => alert.status === 'resolved').length
    };

    // Component for statistics card
    const StatCard = ({ icon, title, value, bgColor, iconBgColor }) => (
        <div className={`${bgColor} p-5 rounded-lg shadow-md mb-4`}>
            <div className="flex items-center mb-2">
                <div className={`${iconBgColor} p-3 rounded-md mr-4`}>
                    {icon}
                </div>
                <div className="flex-1">
                    <span className="text-lg font-semibold block">{title}</span>
                    <div className="text-2xl font-bold">{value}</div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="flex h-screen bg-neutral-900 text-white">
            <Sidebar />
            <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-semibold">Security Alerts</h1>
                    <button
                        onClick={fetchAlerts}
                        className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-4 rounded inline-flex items-center transition-colors duration-200"
                    >
                        <FiRefreshCw className="mr-2" />
                        Refresh
                    </button>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                    <StatCard 
                        icon={<FiAlertTriangle className="h-6 w-6 text-white" />} 
                        title="Total Alerts" 
                        value={alertStats.total}
                        bgColor="bg-neutral-800"
                        iconBgColor="bg-neutral-700"
                    />
                    <StatCard 
                        icon={<FiAlertTriangle className="h-6 w-6 text-white" />} 
                        title="Active Alerts" 
                        value={alertStats.active}
                        bgColor="bg-red-900"
                        iconBgColor="bg-red-700"
                    />
                    <StatCard 
                        icon={<FiCheckCircle className="h-6 w-6 text-white" />} 
                        title="Resolved Alerts" 
                        value={alertStats.resolved}
                        bgColor="bg-green-900"
                        iconBgColor="bg-green-700"
                    />
                </div>

                {/* Filter Controls */}
                <div className="flex items-center mb-4 bg-neutral-800 p-3 rounded-lg">
                    <FiFilter className="mr-2 text-neutral-400" />
                    <span className="mr-4 text-neutral-300">Filter:</span>
                    <button
                        onClick={() => handleFilterChange('all')}
                        className={`px-3 py-1 mr-2 rounded ${filterStatus === 'all' ? 'bg-cyan-600 text-white' : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'}`}
                    >
                        All
                    </button>
                    <button
                        onClick={() => handleFilterChange('active')}
                        className={`px-3 py-1 mr-2 rounded ${filterStatus === 'active' ? 'bg-red-600 text-white' : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'}`}
                    >
                        Active
                    </button>
                    <button
                        onClick={() => handleFilterChange('resolved')}
                        className={`px-3 py-1 rounded ${filterStatus === 'resolved' ? 'bg-green-600 text-white' : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'}`}
                    >
                        Resolved
                    </button>
                </div>

                {/* Loading State */}
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="text-xl text-neutral-400">Loading alerts...</div>
                    </div>
                /* Error State */
                ) : error ? (
                    <div className="bg-red-800 border border-red-600 text-red-100 px-4 py-3 rounded relative mb-6" role="alert">
                        <strong className="font-bold">Error:</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                /* No Alerts Found */
                ) : alerts.length === 0 ? (
                     <div className="text-center py-10 text-neutral-500 bg-neutral-800 rounded-lg">
                        No alerts found matching the current filter.
                    </div>
                ) : (
                    /* Alerts Table */
                    <div className="bg-neutral-800 rounded-lg shadow-md overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left table-auto">
                                <thead className="bg-neutral-700 text-neutral-200">
                                    <tr>
                                        <th className="px-4 py-3">Timestamp</th>
                                        <th className="px-4 py-3">Type</th>
                                        <th className="px-4 py-3">Level</th>
                                        <th className="px-4 py-3">Camera/Zone</th>
                                        <th className="px-4 py-3">Status</th>
                                        <th className="px-4 py-3">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {alerts.map((alert) => (
                                        <tr key={alert.id} className="border-b border-neutral-700 hover:bg-neutral-700/50 transition-colors">
                                            <td className="px-4 py-3">{formatTimestamp(alert.timestamp)}</td>
                                            <td className="px-4 py-3 whitespace-nowrap">{alert.type}</td>
                                            <td className="px-4 py-3 capitalize">{alert.level}</td>
                                            <td className="px-4 py-3">{alert.camera_name || alert.zone_id || 'N/A'}</td>
                                            <td className={`px-4 py-3 capitalize ${
                                                alert.status === 'active' ? 'text-red-400' : 'text-green-400'
                                            }`}>
                                                {alert.status}
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                <Link to={`/alerts/${alert.id}`} className="text-cyan-400 hover:text-cyan-300 text-sm">
                                                    View
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default AlertsPage;