import React from 'react';
import { MapPin, Utensils, Calendar, Bus, Landmark, Info } from 'lucide-react';

const DestinationCard = ({ destination }) => {
    // Handle missing or malformed data
    if (!destination || typeof destination !== 'object') {
        return (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-yellow-800">No destination information available</p>
            </div>
        );
    }

    const {
        location,
        details = {},
        response = ''
    } = destination;

    const sections = [
        {
            title: 'Top Attractions',
            icon: <Landmark className="w-5 h-5" />,
            content: details.attractions,
            type: 'list'
        },
        {
            title: 'Local Cuisine',
            icon: <Utensils className="w-5 h-5" />,
            content: details.cuisine,
            type: 'list'
        },
        {
            title: 'Best Time to Visit',
            icon: <Calendar className="w-5 h-5" />,
            content: details.best_time,
            type: 'text'
        },
        {
            title: 'Transportation',
            icon: <Bus className="w-5 h-5" />,
            content: details.transportation,
            type: 'text'
        },
        {
            title: 'Travel Tips',
            icon: <Info className="w-5 h-5" />,
            content: details.tips,
            type: 'list'
        }
    ];

    const renderSection = (section) => {
        if (!section.content || (Array.isArray(section.content) && !section.content.length)) {
            return null;
        }

        return (
            <div key={section.title} className="space-y-2">
                <h3 className="font-semibold flex items-center gap-2 text-gray-800">
                    {section.icon}
                    {section.title}
                </h3>
                {section.type === 'list' && Array.isArray(section.content) ? (
                    <ul className="space-y-1 list-disc list-inside text-gray-600">
                        {section.content.map((item, idx) => (
                            <li key={idx}>{item}</li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-600">{section.content}</p>
                )}
            </div>
        );
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
            <div className="flex items-center gap-2 border-b pb-4">
                <MapPin className="w-6 h-6 text-green-600" />
                <h2 className="text-2xl font-semibold text-gray-900">{location}</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {sections.map(section => renderSection(section))}
            </div>

            {response && (
                <div className="border-t pt-4 mt-6">
                    <p className="text-gray-700 leading-relaxed">{response}</p>
                </div>
            )}
        </div>
    );
};

const MessageBubble = ({ message }) => {
    const renderContent = () => {
        // Handle destination info
        if (message.query_type === 'destination_info') {
            // Pass the entire message as it contains all the required properties
            return <DestinationCard destination={message} />;
        }
        
        // Handle flights data
        if (message.flights && Array.isArray(message.flights)) {
            return (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {message.flights.map((flight, index) => (
                        <FlightCard 
                            key={flight.id || index} 
                            flight={flight} 
                            rank={index + 1}
                        />
                    ))}
                </div>
            );
        }

        // Handle regular text messages
        if (message.content) {
            return (
                <div className="whitespace-pre-wrap">
                    {message.content}
                </div>
            );
        }

        return null;
    };

    return (
        <div className={`max-w-3xl mx-auto ${message.type === 'user' ? 'ml-auto' : ''}`}>
            <div className={`rounded-lg p-4 mb-4 ${
                message.type === 'user' 
                    ? 'bg-green-100 text-green-900 ml-12' 
                    : 'bg-white shadow-sm border'
            }`}>
                {renderContent()}
            </div>
        </div>
    );
};

export { DestinationCard, MessageBubble };