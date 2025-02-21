import React from 'react';

const FlightCard = ({ flight, rank }) => {
    const formatTime = (dateString) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });
        } catch {
            return 'Time unavailable';
        }
    };

    const calculateDuration = (departure, arrival) => {
        try {
            const start = new Date(departure);
            const end = new Date(arrival);
            const duration = (end - start) / (1000 * 60);
            const hours = Math.floor(duration / 60);
            const minutes = Math.floor(duration % 60);
            return `${hours}h ${minutes}m`;
        } catch (error) {
            return 'Duration unavailable';
        }
    };

    return (
        <div className="bg-white shadow-md rounded-lg p-3 border-l-4 border-green-500 relative h-full">
            <div className="absolute -left-3 -top-3 bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center shadow-lg">
                #{rank}
            </div>
            
            <div className="flex flex-col justify-between h-full">
                <div>
                    <div className="flex justify-between items-center mb-2 mt-2">
                        <div className="text-sm font-semibold text-gray-800">
                            {flight.departure} → {flight.arrival}
                        </div>
                        <div className="text-sm font-bold text-green-600">
                            ${flight.price.toLocaleString('en-IN')}
                        </div>
                    </div>
                    
                    <div className="grid grid-cols-1 gap-2">
                        <div>
                            <div className="text-xs text-gray-600">Departure</div>
                            <div className="text-xs font-medium">
                                {formatTime(flight.departure_time)}
                            </div>
                        </div>
                        <div>
                            <div className="text-xs text-gray-600">Arrival</div>
                            <div className="text-xs font-medium">
                                {formatTime(flight.arrival_time)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="mt-2 text-xs">
                    <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {flight.airline}
                    </span>
                    <span className="ml-2 text-gray-500">
                        {calculateDuration(flight.departure_time, flight.arrival_time)}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default FlightCard;