import React from 'react';
import { MoreVertical, Filter } from 'lucide-react';

const CandidatesTable = () => {
    const candidates = [
        { id: 1, name: "Narendra Modi", winRate: "92%", party: "BJP", state: "Varanasi", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/1/1e/Bharatiya_Janata_Party_logo.svg" },
        { id: 2, name: "Rahul Gandhi", winRate: "60%", party: "INC", state: "Wayanad", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/6/6c/Indian_National_Congress_hand_logo.svg" },
        { id: 3, name: "Arvind Kejriwal", winRate: "30%", party: "AAP", state: "New Delhi", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/3/30/Aam_Aadmi_Party_logo_%28English%29.svg" },
        { id: 4, name: "Smriti Irani", winRate: "75%", party: "BJP", state: "Amethi", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/1/1e/Bharatiya_Janata_Party_logo.svg" },
        { id: 5, name: "Shashi Tharoor", winRate: "28%", party: "INC", state: "Thiruvananthapuram", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/6/6c/Indian_National_Congress_hand_logo.svg" },
        { id: 6, name: "Akhilesh Yadav", winRate: "84%", party: "Samajwadi Party (SP)", state: "Uttar Pradesh", partyLogo: "" },
        { id: 7, name: "Chandrababu Naidu", winRate: "55%", party: "Telugu Desam Party (TDP)", state: "Andhra Pradesh", partyLogo: "" },
    ];

    return (
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 mt-8">
            <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-gray-800">All Candidates</h3>
                <div className="flex items-center gap-3">
                    <button className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium">All</button>
                    <button className="text-gray-500 hover:bg-gray-50 px-3 py-1.5 rounded-lg text-sm font-medium">2h</button>
                    <button className="text-gray-500 hover:bg-gray-50 px-3 py-1.5 rounded-lg text-sm font-medium">4h</button>
                    <button className="text-gray-500 hover:bg-gray-50 px-3 py-1.5 rounded-lg text-sm font-medium">8h</button>
                    <button className="text-gray-500 hover:bg-gray-50 px-3 py-1.5 rounded-lg text-sm font-medium">24h</button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-gray-100 text-left">
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">S/N</th>
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Win Rate</th>
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Party</th>
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">State</th>
                            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {candidates.map((candidate, index) => (
                            <tr key={candidate.id} className="hover:bg-gray-50 transition-colors">
                                <td className="py-4 px-4 text-sm text-gray-500">{index + 1}.</td>
                                <td className="py-4 px-4">
                                    <div className="flex items-center gap-3">
                                        <img
                                            src={`https://ui-avatars.com/api/?name=${candidate.name}&background=random`}
                                            alt={candidate.name}
                                            className="w-8 h-8 rounded-full"
                                        />
                                        <span className="font-medium text-gray-900">{candidate.name}</span>
                                    </div>
                                </td>
                                <td className="py-4 px-4 text-sm text-gray-600 font-medium">{candidate.winRate}</td>
                                <td className="py-4 px-4">
                                    <div className="flex items-center gap-2">
                                        {/* Fallback for party logo if empty */}
                                        {candidate.partyLogo ? (
                                            <img src={candidate.partyLogo} alt={candidate.party} className="w-5 h-5 object-contain" />
                                        ) : (
                                            <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-[10px] text-gray-600 font-bold">
                                                {candidate.party[0]}
                                            </div>
                                        )}
                                        <span className="text-sm text-gray-600">{candidate.party}</span>
                                    </div>
                                </td>
                                <td className="py-4 px-4 text-sm text-gray-500">{candidate.state}</td>
                                <td className="py-4 px-4 text-right">
                                    <button className="text-gray-400 hover:text-gray-600">
                                        <MoreVertical size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CandidatesTable;
