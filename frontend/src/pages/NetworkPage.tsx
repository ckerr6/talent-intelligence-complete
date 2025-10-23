export default function NetworkPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Network Graph</h1>
        <p className="mt-2 text-gray-600">
          Visualize connections and discover paths to candidates
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Network graph visualization coming soon...</p>
        <p className="mt-2 text-sm text-gray-500">
          Will show: Interactive force-directed graph, 1st/2nd/3rd degree connections, filtering by company/repo
        </p>
      </div>
    </div>
  );
}

