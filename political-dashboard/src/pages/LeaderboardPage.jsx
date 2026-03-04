import React from 'react';
import CountdownCarousel from '../components/dashboard/CountdownCarousel';
import CandidateCard from '../components/dashboard/CandidateCard';
import CandidatesTable from '../components/dashboard/CandidatesTable';

const topCandidates = [
    { name: "Narendra Modi", party: "BJP", image: "https://ui-avatars.com/api/?name=TN&background=random", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/1/1e/Bharatiya_Janata_Party_logo.svg", popularity: 70, winRate: 92, polls: 60, position: 80 },
    { name: "Rahul Gandhi", party: "INC", image: "https://ui-avatars.com/api/?name=RG&background=random", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/6/6c/Indian_National_Congress_hand_logo.svg", popularity: 40, winRate: 60, polls: 30, position: 40 },
    { name: "Arvind Kejriwal", party: "AAP", image: "https://ui-avatars.com/api/?name=AK&background=random", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/3/30/Aam_Aadmi_Party_logo_%28English%29.svg", popularity: 40, winRate: 30, polls: 30, position: 20 },
    { name: "Smriti Irani", party: "BJP", image: "https://ui-avatars.com/api/?name=SI&background=random", partyLogo: "https://upload.wikimedia.org/wikipedia/commons/1/1e/Bharatiya_Janata_Party_logo.svg", popularity: 83, winRate: 75, polls: 50, position: 60 },
];

const LeaderboardPage = () => {
    return (
        <div className="space-y-6">
            <CountdownCarousel />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {topCandidates.map((c, i) => (
                    <CandidateCard key={i} {...c} />
                ))}
            </div>
            <CandidatesTable />
        </div>
    );
};

export default LeaderboardPage;
