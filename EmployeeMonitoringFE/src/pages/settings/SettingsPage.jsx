import Sidebar from "../../components/layout/Sidebar"; // Import Sidebar

const SettingsPage = () => {
    return (
        <div className="flex h-screen bg-neutral-900 text-white"> {/* Added layout wrapper */}
            <Sidebar /> {/* Added Sidebar */}
            <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto"> {/* Added main content area */}
                <h1 className="text-3xl font-semibold mb-8">Settings</h1> {/* Added title */}
                <div className="bg-neutral-800 p-6 rounded-lg shadow-md">
                    {/* Placeholder for settings content */}
                    <p>Settings content will go here.</p>
                </div>
            </main>
        </div>
    );
}

export default SettingsPage;