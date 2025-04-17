import React, { useState, useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { SERVER_URL } from '../utils/constants';

// Component to handle authenticated image fetching
const AuthenticatedImage = ({ employeeId, alt }) => {
  const [imageData, setImageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { token } = useUser();

  useEffect(() => {
    if (!employeeId || !token) {
      setLoading(false);
      return;
    }

    const fetchImage = async () => {
      try {
        // Create a fetch request with authorization headers
        const response = await fetch(`${SERVER_URL}/employees/${employeeId}/profile-picture`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to load image: ${response.status}`);
        }

        // Convert the response to a blob
        const blob = await response.blob();
        
        // Create an object URL from the blob
        const imageUrl = URL.createObjectURL(blob);
        setImageData(imageUrl);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching image:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchImage();

    // Cleanup function to revoke object URL when component unmounts
    return () => {
      if (imageData) {
        URL.revokeObjectURL(imageData);
      }
    };
  }, [employeeId, token]);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-neutral-700">
        <span className="text-xs text-neutral-400">Loading...</span>
      </div>
    );
  }

  if (error || !imageData) {
    // Display initials as fallback
    return (
      <div className="w-full h-full flex items-center justify-center text-neutral-400 bg-neutral-600">
        {alt ? alt.split(' ').map(name => name.charAt(0)).join('') : '?'}
      </div>
    );
  }

  return (
    <img 
      src={imageData} 
      alt={alt}
      className="w-full h-full object-cover"
      onError={() => setError('Failed to load image')}
    />
  );
};

export default AuthenticatedImage;