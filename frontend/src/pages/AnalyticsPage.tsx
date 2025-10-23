import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AnalyticsPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to Market Intelligence page
    navigate('/market', { replace: true });
  }, [navigate]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <p className="text-gray-600">Redirecting to Market Intelligence...</p>
      </div>
    </div>
  );
}

