import type { Person } from '../../types';

interface ProfileHeaderProps {
  person: Person;
}

export default function ProfileHeader({ person }: ProfileHeaderProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-secondary-400 flex items-center justify-center text-white text-2xl font-bold">
            {person.full_name
              .split(' ')
              .map((n) => n[0])
              .join('')
              .toUpperCase()
              .slice(0, 2)}
          </div>

          {/* Name and headline */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{person.full_name}</h1>
            {person.headline && (
              <p className="mt-1 text-lg text-gray-600">{person.headline}</p>
            )}
            {person.location && (
              <p className="mt-2 text-sm text-gray-500 flex items-center">
                <span className="mr-1">📍</span>
                {person.location}
              </p>
            )}
          </div>
        </div>

        {/* LinkedIn Link */}
        {person.linkedin_url && (
          <a
            href={person.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <span>in</span>
            <span>LinkedIn</span>
          </a>
        )}
      </div>
    </div>
  );
}

